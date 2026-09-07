"""
app/config.py

Centralised configuration manager for the Sovereign AI Workbench.

Settings are loaded from environment variables, with an optional
.env file at the project root.  Every variable has a sensible
default so the application starts correctly on a fresh clone
without any manual configuration.

Usage anywhere in the application:

    from app.config import settings

    url  = settings.ollama_base_url
    path = settings.db_path
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# ---------------------------------------------------------------------------
# Resolve project root so relative paths in .env work regardless of the
# working directory the server process is started from.
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parents[1]
_ENV_FILE = _ROOT / ".env"


class Settings(BaseSettings):
    """
    Application settings.

    Priority order (highest → lowest):
        1. Real environment variables set in the shell / OS
        2. Variables in .env (if the file exists)
        3. The defaults declared below
    """

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        # Unknown env vars are silently ignored — safe in production.
        extra="ignore",
        # Allow attribute access on the frozen model.
        frozen=True,
    )

    # ------------------------------------------------------------------
    # AI Models
    # ------------------------------------------------------------------

    ollama_base_url: str = Field(
        default="http://127.0.0.1:11434",
        description="Base URL of the local Ollama daemon.",
    )

    main_model: str = Field(
        default="qwen3:4b",
        description="Primary reasoning / general-purpose model.",
    )

    code_model: str = Field(
        default="qwen2.5-coder:7b",
        description="Code generation and debugging model.",
    )

    vision_model: str = Field(
        default="qwen2.5vl:3b",
        description="Vision / multimodal model.",
    )

    ollama_timeout: int = Field(
        default=120,
        ge=5,
        description="Inference request timeout in seconds.",
    )

    # ------------------------------------------------------------------
    # Storage — stored as strings; use .resolved_* properties for Paths
    # ------------------------------------------------------------------

    upload_dir: str = Field(
        default="data/uploads",
        description="Directory for user-uploaded files.",
    )

    db_path: str = Field(
        default="data/app.db",
        description="SQLite database file path.",
    )

    chroma_dir: str = Field(
        default="data/vector_db",
        description="ChromaDB vector store directory.",
    )

    artifact_dir: str = Field(
        default="data/artifacts",
        description="Generated Office artifact output directory.",
    )

    audit_log_path: str = Field(
        default="logs/audit.jsonl",
        description="Append-only JSONL sovereignty audit log.",
    )

    executions_dir: str = Field(
        default="data/executions",
        description="Scratch space for sandbox temp files.",
    )

    # ------------------------------------------------------------------
    # Security
    # ------------------------------------------------------------------

    sovereign_mode: bool = Field(
        default=True,
        description=(
            "Block any non-loopback outbound connection attempt "
            "detected by the application's NetworkMonitor."
        ),
    )

    sandbox_network_mode: str = Field(
        default="none",
        description='Docker network mode for sandboxed execution ("none" recommended).',
    )

    sandbox_image: str = Field(
        default="python:3.13-slim",
        description="Docker image for the Python sandbox.",
    )

    sandbox_timeout: int = Field(
        default=10,
        ge=1,
        description="Maximum sandbox execution time in seconds.",
    )

    sandbox_memory: str = Field(
        default="512m",
        description="Memory cap for each sandbox container.",
    )

    # ------------------------------------------------------------------
    # API Server
    # ------------------------------------------------------------------

    api_host: str = Field(
        default="127.0.0.1",
        description="Bind address for the Uvicorn server.",
    )

    api_port: int = Field(
        default=8000,
        ge=1,
        le=65535,
    )

    log_level: str = Field(
        default="info",
        description="Uvicorn / application log level.",
    )

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------

    @field_validator("ollama_base_url")
    @classmethod
    def _must_be_local(cls, v: str) -> str:
        """
        Reject any Ollama URL that is not a loopback address.

        This is an early-startup guard — it fires before any request
        is processed, so a misconfigured OLLAMA_BASE_URL is caught
        immediately rather than at inference time.
        """
        allowed_prefixes = (
            "http://127.0.0.1",
            "http://localhost",
            "http://[::1]",
        )
        if not any(v.startswith(p) for p in allowed_prefixes):
            raise ValueError(
                f"OLLAMA_BASE_URL must point to a loopback address "
                f"in sovereign mode. Got: {v!r}"
            )
        return v

    @field_validator("log_level")
    @classmethod
    def _normalise_log_level(cls, v: str) -> str:
        valid = {"debug", "info", "warning", "error", "critical"}
        norm = v.lower().strip()
        if norm not in valid:
            raise ValueError(
                f"LOG_LEVEL must be one of {valid}. Got: {v!r}"
            )
        return norm

    # ------------------------------------------------------------------
    # Resolved Path helpers
    # Paths in .env are relative to the project root; these properties
    # return absolute Path objects ready for use in os/Path calls.
    # ------------------------------------------------------------------

    @property
    def resolved_upload_dir(self) -> Path:
        return (_ROOT / self.upload_dir).resolve()

    @property
    def resolved_db_path(self) -> Path:
        return (_ROOT / self.db_path).resolve()

    @property
    def resolved_chroma_dir(self) -> Path:
        return (_ROOT / self.chroma_dir).resolve()

    @property
    def resolved_artifact_dir(self) -> Path:
        return (_ROOT / self.artifact_dir).resolve()

    @property
    def resolved_audit_log_path(self) -> Path:
        return (_ROOT / self.audit_log_path).resolve()

    @property
    def resolved_executions_dir(self) -> Path:
        return (_ROOT / self.executions_dir).resolve()


# ---------------------------------------------------------------------------
# Module-level singleton — import this everywhere
# ---------------------------------------------------------------------------

settings = Settings()
