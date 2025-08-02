from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.schemas import ChatRequest, ChatResponse, ErrorResponse
from app.services.db_service import db_service
from app.services.llm_service import llm_service
from app.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Security scheme for Bearer token
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify the Bearer token"""
    if credentials.credentials != settings.forge_ai_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials.credentials

@router.post("/chat", response_model=ChatResponse)
async def handle_chat(request: ChatRequest, token: str = Depends(verify_token)):
    """Handle chat messages - both context additions and questions"""
    try:
        logger.info(f"Processing chat for forge: {request.forge_id}, role: {request.role_id}, question: {request.is_question}")
        
        # Get current state from database
        state = await db_service.get_app_state(request.forge_id)
        
        # Find the role
        role = None
        for r in state["roles"]:
            if r["id"] == request.role_id:
                role = r
                break
        
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        
        # Add user message to chat
        role_chat = await db_service.add_chat_message(
            request.forge_id, 
            request.role_id, 
            request.message, 
            "user"
        )
        
        if not role_chat:
            raise HTTPException(status_code=500, detail="Failed to save chat message")
        
        ai_response = None
        
        if request.is_question:
            # Generate AI response for questions
            logger.info("Generating AI response for question")
            
            # Get current briefing for context
            latest_synthesis = None
            if state.get("syntheses"):
                latest_synthesis = state["syntheses"][-1]
            
            current_briefing = "No current briefing"
            if latest_synthesis and state.get("todos", {}).get(latest_synthesis["id"]):
                briefings = state["todos"][latest_synthesis["id"]]
                for briefing in briefings:
                    if briefing["roleId"] == request.role_id:
                        current_briefing = briefing["briefing"]
                        break
            
            synthesis_content = latest_synthesis["content"] if latest_synthesis else "No current project context"
            
            # Generate response
            ai_response = await llm_service.generate_chat_response(
                role_chat["messages"],
                role,
                current_briefing,
                synthesis_content
            )
            
            if ai_response:
                # Add AI response to chat
                updated_role_chat = await db_service.add_chat_message(
                    request.forge_id,
                    request.role_id,
                    ai_response,
                    "ai"
                )
                if updated_role_chat:
                    role_chat = updated_role_chat
        
        # Always add to contributions for synthesis
        if request.is_question and ai_response:
            # For questions, add both the question and answer
            contribution_text = f"Question: {request.message}\n\nAI Facilitator Response: {ai_response}"
        else:
            # For context, just add the message
            contribution_text = request.message
        
        success = await db_service.add_contribution(request.forge_id, request.role_id, contribution_text)
        if not success:
            logger.warning("Failed to add contribution to database")
        
        logger.info(f"Chat processed successfully for forge: {request.forge_id}")
        
        return ChatResponse(
            success=True,
            message="Chat message processed successfully",
            ai_response=ai_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat processing: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") 