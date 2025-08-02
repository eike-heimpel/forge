import json
import httpx
import logging
from typing import Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json"
        }
    
    async def generate_text(self, prompt: str, max_tokens: int = 1500, temperature: float = 0.6) -> Optional[str]:
        """Generate text using OpenRouter API"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json={
                        "model": settings.openrouter_model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": max_tokens,
                        "temperature": temperature
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error calling OpenRouter API: {e}")
            return None
    
    async def synthesize_conversation(self, goal: str, roles_text: str, contributions_text: str) -> Optional[Dict[str, Any]]:
        """Generate synthesis using the synthesis prompt"""
        from prompts.synthesis import synthesis_prompt
        
        prompt = synthesis_prompt(goal, roles_text, contributions_text)
        
        try:
            response = await self.generate_text(prompt, max_tokens=2000, temperature=0.6)
            if not response:
                return None
            
            # Strip markdown code block formatting if present
            clean_response = response.strip()
            if clean_response.startswith('```json'):
                clean_response = clean_response.replace('```json', '').replace('```', '').strip()
            elif clean_response.startswith('```'):
                clean_response = clean_response.replace('```', '').strip()
            
            # Parse JSON response
            parsed_synthesis = json.loads(clean_response)
            return parsed_synthesis
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse synthesis JSON: {e}")
            logger.error(f"Raw response: {response}")
            return None
        except Exception as e:
            logger.error(f"Error in synthesis: {e}")
            return None
    
    async def generate_chat_response(self, chat_messages: list, role: Dict[str, str], current_briefing: str, synthesis: str) -> Optional[str]:
        """Generate chat response using the chat response prompt"""
        from prompts.chat_response import chat_response_prompt
        
        prompt = chat_response_prompt(chat_messages, role, current_briefing, synthesis)
        
        try:
            response = await self.generate_text(prompt, max_tokens=300, temperature=0.3)
            return response
            
        except Exception as e:
            logger.error(f"Error generating chat response: {e}")
            return None

# Global LLM service instance
llm_service = LLMService() 