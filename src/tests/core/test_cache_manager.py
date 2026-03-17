import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import sys
import importlib

class TestCacheManager(unittest.TestCase):
    def setUp(self):
        # Save original sys.modules
        self._orig_modules = sys.modules.copy()

        # Mock some dependencies that might be missing
        self.needed_mocks = [
            'tenacity', 'redis', 'curl_cffi', 'nodriver', 'bs4', 'playwright', 'diskcache'
        ]

        for module in self.needed_mocks:
            if module not in sys.modules:
                sys.modules[module] = MagicMock()

        # To avoid MagicMock returned by cache.get, we'll patch diskcache properly
        # Or better yet, just mock diskcache as None in sys.modules so it falls back to L1
        sys.modules['diskcache'] = None

        # Reload cache_manager to apply the diskcache=None mock
        import core.cache_manager
        importlib.reload(core.cache_manager)

        self.cache_manager_module = core.cache_manager

        # Reset the global cache manager before each test
        self.cache_manager_module._cache_manager = None
        self.cache = self.cache_manager_module.get_cache_manager()
        self.cache.clear_all()

    def tearDown(self):
        # Restore sys.modules
        for module in self.needed_mocks:
            if module in sys.modules and sys.modules[module] != self._orig_modules.get(module):
                if module in self._orig_modules:
                    sys.modules[module] = self._orig_modules[module]
                else:
                    del sys.modules[module]

        # Restore diskcache module in sys.modules if it existed
        if 'diskcache' in self._orig_modules:
            sys.modules['diskcache'] = self._orig_modules['diskcache']
        elif 'diskcache' in sys.modules:
            del sys.modules['diskcache']

        # Reload cache_manager to restore its original state
        import core.cache_manager
        importlib.reload(core.cache_manager)

    def test_cached_decorator_hit_miss(self):
        """Test that cache hits and misses are properly handled by the cached decorator."""
        call_count = 0

        @self.cache_manager_module.cached(ttl=1, key_prefix="test_prefix")
        def dummy_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call: cache miss
        result1 = dummy_function(5)
        self.assertEqual(result1, 10)
        self.assertEqual(call_count, 1)

        # Second call: cache hit
        result2 = dummy_function(5)
        self.assertEqual(result2, 10)
        self.assertEqual(call_count, 1)

        # Third call with different arg: cache miss
        result3 = dummy_function(10)
        self.assertEqual(result3, 20)
        self.assertEqual(call_count, 2)

    def test_cached_decorator_ttl_expiration(self):
        """Test that the cache correctly expires based on the provided TTL."""
        call_count = 0

        @self.cache_manager_module.cached(ttl=1, key_prefix="ttl_test")
        def dummy_function():
            nonlocal call_count
            call_count += 1
            return "data"

        # First call: cache miss
        dummy_function()
        self.assertEqual(call_count, 1)

        # Immediate second call: cache hit
        dummy_function()
        self.assertEqual(call_count, 1)

        # Manipulate the internal cache entry to simulate expiration
        cache_key = self.cache._generate_key("ttl_test", (), {})

        # Manually set the creation time to the past to make it expire
        entry = self.cache.l1_cache[cache_key]
        entry.created_at = datetime.now() - timedelta(seconds=2)

        # Third call after expiration: cache miss
        dummy_function()
        self.assertEqual(call_count, 2)

    def test_cached_decorator_none_not_cached(self):
        """Test that a function returning None is not cached."""
        call_count = 0

        @self.cache_manager_module.cached(ttl=10)
        def returns_none():
            nonlocal call_count
            call_count += 1
            return None

        # First call
        returns_none()
        self.assertEqual(call_count, 1)

        # Second call, should not be cached since it returned None
        returns_none()
        self.assertEqual(call_count, 2)

if __name__ == '__main__':
    unittest.main()
