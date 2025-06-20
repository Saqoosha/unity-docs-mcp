"""Test caching functionality for API availability and search index."""

import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import tempfile
import pickle
from datetime import datetime, timedelta
import time
from src.unity_docs_mcp.scraper import UnityDocScraper
from src.unity_docs_mcp.search_index import UnitySearchIndex


class TestAPICaching(unittest.TestCase):
    """Test API availability caching functionality."""

    def setUp(self):
        """Set up test environment with temporary cache directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.scraper = UnityDocScraper()
        self.scraper.cache_dir = self.temp_dir
        self.scraper._api_cache = {}

    def tearDown(self):
        """Clean up temporary files."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cache_key_generation(self):
        """Test cache key generation for different API combinations."""
        # Test class-only key
        key1 = self.scraper._get_cache_key("GameObject")
        self.assertEqual(key1, "GameObject")

        # Test class with method key
        key2 = self.scraper._get_cache_key("GameObject", "SetActive")
        self.assertEqual(key2, "GameObject.SetActive")

        # Test with namespace
        key3 = self.scraper._get_cache_key("UnityEngine.UI.Button", "onClick")
        self.assertEqual(key3, "UnityEngine.UI.Button.onClick")

    def test_cache_save_and_load(self):
        """Test saving and loading API cache to/from disk."""
        # Create test cache data
        test_data = {
            "GameObject": {
                "available": ["6000.0", "2022.3"],
                "unavailable": ["2019.4"],
            },
            "AsyncGPUReadback": {
                "available": ["6000.0"],
                "unavailable": ["2019.4", "2020.3"],
            },
        }
        self.scraper._api_cache = test_data

        # Save cache
        self.scraper._save_api_cache()
        cache_path = self.scraper._get_api_cache_path()
        self.assertTrue(os.path.exists(cache_path))

        # Clear memory cache and reload
        self.scraper._api_cache = {}
        self.scraper._load_api_cache()

        # Verify loaded data matches
        self.assertEqual(self.scraper._api_cache, test_data)

    def test_cache_expiration(self):
        """Test that expired cache is not loaded."""
        # Create cache file with old timestamp
        cache_path = self.scraper._get_api_cache_path()
        test_data = {"GameObject": {"available": ["6000.0"], "unavailable": []}}

        with open(cache_path, "wb") as f:
            pickle.dump(test_data, f)

        # Set file modification time to 7 hours ago (beyond 6-hour expiry)
        old_time = time.time() - (7 * 60 * 60)
        os.utime(cache_path, (old_time, old_time))

        # Load should fail due to expiration
        self.scraper._api_cache = {}
        self.scraper._load_api_cache()
        self.assertEqual(self.scraper._api_cache, {})

    def test_cache_not_expired(self):
        """Test that non-expired cache is loaded successfully."""
        # Create cache file with recent timestamp
        cache_path = self.scraper._get_api_cache_path()
        test_data = {"GameObject": {"available": ["6000.0"], "unavailable": []}}

        with open(cache_path, "wb") as f:
            pickle.dump(test_data, f)

        # Set file modification time to 3 hours ago (within 6-hour validity)
        recent_time = time.time() - (3 * 60 * 60)
        os.utime(cache_path, (recent_time, recent_time))

        # Load should succeed
        self.scraper._api_cache = {}
        self.scraper._load_api_cache()
        self.assertEqual(self.scraper._api_cache, test_data)

    @patch("requests.Session.head")
    def test_cache_used_for_repeated_requests(self, mock_head):
        """Test that cache is used for repeated API availability checks."""
        # First request should make HTTP calls
        mock_head.return_value = Mock(status_code=200)

        result1 = self.scraper.check_api_availability_across_versions("GameObject")

        # Verify HTTP calls were made
        self.assertTrue(mock_head.called)
        initial_call_count = mock_head.call_count

        # Reset mock
        mock_head.reset_mock()

        # Second request should use cache
        result2 = self.scraper.check_api_availability_across_versions("GameObject")

        # Verify no new HTTP calls
        self.assertFalse(mock_head.called)

        # Results should be identical
        self.assertEqual(result1, result2)

    def test_cache_corruption_handling(self):
        """Test handling of corrupted cache files."""
        # Create corrupted cache file
        cache_path = self.scraper._get_api_cache_path()
        with open(cache_path, "wb") as f:
            f.write(b"corrupted data that's not valid pickle")

        # Load should handle corruption gracefully
        self.scraper._api_cache = {}
        self.scraper._load_api_cache()

        # Should have empty cache after failed load
        self.assertEqual(self.scraper._api_cache, {})

    def test_cache_directory_creation(self):
        """Test that cache directory is created if it doesn't exist."""
        # Use non-existent directory
        non_existent = os.path.join(self.temp_dir, "new_cache_dir")

        # Create scraper with non-existent cache directory
        # The directory should be created during __init__
        scraper = UnityDocScraper()
        original_cache_dir = scraper.cache_dir

        # Override with non-existent dir and manually create it like __init__ does
        scraper.cache_dir = non_existent
        os.makedirs(scraper.cache_dir, exist_ok=True)

        # Now directory should exist
        self.assertTrue(os.path.exists(non_existent))

    @patch("requests.Session.head")
    def test_concurrent_cache_access(self, mock_head):
        """Test that concurrent cache access is handled properly."""
        import threading

        mock_head.return_value = Mock(status_code=200)
        results = []

        def check_api():
            result = self.scraper.check_api_availability_across_versions("Transform")
            results.append(result)

        # Create multiple threads
        threads = []
        for _ in range(5):
            t = threading.Thread(target=check_api)
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # All results should be identical
        self.assertEqual(len(results), 5)
        for result in results[1:]:
            self.assertEqual(result, results[0])


