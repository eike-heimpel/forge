import time
import re
from typing import Dict, Any, Optional, List
from openai import AsyncOpenAI
from loguru import logger

from app.models.schemas import AIPrompt, PromptTestResponse


class PromptTestService:
    """Service for testing and evaluating AI prompts"""
    
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
    
    def render_prompt_template(self, template: str, variables: Dict[str, Any]) -> str:
        """Render a prompt template with provided variables using simple string replacement"""
        rendered = template
        
        for var_name, value in variables.items():
            # Handle both simple variables and nested dict access
            placeholder = f"{{{{ {var_name} }}}}"
            rendered = rendered.replace(placeholder, str(value))
            
            # Handle dict access patterns like {{ role['name'] }}
            if isinstance(value, dict):
                for key, nested_value in value.items():
                    nested_placeholder = f"{{{{ {var_name}['{key}'] }}}}"
                    rendered = rendered.replace(nested_placeholder, str(nested_value))
        
        return rendered
    
    def validate_required_variables(self, template: str, expected_vars: List[str], provided_vars: Dict[str, Any]) -> List[str]:
        """Validate that all required variables are provided and return missing ones"""
        missing_vars = []
        
        for var in expected_vars:
            if var not in provided_vars:
                missing_vars.append(var)
                continue
                
            # Check for nested dict access in template
            if isinstance(provided_vars[var], dict):
                # Find patterns like {{ role['name'] }} in template
                pattern = rf"\{{\{{\s*{re.escape(var)}\['([^']+)'\]\s*\}}\}}"
                matches = re.findall(pattern, template)
                for key in matches:
                    if key not in provided_vars[var]:
                        missing_vars.append(f"{var}['{key}']")
        
        return missing_vars
    
    def get_sample_variables(self, expected_vars: List[str]) -> Dict[str, str]:
        """Generate sample values for expected variables"""
        samples = {}
        
        for var in expected_vars:
            if var == "goal":
                samples[var] = "Build a mobile app for task management"
            elif var == "latest_contribution_text":
                samples[var] = "I think we should use React Native for cross-platform compatibility"
            elif var == "context":
                samples[var] = "Previous discussion about technology stack choices"
            elif var == "history":
                samples[var] = "User A: What framework should we use?\nUser B: I suggest React Native\nUser A: That sounds good"
            elif var == "role":
                samples[var] = "{'name': 'John Doe', 'title': 'Senior Developer'}"
            elif var == "roles_text":
                samples[var] = "John Doe (Senior Developer), Jane Smith (UI/UX Designer), Bob Wilson (Project Manager)"
            elif var == "contributions_text":
                samples[var] = "John: We need to decide on the tech stack\nJane: I suggest focusing on user experience first\nBob: Let's align on timeline and priorities"
            elif var == "current_briefing":
                samples[var] = "You're responsible for the technical architecture decisions. The team is currently discussing framework options."
            elif var == "synthesis":
                samples[var] = "The team has agreed on React Native for mobile development and is now discussing state management approaches."
            elif var == "chat_history_text":
                samples[var] = "John: What about Redux for state management?\nJane: I prefer Zustand for its simplicity\nBob: Both are good options, let's prototype with both"
            else:
                samples[var] = f"Sample value for {var}"
        
        return samples
    
    async def test_prompt(self, prompt: AIPrompt, variables: Dict[str, Any]) -> PromptTestResponse:
        """Test a prompt with provided variables"""
        start_time = time.time()
        
        try:
            # Validate required variables
            missing_vars = self.validate_required_variables(prompt.template, prompt.expected_vars, variables)
            if missing_vars:
                raise ValueError(f"Missing required variables: {', '.join(missing_vars)}")
            
            # Render the template
            rendered_prompt = self.render_prompt_template(prompt.template, variables)
            
            # Prepare the chat parameters
            chat_params = {
                "model": prompt.parameters.model,
                "messages": [
                    {"role": "system", "content": "You are an AI assistant helping to test prompt responses."},
                    {"role": "user", "content": rendered_prompt}
                ],
                "temperature": prompt.parameters.temperature,
                "max_tokens": prompt.parameters.max_tokens
            }
            
            # Add response format if specified
            if prompt.parameters.response_format:
                chat_params["response_format"] = {"type": prompt.parameters.response_format.type}
            
            # Call the AI model
            response = await self.client.chat.completions.create(**chat_params)
            
            # Calculate execution time
            execution_time = int((time.time() - start_time) * 1000)
            
            # Extract response content
            ai_response = response.choices[0].message.content.strip()
            
            # Get token usage if available
            tokens_used = response.usage.total_tokens if response.usage else None
            
            return PromptTestResponse(
                prompt_name=prompt.name,
                prompt_version=prompt.version,
                rendered_prompt=rendered_prompt,
                model_response=ai_response,
                execution_time_ms=execution_time,
                model_used=prompt.parameters.model,
                tokens_used=tokens_used
            )
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            logger.error(f"Error testing prompt '{prompt.name}': {e}")
            
            return PromptTestResponse(
                prompt_name=prompt.name,
                prompt_version=prompt.version,
                rendered_prompt="Error occurred during rendering",
                model_response=f"Error: {str(e)}",
                execution_time_ms=execution_time,
                model_used=prompt.parameters.model,
                tokens_used=None
            ) 