"""Unit tests for the Markdown Scanner."""

import os
import tempfile
from pathlib import Path

import pytest

from foxmdviewer.utils.scanner import MarkdownScanner, scan_markdown_files


class TestMarkdownScanner:
    """Test suite for MarkdownScanner class."""

    def test_scanner_init_with_valid_directory(self, temp_directory):
        """Test scanner initialization with valid directory."""
        scanner = MarkdownScanner(temp_directory)

        assert scanner.base_dir == temp_directory.resolve()
        assert scanner.max_depth is None
        assert ".git" in scanner.exclude_dirs

    def test_scanner_init_with_invalid_directory(self):
        """Test scanner initialization with invalid directory."""
        with pytest.raises(ValueError, match="does not exist"):
            MarkdownScanner(Path("/nonexistent/path"))

    def test_scanner_init_with_file_not_directory(self, temp_markdown_file):
        """Test scanner initialization with file instead of directory."""
        with pytest.raises(ValueError, match="not a directory"):
            MarkdownScanner(temp_markdown_file)

    def test_scan_empty_directory(self, temp_directory):
        """Test scanning empty directory returns no files."""
        scanner = MarkdownScanner(temp_directory)
        files = scanner.scan()

        assert files == []

    def test_scan_single_markdown_file(self, temp_markdown_file):
        """Test scanning directory with single markdown file."""
        scanner = MarkdownScanner(temp_markdown_file.parent)
        files = scanner.scan()

        assert len(files) == 1
        assert files[0].filename == "test.md"
        assert files[0].title == "Test Title"

    def test_scan_multiple_markdown_files(self, temp_markdown_files):
        """Test scanning directory with multiple markdown files."""
        scanner = MarkdownScanner(temp_markdown_files[0].parent.parent)
        files = scanner.scan()

        assert len(files) == 5

        filenames = [f.filename for f in files]
        assert "README.md" in filenames
        assert "CHANGELOG.md" in filenames
        assert "guide.md" in filenames
        assert "api.md" in filenames
        assert "config.md" in filenames

    def test_scan_respects_exclude_dirs(self, temp_directory):
        """Test that scanner excludes specified directories."""
        # Create .git directory with markdown file
        git_dir = temp_directory / ".git"
        git_dir.mkdir()
        (git_dir / "README.md").write_text("# Git README")

        # Create regular markdown file
        (temp_directory / "regular.md").write_text("# Regular")

        scanner = MarkdownScanner(temp_directory)
        files = scanner.scan()

        assert len(files) == 1
        assert files[0].filename == "regular.md"

    def test_scan_respects_max_depth(self, temp_directory):
        """Test that scanner respects max_depth parameter."""
        # Create nested structure
        level1 = temp_directory / "level1"
        level2 = level1 / "level2"
        level3 = level2 / "level3"
        level3.mkdir(parents=True)

        (temp_directory / "root.md").write_text("# Root")
        (level1 / "l1.md").write_text("# Level 1")
        (level2 / "l2.md").write_text("# Level 2")
        (level3 / "l3.md").write_text("# Level 3")

        scanner = MarkdownScanner(temp_directory, max_depth=1)
        files = scanner.scan()

        filenames = [f.filename for f in files]
        assert "root.md" in filenames
        assert "l1.md" in filenames
        assert "l2.md" not in filenames
        assert "l3.md" not in filenames

    def test_extract_title_from_h1(self, temp_directory):
        """Test title extraction from H1 heading."""
        md_file = temp_directory / "title_test.md"
        md_file.write_text("# My Awesome Title\n\nContent here.")

        scanner = MarkdownScanner(temp_directory)
        files = scanner.scan()

        assert files[0].title == "My Awesome Title"

    def test_extract_title_none_if_no_h1(self, temp_directory):
        """Test title is None when no H1 heading exists."""
        md_file = temp_directory / "no_title.md"
        md_file.write_text("## Subtitle\n\nNo main title.")

        scanner = MarkdownScanner(temp_directory)
        files = scanner.scan()

        assert files[0].title is None

    def test_extract_preview(self, temp_directory):
        """Test preview extraction from content."""
        md_file = temp_directory / "preview.md"
        md_file.write_text(
            "# Title\n\nThis is the first paragraph.\n\nSecond paragraph here."
        )

        scanner = MarkdownScanner(temp_directory)
        files = scanner.scan()

        preview = files[0].preview
        assert preview is not None
        assert "first paragraph" in preview
        assert "Second paragraph" in preview

    def test_file_metadata(self, temp_markdown_file):
        """Test that file metadata is correctly extracted."""
        scanner = MarkdownScanner(temp_markdown_file.parent)
        files = scanner.scan()

        file = files[0]

        assert file.path == temp_markdown_file
        assert file.filename == "test.md"
        assert file.relative_path == "test.md"
        assert file.size > 0
        assert file.modified_at is not None

    def test_scan_non_markdown_files_ignored(self, temp_directory):
        """Test that non-markdown files are ignored."""
        (temp_directory / "document.md").write_text("# MD File")
        (temp_directory / "script.py").write_text("print('hello')")
        (temp_directory / "data.txt").write_text("Some text")
        (temp_directory / "config.yaml").write_text("key: value")

        scanner = MarkdownScanner(temp_directory)
        files = scanner.scan()

        assert len(files) == 1
        assert files[0].filename == "document.md"

    def test_scan_convenience_function(self, temp_markdown_files):
        """Test scan_markdown_files convenience function."""
        base_dir = temp_markdown_files[0].parent.parent
        files = scan_markdown_files(base_dir)

        assert len(files) == 5

    def test_relative_path_calculation(self, temp_directory):
        """Test that relative path is calculated correctly."""
        subdir = temp_directory / "subdir" / "nested"
        subdir.mkdir(parents=True)
        md_file = subdir / "file.md"
        md_file.write_text("# Test")

        scanner = MarkdownScanner(temp_directory)
        files = scanner.scan()

        assert files[0].relative_path == "subdir/nested/file.md"

    def test_large_file_skipped(self, temp_directory):
        """Test that files exceeding max size are skipped."""
        from foxmdviewer.config import settings

        # Create a large file
        large_content = "x" * (settings.max_file_size + 1)
        large_file = temp_directory / "large.md"
        large_file.write_text(large_content)

        # Create a normal file
        (temp_directory / "normal.md").write_text("# Normal")

        scanner = MarkdownScanner(temp_directory)
        files = scanner.scan()

        # Should only find the normal file
        assert len(files) == 1
        assert files[0].filename == "normal.md"

    def test_unicode_content_handling(self, temp_directory):
        """Test handling of unicode content in markdown files."""
        md_file = temp_directory / "unicode.md"
        md_file.write_text(
            "# Título em Português\n\nConteúdo com acentos: áéíóú", encoding="utf-8"
        )

        scanner = MarkdownScanner(temp_directory)
        files = scanner.scan()

        assert files[0].title == "Título em Português"
        preview = files[0].preview
        assert preview is not None
        assert "acentos" in preview
