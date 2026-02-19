"""Pytest configuration and fixtures."""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def temp_directory():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_markdown_file(temp_directory):
    """Create a temporary markdown file for tests."""
    md_file = temp_directory / "test.md"
    md_file.write_text(
        "# Test Title\n\nThis is test content.\n\n## Section 1\n\nMore content."
    )
    return md_file


@pytest.fixture
def temp_markdown_files(temp_directory):
    """Create multiple temporary markdown files for tests."""
    files = []

    # Root level files
    (temp_directory / "README.md").write_text("# README\n\nProject description.")
    (temp_directory / "CHANGELOG.md").write_text(
        "# Changelog\n\n## v1.0.0\n\n- Initial release"
    )

    # Subdirectory files
    docs_dir = temp_directory / "docs"
    docs_dir.mkdir()
    (docs_dir / "guide.md").write_text("# Guide\n\nUser guide content.")
    (docs_dir / "api.md").write_text("# API Reference\n\nAPI documentation.")

    # Nested subdirectory
    advanced_dir = docs_dir / "advanced"
    advanced_dir.mkdir()
    (advanced_dir / "config.md").write_text(
        "# Configuration\n\nAdvanced config options."
    )

    files.extend(
        [
            temp_directory / "README.md",
            temp_directory / "CHANGELOG.md",
            docs_dir / "guide.md",
            docs_dir / "api.md",
            advanced_dir / "config.md",
        ]
    )

    return files


@pytest.fixture
def sample_markdown_content():
    """Sample markdown content for tests."""
    return """# Main Title

This is a paragraph with **bold** and *italic* text.

## Section 1

- Item 1
- Item 2
- Item 3

### Subsection

1. Numbered item 1
2. Numbered item 2

## Code Examples

```python
def hello():
    print("Hello, World!")
```

## Table

| Column 1 | Column 2 |
|----------|----------|
| Data 1   | Data 2   |

## Links

[Google](https://google.com)
"""


@pytest.fixture
def mock_settings(temp_directory):
    """Mock settings for tests."""
    from app.config import Settings

    return Settings(
        base_dir=temp_directory,
        debug=True,
        auto_open_browser=False,
        watch_files=False,
        cache_enabled=False,
    )
