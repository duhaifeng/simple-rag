"""Application settings — env vars + profiles.yaml."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Core settings loaded from environment variables."""

    # --- Database ---
    pg_dsn: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/simple_rag"

    # --- Storage ---
    storage_dir: str = "./data/storage"  # local file storage for raw docs / parsed artifacts

    # --- Profiles config path ---
    profiles_path: str = str(Path(__file__).resolve().parent.parent.parent.parent / "configs" / "profiles.yaml")

    # --- Server ---
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    model_config = {"env_prefix": "RAG_", "env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()


def load_profiles(path: str | None = None) -> dict[str, Any]:
    """Load profiles.yaml and resolve ${ENV_VAR} placeholders."""
    path = path or get_settings().profiles_path
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()

    # Resolve ${VAR} placeholders from environment
    import re

    def _resolve(match: re.Match) -> str:
        var = match.group(1)
        return os.environ.get(var, match.group(0))

    resolved = re.sub(r"\$\{(\w+)}", _resolve, raw)
    return yaml.safe_load(resolved)
