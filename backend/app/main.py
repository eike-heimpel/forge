import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings
from app.services.database import init_database, db_service
from app.routes.webhook import router as webhook_router
from app.routes.prompts import router as prompts_router
from app.routes.system import router as system_router


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
    description="""
    Production-ready AI processing service for Forge collaboration tool.
    
    ## Features
    
    * **AI-Powered Contribution Triage** - Automatically analyze and route user contributions
    * **Dynamic Prompt Management** - Database-driven prompt configuration with versioning
    * **Comprehensive Testing API** - Test and evaluate prompts before deployment
    * **Asynchronous Processing** - High-performance webhook processing with background tasks
    
    ## Authentication
    
    Webhook endpoints require Bearer token authentication.
    
    ## Models
    
    Using Google Gemini 2.5 models via OpenRouter:
    - **Flash-Lite**: Fast, cost-effective triage decisions
    - **Flash**: Comprehensive responses and synthesis generation
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules with proper organization
app.include_router(system_router)  # Root level endpoints (/, /health, /status)
app.include_router(webhook_router, prefix="/api")  # /api/webhook/*
app.include_router(prompts_router, prefix="/api")   # /api/prompts/*


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
            logger.warning(f"Required prompt '{prompt_name}' not found in database. Run 'make seed-prompts-force' to initialize prompts.")
        else:
            logger.info(f"✓ Found prompt '{prompt_name}' v{prompt.version} using model '{prompt.parameters.model}'")
    
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