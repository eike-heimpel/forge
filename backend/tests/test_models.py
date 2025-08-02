"""
Test Pydantic models and data validation
"""
import pytest
from datetime import datetime
from bson import ObjectId

from app.models.schemas import (
    Forge, Contribution, AIPrompt, ForgeMember,
    PromptParameters, ResponseFormat,
    ForgeStatus, MemberRole, ContributionType, PromptStatus,
    UserMessageContent, ProcessContributionRequest,
    TriageResponse, TriageAction
)


def test_forge_model_creation():
    """Test creating a valid Forge model"""
    # Use the alias _id for the field since that's what the model expects
    member = ForgeMember(_id="507f1f77bcf86cd799439011", role=MemberRole.OWNER)
    
    forge = Forge(
        goal="Test the collaboration system",
        status=ForgeStatus.ACTIVE,
        members=[member]
    )
    
    assert forge.goal == "Test the collaboration system"
    assert forge.status == ForgeStatus.ACTIVE
    assert len(forge.members) == 1
    assert forge.members[0].role == MemberRole.OWNER


def test_prompt_parameters_validation():
    """Test PromptParameters model with different configurations"""
    # Basic parameters
    params = PromptParameters(
        model="openai/gpt-4o",
        temperature=0.7,
        max_tokens=1000
    )
    assert params.model == "openai/gpt-4o"
    assert params.temperature == 0.7
    assert params.max_tokens == 1000
    assert params.response_format is None
    
    # With response format
    params_with_format = PromptParameters(
        model="openai/gpt-4o-mini",
        temperature=0.1,
        max_tokens=100,
        response_format=ResponseFormat(type="json_object")
    )
    assert params_with_format.response_format.type == "json_object"


def test_ai_prompt_model():
    """Test AIPrompt model creation"""
    params = PromptParameters(
        model="openai/gpt-4o-mini",
        temperature=0.1,
        max_tokens=100
    )
    
    prompt = AIPrompt(
        name="test_prompt",
        version=1,
        status=PromptStatus.ACTIVE,
        description="Test prompt for validation",
        parameters=params,
        expected_vars=["goal", "context"],
        template="Test template with {{ goal }} and {{ context }}"
    )
    
    assert prompt.name == "test_prompt"
    assert prompt.version == 1
    assert prompt.status == PromptStatus.ACTIVE
    assert prompt.parameters.model == "openai/gpt-4o-mini"
    assert len(prompt.expected_vars) == 2


def test_contribution_model():
    """Test Contribution model with different content types"""
    # User message contribution
    user_content = UserMessageContent(text="Hello team!")
    
    contribution = Contribution(
        forgeId="507f1f77bcf86cd799439011",
        authorId="507f1f77bcf86cd799439012", 
        type=ContributionType.USER_MESSAGE,
        content=user_content
    )
    
    assert contribution.type == ContributionType.USER_MESSAGE
    assert contribution.content.text == "Hello team!"
    assert contribution.sourceContributionIds == []


def test_webhook_request_validation():
    """Test webhook request model validation"""
    request = ProcessContributionRequest(
        forgeId="507f1f77bcf86cd799439011",
        newContributionId="507f1f77bcf86cd799439012"
    )
    
    assert ObjectId.is_valid(request.forgeId)
    assert ObjectId.is_valid(request.newContributionId)


def test_triage_response_validation():
    """Test AI triage response validation"""
    # Valid triage actions
    for action in [TriageAction.LOG_ONLY, TriageAction.ANSWER_DIRECTLY, TriageAction.SYNTHESIZE]:
        response = TriageResponse(action=action)
        assert response.action == action


def test_invalid_model_data():
    """Test that invalid data raises validation errors"""
    with pytest.raises(ValueError):
        # Invalid ObjectId using the correct field name
        ForgeMember(_id="invalid-objectid", role=MemberRole.OWNER)
    
    with pytest.raises(ValueError):
        # Invalid temperature (should be float)
        PromptParameters(
            model="test",
            temperature="invalid",  # Should be float
            max_tokens=100
        ) 