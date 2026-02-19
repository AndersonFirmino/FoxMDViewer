"""File scanner utility for finding markdown files.

This module provides functionality to recursively scan directories
for markdown files with performance optimization.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from app.config import settings
from app.models import MarkdownFile

console = Console()


class MarkdownScanner:
    """Scans directories for markdown files with metadata extraction.

    This class provides efficient recursive scanning with:
    - Configurable depth limit
    - File size filtering
    - Title extraction from content
    - Preview generation

    Attributes:
        base_dir: Base directory to scan from
        max_depth: Maximum recursion depth (None = unlimited)
        exclude_dirs: Directories to exclude from scanning

    Example:
        >>> scanner = MarkdownScanner(Path("/home/user/docs"))
        >>> files = scanner.scan()
        >>> print(f"Found {len(files)} markdown files")
    """

    def __init__(
        self,
        base_dir: Path,
        max_depth: Optional[int] = None,
        exclude_dirs: Optional[list[str]] = None,
    ) -> None:
        """Initialize scanner with configuration.

        Args:
            base_dir: Base directory to scan
            max_depth: Maximum recursion depth (None = unlimited)
            exclude_dirs: List of directory names to exclude

        Raises:
            ValueError: If base_dir doesn't exist or isn't a directory
        """
        if not base_dir.exists():
            raise ValueError(f"Base directory does not exist: {base_dir}")
        if not base_dir.is_dir():
            raise ValueError(f"Base path is not a directory: {base_dir}")

        self.base_dir = base_dir.resolve()
        self.max_depth = max_depth
        self.exclude_dirs = set(exclude_dirs or [".git", "__pycache__", "node_modules"])

    def scan(self) -> list[MarkdownFile]:
        """Scan base directory for all markdown files.

        Returns:
            List of MarkdownFile objects with metadata

        Example:
            >>> scanner = MarkdownScanner(Path("."))
            >>> files = scanner.scan()
        """
        files = list(self._scan_recursive())
        console.print(f"[green]✓[/green] Found {len(files)} markdown files")
        return files

    def _scan_recursive(self) -> Iterator[MarkdownFile]:
        """Recursively scan directories yielding markdown files.

        Yields:
            MarkdownFile: Each found markdown file with metadata
        """
        for root, dirs, files in os.walk(self.base_dir):
            root_path = Path(root)

            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]

            if self.max_depth is not None:
                depth = len(root_path.relative_to(self.base_dir).parts)
                if depth > self.max_depth:
                    continue

            for filename in files:
                if filename.endswith(".md"):
                    file_path = root_path / filename
                    try:
                        yield self._create_markdown_file(file_path)
                    except (OSError, ValueError) as e:
                        console.print(f"[yellow]⚠[/yellow] Skipping {file_path}: {e}")
                        continue

    def _create_markdown_file(self, file_path: Path) -> MarkdownFile:
        """Create MarkdownFile object with metadata.

        Args:
            file_path: Path to markdown file

        Returns:
            MarkdownFile: File object with complete metadata

        Raises:
            OSError: If file cannot be read
            ValueError: If file is too large
        """
        stat = file_path.stat()

        if stat.st_size > settings.max_file_size:
            raise ValueError(f"File too large: {stat.st_size} bytes")

        relative_path = str(file_path.relative_to(self.base_dir))

        title = self._extract_title(file_path)
        preview = self._extract_preview(file_path)

        return MarkdownFile(
            path=file_path,
            relative_path=relative_path,
            filename=file_path.name,
            size=stat.st_size,
            modified_at=datetime.fromtimestamp(stat.st_mtime),
            created_at=datetime.fromtimestamp(stat.st_ctime) if stat.st_ctime else None,
            title=title,
            preview=preview,
        )

    def _extract_title(self, file_path: Path) -> Optional[str]:
        """Extract title from first H1 heading in file.

        Args:
            file_path: Path to markdown file

        Returns:
            str or None: Extracted title or None if not found
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("# "):
                        return line[2:].strip()
                    if line:
                        break
        except (OSError, UnicodeDecodeError):
            pass
        return None

    def _extract_preview(self, file_path: Path) -> Optional[str]:
        """Extract first non-empty, non-heading paragraph as preview.

        Args:
            file_path: Path to markdown file

        Returns:
            str or None: Preview text or None if not found
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                in_code_block = False
                preview_lines = []

                for line in f:
                    line = line.strip()

                    if line.startswith("```"):
                        in_code_block = not in_code_block
                        continue

                    if in_code_block or line.startswith("#"):
                        continue

                    if line and not line.startswith("```"):
                        preview_lines.append(line)
                        if len(" ".join(preview_lines)) > 200:
                            break

                if preview_lines:
                    preview = " ".join(preview_lines)
                    if len(preview) > 197:
                        preview = preview[:197] + "..."
                    return preview

        except (OSError, UnicodeDecodeError):
            pass
        return None


def scan_markdown_files(
    base_dir: Optional[Path] = None,
    max_depth: Optional[int] = None,
    exclude_dirs: Optional[list[str]] = None,
) -> list[MarkdownFile]:
    """Convenience function to scan for markdown files.

    Args:
        base_dir: Base directory to scan (defaults to settings.base_dir)
        max_depth: Maximum recursion depth
        exclude_dirs: Directories to exclude

    Returns:
        List of markdown files found

    Example:
        >>> files = scan_markdown_files(Path("."))
        >>> print(f"Found {len(files)} files")
    """
    scanner = MarkdownScanner(
        base_dir=base_dir or settings.base_dir,
        max_depth=max_depth,
        exclude_dirs=exclude_dirs,
    )
    return scanner.scan()
