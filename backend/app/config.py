"""
DevCrew Backend — Application Configuration

All settings are loaded from environment variables (or .env file).
Never hard-code secrets. Use .env.example as a reference.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ─────────────────────────────────────────────────────────
    app_env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = False
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    frontend_url: str = "http://localhost:5173"

    # ── Security ────────────────────────────────────────────────────────────
    jwt_secret: str = Field(..., min_length=32)
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    # ── Database ────────────────────────────────────────────────────────────
    database_url: str = Field(
        default="postgresql+asyncpg://devcrew:devcrew_password@localhost:5432/devcrew"
    )
    database_url_sync: str = Field(
        default="postgresql://devcrew:devcrew_password@localhost:5432/devcrew"
    )

    # ── LLM Providers ───────────────────────────────────────────────────────
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"

    # Google Gemini (free tier) — https://aistudio.google.com/app/apikey
    gemini_api_key: str = ""
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai"

    # ── Model Routing ───────────────────────────────────────────────────────
    # Defaults to Groq (free tier) — override via environment variables in production
    primary_model: str = "llama-3.3-70b-versatile"
    primary_provider: str = "groq"

    coding_model: str = "llama-3.3-70b-versatile"
    coding_provider: str = "groq"

    fast_model: str = "llama-3.1-8b-instant"
    fast_provider: str = "groq"

    # ── ChromaDB ────────────────────────────────────────────────────────────
    chroma_host: str = "localhost"
    chroma_port: int = 8001
    chroma_url: str = "http://localhost:8001"

    # ── GitHub ──────────────────────────────────────────────────────────────
    github_token: str = ""
    github_username: str = ""

    # ── Workspace ───────────────────────────────────────────────────────────
    workspace_base_path: str = "./workspaces"
    max_workspace_size_mb: int = 500

    # ── Sandbox ─────────────────────────────────────────────────────────────
    sandbox_timeout_seconds: int = 60
    sandbox_max_output_bytes: int = 1_048_576  # 1 MB
    enable_docker_sandbox: bool = False

    # ── Agent Limits ────────────────────────────────────────────────────────
    max_iterations_per_project: int = 10
    max_retries_per_agent: int = 3

    # ── Rate Limiting ───────────────────────────────────────────────────────
    rate_limit_requests_per_minute: int = 60
    max_concurrent_projects_per_user: int = 3

    @field_validator("database_url", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str) -> str:
        if isinstance(v, str):
            if v.startswith("postgres://"):
                return v.replace("postgres://", "postgresql+asyncpg://", 1)
            elif v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
                return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters long.")
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def cors_origins(self) -> list[str]:
        return [
            self.frontend_url,
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:5174",
            "http://localhost:5175",
            "http://localhost:5176",
            "http://localhost:5177",
        ]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance. Call this everywhere instead of Settings()."""
    return Settings()
