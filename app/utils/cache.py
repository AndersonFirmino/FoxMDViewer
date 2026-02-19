"""Cache manager for HTML content.

This module provides intelligent caching functionality for
rendered markdown HTML with TTL support.
"""

import time
from collections import OrderedDict
from pathlib import Path
from threading import RLock
from typing import Optional

from rich.console import Console

from app.config import settings

console = Console()


class CacheEntry:
    """Represents a single cache entry with metadata.

    Attributes:
        content: Cached content
        created_at: Timestamp when entry was created
        access_count: Number of times entry was accessed
        file_mtime: File modification time for invalidation
    """

    def __init__(self, content: str, file_mtime: float, ttl: int = 300) -> None:
        """Initialize cache entry.

        Args:
            content: Content to cache
            file_mtime: File modification timestamp
            ttl: Time-to-live in seconds
        """
        self.content = content
        self.created_at = time.time()
        self.access_count = 0
        self.file_mtime = file_mtime
        self.ttl = ttl

    def is_expired(self) -> bool:
        """Check if cache entry has expired.

        Returns:
            bool: True if expired, False otherwise
        """
        return (time.time() - self.created_at) > self.ttl

    def is_stale(self, current_mtime: float) -> bool:
        """Check if cache entry is stale (file modified).

        Args:
            current_mtime: Current file modification time

        Returns:
            bool: True if stale, False otherwise
        """
        return current_mtime > self.file_mtime

    def touch(self) -> None:
        """Mark entry as recently accessed."""
        self.access_count += 1


class HTMLCache:
    """Thread-safe LRU cache for HTML content.

    This class provides efficient caching with:
    - LRU (Least Recently Used) eviction
    - TTL-based expiration
    - File modification-based invalidation
    - Thread-safe operations
    - Memory limit enforcement

    Attributes:
        max_size: Maximum number of entries
        default_ttl: Default TTL in seconds
        max_memory_mb: Maximum memory usage in MB

    Example:
        >>> cache = HTMLCache(max_size=100)
        >>> cache.set(path, html_content, file_mtime)
        >>> html = cache.get(path, current_mtime)
    """

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: Optional[int] = None,
        max_memory_mb: int = 100,
    ) -> None:
        """Initialize cache with configuration.

        Args:
            max_size: Maximum number of entries (default: 1000)
            default_ttl: Default TTL in seconds (default: from settings)
            max_memory_mb: Maximum memory usage in MB (default: 100)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl or settings.cache_ttl
        self.max_memory_mb = max_memory_mb
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = RLock()
        self._current_size = 0

    def get(
        self, file_path: Path, current_mtime: Optional[float] = None
    ) -> Optional[str]:
        """Get cached HTML content if valid.

        Args:
            file_path: Path to markdown file
            current_mtime: Current file modification time

        Returns:
            str or None: Cached HTML or None if not found/expired

        Example:
            >>> html = cache.get(Path("doc.md"), os.path.getmtime("doc.md"))
        """
        if not settings.cache_enabled:
            return None

        key = str(file_path)

        with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                return None

            if current_mtime and entry.is_stale(current_mtime):
                self._evict(key)
                return None

            if entry.is_expired():
                self._evict(key)
                return None

            self._cache.move_to_end(key)
            entry.touch()

            return entry.content

    def set(
        self,
        file_path: Path,
        content: str,
        file_mtime: float,
        ttl: Optional[int] = None,
    ) -> None:
        """Cache HTML content with metadata.

        Args:
            file_path: Path to markdown file
            content: HTML content to cache
            file_mtime: File modification timestamp
            ttl: Custom TTL in seconds (optional)

        Example:
            >>> cache.set(Path("doc.md"), html, os.path.getmtime("doc.md"))
        """
        if not settings.cache_enabled:
            return

        key = str(file_path)
        entry_size = len(content.encode("utf-8"))

        with self._lock:
            if key in self._cache:
                old_entry = self._cache[key]
                self._current_size -= len(old_entry.content.encode("utf-8"))

            while (
                len(self._cache) >= self.max_size
                or self._current_size + entry_size > self.max_memory_mb * 1024 * 1024
            ):
                if not self._cache:
                    break
                oldest_key = next(iter(self._cache))
                self._evict(oldest_key)

            entry = CacheEntry(
                content=content, file_mtime=file_mtime, ttl=ttl or self.default_ttl
            )

            self._cache[key] = entry
            self._current_size += entry_size

    def invalidate(self, file_path: Path) -> bool:
        """Invalidate cache entry for a file.

        Args:
            file_path: Path to file to invalidate

        Returns:
            bool: True if entry was removed, False if not found
        """
        key = str(file_path)

        with self._lock:
            if key in self._cache:
                self._evict(key)
                return True
            return False

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._current_size = 0
            console.print("[yellow]🗑[/yellow]  Cache cleared")

    def _evict(self, key: str) -> None:
        """Evict a specific cache entry.

        Args:
            key: Cache key to evict
        """
        if key in self._cache:
            entry = self._cache.pop(key)
            self._current_size -= len(entry.content.encode("utf-8"))

    def stats(self) -> dict[str, int | float]:
        """Get cache statistics.

        Returns:
            dict: Cache statistics including size, memory usage, hit rate
        """
        with self._lock:
            total_access = sum(e.access_count for e in self._cache.values())
            return {
                "entries": len(self._cache),
                "max_entries": self.max_size,
                "memory_mb": self._current_size / (1024 * 1024),
                "max_memory_mb": self.max_memory_mb,
                "total_access": total_access,
            }


html_cache = HTMLCache()
