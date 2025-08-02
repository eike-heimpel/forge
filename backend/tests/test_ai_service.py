"""
Test AI service operations
"""
import pytest
import json
from unittest.mock import AsyncMock, patch
from bson import ObjectId

from app.services.ai_service import AIService
from app.models.schemas import (
    AIPrompt, PromptParameters, PromptStatus, ResponseFormat,
    Contribution, ContributionType, UserMessageContent,
    TriageAction, TriageResponse
)


@pytest.fixture
def ai_service():
    """Create AIService instance for testing"""
    return AIService(api_key="test-api-key")


@pytest.fixture
def mock_triage_prompt():
    """Mock triage prompt"""
    params = PromptParameters(
        model="openai/gpt-4o-mini",
        temperature=0.1,
        max_tokens=100,
        response_format=ResponseFormat(type="json_object")
    )
    return AIPrompt(
        name="contribution_triage_agent",
        version=1,
        status=PromptStatus.ACTIVE,
        description="Test triage prompt",
        parameters=params,
        expected_vars=["goal", "latest_contribution_text"],
        template="Analyze: {{ goal }} - {{ latest_contribution_text }}"
    )


@pytest.fixture
def mock_contribution():
    """Mock contribution for testing"""
    return Contribution(
        id="507f1f77bcf86cd799439011",
        forgeId="507f1f77bcf86cd799439012",
        authorId="507f1f77bcf86cd799439013", 
        type=ContributionType.USER_MESSAGE,
        content=UserMessageContent(text="What should we do next?")
    )


@pytest.mark.asyncio
async def test_extract_contribution_text(ai_service, mock_contribution):
    """Test extracting text from different contribution types"""
    # Test user message
    text = ai_service._extract_contribution_text(mock_contribution)
    assert text == "What should we do next?"


@pytest.mark.asyncio
async def test_build_conversation_context(ai_service, mock_contribution):
    """Test building conversation context"""
    contributions = [mock_contribution]
    goal = "Complete the project"
    
    context = ai_service._build_conversation_context(contributions, goal)
    
    assert "Goal: Complete the project" in context
    assert "Recent conversation:" in context
    assert "User: What should we do next?" in context


@pytest.mark.asyncio
async def test_build_full_conversation_history(ai_service, mock_contribution):
    """Test building full conversation history"""
    contributions = [mock_contribution]
    
    history = ai_service._build_full_conversation_history(contributions)
    
    assert "User: What should we do next?" in history
    # Should include timestamp
    assert "[20" in history  # Year in timestamp


@pytest.mark.asyncio
@patch('app.services.ai_service.AsyncOpenAI')
async def test_triage_contribution_log_only(mock_openai_class, ai_service, mock_triage_prompt, mock_contribution):
    """Test triage decision: LOG_ONLY"""
    # Mock database
    mock_db = AsyncMock()
    mock_db.get_active_prompt.return_value = mock_triage_prompt
    mock_db.get_contribution_by_id.return_value = mock_contribution
    mock_db.get_forge_goal.return_value = "Test goal"
    
    # Mock OpenAI response
    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_choice = AsyncMock()
    mock_choice.message.content = '{"action": "LOG_ONLY"}'
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    mock_openai_class.return_value = mock_client
    
    # Replace the client in ai_service
    ai_service.client = mock_client
    
    result = await ai_service._triage_contribution(
        mock_db, 
        "507f1f77bcf86cd799439012",
        "507f1f77bcf86cd799439011"
    )
    
    assert result is not None
    assert result.action == TriageAction.LOG_ONLY


@pytest.mark.asyncio
@patch('app.services.ai_service.AsyncOpenAI')
async def test_triage_contribution_synthesize(mock_openai_class, ai_service, mock_triage_prompt, mock_contribution):
    """Test triage decision: SYNTHESIZE"""
    # Mock database
    mock_db = AsyncMock()
    mock_db.get_active_prompt.return_value = mock_triage_prompt
    mock_db.get_contribution_by_id.return_value = mock_contribution
    mock_db.get_forge_goal.return_value = "Test goal"
    
    # Mock OpenAI response
    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_choice = AsyncMock()
    mock_choice.message.content = '{"action": "SYNTHESIZE"}'
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    # Replace the client in ai_service
    ai_service.client = mock_client
    
    result = await ai_service._triage_contribution(
        mock_db,
        "507f1f77bcf86cd799439012",
        "507f1f77bcf86cd799439011"
    )
    
    assert result is not None
    assert result.action == TriageAction.SYNTHESIZE


@pytest.mark.asyncio
async def test_triage_invalid_json_response(ai_service, mock_triage_prompt, mock_contribution):
    """Test triage with invalid JSON response - should default to LOG_ONLY"""
    # Mock database
    mock_db = AsyncMock()
    mock_db.get_active_prompt.return_value = mock_triage_prompt
    mock_db.get_contribution_by_id.return_value = mock_contribution
    mock_db.get_forge_goal.return_value = "Test goal"
    
    # Mock OpenAI response with invalid JSON
    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_choice = AsyncMock()
    mock_choice.message.content = 'Invalid JSON response'
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    # Replace the client in ai_service
    ai_service.client = mock_client
    
    result = await ai_service._triage_contribution(
        mock_db,
        "507f1f77bcf86cd799439012",
        "507f1f77bcf86cd799439011"
    )
    
    assert result is not None
    assert result.action == TriageAction.LOG_ONLY  # Default fallback


@pytest.mark.asyncio
async def test_triage_missing_prompt(ai_service):
    """Test triage when prompt is missing"""
    # Mock database with no prompt
    mock_db = AsyncMock()
    mock_db.get_active_prompt.return_value = None
    
    result = await ai_service._triage_contribution(
        mock_db,
        "507f1f77bcf86cd799439012",
        "507f1f77bcf86cd799439011"
    )
    
    assert result is None 