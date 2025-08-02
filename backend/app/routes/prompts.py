from fastapi import APIRouter, HTTPException, Depends, Query
from loguru import logger
import json

from app.models.schemas import (
    PromptsListResponse, PromptDetailResponse, PromptTestRequest, PromptTestResponse,
    PromptInfo
)
from app.services.database import get_database, DatabaseService
from app.services.prompt_test_service import PromptTestService
from app.config import settings

router = APIRouter(
    prefix="/prompts",
    tags=["Prompt Testing"],
    responses={404: {"description": "Prompt not found"}}
)

# Initialize the prompt test service
prompt_test_service = PromptTestService(api_key=settings.openrouter_api_key)


@router.get(
    "",
    response_model=PromptsListResponse,
    summary="List Available Prompts",
    description="Get all active prompts available for testing with their basic configuration"
)
async def list_prompts(db: DatabaseService = Depends(get_database)):
    """
    **Discover available prompts** - Step 1 of the testing workflow.
    
    Returns all active prompts with their configuration, expected variables,
    and model information to help you choose which prompt to test.
    """
    try:
        prompts = await db.list_active_prompts()
        
        prompt_infos = []
        for prompt in prompts:
            prompt_infos.append(PromptInfo(
                name=prompt.name,
                version=prompt.version,
                description=prompt.description,
                expected_vars=prompt.expected_vars,
                parameters=prompt.parameters,
                assertivenessLevel=prompt.assertivenessLevel
            ))
        
        return PromptsListResponse(
            prompts=prompt_infos,
            total_count=len(prompt_infos)
        )
        
    except Exception as e:
        logger.error(f"Error listing prompts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve prompts")


@router.get(
    "/{prompt_name}",
    response_model=PromptDetailResponse,
    summary="Get Prompt Details",
    description="Get detailed information about a specific prompt including template preview and sample variables"
)
async def get_prompt_details(
    prompt_name: str,
    version: int = Query(None, description="Specific version number (defaults to latest active)"),
    db: DatabaseService = Depends(get_database)
):
    """
    **Understand prompt requirements** - Step 1.5 of the testing workflow.
    
    Get comprehensive information about a prompt including:
    - Expected variables and their purpose
    - Template preview to understand the prompt structure  
    - Sample variables for quick testing
    - Model configuration details
    """
    try:
        prompt = await db.get_prompt_by_name_and_version(prompt_name, version)
        if not prompt:
            raise HTTPException(status_code=404, detail=f"Prompt '{prompt_name}' not found")
        
        # Generate sample variables for this prompt
        sample_variables = prompt_test_service.get_sample_variables(prompt.expected_vars)
        
        # Create template preview (first 200 chars)
        template_preview = prompt.template[:200]
        if len(prompt.template) > 200:
            template_preview += "..."
        
        prompt_info = PromptInfo(
            name=prompt.name,
            version=prompt.version,
            description=prompt.description,
            expected_vars=prompt.expected_vars,
            parameters=prompt.parameters,
            assertivenessLevel=prompt.assertivenessLevel
        )
        
        return PromptDetailResponse(
            prompt=prompt_info,
            template_preview=template_preview,
            sample_variables=sample_variables
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting prompt details for '{prompt_name}': {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve prompt details")


@router.get(
    "/{prompt_name}/sample",
    response_model=dict,
    summary="Get Sample Variables",
    description="Get realistic sample data for prompt variables to quickly test prompts"
)
async def get_prompt_sample_variables(
    prompt_name: str,
    version: int = Query(None, description="Specific version number (defaults to latest active)"),
    db: DatabaseService = Depends(get_database)
):
    """
    **Get sample test data** - Quick way to get realistic variables for testing.
    
    Returns sample variables that work well with the prompt, plus usage examples
    for immediate testing via curl or other tools.
    """
    try:
        prompt = await db.get_prompt_by_name_and_version(prompt_name, version)
        if not prompt:
            raise HTTPException(status_code=404, detail=f"Prompt '{prompt_name}' not found")
        
        sample_variables = prompt_test_service.get_sample_variables(prompt.expected_vars)
        
        # Properly format the curl example with JSON serialization
        sample_json = json.dumps({"variables": sample_variables})
        curl_example = f"curl -X POST /api/prompts/{prompt_name}/test -H 'Content-Type: application/json' -d '{sample_json}'"
        
        return {
            "prompt_name": prompt_name,
            "prompt_version": prompt.version,
            "sample_variables": sample_variables,
            "usage_example": {
                "curl": curl_example,
                "description": "Copy the sample_variables above and modify them as needed for testing"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sample variables for '{prompt_name}': {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve sample variables")


@router.post(
    "/{prompt_name}/test",
    response_model=PromptTestResponse,
    summary="Execute Prompt Test",
    description="Test a prompt with your variables and get AI model response with performance metrics"
)
async def test_prompt(
    prompt_name: str,
    request: PromptTestRequest,
    version: int = Query(None, description="Specific version number (defaults to latest active)"),
    db: DatabaseService = Depends(get_database)
):
    """
    **Execute prompt with your data** - Step 2 of the testing workflow.
    
    Submit your variables to test the prompt and receive:
    - The rendered prompt (with variables substituted)
    - AI model response
    - Performance metrics (execution time, tokens used)
    - Model configuration used
    
    **Example request body:**
    ```json
    {
      "variables": {
        "goal": "Build a mobile app for task management",
        "latest_contribution_text": "I think we should use React Native"
      }
    }
    ```
    """
    try:
        # Get the prompt
        prompt = await db.get_prompt_by_name_and_version(prompt_name, version)
        if not prompt:
            raise HTTPException(status_code=404, detail=f"Prompt '{prompt_name}' not found")
        
        # Test the prompt with provided variables
        result = await prompt_test_service.test_prompt(prompt, request.variables)
        
        logger.info(f"Successfully tested prompt '{prompt_name}' in {result.execution_time_ms}ms")
        return result
        
    except HTTPException:
        raise
    except ValueError as e:
        # This handles missing required variables
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error testing prompt '{prompt_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to test prompt: {str(e)}") 