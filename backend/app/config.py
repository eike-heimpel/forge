import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # MongoDB
    mongo_uri: str = os.getenv("MONGO_URI", "")
    mongo_database: str = os.getenv("MONGO_DATABASE", "forge")
    
    # OpenRouter/OpenAI API
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    
    # API Security - this secures the webhook endpoint
    forge_ai_api_key: str = os.getenv("FORGE_AI_API_KEY", "forge-dev-key-change-in-production")
    
    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")
    
    # Service configuration
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    
    # CORS origins for the frontend
    cors_origins: list = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://*.vercel.app"
    ]
    
    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings() 