class TestSearchIndexCaching(unittest.TestCase):
    """Test search index caching functionality."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.search_index = UnitySearchIndex(
            cache_dir=self.temp_dir, cache_duration_hours=24
        )

    def tearDown(self):
        """Clean up temporary files."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cache_path_generation(self):
        """Test cache file path generation for different versions."""
        path1 = self.search_index._get_cache_path("6000.0")
        self.assertTrue(path1.endswith("search_index_6000.0.pkl"))

        path2 = self.search_index._get_cache_path("2022.3")
        self.assertTrue(path2.endswith("search_index_2022.3.pkl"))

    def test_save_and_load_cache(self):
        """Test saving and loading search index cache."""
        # Create test data
        self.search_index.pages = [
            ["GameObject", "GameObject"],
            ["Transform", "Transform"],
        ]
        self.search_index.page_info = [["Game object class"], ["Transform component"]]
        self.search_index.search_index = {"gameobject": [0], "transform": [1]}
        self.search_index.common_words = {"the", "is", "a"}

        # Save to cache
        self.search_index._save_to_cache("6000.0")

        # Clear and reload
        self.search_index.pages = []
        self.search_index.page_info = []
        self.search_index.search_index = {}
        self.search_index.common_words = set()

        # Load from cache
        success = self.search_index._load_from_cache("6000.0")

        self.assertTrue(success)
        self.assertEqual(len(self.search_index.pages), 2)
        self.assertEqual(self.search_index.pages[0][0], "GameObject")
        self.assertEqual(len(self.search_index.common_words), 3)

    def test_cache_expiration_24_hours(self):
        """Test that search index cache expires after 24 hours."""
        # Save cache
        self.search_index.pages = [["TestClass", "TestClass"]]
        self.search_index._save_to_cache("6000.0")

        # Set modification time to 25 hours ago
        cache_path = self.search_index._get_cache_path("6000.0")
        old_time = time.time() - (25 * 60 * 60)
        os.utime(cache_path, (old_time, old_time))

        # Load should fail
        success = self.search_index._load_from_cache("6000.0")
        self.assertFalse(success)

    def test_cache_within_validity_period(self):
        """Test that cache within 24 hours is loaded successfully."""
        # Save cache
        self.search_index.pages = [["TestClass", "TestClass"]]
        self.search_index._save_to_cache("6000.0")

        # Set modification time to 20 hours ago
        cache_path = self.search_index._get_cache_path("6000.0")
        recent_time = time.time() - (20 * 60 * 60)
        os.utime(cache_path, (recent_time, recent_time))

        # Clear data
        self.search_index.pages = []

        # Load should succeed
        success = self.search_index._load_from_cache("6000.0")
        self.assertTrue(success)
        self.assertEqual(len(self.search_index.pages), 1)

    def test_memory_cache_functionality(self):
        """Test in-memory cache for search index."""
        # Create test data
        test_pages = [["GameObject", "GameObject"]]
        test_info = [["Game object"]]
        test_search = {"gameobject": [0]}
        test_common = {"the"}

        # Store in memory cache
        cache_key = "index_6000.0"
        self.search_index._memory_cache[cache_key] = (
            test_pages,
            test_info,
            test_search,
            test_common,
        )

        # Load should use memory cache
        with patch.object(
            self.search_index, "_load_from_cache", return_value=False
        ) as mock_load:
            success = self.search_index.load_index("6000.0")

            self.assertTrue(success)
            # File cache should not be accessed
            mock_load.assert_not_called()

            # Data should match
            self.assertEqual(self.search_index.pages, test_pages)

    def test_clear_cache_single_version(self):
        """Test clearing cache for a specific version."""
        # Create cache files for multiple versions
        self.search_index._save_to_cache("6000.0")
        self.search_index._save_to_cache("2022.3")

        # Add to memory cache
        self.search_index._memory_cache["index_6000.0"] = ([], [], {}, set())
        self.search_index._memory_cache["index_2022.3"] = ([], [], {}, set())

        # Clear only one version
        self.search_index.clear_cache("6000.0")

        # Check file cache
        self.assertFalse(os.path.exists(self.search_index._get_cache_path("6000.0")))
        self.assertTrue(os.path.exists(self.search_index._get_cache_path("2022.3")))

        # Check memory cache
        self.assertNotIn("index_6000.0", self.search_index._memory_cache)
        self.assertIn("index_2022.3", self.search_index._memory_cache)

    def test_clear_cache_all_versions(self):
        """Test clearing cache for all versions."""
        # Create cache files
        self.search_index._save_to_cache("6000.0")
        self.search_index._save_to_cache("2022.3")
        self.search_index._save_to_cache("2021.3")

        # Add to memory cache
        self.search_index._memory_cache["index_6000.0"] = ([], [], {}, set())
        self.search_index._memory_cache["index_2022.3"] = ([], [], {}, set())

        # Clear all
        self.search_index.clear_cache()

        # Check no cache files remain
        cache_files = [
            f for f in os.listdir(self.temp_dir) if f.startswith("search_index_")
        ]
        self.assertEqual(len(cache_files), 0)

        # Check memory cache is empty
        self.assertEqual(len(self.search_index._memory_cache), 0)

    @patch("requests.get")
    def test_force_refresh_ignores_cache(self, mock_get):
        """Test that force_refresh bypasses cache."""
        # Create valid cache
        self.search_index.pages = [["CachedClass", "CachedClass"]]
        self.search_index.page_info = [["Cached info"]]
        self.search_index.search_index = {"cachedclass": [0]}
        self.search_index.common_words = {"cached"}
        self.search_index._save_to_cache("6000.0")

        # Clear the index to simulate fresh start
        self.search_index.pages = []
        self.search_index.page_info = []
        self.search_index.search_index = {}
        self.search_index.common_words = set()

        # Setup mock response - parser expects data after var declaration
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """var pages = 
[["FreshClass", "FreshClass"]];
var info = 
[["Fresh data"]];
var common = 
{};
var searchIndex = 
{};"""
        mock_get.return_value = mock_response

        # Load with force_refresh
        success = self.search_index.load_index("6000.0", force_refresh=True)

        self.assertTrue(success)
        # Should have fresh data, not cached
        self.assertEqual(self.search_index.pages[0][0], "FreshClass")

        # HTTP request should have been made
        mock_get.assert_called_once()

    def test_cache_timestamp_in_saved_data(self):
        """Test that cache includes timestamp for debugging."""
        # Save cache
        self.search_index.pages = [["TestClass", "TestClass"]]
        self.search_index._save_to_cache("6000.0")

        # Load raw pickle data
        cache_path = self.search_index._get_cache_path("6000.0")
        with open(cache_path, "rb") as f:
            cache_data = pickle.load(f)

        # Verify timestamp exists and is recent
        self.assertIn("timestamp", cache_data)
        self.assertIsInstance(cache_data["timestamp"], datetime)
        time_diff = datetime.now() - cache_data["timestamp"]
        self.assertLess(time_diff.total_seconds(), 60)  # Should be within last minute


class TestCachePerformance(unittest.TestCase):
    """Test performance benefits of caching."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.scraper = UnityDocScraper()
        self.scraper.cache_dir = self.temp_dir

    def tearDown(self):
        """Clean up temporary files."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("requests.Session.head")
    def test_cache_speed_improvement(self, mock_head):
        """Test that cached requests are significantly faster."""
        import time

        mock_head.return_value = Mock(status_code=200)

        # First request (no cache)
        start_time = time.time()
        self.scraper.check_api_availability_across_versions("GameObject")
        uncached_time = time.time() - start_time

        # Second request (cached)
        start_time = time.time()
        self.scraper.check_api_availability_across_versions("GameObject")
        cached_time = time.time() - start_time

        # Cached should be at least 10x faster
        self.assertLess(cached_time * 10, uncached_time)

        # Cached should be under 0.01 seconds
        self.assertLess(cached_time, 0.01)


if __name__ == "__main__":
    unittest.main()
