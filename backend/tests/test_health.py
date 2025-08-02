"""
Test health and status endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from app.main import app


client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint returns basic info"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Forge AI Service is running"
    assert data["version"] == "1.0.0"
    assert data["architecture"] == "PoC with webhook processing"


@patch('app.main.db_service')
def test_health_endpoint_healthy(mock_db_service):
    """Test health endpoint when database is healthy"""
    mock_db_service.health_check = AsyncMock(return_value=True)
    
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "forge-ai-service"


@patch('app.main.db_service')
def test_health_endpoint_unhealthy(mock_db_service):
    """Test health endpoint when database is unhealthy"""
    mock_db_service.health_check = AsyncMock(return_value=False)
    
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unhealthy"
    assert data["service"] == "forge-ai-service"


@patch('app.main.db_service')
def test_status_endpoint(mock_db_service):
    """Test the detailed status endpoint"""
    mock_db_service.health_check = AsyncMock(return_value=True)
    
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "forge-ai-service"
    assert data["version"] == "1.0.0"
    assert "database" in data
    assert "ai" in data
    assert data["ai"]["configuration"] == "Dynamic - models configured per prompt in database" 