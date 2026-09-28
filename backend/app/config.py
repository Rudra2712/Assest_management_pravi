import os
from functools import lru_cache
from pathlib import Path
from typing import Any, List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent

# Vercel sets this automatically in every serverless function invocation.
# Detecting it lets local dev and Vercel share one codebase without env-file
# gymnastics: only the filesystem path and DB pooling strategy need to differ.
IS_SERVERLESS = bool(os.environ.get("VERCEL"))
DEFAULT_UPLOAD_DIR = Path("/tmp/uploads") if IS_SERVERLESS else BACKEND_DIR / "uploads"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENVIRONMENT: str = "development"
    APP_NAME: str = "R&B Asset Inventory"
    API_V1_PREFIX: str = "/api/v1"

    SECRET_KEY: str = "dev-secret-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://assest-management-pravi.vercel.app",
    ]

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_url(cls, v: Any) -> Any:
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("postgres://"):
                return v.replace("postgres://", "postgresql+psycopg://", 1)
            if v.startswith("postgresql://") and not v.startswith("postgresql+"):
                return v.replace("postgresql://", "postgresql+psycopg://", 1)
        return v

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> Any:
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [x.strip() for x in v.split(",") if x.strip()]
        return v

    # Normal locally-installed PostgreSQL. No PostGIS or Docker required.
    DATABASE_URL: str = "postgresql+psycopg://rb_admin:rb_dev_password@localhost:5432/rb_assets"

    # Local filesystem storage for the hackathon MVP. Swappable for S3 later via
    # app.utils.storage without touching document business logic.
    # On Vercel this lands in /tmp, which is NOT persistent across invocations —
    # see docs/deployment.md for why document uploads need external storage there.
    UPLOAD_DIR: Path = DEFAULT_UPLOAD_DIR
    MAX_UPLOAD_SIZE_MB: int = 25
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = [
        ".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx", ".xls", ".xlsx", ".dwg"
    ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
