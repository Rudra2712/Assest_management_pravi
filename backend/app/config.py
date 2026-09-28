from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENVIRONMENT: str = "development"
    APP_NAME: str = "R&B Asset Inventory"
    API_V1_PREFIX: str = "/api/v1"

    SECRET_KEY: str = "dev-secret-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173"]

    # Normal locally-installed PostgreSQL + PostGIS. No Docker required.
    DATABASE_URL: str = "postgresql+psycopg://rb_admin:rb_dev_password@localhost:5432/rb_assets"

    # Local filesystem storage for the hackathon MVP. Swappable for S3 later via
    # app.utils.storage without touching document business logic.
    UPLOAD_DIR: Path = BACKEND_DIR / "uploads"
    MAX_UPLOAD_SIZE_MB: int = 25
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = [
        ".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx", ".xls", ".xlsx", ".dwg", ".csv"
    ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
