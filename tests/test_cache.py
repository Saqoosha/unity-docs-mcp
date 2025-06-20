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



if __name__ == "__main__":
    unittest.main()
