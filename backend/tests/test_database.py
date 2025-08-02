"""
Test database service operations
"""
import pytest
from unittest.mock import AsyncMock, patch
from bson import ObjectId

from app.services.database import DatabaseService
from app.models.schemas import (
    AIPrompt, PromptParameters, PromptStatus, ResponseFormat,
    Contribution, ContributionType, UserMessageContent
)


@pytest.fixture
def mock_prompt_doc():
    """Mock MongoDB document for AI prompt"""
    return {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "name": "test_prompt", 
        "version": 1,
        "status": "active",
        "description": "Test prompt",
        "parameters": {
            "model": "openai/gpt-4o",
            "temperature": 0.7,
            "max_tokens": 1000,
            "response_format": {"type": "json_object"}
        },
        "expected_vars": ["goal", "context"],
        "template": "Test template"
    }


@pytest.fixture
def mock_contribution_doc():
    """Mock MongoDB document for contribution"""
    return {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "forgeId": ObjectId("507f1f77bcf86cd799439012"),
        "authorId": ObjectId("507f1f77bcf86cd799439013"),
        "type": "USER_MESSAGE",
        "createdAt": "2025-01-01T00:00:00Z",
        "content": {"text": "Test message"},
        "sourceContributionIds": []
    }


@pytest.mark.asyncio
async def test_get_active_prompt_success(mock_prompt_doc):
    """Test successful prompt retrieval"""
    db_service = DatabaseService("mongodb://test", "test_db")
    
    # Mock the collection and find_one method
    mock_collection = AsyncMock()
    mock_collection.find_one.return_value = mock_prompt_doc
    db_service.ai_prompts = mock_collection
    
    result = await db_service.get_active_prompt("test_prompt")
    
    assert result is not None
    assert result.name == "test_prompt"
    assert result.version == 1
    assert result.parameters.model == "openai/gpt-4o"
    assert result.parameters.response_format.type == "json_object"
    
    # Verify the query was called correctly
    mock_collection.find_one.assert_called_once_with(
        {"name": "test_prompt", "status": PromptStatus.ACTIVE},
        sort=[("version", -1)]
    )


@pytest.mark.asyncio
async def test_get_active_prompt_not_found():
    """Test prompt retrieval when prompt doesn't exist"""
    db_service = DatabaseService("mongodb://test", "test_db")
    
    mock_collection = AsyncMock()
    mock_collection.find_one.return_value = None
    db_service.ai_prompts = mock_collection
    
    result = await db_service.get_active_prompt("nonexistent_prompt")
    
    assert result is None


@pytest.mark.asyncio
async def test_create_prompt():
    """Test creating a new AI prompt"""
    db_service = DatabaseService("mongodb://test", "test_db")
    
    # Mock the collection
    mock_collection = AsyncMock()
    mock_result = AsyncMock()
    mock_result.inserted_id = ObjectId("507f1f77bcf86cd799439011")
    mock_collection.insert_one.return_value = mock_result
    db_service.ai_prompts = mock_collection
    
    # Create a prompt to insert
    params = PromptParameters(
        model="openai/gpt-4o",
        temperature=0.7,
        max_tokens=1000
    )
    prompt = AIPrompt(
        name="new_prompt",
        version=1,
        status=PromptStatus.ACTIVE,
        description="New test prompt",
        parameters=params,
        expected_vars=["test"],
        template="Test template"
    )
    
    result = await db_service.create_prompt(prompt)
    
    assert result == ObjectId("507f1f77bcf86cd799439011")
    mock_collection.insert_one.assert_called_once()


@pytest.mark.asyncio
async def test_get_contribution_by_id(mock_contribution_doc):
    """Test retrieving contribution by ID"""
    db_service = DatabaseService("mongodb://test", "test_db")
    
    mock_collection = AsyncMock()
    mock_collection.find_one.return_value = mock_contribution_doc
    db_service.contributions = mock_collection
    
    contribution_id = ObjectId("507f1f77bcf86cd799439011")
    result = await db_service.get_contribution_by_id(contribution_id)
    
    assert result is not None
    assert result.type == ContributionType.USER_MESSAGE
    assert result.content.text == "Test message"
    
    mock_collection.find_one.assert_called_once_with({"_id": contribution_id})


@pytest.mark.asyncio 
async def test_health_check():
    """Test database health check"""
    db_service = DatabaseService("mongodb://test", "test_db")
    
    # Mock successful ping
    mock_client = AsyncMock()
    mock_admin = AsyncMock()
    mock_admin.command.return_value = {"ok": 1}
    mock_client.admin = mock_admin
    db_service.client = mock_client
    
    result = await db_service.health_check()
    assert result is True
    
    # Mock failed ping
    mock_admin.command.side_effect = Exception("Connection failed")
    result = await db_service.health_check()
    assert result is False


@pytest.mark.asyncio
async def test_get_forge_goal():
    """Test getting forge goal (lightweight query)"""
    db_service = DatabaseService("mongodb://test", "test_db")
    
    mock_collection = AsyncMock()
    mock_collection.find_one.return_value = {"goal": "Test collaboration goal"}
    db_service.forges = mock_collection
    
    forge_id = ObjectId("507f1f77bcf86cd799439011")
    result = await db_service.get_forge_goal(forge_id) 
    
    assert result == "Test collaboration goal"
    mock_collection.find_one.assert_called_once_with(
        {"_id": forge_id}, 
        {"goal": 1}
    ) 