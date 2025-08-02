from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.schemas import SynthesizeRequest, SynthesizeResponse, ErrorResponse
from app.services.db_service import db_service
from app.services.llm_service import llm_service
from app.config import settings
from datetime import datetime
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

@router.post("/synthesize", response_model=SynthesizeResponse)
async def synthesize_conversation(request: SynthesizeRequest, token: str = Depends(verify_token)):
    """Process a forge conversation and generate synthesis + individual briefings"""
    try:
        logger.info(f"Starting synthesis for forge: {request.forge_id}")
        
        # Get current state from database
        state = await db_service.get_app_state(request.forge_id)
        
        if not state.get("contributions"):
            raise HTTPException(status_code=400, detail="No contributions found to synthesize")
        
        # Prepare context for LLM
        contributions_text = "\n\n".join([
            f"{c['authorName']} ({c['authorTitle']}): {c['text']}"
            for c in state["contributions"]
        ])
        
        roles_text = "\n".join([
            f"- {r['name']}: {r['title']} (ID: {r['id']})"
            for r in state["roles"]
        ])
        
        # Generate synthesis using LLM
        logger.info("Calling LLM for synthesis")
        parsed_synthesis = await llm_service.synthesize_conversation(
            state["goal"], 
            roles_text, 
            contributions_text
        )
        
        if not parsed_synthesis:
            raise HTTPException(status_code=500, detail="Failed to generate synthesis")
        
        # Create synthesis record
        synthesis_id = str(int(datetime.now().timestamp() * 1000))
        synthesis_record = {
            "id": synthesis_id,
            "content": parsed_synthesis["overallContext"],
            "sourceContributions": [c["id"] for c in state["contributions"]],
            "timestamp": datetime.now().isoformat(),
        }
        
        # Save synthesis to database
        success = await db_service.add_synthesis(request.forge_id, synthesis_record)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save synthesis")
        
        # Create individual briefings
        briefings = []
        for role in state["roles"]:
            individual_briefing = parsed_synthesis["individualBriefings"].get(role["id"])
            if not individual_briefing:
                logger.warning(f"No briefing found for role {role['id']}")
                briefing_text = f"Hi {role['name']}, no specific briefing was generated for your role. Please check the overall context."
            else:
                # Combine all parts of the individual briefing
                briefing_text = individual_briefing["briefing"]
                
                if individual_briefing.get("questions"):
                    briefing_text += "\n\n**Questions:**\n" + "\n".join([
                        f"- {q}" for q in individual_briefing["questions"]
                    ])
                
                if individual_briefing.get("todos"):
                    briefing_text += "\n\n**Next Steps:**\n" + "\n".join([
                        f"- {t}" for t in individual_briefing["todos"]
                    ])
                
                if individual_briefing.get("priorities"):
                    briefing_text += f"\n\n**Priority:** {individual_briefing['priorities']}"
            
            briefings.append({
                "roleId": role["id"],
                "briefing": briefing_text
            })
        
        # Save briefings to database
        success = await db_service.add_todos(request.forge_id, synthesis_id, briefings)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save briefings")
        
        logger.info(f"Synthesis completed successfully for forge: {request.forge_id}")
        
        return SynthesizeResponse(
            success=True,
            message="Synthesis completed successfully",
            synthesis_id=synthesis_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in synthesis: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") 