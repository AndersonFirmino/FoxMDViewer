"""File watching service using Watchdog.

This module provides real-time file system monitoring for
markdown files with event notifications.
"""

import asyncio
from pathlib import Path
from threading import Thread
from typing import Callable, Optional

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer
from rich.console import Console

from app.config import settings

console = Console()


class MarkdownEventHandler(FileSystemEventHandler):
    """Event handler for markdown file changes.

    This class processes file system events and triggers
    callbacks for markdown files only.

    Attributes:
        callback: Async callback function for file events
        loop: Event loop for async callback execution

    Example:
        >>> handler = MarkdownEventHandler(callback)
        >>> observer.schedule(handler, path, recursive=True)
    """

    def __init__(
        self,
        callback: Callable[[str, Path], None],
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:
        """Initialize event handler.

        Args:
            callback: Callback function(event_type, file_path)
            loop: Event loop for async execution (optional)
        """
        super().__init__()
        self.callback = callback
        self.loop = loop or asyncio.get_event_loop()

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification event.

        Args:
            event: File system event
        """
        if not event.is_directory and event.src_path.endswith(".md"):
            self._trigger_callback("modified", Path(event.src_path))

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation event.

        Args:
            event: File system event
        """
        if not event.is_directory and event.src_path.endswith(".md"):
            self._trigger_callback("created", Path(event.src_path))

    def on_deleted(self, event: FileSystemEvent) -> None:
        """Handle file deletion event.

        Args:
            event: File system event
        """
        if not event.is_directory and event.src_path.endswith(".md"):
            self._trigger_callback("deleted", Path(event.src_path))

    def _trigger_callback(self, event_type: str, file_path: Path) -> None:
        """Trigger callback with event information.

        Args:
            event_type: Type of event (modified, created, deleted)
            file_path: Path to affected file
        """
        try:
            if asyncio.iscoroutinefunction(self.callback):
                asyncio.run_coroutine_threadsafe(
                    self.callback(event_type, file_path), self.loop
                )
            else:
                self.callback(event_type, file_path)
        except Exception as e:
            console.print(
                f"[red]✗[/red] Callback error for {event_type} on {file_path}: {e}"
            )


class FileWatcher:
    """Watches markdown files for changes with watchdog.

    This class provides file monitoring with:
    - Recursive directory watching
    - Event filtering for .md files only
    - Async callback support
    - Graceful shutdown handling

    Attributes:
        watch_path: Path to watch for changes
        recursive: Watch subdirectories recursively
        callback: Callback function for events

    Example:
        >>> watcher = FileWatcher(Path("."), callback=handle_change)
        >>> watcher.start()
        >>> # ... later ...
        >>> watcher.stop()
    """

    def __init__(
        self,
        watch_path: Path,
        callback: Callable[[str, Path], None],
        recursive: bool = True,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:
        """Initialize file watcher.

        Args:
            watch_path: Directory path to watch
            callback: Callback function(event_type, file_path)
            recursive: Watch subdirectories (default: True)
            loop: Event loop for async callbacks

        Raises:
            ValueError: If watch_path doesn't exist
        """
        if not watch_path.exists():
            raise ValueError(f"Watch path does not exist: {watch_path}")

        self.watch_path = watch_path.resolve()
        self.recursive = recursive
        self.callback = callback
        self.loop = loop or asyncio.get_event_loop()

        self._observer: Optional[Observer] = None
        self._running = False

    def start(self) -> None:
        """Start watching for file changes.

        Raises:
            RuntimeError: If watcher is already running
        """
        if self._running:
            raise RuntimeError("File watcher is already running")

        console.print(f"[cyan]👁[/cyan] Watching for changes in {self.watch_path}")

        event_handler = MarkdownEventHandler(callback=self.callback, loop=self.loop)

        self._observer = Observer()
        self._observer.schedule(
            event_handler, str(self.watch_path), recursive=self.recursive
        )

        self._observer.start()
        self._running = True

        console.print("[green]✓[/green] File watcher started")

    def stop(self) -> None:
        """Stop watching for file changes."""
        if not self._running or self._observer is None:
            return

        console.print("[yellow]⏹[/yellow] Stopping file watcher...")

        self._observer.stop()
        self._observer.join(timeout=5.0)

        self._running = False
        self._observer = None

        console.print("[green]✓[/green] File watcher stopped")

    def is_running(self) -> bool:
        """Check if watcher is currently running.

        Returns:
            bool: True if running, False otherwise
        """
        return self._running

    def __enter__(self) -> "FileWatcher":
        """Context manager entry.

        Returns:
            FileWatcher: Self instance
        """
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.stop()


def create_file_watcher(
    watch_path: Path,
    callback: Callable[[str, Path], None],
    loop: Optional[asyncio.AbstractEventLoop] = None,
) -> Optional[FileWatcher]:
    """Factory function to create file watcher.

    Args:
        watch_path: Path to watch
        callback: Event callback function
        loop: Event loop for async callbacks

    Returns:
        FileWatcher or None: Configured file watcher instance or None if disabled

    Example:
        >>> watcher = create_file_watcher(Path("."), handle_change)
        >>> if watcher:
        ...     watcher.start()
    """
    if not settings.watch_files:
        console.print("[yellow]ℹ[/yellow]  File watching is disabled")
        return None

    return FileWatcher(watch_path, callback, loop=loop)
