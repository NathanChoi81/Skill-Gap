"""Application configuration from environment."""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "local"
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    database_url: str = "sqlite:///./skillgap.db"
    ollama_base_url: str = "http://localhost:11434"
    cors_origins: str = "http://localhost:5173"
    max_resume_mb: int = 5
    log_level: str = "info"

    # Cookie names
    access_token_cookie_name: str = "skillgap_access_token"
    refresh_token_cookie_name: str = "skillgap_refresh_token"

    @property
    def is_local(self) -> bool:
        return self.app_env.lower() == "local"

    @property
    def cookie_secure(self) -> bool:
        """Secure flag for cookies: off on localhost so HTTP works in dev."""
        return not self.is_local

    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
