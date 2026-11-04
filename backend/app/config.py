from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, read from environment variables (see .env.example)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "DocVerify AI"
    database_url: str = "postgresql+psycopg://docverify:docverify@db:5432/docverify"

    jwt_secret: str = "change-me-in-production-please-use-a-long-random-string"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60

    upload_dir: str = "/data/uploads"
    max_upload_mb: int = 10

    # Login lockout (US-02)
    max_failed_logins: int = 5
    lockout_minutes: int = 10

    # First admin account, created on startup if no admin exists
    admin_email: str = "admin@docverify.local"
    admin_password: str = "ChangeMe-Admin-123"

    cors_origins: str = "http://localhost:8080,http://localhost:5173"

    # Phase 3: separate AI service
    ai_service_url: str = "http://ai-service:8001"


@lru_cache
def get_settings() -> Settings:
    return Settings()
