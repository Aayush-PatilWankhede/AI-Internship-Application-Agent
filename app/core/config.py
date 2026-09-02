"""Application settings loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the FastAPI application."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AI Internship Agent"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/internship_agent"
    upload_dir: Path = Path("uploads")
    max_upload_size_mb: int = 10
    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "gpt-oss:120b-cloud"

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    cookie_secure: bool = False
    cookie_samesite: str = "lax"
    access_cookie_name: str = "access_token"
    refresh_cookie_name: str = "refresh_token"

    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> list[str]:
        """Strip trailing slashes from origins and accept comma-separated strings."""
        if isinstance(value, str):
            value_str = value.strip()
            if value_str.startswith("[") and value_str.endswith("]"):
                import json
                try:
                    parsed = json.loads(value_str)
                    if isinstance(parsed, list):
                        return [str(origin).strip().rstrip("/") for origin in parsed if str(origin).strip()]
                except Exception:
                    pass
            return [origin.strip().rstrip("/") for origin in value_str.split(",") if origin.strip()]
        if isinstance(value, (list, tuple, set)):
            return [str(origin).strip().rstrip("/") for origin in value if str(origin).strip()]
        return value  # type: ignore[return-value]

    latex_compiler_path: str = "pdflatex"
    latex_compile_timeout_seconds: int = 60
    resume_template_path: Path = Path("app/templates/resume/resume_template.tex.j2")
    tailored_resume_dir: Path = Path("tailored_resumes")
    cover_letter_template_path: Path = Path(
        "app/templates/cover_letter/cover_letter_template.tex.j2"
    )
    tailored_cover_letter_dir: Path = Path("tailored_cover_letters")


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
