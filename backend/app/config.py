"""
Configuration settings for the Forge AI backend
"""
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Required settings
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_database: str = "forge"
    openrouter_api_key: str
    forge_ai_api_key: str
    
    # Optional settings
    environment: str = "development"
    log_level: str = "INFO"
    
    # CORS origins for FastAPI
    cors_origins: list = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://*.vercel.app"
    ]
    
    model_config = ConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings() 