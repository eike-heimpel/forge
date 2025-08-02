from fastapi import FastAPI, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.routes import synthesize, chat
from app.config import settings

app = FastAPI(
    title="Forge AI Service",
    description="AI processing service for Forge collaboration tool",
    version="0.1.0"
)

# Security scheme for Bearer token
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify the Bearer token"""
    if credentials.credentials != settings.forge_ai_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials.credentials

# Add CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(synthesize.router, prefix="/api")
app.include_router(chat.router, prefix="/api")

@app.get("/")
def root():
    return {"message": "Forge AI Service is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "forge-ai-service"}

@app.get("/api/env-status")
async def env_status(token: str = Depends(verify_token)):
    """Check environment variable configuration status"""
    # Check environment variables without revealing their values
    env_status = {
        "mongo_uri": {
            "configured": bool(settings.mongo_uri),
            "length": len(settings.mongo_uri) if settings.mongo_uri else 0
        },
        "openrouter_api_key": {
            "configured": bool(settings.openrouter_api_key),
            "length": len(settings.openrouter_api_key) if settings.openrouter_api_key else 0
        },
        "openrouter_model": {
            "configured": bool(settings.openrouter_model),
            "value": settings.openrouter_model  # This one is safe to show
        },
        "forge_ai_api_key": {
            "configured": bool(settings.forge_ai_api_key),
            "length": len(settings.forge_ai_api_key) if settings.forge_ai_api_key else 0
        },
        "environment": {
            "configured": bool(settings.environment),
            "value": settings.environment  # This one is safe to show
        },
        "log_level": {
            "configured": bool(settings.log_level),
            "value": settings.log_level  # This one is safe to show
        }
    }
    
    # Count configured vs total
    total_vars = len(env_status)
    configured_vars = sum(1 for var in env_status.values() if var["configured"])
    
    return {
        "status": "complete" if configured_vars == total_vars else "incomplete",
        "summary": {
            "configured": configured_vars,
            "total": total_vars,
            "missing": total_vars - configured_vars
        },
        "environment_variables": env_status
    } 