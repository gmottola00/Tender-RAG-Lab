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
    
    # Neo4j Knowledge Graph configuration
    NEO4J_URI: str = Field(
        default="bolt://localhost:7687",
        env="NEO4J_URI",
        description="Neo4j connection URI (bolt:// for local, neo4j+s:// for Aura)"
    )
    NEO4J_USER: str = Field(
        default="neo4j",
        env="NEO4J_USER",
        description="Neo4j username",
        validation_alias="NEO4J_USERNAME"  # Support both NEO4J_USER and NEO4J_USERNAME
    )
    NEO4J_PASSWORD: str = Field(
        default="neo4j",
        env="NEO4J_PASSWORD",
        description="Neo4j password"
    )
    NEO4J_DATABASE: str = Field(
        default="neo4j",
        env="NEO4J_DATABASE",
        description="Neo4j database name"
    )
    NEO4J_ENV: str = Field(
        default="local",
        env="NEO4J_ENV",
        description="Neo4j environment: local (Docker) or aura (Cloud)"
    )
    
    # Neo4j Aura specific (optional, for monitoring/metadata)
    AURA_INSTANCEID: str | None = Field(
        default=None,
        env="AURA_INSTANCEID",
        description="Neo4j Aura instance ID (cloud only)"
    )
    AURA_INSTANCENAME: str | None = Field(
        default=None,
        env="AURA_INSTANCENAME",
        description="Neo4j Aura instance name (cloud only)"
    )
    
    @property
    def is_neo4j_aura(self) -> bool:
        """Check if using Neo4j Aura (cloud)."""
        return self.NEO4J_ENV == "aura" or self.NEO4J_URI.startswith("neo4j+s://")

settings = Settings()
logger = app_logger.get_logger(__name__)

def get_settings() -> Settings:
    """
    Get application settings singleton.
    
    Returns:
        Settings instance
    """
    return settings
