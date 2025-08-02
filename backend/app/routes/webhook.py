import asyncio
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from bson import ObjectId
from loguru import logger

from app.models.schemas import ProcessContributionRequest, ProcessContributionResponse, ErrorResponse
from app.services.database import get_database, DatabaseService
from app.services.ai_service import AIService
from app.config import settings


router = APIRouter(
    prefix="/webhook",
    tags=["Webhook Processing"],
    responses={
        400: {"description": "Invalid request format"},
        401: {"description": "Invalid or missing authentication token"},
        404: {"description": "Resource not found"}
    }
)

security = HTTPBearer()


def verify_webhook_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify the Bearer token for webhook authentication"""
    if credentials.credentials != settings.forge_ai_api_key:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    return credentials.credentials


# Initialize AI service
ai_service = AIService(api_key=settings.openrouter_api_key)


@router.post(
    "/process-contribution",
    response_model=ProcessContributionResponse,
    summary="Process New Contribution",
    description="Webhook endpoint to process new user contributions through the AI triage system"
)
async def process_contribution_webhook(
    request: ProcessContributionRequest,
    background_tasks: BackgroundTasks,
    db: DatabaseService = Depends(get_database),
    token: str = Depends(verify_webhook_token)
):
    """
    **Main AI Processing Webhook** - Processes new contributions through the AI system.
    
    This endpoint implements the core AI workflow:
    1. **Triage**: Analyze contribution to decide next action
    2. **Action**: Execute direct response or full synthesis based on triage
    
    **Authentication Required**: Bearer token in Authorization header
    
    **Workflow:**
    - Validates contribution and forge exist
    - Queues AI processing as background task
    - Returns immediate 200 OK response
    - AI processing happens asynchronously
    
    **Request Body:**
    ```json
    {
      "forgeId": "507f1f77bcf86cd799439011",
      "newContributionId": "507f1f77bcf86cd799439012"
    }
    ```
    """
    try:
        # Validate ObjectIds
        try:
            forge_id = ObjectId(request.forgeId)
            contribution_id = ObjectId(request.newContributionId)
        except Exception as e:
            logger.error(f"Invalid ObjectId in request: {e}")
            raise HTTPException(status_code=400, detail="Invalid forge or contribution ID format")
        
        # Verify the contribution exists
        contribution = await db.get_contribution_by_id(contribution_id)
        if not contribution:
            logger.error(f"Contribution {contribution_id} not found")
            raise HTTPException(status_code=404, detail="Contribution not found")
        
        # Verify the forge exists  
        forge = await db.get_forge_by_id(forge_id)
        if not forge:
            logger.error(f"Forge {forge_id} not found")
            raise HTTPException(status_code=404, detail="Forge not found")
        
        logger.info(f"Received webhook for contribution {contribution_id} in forge {forge_id}")
        
        # Add the AI processing task to background tasks
        # This allows us to return a fast 200 OK response while the AI work happens asynchronously
        background_tasks.add_task(
            process_contribution_background,
            db, forge_id, contribution_id
        )
        
        return ProcessContributionResponse(
            status="accepted",
            message="Contribution processing started",
            contributionId=str(contribution_id)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/health",
    summary="Webhook Health Check",
    description="Health check endpoint specifically for webhook service status"
)
async def webhook_health():
    """
    **Webhook Service Health** - Quick health check for webhook processing capability.
    
    Returns webhook service status and AI configuration information.
    Useful for monitoring and debugging webhook processing issues.
    """
    return {
        "status": "healthy",
        "service": "forge-ai-webhook",
        "ai_configuration": "Dynamic - models configured per prompt in database",
        "authentication": "Bearer token required",
        "processing": "Asynchronous background tasks"
    }


async def process_contribution_background(db: DatabaseService, forge_id: ObjectId, contribution_id: ObjectId):
    """
    **Background AI Processing Task**
    
    Implements the multi-stage AI processing pipeline:
    1. Triage contribution to determine action
    2. Execute appropriate AI response (direct answer or synthesis)
    3. Store results back to database
    
    This runs asynchronously after webhook returns 200 OK.
    """
    try:
        await ai_service.process_contribution(db, forge_id, contribution_id)
        logger.info(f"Successfully processed contribution {contribution_id}")
        
    except Exception as e:
        logger.error(f"Error in background AI processing for contribution {contribution_id}: {e}")
        # In a production system, you might want to:
        # - Retry failed tasks
        # - Send error notifications
        # - Update contribution status to indicate failure 