"""Unit tests for the HTML Cache."""

import time
from pathlib import Path

import pytest

from foxmdviewer.utils.cache import CacheEntry, HTMLCache


class TestCacheEntry:
    """Test suite for CacheEntry class."""

    def test_cache_entry_creation(self):
        """Test cache entry creation with basic values."""
        entry = CacheEntry(content="<html>Test</html>", file_mtime=time.time(), ttl=300)

        assert entry.content == "<html>Test</html>"
        assert entry.ttl == 300
        assert entry.access_count == 0

    def test_cache_entry_not_expired(self):
        """Test that fresh entry is not expired."""
        entry = CacheEntry(content="content", file_mtime=time.time(), ttl=300)

        assert not entry.is_expired()

    def test_cache_entry_expired(self):
        """Test that old entry is expired."""
        entry = CacheEntry(
            content="content",
            file_mtime=time.time(),
            ttl=1,  # 1 second TTL
        )

        # Manually set created_at to past
        entry.created_at = time.time() - 2

        assert entry.is_expired()

    def test_cache_entry_not_stale(self):
        """Test that entry is not stale if file not modified."""
        current_mtime = time.time()
        entry = CacheEntry(content="content", file_mtime=current_mtime, ttl=300)

        assert not entry.is_stale(current_mtime)

    def test_cache_entry_stale(self):
        """Test that entry is stale if file modified."""
        old_mtime = time.time() - 10
        new_mtime = time.time()

        entry = CacheEntry(content="content", file_mtime=old_mtime, ttl=300)

        assert entry.is_stale(new_mtime)

    def test_cache_entry_touch(self):
        """Test that touch increments access count."""
        entry = CacheEntry(content="content", file_mtime=time.time(), ttl=300)

        assert entry.access_count == 0

        entry.touch()
        assert entry.access_count == 1

        entry.touch()
        assert entry.access_count == 2


class TestHTMLCache:
    """Test suite for HTMLCache class."""

    def test_cache_creation(self):
        """Test cache creation with default values."""
        cache = HTMLCache()

        assert cache.max_size == 1000
        assert cache.default_ttl == 300
        assert cache.max_memory_mb == 100

    def test_cache_creation_custom_values(self):
        """Test cache creation with custom values."""
        cache = HTMLCache(max_size=100, default_ttl=600, max_memory_mb=50)

        assert cache.max_size == 100
        assert cache.default_ttl == 600
        assert cache.max_memory_mb == 50

    def test_cache_set_and_get(self, temp_markdown_file):
        """Test setting and getting cache entries."""
        cache = HTMLCache()
        file_mtime = temp_markdown_file.stat().st_mtime
        content = "<html>Rendered content</html>"

        cache.set(temp_markdown_file, content, file_mtime)

        cached = cache.get(temp_markdown_file, file_mtime)
        assert cached == content

    def test_cache_get_returns_none_if_not_found(self, temp_markdown_file):
        """Test that get returns None for uncached files."""
        cache = HTMLCache()

        cached = cache.get(temp_markdown_file, time.time())
        assert cached is None

    def test_cache_invalidate(self, temp_markdown_file):
        """Test cache invalidation for specific file."""
        cache = HTMLCache()
        file_mtime = temp_markdown_file.stat().st_mtime
        content = "<html>Content</html>"

        cache.set(temp_markdown_file, content, file_mtime)

        # Verify cached
        assert cache.get(temp_markdown_file, file_mtime) == content

        # Invalidate
        result = cache.invalidate(temp_markdown_file)
        assert result is True

        # Verify no longer cached
        assert cache.get(temp_markdown_file, file_mtime) is None

    def test_cache_invalidate_nonexistent(self, temp_markdown_file):
        """Test invalidating non-existent cache entry."""
        cache = HTMLCache()

        result = cache.invalidate(temp_markdown_file)
        assert result is False

    def test_cache_clear(self, temp_markdown_files):
        """Test clearing all cache entries."""
        cache = HTMLCache()

        # Add multiple entries
        for md_file in temp_markdown_files:
            file_mtime = md_file.stat().st_mtime
            cache.set(md_file, f"content-{md_file.name}", file_mtime)

        # Verify entries exist
        assert len(cache._cache) == 5

        # Clear cache
        cache.clear()

        # Verify all entries removed
        assert len(cache._cache) == 0

    def test_cache_lru_eviction(self, temp_directory):
        """Test LRU eviction when max_size is reached."""
        cache = HTMLCache(max_size=3)

        # Create 5 files
        files = []
        for i in range(5):
            md_file = temp_directory / f"file{i}.md"
            md_file.write_text(f"# File {i}")
            files.append(md_file)

        # Add first 3 files
        for i, md_file in enumerate(files[:3]):
            file_mtime = md_file.stat().st_mtime
            cache.set(md_file, f"content-{i}", file_mtime)

        assert len(cache._cache) == 3

        # Add 4th file (should evict oldest)
        file_mtime = files[3].stat().st_mtime
        cache.set(files[3], "content-3", file_mtime)

        assert len(cache._cache) == 3
        # First file should be evicted
        assert cache.get(files[0], files[0].stat().st_mtime) is None

    def test_cache_stats(self, temp_markdown_files):
        """Test cache statistics."""
        cache = HTMLCache()

        # Add some entries
        for md_file in temp_markdown_files[:3]:
            file_mtime = md_file.stat().st_mtime
            cache.set(md_file, f"content-{md_file.name}", file_mtime)

        stats = cache.stats()

        assert stats["entries"] == 3
        assert stats["max_entries"] == 1000
        assert stats["memory_mb"] > 0
        assert stats["total_access"] == 0  # No gets yet

    def test_cache_updates_existing_entry(self, temp_markdown_file):
        """Test that setting same key updates the entry."""
        cache = HTMLCache()
        file_mtime = temp_markdown_file.stat().st_mtime

        cache.set(temp_markdown_file, "old content", file_mtime)
        cache.set(temp_markdown_file, "new content", file_mtime)

        cached = cache.get(temp_markdown_file, file_mtime)
        assert cached == "new content"
        assert len(cache._cache) == 1

    def test_cache_respects_ttl(self, temp_markdown_file):
        """Test that cache respects custom TTL."""
        cache = HTMLCache(default_ttl=300)
        file_mtime = temp_markdown_file.stat().st_mtime

        # Set with short TTL
        cache.set(temp_markdown_file, "content", file_mtime, ttl=1)

        # Get immediately - should work
        cached = cache.get(temp_markdown_file, file_mtime)
        assert cached == "content"

        # Wait for TTL to expire
        time.sleep(1.5)

        # Get after expiration - should return None
        cached = cache.get(temp_markdown_file, file_mtime)
        assert cached is None

    def test_cache_stale_detection(self, temp_markdown_file):
        """Test that cache detects stale content when file modified."""
        cache = HTMLCache()
        cache.clear()  # Ensure clean state

        old_mtime = temp_markdown_file.stat().st_mtime

        cache.set(temp_markdown_file, "old content", old_mtime)

        # Verify content was cached
        cached = cache.get(temp_markdown_file, old_mtime)
        assert cached == "old content"

        # Modify file (simulate by changing mtime)
        import time

        time.sleep(0.1)  # Ensure mtime changes
        temp_markdown_file.write_text("# Modified content")
        new_mtime = temp_markdown_file.stat().st_mtime

        # Get with new mtime should return None (stale)
        cached = cache.get(temp_markdown_file, new_mtime)
        assert cached is None
        cached = cache.get(temp_markdown_file, new_mtime)
        assert cached is None
