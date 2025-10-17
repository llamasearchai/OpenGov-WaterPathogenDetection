"""Configuration management for OpenGov-WaterPathogenDetection (Pydantic v2 style)."""

from functools import lru_cache
from typing import Optional
import os

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings for OpenGov-WaterPathogenDetection.

    Environment variable mapping uses the OPENWATERPATHOGENDETECTION_ prefix by default where explicit
    env var names are not provided. Explicit names are retained only where they differ or are
    shared (e.g., OPENAI_API_KEY).
    """

    # Pydantic settings configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
        env_prefix="OPENWATERPATHOGENDETECTION_"  # Enables prefixed environment variables
    )

    # Application
    app_name: str = "OpenGov-WaterPathogenDetection"
    version: str = "1.0.0"
    debug: bool = False  # OPENWATERPATHOGENDETECTION_DEBUG

    # Database
    database_url: str = "sqlite:///data/opengovwaterpathogendetection.db"  # OPENWATERPATHOGENDETECTION_DATABASE_URL

    # AI/LLM Providers
    openai_api_key: Optional[str] = None  # Supports OPENAI_API_KEY (unprefixed) or OPENWATERPATHOGENDETECTION_OPENAI_API_KEY
    openai_model: str = "gpt-4"  # OPENWATERPATHOGENDETECTION_OPENAI_MODEL
    ollama_base_url: str = "http://localhost:11434"  # OPENWATERPATHOGENDETECTION_OLLAMA_BASE_URL
    ollama_model: str = "llama2:7b"  # OPENWATERPATHOGENDETECTION_OLLAMA_MODEL

    # Logging
    log_level: str = "INFO"  # OPENWATERPATHOGENDETECTION_LOG_LEVEL
    structured_logging: bool = True  # OPENWATERPATHOGENDETECTION_STRUCTURED_LOGGING

    # Performance
    max_concurrent_analyses: int = 5  # OPENWATERPATHOGENDETECTION_MAX_CONCURRENT_ANALYSES
    request_timeout: int = 300  # OPENWATERPATHOGENDETECTION_REQUEST_TIMEOUT

    @field_validator("debug", mode="before")
    @classmethod
    def _coerce_debug(cls, v):  # noqa: D401
        """Coerce common truthy string forms to boolean."""
        if isinstance(v, str):
            return v.lower() in {"1", "true", "yes", "on"}
        return v

    @field_validator("openai_api_key", mode="before")
    @classmethod
    def _load_openai_key(cls, v):  # noqa: D401
        """Allow unprefixed OPENAI_API_KEY to populate setting.

        With env_prefix configured, the framework will look for
        OPENWATERPATHOGENDETECTION_OPENAI_API_KEY by default. This validator adds
        support for the more common OPENAI_API_KEY without the project
        prefix when the prefixed variant is not provided.
        """
        if v:  # already provided (prefixed variant)
            return v
        return os.getenv("OPENAI_API_KEY") or v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance (avoids re-parsing env)."""
    return Settings()  # type: ignore[call-arg]


def reload_settings() -> Settings:
    """Clear the settings cache and return a fresh Settings instance.

    Useful for tests that need to observe environment variable changes
    after the first call to get_settings(). Production code should almost
    always call get_settings() for efficiency.
    """
    get_settings.cache_clear()
    return get_settings()