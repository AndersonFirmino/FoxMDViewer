"""Configuration module for mdviewer application.

This module provides centralized configuration management with environment
variable support and type safety using Pydantic.

Example:
    >>> from app.config import settings
    >>> print(settings.host)
    '127.0.0.1'
"""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support.

    Attributes:
        host: Server host address
        port: Server port (0 for auto-detection)
        debug: Enable debug mode
        base_dir: Base directory to scan for markdown files
        auto_open_browser: Automatically open browser on startup
        cache_enabled: Enable HTML caching
        cache_ttl: Cache time-to-live in seconds
        watch_files: Enable file watching with watchdog
        max_file_size: Maximum file size in bytes to process
    """

    host: str = Field(default="127.0.0.1", description="Server host")
    port: int = Field(default=0, description="Server port (0 = auto-detect)")
    debug: bool = Field(default=False, description="Debug mode")
    base_dir: Path = Field(default=Path.cwd(), description="Base directory to scan")
    auto_open_browser: bool = Field(default=True, description="Auto-open browser")
    cache_enabled: bool = Field(default=True, description="Enable HTML caching")
    cache_ttl: int = Field(default=300, description="Cache TTL in seconds")
    watch_files: bool = Field(default=True, description="Enable file watching")
    max_file_size: int = Field(default=10 * 1024 * 1024, description="Max file size")

    class Config:
        """Pydantic configuration."""

        env_prefix = "MDVIEWER_"
        env_file = ".env"
        case_sensitive = False


def get_settings(base_dir: Optional[Path] = None) -> Settings:
    """Get application settings with optional base directory override.

    Args:
        base_dir: Override base directory (defaults to current working directory)

    Returns:
        Settings: Configured settings instance

    Example:
        >>> settings = get_settings(Path("/home/user/docs"))
        >>> print(settings.base_dir)
        PosixPath('/home/user/docs')
    """
    if base_dir:
        return Settings(base_dir=base_dir.resolve())
    return Settings()


settings = get_settings()
