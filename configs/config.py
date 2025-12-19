import os
import logging

# Check if we're in documentation build mode BEFORE loading .env
IS_DOCS_BUILD = os.getenv("SPHINX_BUILD", "").lower() in ("true", "1", "yes")

# Only load .env if not in docs build mode
if not IS_DOCS_BUILD:
    from dotenv import load_dotenv
    load_dotenv()

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, Field
from configs.logger import app_logger

class Settings(BaseSettings):
    """Application settings with defaults for documentation builds."""
    
    model_config = SettingsConfigDict(
        env_file=".env" if not IS_DOCS_BUILD else None,
        extra="ignore",
    )
    
    # Application metadata
    PROJECT_NAME: str = "Tickup API"
    VERSION: str = "1.0.0"

    # Database configuration
    # In docs build: use dummy values with async driver
    # In production: require .env values
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://localhost/tender_rag_docs",
        env="DATABASE_URL",
        description="PostgreSQL database URL (must use asyncpg driver)"
    )
    
    # Supabase configuration
    SUPABASE_PSW: str = Field(
        default="dummy_password_for_docs",
        env="SUPABASE_PSW",
        description="Supabase database password"
    )
    SUPABASE_URL: str = Field(
        default="https://dummy.supabase.co",
        env="SUPABASE_URL",
        description="Supabase project URL"
    )
    SUPABASE_KEY: SecretStr = Field(
        default="dummy_key_for_docs",
        env="SUPABASE_KEY",
        description="Supabase anon/public key"
    )
    SUPABASE_JWT: str = Field(
        default="dummy_jwt_for_docs",
        env="SUPABASE_JWT",
        description="Supabase JWT secret"
    )
    SUPABASE_SERVICE_ROLE_KEY: SecretStr | None = Field(
        default=None,
        env="SUPABASE_SERVICE_ROLE_KEY",
        description="Supabase service role key (optional)"
    )
    
    # Storage configuration
    STORAGE_BUCKET: str | None = Field(
        default="documents",
        env="STORAGE_BUCKET",
        description="Supabase storage bucket name"
    )

settings = Settings()
logger = app_logger.get_logger(__name__)
