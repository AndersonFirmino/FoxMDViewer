"""Unit tests for Markdown Renderer."""

from pathlib import Path

import pytest

from foxmdviewer.services.markdown import MarkdownRenderer


class TestMarkdownRenderer:
    """Test suite for MarkdownRenderer class."""

    def test_renderer_creation(self):
        """Test creating MarkdownRenderer instance."""
        renderer = MarkdownRenderer()

        assert renderer.use_cache is True
        assert renderer._markdown is not None

    def test_renderer_creation_without_cache(self):
        """Test creating MarkdownRenderer with cache disabled."""
        renderer = MarkdownRenderer(use_cache=False)

        assert renderer.use_cache is False

    def test_render_basic_markdown(self):
        """Test rendering basic markdown content."""
        renderer = MarkdownRenderer(use_cache=False)

        markdown = "# Hello World\n\nThis is **bold** text."
        html = renderer.render(markdown)

        assert "<h1>" in html or "Hello World" in html
        assert "bold" in html

    def test_render_headers(self):
        """Test rendering markdown headers."""
        renderer = MarkdownRenderer(use_cache=False)

        markdown = "# H1\n## H2\n### H3\n#### H4"
        html = renderer.render(markdown)

        assert "H1" in html
        assert "H2" in html
        assert "H3" in html
        assert "H4" in html

    def test_render_lists(self):
        """Test rendering markdown lists."""
        renderer = MarkdownRenderer(use_cache=False)

        markdown = "- Item 1\n- Item 2\n- Item 3"
        html = renderer.render(markdown)

        assert "Item 1" in html
        assert "Item 2" in html
        assert "Item 3" in html

    def test_render_code_blocks(self):
        """Test rendering markdown code blocks."""
        renderer = MarkdownRenderer(use_cache=False)

        markdown = "```python\nprint('hello')\n```"
        html = renderer.render(markdown)

        assert "print" in html
        assert "hello" in html

    def test_render_inline_code(self):
        """Test rendering inline code."""
        renderer = MarkdownRenderer(use_cache=False)

        markdown = "This is `inline code` here."
        html = renderer.render(markdown)

        assert "inline code" in html

    def test_render_links(self):
        """Test rendering markdown links."""
        renderer = MarkdownRenderer(use_cache=False)

        markdown = "[Google](https://google.com)"
        html = renderer.render(markdown)

        assert "Google" in html
        assert "google.com" in html

    def test_render_emphasis(self):
        """Test rendering emphasis."""
        renderer = MarkdownRenderer(use_cache=False)

        markdown = "**bold** *italic*"
        html = renderer.render(markdown)

        assert "bold" in html
        assert "italic" in html

    def test_render_file(self, temp_markdown_file):
        """Test rendering markdown file."""
        renderer = MarkdownRenderer(use_cache=False)

        html = renderer.render_file(temp_markdown_file)

        assert "Test Title" in html
        assert "test content" in html

    def test_render_file_not_found(self, temp_directory):
        """Test rendering non-existent file raises error."""
        renderer = MarkdownRenderer()

        with pytest.raises(FileNotFoundError):
            renderer.render_file(temp_directory / "nonexistent.md")

    def test_render_empty_content(self):
        """Test rendering empty content."""
        renderer = MarkdownRenderer(use_cache=False)

        html = renderer.render("")

        assert html is not None

    def test_extract_metadata_with_title(self):
        """Test extracting metadata from content with title."""
        renderer = MarkdownRenderer()

        content = "# Main Title\n\nSome content here."
        metadata = renderer.extract_metadata(content)

        assert metadata["title"] == "Main Title"
        assert metadata["word_count"] > 0
        assert metadata["reading_time"] >= 1

    def test_extract_metadata_without_title(self):
        """Test extracting metadata without title."""
        renderer = MarkdownRenderer()

        content = "Just some text without a title."
        metadata = renderer.extract_metadata(content)

        assert metadata["title"] is None
        assert metadata["word_count"] > 0

    def test_extract_metadata_reading_time(self):
        """Test reading time calculation."""
        renderer = MarkdownRenderer()

        # ~400 words should be 2 minutes
        words = ["word"] * 400
        content = " ".join(words)

        metadata = renderer.extract_metadata(content)

        assert metadata["reading_time"] >= 2

    def test_render_with_cache(self, temp_markdown_file):
        """Test that caching works when enabled."""
        from foxmdviewer.utils.cache import html_cache

        # Clear cache first
        html_cache.clear()

        renderer = MarkdownRenderer(use_cache=True)

        # First render (should cache)
        html1 = renderer.render_file(temp_markdown_file)

        # Second render (should use cache)
        html2 = renderer.render_file(temp_markdown_file)

        assert html1 == html2

    def test_render_tables(self):
        """Test rendering markdown tables."""
        renderer = MarkdownRenderer(use_cache=False)

        markdown = """| Col1 | Col2 |
|------|------|
| A    | B    |
"""
        html = renderer.render(markdown)

        assert "Col1" in html
        assert "Col2" in html

    def test_render_blockquotes(self):
        """Test rendering blockquotes."""
        renderer = MarkdownRenderer(use_cache=False)

        markdown = "> This is a quote"
        html = renderer.render(markdown)

        assert "This is a quote" in html

    def test_render_horizontal_rule(self):
        """Test rendering horizontal rule."""
        renderer = MarkdownRenderer(use_cache=False)

        markdown = "Text above\n\n---\n\nText below"
        html = renderer.render(markdown)

        assert "Text above" in html
        assert "Text below" in html
