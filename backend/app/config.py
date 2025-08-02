import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # MongoDB
    mongo_uri: str = os.getenv("MONGO_URI", "")
    
    # OpenRouter API
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_model: str = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-exp")
    
    # API Security
    forge_ai_api_key: str = os.getenv("FORGE_AI_API_KEY", "forge-dev-key-change-in-production")
    
    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")
    
    # Optional service configuration
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields instead of raising errors

settings = Settings() 