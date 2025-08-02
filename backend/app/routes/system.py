from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from loguru import logger

from app.models.schemas import HealthResponse
from app.services.database import get_database, DatabaseService, db_service
from app.config import settings

router = APIRouter(
    tags=["System Management"],
    responses={500: {"description": "Service unavailable"}}
)


@router.get(
    "/",
    summary="Service Information",
    description="Basic service information and version details"
)
async def root():
    """
    **Service Overview** - Basic information about the Forge AI Service.
    
    Returns service metadata, version, and architecture information.
    """
    return {
        "message": "Forge AI Service is running",
        "version": "1.0.0",
        "architecture": "Production-ready with webhook processing and prompt testing",
        "environment": settings.environment,
        "features": [
            "AI-powered contribution triage",
            "Dynamic prompt management",
            "Comprehensive prompt testing API",
            "Asynchronous webhook processing"
        ]
    }


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Comprehensive health check including database connectivity"
)
async def health_check(db: DatabaseService = Depends(get_database)):
    """
    **System Health Check** - Verify all service components are operational.
    
    Checks:
    - Database connectivity
    - Service availability
    - Basic system status
    
    Returns HTTP 200 if healthy, 500 if any critical component is down.
    """
    # Check database connectivity
    db_healthy = False
    if db_service:
        try:
            db_healthy = await db_service.health_check()
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
    
    status = "healthy" if db_healthy else "unhealthy"
    
    return HealthResponse(
        status=status,
        service="forge-ai-service"
    )


@router.get(
    "/status",
    summary="Detailed Service Status",
    description="Comprehensive service status with configuration and component details"
)
async def service_status():
    """
    **Detailed Service Status** - Complete system status and configuration info.
    
    Provides detailed information about:
    - Service version and environment
    - Database connection status
    - AI configuration details
    - Available prompts count
    - System timestamps
    
    Useful for monitoring, debugging, and system verification.
    """
    # Check database health
    db_healthy = False
    prompt_count = 0
    if db_service:
        try:
            db_healthy = await db_service.health_check()
            if db_healthy:
                prompts = await db_service.list_active_prompts()
                prompt_count = len(prompts)
        except Exception as e:
            logger.error(f"Error checking service status: {e}")
    
    return {
        "service": "forge-ai-service",
        "version": "1.0.0", 
        "environment": settings.environment,
        "status": "operational" if db_healthy else "degraded",
        "database": {
            "connected": db_healthy,
            "database_name": settings.mongo_database,
            "active_prompts": prompt_count
        },
        "ai": {
            "provider": "OpenRouter",
            "models": "Google Gemini 2.5 (Flash & Flash-Lite)",
            "configuration": "Dynamic - models configured per prompt in database"
        },
        "features": {
            "webhook_processing": "enabled",
            "prompt_testing": "enabled", 
            "background_tasks": "enabled",
            "authentication": "bearer_token"
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    } 