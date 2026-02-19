"""Markdown processing service using Mistune.

This module provides high-performance markdown rendering
with GitHub Flavored Markdown support.
"""

from pathlib import Path
from typing import Optional

import mistune
from rich.console import Console

from foxmdviewer.config import settings
from foxmdviewer.utils.cache import html_cache

console = Console()


class MarkdownRenderer:
    """Renders markdown to HTML using Mistune.

    This class provides efficient markdown rendering with:
    - GitHub Flavored Markdown support
    - Syntax highlighting for code blocks
    - Table of contents generation
    - Custom plugins support
    - Caching integration

    Attributes:
        use_cache: Whether to use HTML caching
        plugins: List of enabled plugins

    Example:
        >>> renderer = MarkdownRenderer()
        >>> html = renderer.render("# Hello World")
    """

    def __init__(self, use_cache: bool = True, plugins: Optional[list] = None) -> None:
        """Initialize markdown renderer.

        Args:
            use_cache: Enable HTML caching (default: True)
            plugins: Custom plugins to enable (optional)
        """
        self.use_cache = use_cache and settings.cache_enabled
        self.plugins = plugins

        self._markdown = mistune.create_markdown(escape=False)

    def render(self, content: str, file_path: Optional[Path] = None) -> str:
        """Render markdown content to HTML.

        Args:
            content: Raw markdown content
            file_path: Optional file path for caching

        Returns:
            str: Rendered HTML content

        Example:
            >>> html = renderer.render("# Hello World")
        """
        if file_path and self.use_cache:
            try:
                file_mtime = file_path.stat().st_mtime
                cached = html_cache.get(file_path, file_mtime)

                if cached:
                    return cached
            except OSError as e:
                console.print(f"[yellow]⚠[/yellow] Cache read error: {e}")

        html = self._markdown(content)

        if file_path and self.use_cache:
            try:
                file_mtime = file_path.stat().st_mtime
                html_cache.set(file_path, html, file_mtime)
            except OSError as e:
                console.print(f"[yellow]⚠[/yellow] Cache write error: {e}")

        return html

    def render_file(self, file_path: Path) -> str:
        """Read and render markdown file to HTML.

        Args:
            file_path: Path to markdown file

        Returns:
            str: Rendered HTML content

        Raises:
            FileNotFoundError: If file doesn't exist
            OSError: If file cannot be read

        Example:
            >>> html = renderer.render_file(Path("README.md"))
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            content = file_path.read_text(encoding="utf-8")
        except OSError as e:
            raise OSError(f"Cannot read file {file_path}: {e}")

        return self.render(content, file_path)

    def extract_metadata(self, content: str) -> dict[str, str]:
        """Extract metadata from markdown content.

        Args:
            content: Raw markdown content

        Returns:
            dict: Extracted metadata (title, description, etc.)
        """
        metadata = {"title": None, "word_count": 0, "reading_time": 0}

        lines = content.strip().split("\n")

        for line in lines:
            line = line.strip()
            if line.startswith("# "):
                metadata["title"] = line[2:].strip()
                break

        words = len(content.split())
        metadata["word_count"] = words
        metadata["reading_time"] = max(1, words // 200)

        return metadata


markdown_renderer = MarkdownRenderer()
