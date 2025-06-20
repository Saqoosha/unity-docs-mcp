"""Tests for Unity search index functionality."""

import unittest
from unittest.mock import Mock, patch, mock_open
import json
import os
import tempfile
from datetime import datetime, timedelta

import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from unity_docs_mcp.search_index import UnitySearchIndex


class TestUnitySearchIndex(unittest.TestCase):
    """Test cases for UnitySearchIndex class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.search_index = UnitySearchIndex(cache_dir=self.temp_dir)

        # Sample data for testing
        self.sample_pages = [
            ["GameObject", "GameObject"],
            ["GameObject.SetActive", "GameObject.SetActive"],
            ["Transform", "Transform"],
            ["Transform-position", "Transform.position"],
            ["Vector3", "Vector3"],
            ["Debug.Log", "Debug.Log"],
        ]

        self.sample_info = [
            ["Base class for all entities in Unity Scenes.", 0],
            [
                "Activates/Deactivates the GameObject, depending on the given true or false value.",
                1,
            ],
            ["Position, rotation and scale of an object.", 0],
            ["The world space position of the Transform.", 1],
            ["Representation of 3D vectors and points.", 0],
            ["Logs a message to the Unity Console.", 1],
        ]

        self.sample_search_index = {
            "gameobject": [0, 1],
            "setactive": [1],
            "transform": [2, 3],
            "position": [3],
            "vector3": [4],
            "debug": [5],
            "log": [5],
            "class": [0, 2, 4],
            "base": [0],
            "entities": [0],
            "space": [3],
            "world": [3],
        }

        self.sample_common = {"a": 1, "the": 1, "is": 1, "in": 1, "of": 1, "to": 1}

        # Sample index.js content
        self.sample_index_js = f"""//
