import asyncio
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from bson import ObjectId
from loguru import logger

from app.models.schemas import ProcessContributionRequest, ProcessContributionResponse, ErrorResponse
from app.services.database import get_database, DatabaseService
from app.services.ai_service import AIService
from app.config import settings


router = APIRouter()
security = HTTPBearer()


def verify_webhook_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify the Bearer token for webhook authentication"""
    if credentials.credentials != settings.forge_ai_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials.credentials


# Initialize AI service
ai_service = AIService(
    api_key=settings.openrouter_api_key
)


@router.post("/webhook/process-contribution", response_model=ProcessContributionResponse)
async def process_contribution_webhook(
    request: ProcessContributionRequest,
    background_tasks: BackgroundTasks,
    db: DatabaseService = Depends(get_database),
    token: str = Depends(verify_webhook_token)
):
    """
    Webhook endpoint to receive and process new contributions from the SvelteKit BFF.
    This implements the PoC architecture's asynchronous handoff mechanism.
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


async def process_contribution_background(db: DatabaseService, forge_id: ObjectId, contribution_id: ObjectId):
    """
    Background task that performs the actual AI processing.
    This implements the AI triage and action system from the architecture.
    """
    try:
        await ai_service.process_contribution(db, forge_id, contribution_id)
        logger.info(f"Successfully processed contribution {contribution_id}")
        
    except Exception as e:
        logger.error(f"Error in background processing for contribution {contribution_id}: {e}")
        # In a production system, you might want to:
        # - Retry failed tasks
        # - Send error notifications
        # - Update contribution status to "failed"


@router.get("/webhook/health")
async def webhook_health():
    """Health check endpoint for the webhook service"""
    return {
        "status": "healthy",
        "service": "forge-ai-webhook",
        "ai_configuration": "Dynamic - models configured per prompt in database"
    } 