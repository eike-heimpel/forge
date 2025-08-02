import sys
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings
from app.services.database import init_database, db_service
from app.routes.webhook import router as webhook_router
from app.models.schemas import HealthResponse, ErrorResponse


# Configure logging
logger.remove()  # Remove default handler
logger.add(
    sys.stdout,
    level=settings.log_level,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    colorize=True
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - startup and shutdown"""
    # Startup
    logger.info("Starting Forge AI Service...")
    
    # Validate required environment variables
    if not settings.mongo_uri:
        logger.error("MONGO_URI environment variable is required")
        raise RuntimeError("Missing required configuration: MONGO_URI")
        
    if not settings.openrouter_api_key:
        logger.error("OPENROUTER_API_KEY environment variable is required")
        raise RuntimeError("Missing required configuration: OPENROUTER_API_KEY")
    
    # Initialize database connection
    try:
        await init_database(settings.mongo_uri)
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    # Initialize AI prompts if needed
    await initialize_default_prompts()
    
    logger.info("Forge AI Service startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Forge AI Service...")
    if db_service:
        await db_service.disconnect()
    logger.info("Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Forge AI Service",
    description="AI processing service for Forge collaboration tool - PoC Architecture",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(webhook_router, prefix="/api")


# Root endpoints
@app.get("/")
async def root():
    return {
        "message": "Forge AI Service is running",
        "version": "1.0.0",
        "architecture": "PoC with webhook processing",
        "environment": settings.environment
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check endpoint"""
    # Check database connectivity
    db_healthy = False
    if db_service:
        try:
            db_healthy = await db_service.health_check()
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
    
    return HealthResponse(
        status="healthy" if db_healthy else "unhealthy",
        service="forge-ai-service"
    )


@app.get("/api/status")
async def service_status():
    """Detailed service status endpoint"""
    db_healthy = False
    if db_service:
        try:
            db_healthy = await db_service.health_check()
        except Exception:
            pass
    
    return {
        "service": "forge-ai-service",
        "version": "1.0.0", 
        "environment": settings.environment,
        "database": {
            "connected": db_healthy,
            "database_name": settings.mongo_database
        },
        "ai": {
            "configuration": "Dynamic - models configured per prompt in database",
            "api_provider": "OpenRouter"
        },
        "timestamp": datetime.utcnow().isoformat()
    }


async def initialize_default_prompts():
    """Check if required prompts exist in database"""
    if not db_service:
        return
        
    required_prompts = [
        "contribution_triage_agent",
        "direct_response_agent", 
        "synthesis_facilitator_default"
    ]
    
    for prompt_name in required_prompts:
        prompt = await db_service.get_active_prompt(prompt_name)
        if not prompt:
            logger.warning(f"Required prompt '{prompt_name}' not found in database. AI functionality may not work.")
        else:
            logger.info(f"Found prompt '{prompt_name}' v{prompt.version} using model '{prompt.parameters.model}'")
    
    logger.info("Prompt validation complete")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower()
    ) 