// Search index for Unity script documentation
//
var pages = 
{json.dumps(self.sample_pages)};
var info = 
{json.dumps(self.sample_info)};
var common = 
{json.dumps(self.sample_common)};
var searchIndex = 
{json.dumps(self.sample_search_index)};
"""

    def tearDown(self):
        """Clean up test fixtures."""
        # Remove temp directory
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_init(self):
        """Test initialization."""
        index = UnitySearchIndex()
        self.assertEqual(index.pages, [])
        self.assertEqual(index.page_info, [])
        self.assertEqual(index.search_index, {})
        self.assertEqual(index.common_words, set())
        self.assertFalse(index._loaded)

    def test_init_with_custom_cache_dir(self):
        """Test initialization with custom cache directory."""
        custom_dir = os.path.join(self.temp_dir, "custom_cache")
        index = UnitySearchIndex(cache_dir=custom_dir, cache_duration_hours=48)
        self.assertEqual(index.cache_dir, custom_dir)
        self.assertEqual(index.cache_duration, timedelta(hours=48))
        self.assertTrue(os.path.exists(custom_dir))

    @patch("requests.get")
    def test_load_index_success(self, mock_get):
        """Test successful index loading."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = self.sample_index_js
        mock_get.return_value = mock_response

        # Load index
        result = self.search_index.load_index("6000.0")

        self.assertTrue(result)
        self.assertEqual(len(self.search_index.pages), 6)
        self.assertEqual(len(self.search_index.page_info), 6)
        self.assertEqual(len(self.search_index.search_index), 12)
        self.assertEqual(len(self.search_index.common_words), 6)
        self.assertTrue(self.search_index._loaded)

    @patch("requests.get")
    def test_load_index_failure(self, mock_get):
        """Test index loading failure."""
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        # Load index
        result = self.search_index.load_index("6000.0")

        self.assertFalse(result)
        self.assertFalse(self.search_index._loaded)

    @patch("unity_docs_mcp.search_index.UnitySearchIndex.load_index")
    def test_search_basic(self, mock_load_index):
        """Test basic search functionality."""
        # Prevent actual loading
        mock_load_index.return_value = False

        # Manually set up search data
        self.search_index.pages = self.sample_pages
        self.search_index.page_info = self.sample_info
        self.search_index.search_index = self.sample_search_index
        self.search_index.common_words = set(self.sample_common.keys())
        self.search_index._loaded = True
        # Also add to memory cache to prevent reloading
        self.search_index._memory_cache["index_6000.0"] = (
            self.sample_pages,
            self.sample_info,
            self.sample_search_index,
            set(self.sample_common.keys()),
        )

        # Test search for "GameObject"
        results = self.search_index.search("GameObject", max_results=5)

        self.assertGreater(len(results), 0)
        # GameObject should be in the results (but may not be first due to scoring)
        titles = [r["title"] for r in results]
        self.assertIn("GameObject", titles)
        # Check URL format
        gameobject_result = next(r for r in results if r["title"] == "GameObject")
        self.assertIn("GameObject.html", gameobject_result["url"])

    @patch("unity_docs_mcp.search_index.UnitySearchIndex.load_index")
    def test_search_multiple_terms(self, mock_load_index):
        """Test search with multiple terms."""
        # Prevent actual loading
        mock_load_index.return_value = False

        # Set up search data
        self.search_index.pages = self.sample_pages
        self.search_index.page_info = self.sample_info
        self.search_index.search_index = self.sample_search_index
        self.search_index.common_words = set(self.sample_common.keys())
        self.search_index._loaded = True
        # Also add to memory cache
        self.search_index._memory_cache["index_6000.0"] = (
            self.sample_pages,
            self.sample_info,
            self.sample_search_index,
            set(self.sample_common.keys()),
        )

        # Test search for "debug log"
        results = self.search_index.search("debug log", max_results=5)

        self.assertGreater(len(results), 0)
        # Debug.Log should be in the results
        titles = [r["title"] for r in results]
        self.assertIn("Debug.Log", titles)

    @patch("unity_docs_mcp.search_index.UnitySearchIndex.load_index")
    def test_search_case_insensitive(self, mock_load_index):
        """Test case-insensitive search."""
        # Prevent actual loading
        mock_load_index.return_value = False

        # Set up search data
        self.search_index.pages = self.sample_pages
        self.search_index.page_info = self.sample_info
        self.search_index.search_index = self.sample_search_index
        self.search_index.common_words = set(self.sample_common.keys())
        self.search_index._loaded = True
        # Also add to memory cache
        self.search_index._memory_cache["index_6000.0"] = (
            self.sample_pages,
            self.sample_info,
            self.sample_search_index,
            set(self.sample_common.keys()),
        )

        # Test search with different cases
        results1 = self.search_index.search("GAMEOBJECT")
        results2 = self.search_index.search("gameobject")
        results3 = self.search_index.search("GameObject")

        # All should return same results
        self.assertEqual(len(results1), len(results2))
        self.assertEqual(len(results2), len(results3))

    @patch("unity_docs_mcp.search_index.UnitySearchIndex.load_index")
    def test_search_common_words_ignored(self, mock_load_index):
        """Test that common words are ignored in search."""
        # Prevent actual loading
        mock_load_index.return_value = False

        # Set up search data
        self.search_index.pages = self.sample_pages
        self.search_index.page_info = self.sample_info
        self.search_index.search_index = self.sample_search_index
        self.search_index.common_words = set(self.sample_common.keys())
        self.search_index._loaded = True
        # Also add to memory cache
        self.search_index._memory_cache["index_6000.0"] = (
            self.sample_pages,
            self.sample_info,
            self.sample_search_index,
            set(self.sample_common.keys()),
        )

        # Search for a common word
        results = self.search_index.search("the")

        # Should return no results since "the" is a common word
        self.assertEqual(len(results), 0)

    @patch("unity_docs_mcp.search_index.UnitySearchIndex.load_index")
    def test_search_not_loaded(self, mock_load_index):
        """Test search when index is not loaded."""
        # Mock load_index to return False (failed to load)
        mock_load_index.return_value = False

        # Don't load index
        results = self.search_index.search("GameObject")

        # Should return empty list
        self.assertEqual(results, [])

    def test_suggest_classes(self):
        """Test class name suggestions."""
        # Set up search data
        self.search_index.pages = self.sample_pages
        self.search_index.page_info = self.sample_info
        self.search_index._loaded = True

        # Test suggestions for "game"
        suggestions = self.search_index.suggest_classes("game")

        self.assertIn("GameObject", suggestions)
        self.assertNotIn("Transform", suggestions)

    def test_suggest_classes_case_insensitive(self):
        """Test case-insensitive class suggestions."""
        # Set up search data
        self.search_index.pages = self.sample_pages
        self.search_index.page_info = self.sample_info
        self.search_index._loaded = True

        # Test suggestions with different cases
        suggestions1 = self.search_index.suggest_classes("GAME")
        suggestions2 = self.search_index.suggest_classes("game")

        self.assertEqual(suggestions1, suggestions2)

    def test_cache_save_and_load(self):
        """Test cache saving and loading."""
        # Set up search data
        self.search_index.pages = self.sample_pages
        self.search_index.page_info = self.sample_info
        self.search_index.search_index = self.sample_search_index
        self.search_index.common_words = set(self.sample_common.keys())

        # Save to cache
        self.search_index._save_to_cache("test_version")

        # Create new instance and load from cache
        new_index = UnitySearchIndex(cache_dir=self.temp_dir)
        result = new_index._load_from_cache("test_version")

        self.assertTrue(result)
        self.assertEqual(new_index.pages, self.sample_pages)
        self.assertEqual(new_index.search_index, self.sample_search_index)

    def test_cache_expiration(self):
        """Test cache expiration."""
        # Create index with short cache duration
        index = UnitySearchIndex(cache_dir=self.temp_dir, cache_duration_hours=0)

        # Set up and save data
        index.pages = self.sample_pages
        index._save_to_cache("test_version")

        # Try to load - should fail due to expiration
        result = index._load_from_cache("test_version")
        self.assertFalse(result)

    def test_clear_cache(self):
        """Test cache clearing."""
        # Save some cache files
        self.search_index._save_to_cache("version1")
        self.search_index._save_to_cache("version2")

        # Clear specific version
        self.search_index.clear_cache("version1")
        cache_file1 = self.search_index._get_cache_path("version1")
        self.assertFalse(os.path.exists(cache_file1))

        # Version 2 should still exist
        cache_file2 = self.search_index._get_cache_path("version2")
        self.assertTrue(os.path.exists(cache_file2))

        # Clear all
        self.search_index.clear_cache()
        self.assertFalse(os.path.exists(cache_file2))

    @patch("unity_docs_mcp.search_index.UnitySearchIndex.load_index")
    def test_combined_search_term(self, mock_load_index):
        """Test search with combined terms (no spaces)."""
        # Prevent actual loading
        mock_load_index.return_value = False

        # Set up search data
        self.search_index.pages = self.sample_pages
        self.search_index.page_info = self.sample_info
        self.search_index.search_index = {
            "gameobject": [0, 1],
            "setactive": [1],
            "gameobjectsetactive": [1],  # Combined term
        }
        self.search_index.common_words = set()
        self.search_index._loaded = True
        # Also add to memory cache
        self.search_index._memory_cache["index_6000.0"] = (
            self.sample_pages,
            self.sample_info,
            self.search_index.search_index,
            set(),
        )

        # Search for "gameobject setactive" should also try "gameobjectsetactive"
        results = self.search_index.search("gameobject setactive")

        # Should find GameObject.SetActive
        found_titles = [r["title"] for r in results]
        self.assertIn("GameObject.SetActive", found_titles)


if __name__ == "__main__":
    unittest.main()
