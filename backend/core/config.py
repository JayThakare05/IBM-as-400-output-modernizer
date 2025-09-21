# core/config.py - Application Configuration
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""

    # App Info
    APP_NAME: str = "AS/400 Legacy Modernization API"
    APP_DESCRIPTION: str = "AI-Powered API for modernizing legacy AS/400 systems"
    APP_VERSION: str = "2.0.0"

    # Server
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    DEBUG: bool = Field(default=True, env="DEBUG")

    # CORS
    ALLOWED_HOSTS: List[str] = Field(default=["*"], env="ALLOWED_HOSTS")

    # AI/ML
    AI_MODEL_NAME: str = Field(default="google/flan-t5-small", env="AI_MODEL_NAME")
    ENABLE_AI_PROCESSING: bool = Field(default=True, env="ENABLE_AI_PROCESSING")

    # File Processing
    MAX_FILE_SIZE_MB: int = Field(default=50, env="MAX_FILE_SIZE_MB")
    MAX_RECORDS_DISPLAY: int = Field(default=1000, env="MAX_RECORDS_DISPLAY")

    # Caching
    ENABLE_CACHING: bool = Field(default=True, env="ENABLE_CACHING")
    CACHE_TTL_SECONDS: int = Field(default=300, env="CACHE_TTL_SECONDS")

    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="json", env="LOG_FORMAT")

    # ✅ Pydantic v2 way of handling config
    model_config = {
        "env_file": ".env",
        "case_sensitive": True
    }


# Create global settings instance
settings = Settings()


# Environment-specific configurations
class DevelopmentConfig(Settings):
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"


class ProductionConfig(Settings):
    DEBUG: bool = False
    LOG_LEVEL: str = "WARNING"
    ALLOWED_HOSTS: List[str] = ["yourdomain.com", "api.yourdomain.com"]


class TestingConfig(Settings):
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    ENABLE_AI_PROCESSING: bool = False  # Disable AI for faster testing


def get_settings() -> Settings:
    """Get settings based on environment"""
    env = os.getenv("ENVIRONMENT", "development").lower()

    if env == "production":
        return ProductionConfig()
    elif env == "testing":
        return TestingConfig()
    else:
        return DevelopmentConfig()
