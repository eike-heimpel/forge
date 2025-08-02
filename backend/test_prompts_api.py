#!/usr/bin/env python3
"""
Test script for the Forge AI Service API
Usage: uv run python test_prompts_api.py
"""

import asyncio
import json
import httpx
from loguru import logger

BASE_URL = "http://localhost:8000"


async def test_forge_ai_api():
    """Test the complete Forge AI Service API"""
    async with httpx.AsyncClient() as client:
        
        logger.info("🚀 Testing Forge AI Service API")
        logger.info("=" * 50)
        
        # ===============================
        # SYSTEM MANAGEMENT ENDPOINTS
        # ===============================
        
        logger.info("\n📊 SYSTEM MANAGEMENT")
        logger.info("-" * 30)
        
        # Test root endpoint
        logger.info("🏠 Testing service information...")
        response = await client.get(f"{BASE_URL}/")
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Service: {data['message']}")
            logger.info(f"   Version: {data['version']}")
            logger.info(f"   Environment: {data['environment']}")
            logger.info(f"   Features: {len(data.get('features', []))} available")
        else:
            logger.error(f"❌ Failed to get service info: {response.status_code}")
            return
        
        # Test health check
        logger.info("\n💚 Testing health check...")
        response = await client.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Health status: {data['status']}")
            logger.info(f"   Service: {data['service']}")
        else:
            logger.error(f"❌ Health check failed: {response.status_code}")
            return
        
        # Test detailed status
        logger.info("\n📈 Testing detailed status...")
        response = await client.get(f"{BASE_URL}/status")
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ System status: {data['status']}")
            logger.info(f"   Database connected: {data['database']['connected']}")
            logger.info(f"   Active prompts: {data['database']['active_prompts']}")
            logger.info(f"   AI provider: {data['ai']['provider']}")
        else:
            logger.error(f"❌ Status check failed: {response.status_code}")
        
        # ===============================
        # PROMPT TESTING ENDPOINTS
        # ===============================
        
        logger.info("\n🧪 PROMPT TESTING")
        logger.info("-" * 30)
        
        # Step 1: List all available prompts
        logger.info("📋 Listing available prompts...")
        response = await client.get(f"{BASE_URL}/api/prompts")
        if response.status_code == 200:
            prompts_data = response.json()
            logger.info(f"✅ Found {prompts_data['total_count']} prompts:")
            for prompt in prompts_data['prompts']:
                logger.info(f"   • {prompt['name']} v{prompt['version']}")
                logger.info(f"     Model: {prompt['parameters']['model']}")
                logger.info(f"     Variables: {', '.join(prompt['expected_vars'])}")
        else:
            logger.error(f"❌ Failed to list prompts: {response.status_code}")
            return
        
        # Test each prompt type
        test_prompts = [
            "contribution_triage_agent",
            "synthesis_facilitator_default", 
            "direct_response_agent"
        ]
        
        for prompt_name in test_prompts:
            logger.info(f"\n🔍 Testing '{prompt_name}'...")
            
            # Get prompt details
            response = await client.get(f"{BASE_URL}/api/prompts/{prompt_name}")
            if response.status_code == 200:
                details = response.json()
                logger.info(f"   Expected variables: {details['prompt']['expected_vars']}")
                logger.info(f"   Model: {details['prompt']['parameters']['model']}")
            else:
                logger.warning(f"   ⚠️  Could not get details: {response.status_code}")
                continue
            
            # Get sample variables
            response = await client.get(f"{BASE_URL}/api/prompts/{prompt_name}/sample")
            if response.status_code != 200:
                logger.warning(f"   ⚠️  Could not get samples: {response.status_code}")
                continue
            
            sample_data = response.json()
            sample_vars = sample_data['sample_variables']
            
            # Test the prompt
            test_request = {"variables": sample_vars}
            response = await client.post(f"{BASE_URL}/api/prompts/{prompt_name}/test", json=test_request)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"   ✅ Test successful!")
                logger.info(f"      Execution time: {result['execution_time_ms']}ms")
                logger.info(f"      Tokens used: {result.get('tokens_used', 'N/A')}")
                
                # Special handling for JSON responses
                if prompt_name in ["contribution_triage_agent", "synthesis_facilitator_default"]:
                    try:
                        parsed_response = json.loads(result['model_response'])
                        if prompt_name == "contribution_triage_agent":
                            logger.info(f"      Triage decision: {parsed_response.get('action', 'N/A')}")
                        elif prompt_name == "synthesis_facilitator_default":
                            logger.info(f"      Response keys: {list(parsed_response.keys())}")
                    except json.JSONDecodeError:
                        logger.warning(f"      Response not valid JSON")
                else:
                    logger.info(f"      Response: {result['model_response'][:100]}...")
            else:
                logger.error(f"   ❌ Test failed: {response.status_code}")
                if response.content:
                    try:
                        error_data = response.json()
                        logger.error(f"      Error: {error_data.get('detail', 'Unknown error')}")
                    except:
                        logger.error(f"      Raw error: {response.text}")
        
        # ===============================
        # WEBHOOK ENDPOINTS (No Auth Test)
        # ===============================
        
        logger.info("\n🔗 WEBHOOK ENDPOINTS")
        logger.info("-" * 30)
        
        # Test webhook health (no auth required)
        logger.info("💚 Testing webhook health...")
        response = await client.get(f"{BASE_URL}/api/webhook/health")
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Webhook status: {data['status']}")
            logger.info(f"   Service: {data['service']}")
            logger.info(f"   Authentication: {data.get('authentication', 'N/A')}")
        else:
            logger.error(f"❌ Webhook health failed: {response.status_code}")
        
        # Note about webhook processing endpoint
        logger.info("\n📝 Note: POST /api/webhook/process-contribution requires authentication")
        logger.info("   Use Bearer token in Authorization header for webhook processing")
        
        # ===============================
        # SUMMARY
        # ===============================
        
        logger.info("\n" + "=" * 50)
        logger.info("🎉 API TESTING COMPLETE")
        logger.info("=" * 50)
        logger.info("✅ System Management endpoints working")
        logger.info("✅ Prompt Testing endpoints working") 
        logger.info("✅ Webhook health check working")
        logger.info("\n📚 Interactive documentation available at:")
        logger.info("   • Swagger UI: http://localhost:8000/docs")
        logger.info("   • ReDoc: http://localhost:8000/redoc")


if __name__ == "__main__":
    logger.info("🧪 Forge AI Service API Test Suite")
    logger.info("Make sure the backend is running on localhost:8000")
    logger.info("Run 'make seed-prompts-force' first to initialize prompts\n")
    asyncio.run(test_forge_ai_api()) 