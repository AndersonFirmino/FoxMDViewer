"""Unit tests for Pydantic Models."""

from datetime import datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.models.file import (
    MarkdownFile,
    FileListResponse,
    FileContentResponse,
    FileUpdateEvent,
    SearchQuery,
    SearchResult,
)


class TestMarkdownFile:
    """Test suite for MarkdownFile model."""

    def test_markdown_file_creation(self, temp_markdown_file):
        """Test creating a valid MarkdownFile instance."""
        stat = temp_markdown_file.stat()

        md_file = MarkdownFile(
            path=temp_markdown_file,
            relative_path="test.md",
            filename="test.md",
            size=stat.st_size,
            modified_at=datetime.fromtimestamp(stat.st_mtime),
            title="Test",
            preview="Test content",
        )

        assert md_file.path == temp_markdown_file
        assert md_file.filename == "test.md"
        assert md_file.title == "Test"

    def test_markdown_file_requires_md_extension(self, temp_directory):
        """Test that filename must have .md extension."""
        txt_file = temp_directory / "test.txt"
        txt_file.write_text("test")

        with pytest.raises(ValidationError, match=".md extension"):
            MarkdownFile(
                path=txt_file,
                relative_path="test.txt",
                filename="test.txt",
                size=100,
                modified_at=datetime.now(),
                preview=None,
            )

    def test_markdown_file_validates_path_exists(self):
        """Test that path must exist."""
        nonexistent = Path("/nonexistent/file.md")

        with pytest.raises(ValidationError, match="does not exist"):
            MarkdownFile(
                path=nonexistent,
                relative_path="file.md",
                filename="file.md",
                size=100,
                modified_at=datetime.now(),
                preview=None,
            )

    def test_markdown_file_validates_absolute_path(self, temp_markdown_file):
        """Test that path must be absolute."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(temp_markdown_file.parent)
            md_file = MarkdownFile(
                path=temp_markdown_file,
                relative_path="test.md",
                filename="test.md",
                size=100,
                modified_at=datetime.now(),
                preview=None,
            )
            assert md_file.path.is_absolute()
        finally:
            os.chdir(original_cwd)

    def test_markdown_file_optional_fields(self, temp_markdown_file):
        """Test that title and preview are optional."""
        stat = temp_markdown_file.stat()

        md_file = MarkdownFile(
            path=temp_markdown_file,
            relative_path="test.md",
            filename="test.md",
            size=stat.st_size,
            modified_at=datetime.fromtimestamp(stat.st_mtime),
            preview=None,
        )

        assert md_file.title is None
        assert md_file.preview is None

    def test_markdown_file_size_validation(self, temp_markdown_file):
        """Test that size must be non-negative."""
        with pytest.raises(ValidationError):
            MarkdownFile(
                path=temp_markdown_file,
                relative_path="test.md",
                filename="test.md",
                size=-1,
                modified_at=datetime.now(),
                preview=None,
            )


class TestFileListResponse:
    """Test suite for FileListResponse model."""

    def test_file_list_response_creation(self, temp_markdown_file):
        """Test creating FileListResponse."""
        stat = temp_markdown_file.stat()
        md_file = MarkdownFile(
            path=temp_markdown_file,
            relative_path="test.md",
            filename="test.md",
            size=stat.st_size,
            modified_at=datetime.fromtimestamp(stat.st_mtime),
            preview=None,
        )

        response = FileListResponse(
            files=[md_file], total_count=1, base_dir="/test/dir", scan_time=0.5
        )

        assert len(response.files) == 1
        assert response.total_count == 1
        assert response.scan_time == 0.5

    def test_file_list_response_validates_count(self):
        """Test that total_count must be non-negative."""
        with pytest.raises(ValidationError):
            FileListResponse(files=[], total_count=-1, base_dir="/test", scan_time=0.1)


class TestFileContentResponse:
    """Test suite for FileContentResponse model."""

    def test_file_content_response_creation(self, temp_markdown_file):
        """Test creating FileContentResponse."""
        stat = temp_markdown_file.stat()
        md_file = MarkdownFile(
            path=temp_markdown_file,
            relative_path="test.md",
            filename="test.md",
            size=stat.st_size,
            modified_at=datetime.fromtimestamp(stat.st_mtime),
            preview=None,
        )

        response = FileContentResponse(
            file=md_file,
            raw_content="# Test",
            html_content="<h1>Test</h1>",
            cached=False,
        )

        assert response.raw_content == "# Test"
        assert response.html_content == "<h1>Test</h1>"
        assert not response.cached


class TestFileUpdateEvent:
    """Test suite for FileUpdateEvent model."""

    def test_file_update_event_creation(self, temp_markdown_file):
        """Test creating FileUpdateEvent."""
        event = FileUpdateEvent(event_type="modified", file_path=temp_markdown_file)

        assert event.event_type == "modified"
        assert event.file_path == temp_markdown_file
        assert event.timestamp is not None

    def test_file_update_event_validates_type(self, temp_markdown_file):
        """Test that event_type must be valid."""
        with pytest.raises(ValidationError):
            FileUpdateEvent(event_type="invalid", file_path=temp_markdown_file)

    def test_file_update_event_valid_types(self, temp_markdown_file):
        """Test all valid event types."""
        for event_type in ["created", "modified", "deleted"]:
            event = FileUpdateEvent(event_type=event_type, file_path=temp_markdown_file)
            assert event.event_type == event_type


class TestSearchQuery:
    """Test suite for SearchQuery model."""

    def test_search_query_creation(self):
        """Test creating SearchQuery."""
        query = SearchQuery(
            query="test search", path_filter="docs/", case_sensitive=True, limit=100
        )

        assert query.query == "test search"
        assert query.path_filter == "docs/"
        assert query.case_sensitive is True
        assert query.limit == 100

    def test_search_query_defaults(self):
        """Test SearchQuery default values."""
        query = SearchQuery(query="test")

        assert query.path_filter is None
        assert query.case_sensitive is False
        assert query.limit == 50

    def test_search_query_validates_query_length(self):
        """Test that query has length constraints."""
        with pytest.raises(ValidationError):
            SearchQuery(query="")

        with pytest.raises(ValidationError):
            SearchQuery(query="x" * 1001)

    def test_search_query_validates_limit(self):
        """Test that limit is within bounds."""
        with pytest.raises(ValidationError):
            SearchQuery(query="test", limit=0)

        with pytest.raises(ValidationError):
            SearchQuery(query="test", limit=1001)


class TestSearchResult:
    """Test suite for SearchResult model."""

    def test_search_result_creation(self, temp_markdown_file):
        """Test creating SearchResult."""
        stat = temp_markdown_file.stat()
        md_file = MarkdownFile(
            path=temp_markdown_file,
            relative_path="test.md",
            filename="test.md",
            size=stat.st_size,
            modified_at=datetime.fromtimestamp(stat.st_mtime),
            preview=None,
        )

        result = SearchResult(
            file=md_file,
            matches=[{"line_number": "1", "line": "test line", "context": "context"}],
            match_count=1,
        )

        assert len(result.matches) == 1
        assert result.match_count == 1
