#!/usr/bin/env python3
"""
Integration tests for Forge AI Service
Run this while the service is running
"""

import requests
import json
import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration from environment
HOST = os.getenv("HOST", "localhost")
PORT = os.getenv("PORT", "8000")
BASE_URL = f"http://{HOST}:{PORT}"
API_KEY = os.getenv("FORGE_AI_API_KEY")

if not API_KEY:
    raise ValueError("FORGE_AI_API_KEY not found in environment variables. Please check your .env file.")

def make_request(method: str, endpoint: str, data: Dict = None, headers: Dict = None) -> requests.Response:
    """Make HTTP request with proper headers"""
    default_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    if headers:
        default_headers.update(headers)
    
    url = f"{BASE_URL}{endpoint}"
    
    if method.upper() == "GET":
        return requests.get(url, headers=default_headers)
    elif method.upper() == "POST":
        return requests.post(url, json=data, headers=default_headers)

def test_health_endpoint():
    """Test the health check endpoint"""
    print("🔍 Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "forge-ai-service"
    print("✅ Health endpoint working")

def test_root_endpoint():
    """Test the root endpoint"""
    print("🔍 Testing root endpoint...")
    response = requests.get(f"{BASE_URL}/")
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert "Forge AI Service" in data["message"]
    print("✅ Root endpoint working")

def test_chat_endpoint_auth():
    """Test chat endpoint authentication"""
    print("🔍 Testing chat endpoint authentication...")
    
    # Test without auth header - should get 403 Forbidden from HTTPBearer
    response = requests.post(f"{BASE_URL}/api/chat", json={
        "forge_id": "test_forge",
        "role_id": "1",
        "message": "Hello",
        "is_question": False
    })
    assert response.status_code == 403, f"Expected 403, got {response.status_code}"
    print("✅ Chat auth rejection working")
    
    # Test with invalid auth
    response = requests.post(f"{BASE_URL}/api/chat", 
        headers={"Authorization": "Bearer invalid_key"},
        json={
            "forge_id": "test_forge", 
            "role_id": "1",
            "message": "Hello",
            "is_question": False
        }
    )
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    print("✅ Chat invalid auth rejection working")

def test_synthesize_endpoint_auth():
    """Test synthesize endpoint authentication"""
    print("🔍 Testing synthesize endpoint authentication...")
    
    # Test without auth header - should get 403 Forbidden from HTTPBearer
    response = requests.post(f"{BASE_URL}/api/synthesize", json={
        "forge_id": "test_forge"
    })
    assert response.status_code == 403, f"Expected 403, got {response.status_code}"
    print("✅ Synthesize auth rejection working")

def test_chat_endpoint_with_valid_auth():
    """Test chat endpoint with valid auth (will fail due to DB but should pass auth)"""
    print("🔍 Testing chat endpoint with valid auth...")
    
    response = make_request("POST", "/api/chat", {
        "forge_id": "test_forge",
        "role_id": "1", 
        "message": "Hello world",
        "is_question": False
    })
    
    # Should pass auth but likely fail at DB level
    # We expect either 500 (DB error) or other business logic error, but NOT 401
    assert response.status_code != 401, f"Auth should pass, got {response.status_code}"
    print(f"✅ Chat auth passed (got status {response.status_code} - likely DB/business logic error)")

def test_synthesize_endpoint_with_valid_auth():
    """Test synthesize endpoint with valid auth (will fail due to DB but should pass auth)"""
    print("🔍 Testing synthesize endpoint with valid auth...")
    
    response = make_request("POST", "/api/synthesize", {
        "forge_id": "test_forge"
    })
    
    # Should pass auth but likely fail at DB level  
    # We expect either 500 (DB error) or other business logic error, but NOT 401
    assert response.status_code != 401, f"Auth should pass, got {response.status_code}"
    print(f"✅ Synthesize auth passed (got status {response.status_code} - likely DB/business logic error)")

def test_api_docs():
    """Test that API documentation is accessible"""
    print("🔍 Testing API docs endpoint...")
    response = requests.get(f"{BASE_URL}/docs")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    print("✅ API docs accessible")

def test_openapi_spec():
    """Test that OpenAPI spec is accessible"""
    print("🔍 Testing OpenAPI spec...")
    response = requests.get(f"{BASE_URL}/openapi.json")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    spec = response.json()
    assert spec["info"]["title"] == "Forge AI Service"
    print("✅ OpenAPI spec working")

def test_env_status_endpoint():
    """Test the environment status endpoint"""
    print("🔍 Testing env status endpoint...")
    
    # Test without auth header - should get 403 Forbidden from HTTPBearer
    response = requests.get(f"{BASE_URL}/api/env-status")
    assert response.status_code == 403, f"Expected 403, got {response.status_code}"
    print("✅ Env status auth rejection working")
    
    # Test with valid auth
    response = make_request("GET", "/api/env-status")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert "status" in data
    assert "summary" in data
    assert "environment_variables" in data
    
    # Check structure
    assert data["summary"]["total"] == 6  # We have 6 env vars
    assert "configured" in data["summary"]
    assert "missing" in data["summary"]
    
    # Verify we don't expose secrets
    env_vars = data["environment_variables"]
    
    # These should only have configured/length (no actual values)
    secret_vars = ["mongo_uri", "openrouter_api_key", "forge_ai_api_key"]
    for var in secret_vars:
        assert "configured" in env_vars[var]
        assert "length" in env_vars[var]
        assert "value" not in env_vars[var], f"Secret {var} should not expose value"
    
    # These should show actual values (non-secrets)
    public_vars = ["openrouter_model", "environment", "log_level"]
    for var in public_vars:
        assert "configured" in env_vars[var]
        assert "value" in env_vars[var], f"Public var {var} should show value"
    
    print(f"✅ Env status endpoint working - {data['summary']['configured']}/{data['summary']['total']} vars configured")

def run_all_tests():
    """Run all integration tests"""
    print("🚀 Starting Forge AI Service Integration Tests")
    print(f"🎯 Testing against: {BASE_URL}")
    print("=" * 50)
    
    tests = [
        test_health_endpoint,
        test_root_endpoint,
        test_api_docs,
        test_openapi_spec,
        test_env_status_endpoint,
        test_chat_endpoint_auth,
        test_synthesize_endpoint_auth,
        test_chat_endpoint_with_valid_auth,
        test_synthesize_endpoint_with_valid_auth,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} FAILED: {e}")
            failed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed - check the output above")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1) 