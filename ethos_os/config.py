"""Configuration loader for EthosOS.

Supports loading from:
1. Environment variables (highest priority)
2. .env file in project root
3. ethos.yaml config file (if exists)
4. Default values
"""

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class EthosSettings(BaseSettings):
    """EthosOS application settings."""

    # Database
    database_url: str = Field(
        default="sqlite:///./ethos_os.db",
        description="SQLAlchemy database URL"
    )

    # Qdrant Vector Database
    qdrant_url: str = Field(
        default="http://localhost:6333",
        description="Qdrant server URL"
    )
    qdrant_api_key: str = Field(
        default="",
        description="Qdrant API key"
    )

    # Heartbeat Configuration
    heartbeat_interval: int = Field(
        default=30,
        description="Heartbeat interval in seconds"
    )

    # Working Memory TTL
    working_memory_ttl: int = Field(
        default=3600,
        description="Working memory TTL in seconds (default: 1 hour)"
    )

    # Debug Mode
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


def _load_yaml_config() -> dict[str, Any]:
    """Load configuration from ethos.yaml if it exists."""
    config_path = Path("ethos.yaml")
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f) or {}
    return {}


@lru_cache
def get_settings() -> EthosSettings:
    """Get cached settings instance.
    
    Settings are loaded once and cached. To reload after changing config,
    clear the cache: get_settings.cache_clear()
    """
    yaml_config = _load_yaml_config()
    
    # Merge YAML config with defaults (environment variables override)
    settings_dict = {}
    if yaml_config:
        settings_dict = yaml_config.get("ethos", {})
    
    return EthosSettings(**settings_dict)