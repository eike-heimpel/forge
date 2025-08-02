import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from openai import AsyncOpenAI
from bson import ObjectId
from loguru import logger

from app.models.schemas import (
    Contribution, ContributionType, TriageAction, TriageResponse,
    UserMessageContent, AIResponseContent, AISynthesisContent, 
    AISynthesisStructured, AIPrompt
)
from app.services.database import DatabaseService


class AIService:
    """Service for AI triage and processing of contributions"""
    
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        self.api_key = api_key
    
    async def process_contribution(self, db: DatabaseService, forge_id: ObjectId, contribution_id: ObjectId):
        """
        Main entry point: Process a new contribution through the AI triage system
        This implements the multi-stage AI process from the architecture
        """
        try:
            logger.info(f"Processing contribution {contribution_id} in forge {forge_id}")
            
            # Stage 1: Triage Decision
            triage_decision = await self._triage_contribution(db, forge_id, contribution_id)
            if not triage_decision:
                logger.error(f"Triage failed for contribution {contribution_id}")
                return
            
            logger.info(f"Triage decision for {contribution_id}: {triage_decision.action}")
            
            # Stage 2: Execute Action
            if triage_decision.action == TriageAction.LOG_ONLY:
                logger.info(f"Contribution {contribution_id} logged only, no further action")
                return
                
            elif triage_decision.action == TriageAction.ANSWER_DIRECTLY:
                await self._generate_direct_response(db, forge_id, contribution_id)
                
            elif triage_decision.action == TriageAction.SYNTHESIZE:
                await self._generate_full_synthesis(db, forge_id, contribution_id)
                
        except Exception as e:
            logger.error(f"Error processing contribution {contribution_id}: {e}")
            raise

    async def _triage_contribution(self, db: DatabaseService, forge_id: ObjectId, contribution_id: ObjectId) -> Optional[TriageResponse]:
        """Stage 1: AI Triage - Decide what action to take"""
        try:
            # Get the triage prompt from database
            triage_prompt = await db.get_active_prompt("contribution_triage_agent")
            if not triage_prompt:
                logger.error("No active triage prompt found")
                return None
            
            # Get the contribution and forge context
            contribution = await db.get_contribution_by_id(contribution_id)
            if not contribution:
                logger.error(f"Contribution {contribution_id} not found")
                return None
            
            forge_goal = await db.get_forge_goal(forge_id)
            if not forge_goal:
                logger.error(f"Forge {forge_id} goal not found")
                return None
            
            # Extract the text content from the contribution
            contribution_text = self._extract_contribution_text(contribution)
            
            # Render the triage prompt
            rendered_prompt = triage_prompt.template.replace("{{ goal }}", forge_goal)
            rendered_prompt = rendered_prompt.replace("{{ latest_contribution_text }}", contribution_text)
            
            # Call the triage model with prompt parameters
            chat_params = {
                "model": triage_prompt.parameters.model,
                "messages": [
                    {"role": "system", "content": "You are a triage agent for a collaboration tool. Always respond with valid JSON."},
                    {"role": "user", "content": rendered_prompt}
                ],
                "temperature": triage_prompt.parameters.temperature,
                "max_tokens": triage_prompt.parameters.max_tokens
            }
            
            # Add response format if specified
            if triage_prompt.parameters.response_format:
                chat_params["response_format"] = {"type": triage_prompt.parameters.response_format.type}
            
            response = await self.client.chat.completions.create(**chat_params)
            
            # Parse the JSON response
            response_text = response.choices[0].message.content.strip()
            logger.debug(f"Triage response: {response_text}")
            
            try:
                triage_data = json.loads(response_text)
                return TriageResponse(action=TriageAction(triage_data["action"]))
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.error(f"Invalid triage response: {response_text}, error: {e}")
                # Default to LOG_ONLY if we can't parse the response
                return TriageResponse(action=TriageAction.LOG_ONLY)
                
        except Exception as e:
            logger.error(f"Error in triage: {e}")
            return None

    async def _generate_direct_response(self, db: DatabaseService, forge_id: ObjectId, contribution_id: ObjectId):
        """Stage 2a: Generate a direct AI response to a question"""
        try:
            logger.info(f"Generating direct response for contribution {contribution_id}")
            
            # Get the direct response prompt from database
            direct_response_prompt = await db.get_active_prompt("direct_response_agent")
            if not direct_response_prompt:
                logger.error("No active direct response prompt found")
                return
            
            # Get recent context for the response
            recent_contributions = await db.get_latest_contributions(forge_id, count=10)
            forge_goal = await db.get_forge_goal(forge_id)
            
            # Build context from recent contributions
            context = self._build_conversation_context(recent_contributions, forge_goal)
            
            # Render the prompt
            rendered_prompt = direct_response_prompt.template.replace("{{ context }}", context)
            
            # Generate response using the prompt parameters
            chat_params = {
                "model": direct_response_prompt.parameters.model,
                "messages": [
                    {"role": "system", "content": "You are Forge, an AI facilitator helping teams collaborate effectively."},
                    {"role": "user", "content": rendered_prompt}
                ],
                "temperature": direct_response_prompt.parameters.temperature,
                "max_tokens": direct_response_prompt.parameters.max_tokens
            }
            
            # Add response format if specified
            if direct_response_prompt.parameters.response_format:
                chat_params["response_format"] = {"type": direct_response_prompt.parameters.response_format.type}
            
            response = await self.client.chat.completions.create(**chat_params)
            
            ai_response_text = response.choices[0].message.content.strip()
            
            # Create and save the AI response contribution
            ai_response = Contribution(
                forgeId=forge_id,
                authorId=ObjectId("000000000000000000000000"),  # System user ID
                type=ContributionType.AI_RESPONSE,
                content=AIResponseContent(text=ai_response_text),
                sourceContributionIds=[contribution_id]
            )
            
            response_id = await db.create_contribution(ai_response)
            logger.info(f"Created AI response {response_id} for contribution {contribution_id}")
            
        except Exception as e:
            logger.error(f"Error generating direct response: {e}")
            raise

    async def _generate_full_synthesis(self, db: DatabaseService, forge_id: ObjectId, contribution_id: ObjectId):
        """Stage 2b: Generate a full synthesis of the conversation"""
        try:
            logger.info(f"Generating full synthesis for forge {forge_id}")
            
            # Get synthesis prompt from database
            synthesis_prompt = await db.get_active_prompt("synthesis_facilitator_default")
            if not synthesis_prompt:
                logger.error("No active synthesis prompt found")
                return
            
            # Get full conversation history
            all_contributions = await db.get_forge_contributions(forge_id)
            forge_goal = await db.get_forge_goal(forge_id)
            
            # Build comprehensive conversation history
            history = self._build_full_conversation_history(all_contributions)
            
            # Render the synthesis prompt
            rendered_prompt = synthesis_prompt.template.replace("{{ goal }}", forge_goal or "")
            rendered_prompt = rendered_prompt.replace("{{ history }}", history)
            
            # Generate synthesis using the prompt parameters
            chat_params = {
                "model": synthesis_prompt.parameters.model,
                "messages": [
                    {"role": "system", "content": "You are Forge, an AI facilitator. Generate a structured synthesis as requested."},
                    {"role": "user", "content": rendered_prompt}
                ],
                "temperature": synthesis_prompt.parameters.temperature,
                "max_tokens": synthesis_prompt.parameters.max_tokens
            }
            
            # Add response format if specified
            if synthesis_prompt.parameters.response_format:
                chat_params["response_format"] = {"type": synthesis_prompt.parameters.response_format.type}
            
            response = await self.client.chat.completions.create(**chat_params)
            
            synthesis_text = response.choices[0].message.content.strip()
            logger.debug(f"Synthesis response: {synthesis_text}")
            
            # Parse the structured synthesis response
            try:
                synthesis_data = json.loads(synthesis_text)
                structured_synthesis = AISynthesisStructured(
                    currentState=synthesis_data.get("currentState", ""),
                    emergingConsensus=synthesis_data.get("emergingConsensus", ""),
                    outstandingQuestions=synthesis_data.get("outstandingQuestions", []),
                    nextStepsNeeded=synthesis_data.get("nextStepsNeeded", "")
                )
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Failed to parse synthesis JSON: {e}")
                # Create a fallback structured synthesis
                structured_synthesis = AISynthesisStructured(
                    currentState="Unable to parse synthesis response",
                    emergingConsensus="",
                    outstandingQuestions=[],
                    nextStepsNeeded=""
                )
            
            # Create and save the synthesis contribution
            synthesis_contribution = Contribution(
                forgeId=forge_id,
                authorId=ObjectId("000000000000000000000000"),  # System user ID
                type=ContributionType.AI_SYNTHESIS,
                content=AISynthesisContent(structured=structured_synthesis),
                sourceContributionIds=[contribution_id]
            )
            
            synthesis_id = await db.create_contribution(synthesis_contribution)
            
            # Update the forge's last synthesis reference
            await db.update_forge_last_synthesis(forge_id, synthesis_id)
            
            logger.info(f"Created synthesis {synthesis_id} for forge {forge_id}")
            
        except Exception as e:
            logger.error(f"Error generating synthesis: {e}")
            raise

    def _extract_contribution_text(self, contribution: Contribution) -> str:
        """Extract text content from a contribution for processing"""
        if isinstance(contribution.content, UserMessageContent):
            return contribution.content.text
        elif isinstance(contribution.content, AIResponseContent):
            return contribution.content.text
        elif isinstance(contribution.content, AISynthesisContent):
            return f"Current State: {contribution.content.structured.currentState}"
        else:
            return str(contribution.content)

    def _build_conversation_context(self, contributions: List[Contribution], goal: Optional[str]) -> str:
        """Build conversation context for direct responses"""
        context_parts = []
        
        if goal:
            context_parts.append(f"Goal: {goal}")
        
        context_parts.append("Recent conversation:")
        
        for contrib in contributions[-10:]:  # Last 10 contributions
            content_text = self._extract_contribution_text(contrib)
            author = "User" if contrib.type == ContributionType.USER_MESSAGE else "AI"
            timestamp = contrib.createdAt.strftime("%H:%M")
            context_parts.append(f"[{timestamp}] {author}: {content_text}")
        
        return "\n".join(context_parts)

    def _build_full_conversation_history(self, contributions: List[Contribution]) -> str:
        """Build complete conversation history for synthesis"""
        history_parts = []
        
        for contrib in contributions:
            content_text = self._extract_contribution_text(contrib)
            author = "User" if contrib.type == ContributionType.USER_MESSAGE else "AI"
            timestamp = contrib.createdAt.strftime("%Y-%m-%d %H:%M")
            history_parts.append(f"[{timestamp}] {author}: {content_text}")
        
        return "\n".join(history_parts) 