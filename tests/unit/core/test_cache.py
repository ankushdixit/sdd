"""Unit tests for cache module"""

import time
from unittest.mock import Mock

from sdd.core.cache import Cache, FileCache, get_cache


class TestCache:
    """Test cases for Cache class"""

    def test_init(self):
        """Test cache initialization"""
        cache = Cache(default_ttl=60)
        assert cache.default_ttl == 60
        assert len(cache._cache) == 0

    def test_set_and_get(self):
        """Test setting and getting values"""
        cache = Cache()
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_get_nonexistent(self):
        """Test getting non-existent key"""
        cache = Cache()
        assert cache.get("nonexistent") is None

    def test_ttl_expiration(self):
        """Test TTL expiration"""
        cache = Cache(default_ttl=1)  # 1 second TTL
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        # Wait for expiration
        time.sleep(1.1)
        assert cache.get("key1") is None

    def test_custom_ttl(self):
        """Test custom TTL per key"""
        cache = Cache(default_ttl=60)
        cache.set("key1", "value1", ttl=1)  # 1 second TTL
        assert cache.get("key1") == "value1"

        # Wait for expiration
        time.sleep(1.1)
        assert cache.get("key1") is None

    def test_invalidate(self):
        """Test invalidating cache entries"""
        cache = Cache()
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        cache.invalidate("key1")
        assert cache.get("key1") is None

    def test_clear(self):
        """Test clearing entire cache"""
        cache = Cache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"

        cache.clear()
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_thread_safety(self):
        """Test that cache operations are thread-safe"""
        import threading

        cache = Cache()
        errors = []

        def set_values():
            try:
                for i in range(100):
                    cache.set(f"key{i}", f"value{i}")
            except Exception as e:
                errors.append(e)

        def get_values():
            try:
                for i in range(100):
                    cache.get(f"key{i}")
            except Exception as e:
                errors.append(e)

        # Create multiple threads
        threads = []
        for _ in range(5):
            threads.append(threading.Thread(target=set_values))
            threads.append(threading.Thread(target=get_values))

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Should not have any errors
        assert len(errors) == 0


class TestFileCache:
    """Test cases for FileCache class"""

    def test_init(self):
        """Test file cache initialization"""
        file_cache = FileCache()
        assert file_cache.cache is not None

    def test_init_with_custom_cache(self):
        """Test file cache initialization with custom cache"""
        custom_cache = Cache(default_ttl=120)
        file_cache = FileCache(cache=custom_cache)
        assert file_cache.cache is custom_cache

    def test_load_json_nonexistent_file(self, tmp_path):
        """Test loading non-existent file"""
        file_cache = FileCache()
        nonexistent = tmp_path / "nonexistent.json"

        loader_func = Mock(return_value={"default": "data"})
        result = file_cache.load_json(nonexistent, loader_func)

        loader_func.assert_called_once_with(nonexistent)
        assert result == {"default": "data"}

    def test_load_json_with_caching(self, tmp_path):
        """Test loading JSON with caching"""
        file_cache = FileCache()
        test_file = tmp_path / "test.json"
        test_file.write_text('{"key": "value"}')

        loader_func = Mock(return_value={"key": "value"})

        # First load - should call loader
        result1 = file_cache.load_json(test_file, loader_func)
        assert result1 == {"key": "value"}
        assert loader_func.call_count == 1

        # Second load - should use cache
        result2 = file_cache.load_json(test_file, loader_func)
        assert result2 == {"key": "value"}
        assert loader_func.call_count == 1  # Not called again

    def test_load_json_cache_invalidation_on_file_change(self, tmp_path):
        """Test cache invalidation when file is modified"""
        file_cache = FileCache()
        test_file = tmp_path / "test.json"
        test_file.write_text('{"key": "value1"}')

        loader_func = Mock(side_effect=[{"key": "value1"}, {"key": "value2"}])

        # First load
        result1 = file_cache.load_json(test_file, loader_func)
        assert result1 == {"key": "value1"}

        # Modify file
        time.sleep(0.01)  # Ensure mtime changes
        test_file.write_text('{"key": "value2"}')

        # Second load - should reload due to mtime change
        result2 = file_cache.load_json(test_file, loader_func)
        assert result2 == {"key": "value2"}
        assert loader_func.call_count == 2

    def test_invalidate(self, tmp_path):
        """Test explicit cache invalidation"""
        file_cache = FileCache()
        test_file = tmp_path / "test.json"
        test_file.write_text('{"key": "value"}')

        loader_func = Mock(return_value={"key": "value"})

        # Load and cache
        result1 = file_cache.load_json(test_file, loader_func)
        assert result1 == {"key": "value"}
        assert loader_func.call_count == 1

        # Invalidate
        file_cache.invalidate(test_file)

        # Load again - should call loader
        result2 = file_cache.load_json(test_file, loader_func)
        assert result2 == {"key": "value"}
        assert loader_func.call_count == 2


class TestGetCache:
    """Test cases for get_cache function"""

    def test_get_cache_returns_global_instance(self):
        """Test that get_cache returns the global cache instance"""
        cache1 = get_cache()
        cache2 = get_cache()
        assert cache1 is cache2

    def test_global_cache_is_shared(self):
        """Test that global cache is shared across calls"""
        cache = get_cache()
        cache.set("test_key", "test_value")

        cache2 = get_cache()
        assert cache2.get("test_key") == "test_value"
