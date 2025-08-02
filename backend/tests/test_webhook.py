"""
Test webhook endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from bson import ObjectId

from app.main import app
from app.services.database import get_database
from app.models.schemas import (
    Contribution, Forge, ContributionType, UserMessageContent,
    ForgeStatus, MemberRole, ForgeMember
)


@pytest.fixture
def mock_contribution():
    """Create a mock contribution for testing"""
    return Contribution(
        id="507f1f77bcf86cd799439011",
        forgeId="507f1f77bcf86cd799439012", 
        authorId="507f1f77bcf86cd799439013",
        type=ContributionType.USER_MESSAGE,
        content=UserMessageContent(text="Test message")
    )


@pytest.fixture  
def mock_forge():
    """Create a mock forge for testing"""
    member = ForgeMember(_id="507f1f77bcf86cd799439013", role=MemberRole.OWNER)
    return Forge(
        id="507f1f77bcf86cd799439012",
        goal="Test collaboration",
        status=ForgeStatus.ACTIVE,
        members=[member]
    )


@pytest.fixture
def mock_db_service():
    """Create a mock database service"""
    return AsyncMock()


def test_webhook_health():
    """Test webhook health endpoint"""
    response = TestClient(app).get("/api/webhook/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "forge-ai-webhook"


@patch('app.config.settings.forge_ai_api_key', 'test-key')
def test_webhook_missing_auth(mock_db_service):
    """Test webhook without authentication"""
    app.dependency_overrides[get_database] = lambda: mock_db_service
    client = TestClient(app)
    
    response = client.post(
        "/api/webhook/process-contribution",
        json={
            "forgeId": "507f1f77bcf86cd799439011",
            "newContributionId": "507f1f77bcf86cd799439012"
        }
    )
    assert response.status_code == 403  # No auth header
    
    # Clean up
    app.dependency_overrides.clear()


@patch('app.config.settings.forge_ai_api_key', 'test-key')
def test_webhook_invalid_auth(mock_db_service):
    """Test webhook with invalid authentication"""
    app.dependency_overrides[get_database] = lambda: mock_db_service
    client = TestClient(app)
    
    response = client.post(
        "/api/webhook/process-contribution",
        headers={"Authorization": "Bearer invalid-key"},
        json={
            "forgeId": "507f1f77bcf86cd799439011", 
            "newContributionId": "507f1f77bcf86cd799439012"
        }
    )
    assert response.status_code == 401
    
    # Clean up
    app.dependency_overrides.clear()


@patch('app.config.settings.forge_ai_api_key', 'test-key')
def test_webhook_invalid_objectid(mock_db_service):
    """Test webhook with invalid ObjectId format"""
    app.dependency_overrides[get_database] = lambda: mock_db_service
    client = TestClient(app)
    
    response = client.post(
        "/api/webhook/process-contribution",
        headers={"Authorization": "Bearer test-key"},
        json={
            "forgeId": "invalid-objectid",
            "newContributionId": "507f1f77bcf86cd799439012"
        }
    )
    assert response.status_code == 400
    assert "Invalid forge or contribution ID format" in response.json()["detail"]
    
    # Clean up
    app.dependency_overrides.clear()


@patch('app.config.settings.forge_ai_api_key', 'test-key')
def test_webhook_contribution_not_found(mock_db_service, mock_contribution, mock_forge):
    """Test webhook when contribution doesn't exist"""
    # Mock database methods
    mock_db_service.get_contribution_by_id.return_value = None  # Not found
    mock_db_service.get_forge_by_id.return_value = mock_forge
    
    app.dependency_overrides[get_database] = lambda: mock_db_service
    client = TestClient(app)
    
    response = client.post(
        "/api/webhook/process-contribution", 
        headers={"Authorization": "Bearer test-key"},
        json={
            "forgeId": "507f1f77bcf86cd799439012",
            "newContributionId": "507f1f77bcf86cd799439011"
        }
    )
    assert response.status_code == 404
    assert "Contribution not found" in response.json()["detail"]
    
    # Clean up
    app.dependency_overrides.clear()


@patch('app.config.settings.forge_ai_api_key', 'test-key')
def test_webhook_success(mock_db_service, mock_contribution, mock_forge):
    """Test successful webhook processing"""
    # Configure all async methods properly to avoid RuntimeWarnings
    mock_db_service.get_contribution_by_id.return_value = mock_contribution
    mock_db_service.get_forge_by_id.return_value = mock_forge
    mock_db_service.get_forge_goal.return_value = "Test goal"
    mock_db_service.get_latest_contributions.return_value = [mock_contribution]
    mock_db_service.get_active_prompt.return_value = None  # This will cause triage to return None
    mock_db_service.create_contribution.return_value = "507f1f77bcf86cd799439999"
    
    app.dependency_overrides[get_database] = lambda: mock_db_service
    client = TestClient(app)
    
    response = client.post(
        "/api/webhook/process-contribution",
        headers={"Authorization": "Bearer test-key"},
        json={
            "forgeId": "507f1f77bcf86cd799439012",
            "newContributionId": "507f1f77bcf86cd799439011"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert data["message"] == "Contribution processing started"
    assert data["contributionId"] == "507f1f77bcf86cd799439011"
    
    # Clean up
    app.dependency_overrides.clear() 