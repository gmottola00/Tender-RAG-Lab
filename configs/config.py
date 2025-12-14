from dotenv import load_dotenv
load_dotenv()

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, Field
from configs.logger import app_logger
import logging

class Settings(BaseSettings):
    # carica .env, ignora eventuali chiavi non dichiarate
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )
    # logger.debug(model_config)
    # valori di default
    PROJECT_NAME: str = "Tickup API"
    VERSION: str = "1.0.0"

    # qui mappi esattamente le chiavi che hai nel .env
    DATABASE_URL: str       = Field(..., env="DATABASE_URL")
    SUPABASE_PSW: str       = Field(..., env="SUPABASE_PSW")
    SUPABASE_URL: str       = Field(..., env="SUPABASE_URL")
    SUPABASE_KEY: SecretStr = Field(..., env="SUPABASE_KEY")
    SUPABASE_JWT: str       = Field(..., env="SUPABASE_JWT")
    # Optional service-role key for server-side storage operations
    SUPABASE_SERVICE_ROLE_KEY: SecretStr | None = Field(
        default=None, env="SUPABASE_SERVICE_ROLE_KEY"
    )
    STORAGE_BUCKET: str | None = Field(default=None, env="STORAGE_BUCKET")

settings = Settings()
logger = app_logger.get_logger(__name__)
