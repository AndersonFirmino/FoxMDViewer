"""Data models for mdviewer application.

This module defines Pydantic models for type-safe data handling
throughout the application.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional, Pattern
import re

from pydantic import BaseModel, Field, field_validator


class MarkdownFile(BaseModel):
    """Represents a markdown file with metadata.

    Attributes:
        path: Absolute path to the file
        relative_path: Path relative to base directory
        filename: Name of the file
        size: File size in bytes
        modified_at: Last modification timestamp
        created_at: Creation timestamp (optional)
        title: Extracted title from file (optional)
        preview: First few lines of content (optional)
    """

    path: Path
    relative_path: str
    filename: str
    size: int = Field(ge=0, description="File size in bytes")
    modified_at: datetime
    created_at: Optional[datetime] = None
    title: Optional[str] = None
    preview: Optional[str] = Field(None, max_length=200)

    @field_validator("path")
    @classmethod
    def validate_path_exists(cls, value: Path) -> Path:
        """Ensure path exists and is absolute."""
        if not value.exists():
            raise ValueError(f"Path does not exist: {value}")
        if not value.is_absolute():
            raise ValueError(f"Path must be absolute: {value}")
        return value

    @field_validator("filename")
    @classmethod
    def validate_markdown_extension(cls, value: str) -> str:
        """Ensure file has .md extension."""
        if not value.endswith(".md"):
            raise ValueError(f"File must have .md extension: {value}")
        return value

    class Config:
        """Pydantic configuration."""

        json_encoders = {Path: str, datetime: lambda v: v.isoformat()}


class FileListResponse(BaseModel):
    """Response model for file list endpoint.

    Attributes:
        files: List of markdown files
        total_count: Total number of files found
        base_dir: Base directory that was scanned
        scan_time: Time taken to scan in seconds
    """

    files: list[MarkdownFile]
    total_count: int = Field(ge=0)
    base_dir: str
    scan_time: float = Field(ge=0.0)


class FileContentResponse(BaseModel):
    """Response model for file content endpoint.

    Attributes:
        file: File metadata
        raw_content: Raw markdown content
        html_content: Rendered HTML content
        cached: Whether content was served from cache
    """

    file: MarkdownFile
    raw_content: str
    html_content: str
    cached: bool = False


class FileUpdateEvent(BaseModel):
    """Event model for file system changes.

    Attributes:
        event_type: Type of event (created, modified, deleted)
        file_path: Path to the affected file
        timestamp: When the event occurred
    """

    event_type: str = Field(pattern=r"^(created|modified|deleted)$")
    file_path: Path
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        """Pydantic configuration."""

        json_encoders = {Path: str, datetime: lambda v: v.isoformat()}


class SearchQuery(BaseModel):
    """Search query model with filters.

    Attributes:
        query: Search string
        path_filter: Filter by path pattern (optional)
        case_sensitive: Case sensitive search
        limit: Maximum number of results
    """

    query: str = Field(min_length=1, max_length=1000)
    path_filter: Optional[str] = None
    case_sensitive: bool = False
    limit: int = Field(default=50, ge=1, le=1000)


class SearchResult(BaseModel):
    """Search result model.

    Attributes:
        file: File metadata
        matches: List of matching lines with context
        match_count: Number of matches found
    """

    file: MarkdownFile
    matches: list[dict[str, str]]
    match_count: int = Field(ge=0)
