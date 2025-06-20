"""Additional tests for Unity documentation scraper search functionality."""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from unity_docs_mcp.scraper import UnityDocScraper
from unity_docs_mcp.search_index import UnitySearchIndex


class TestUnityDocScraperSearch(unittest.TestCase):
    """Test cases for UnityDocScraper search functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.scraper = UnityDocScraper()

        # Mock search index
        self.mock_search_index = Mock(spec=UnitySearchIndex)
        self.scraper.search_index = self.mock_search_index

    def test_search_docs_success(self):
        """Test successful search using search index."""
        # Mock search results
        mock_results = [
            {
                "title": "GameObject",
                "url": "https://docs.unity3d.com/6000.0/Documentation/ScriptReference/GameObject.html",
                "description": "Base class for all entities in Unity Scenes.",
            },
            {
                "title": "GameObject.SetActive",
                "url": "https://docs.unity3d.com/6000.0/Documentation/ScriptReference/GameObject.SetActive.html",
                "description": "Activates/Deactivates the GameObject.",
            },
        ]

        self.mock_search_index.search.return_value = mock_results

        # Perform search
        result = self.scraper.search_docs("gameobject", "6000.0")

        # Verify results
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["results"], mock_results)
        self.assertEqual(result["count"], 2)

        # Verify search was called correctly
        self.mock_search_index.search.assert_called_once_with("gameobject", "6000.0")

    def test_search_docs_no_results(self):
        """Test search with no results."""
        self.mock_search_index.search.return_value = []

        result = self.scraper.search_docs("nonexistentclass", "6000.0")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["results"], [])
        self.assertEqual(result["count"], 0)

    def test_search_docs_error(self):
        """Test search with error."""
        self.mock_search_index.search.side_effect = Exception("Search index error")

        result = self.scraper.search_docs("gameobject", "6000.0")

        self.assertEqual(result["status"], "error")
        self.assertIn("error", result)
        self.assertIn("Search index error", result["error"])

    def test_suggest_class_names_from_index(self):
        """Test class name suggestions using search index."""
        # Mock suggestions from index
        mock_suggestions = ["GameObject", "GameObjectUtility"]
        self.mock_search_index.suggest_classes.return_value = mock_suggestions

        suggestions = self.scraper.suggest_class_names("game")

        self.assertEqual(suggestions, mock_suggestions)
        self.mock_search_index.suggest_classes.assert_called_once_with("game")

    def test_suggest_class_names_fallback(self):
        """Test class name suggestions fallback when index returns empty."""
        # Mock empty suggestions from index
        self.mock_search_index.suggest_classes.return_value = []

        suggestions = self.scraper.suggest_class_names("game")

        # Should use fallback common classes
        self.assertIn("GameObject", suggestions)
        self.assertLessEqual(len(suggestions), 10)

    def test_search_integration(self):
        """Test search integration with real-like data."""
        # Set up more realistic mock data
        search_results = [
            {
                "title": "Transform",
                "url": "https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Transform.html",
                "description": "Position, rotation and scale of an object.",
            },
            {
                "title": "Transform.position",
                "url": "https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Transform-position.html",
                "description": "The world space position of the Transform.",
            },
            {
                "title": "Transform.Translate",
                "url": "https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Transform.Translate.html",
                "description": "Moves the transform in the direction and distance of translation.",
            },
        ]

        self.mock_search_index.search.return_value = search_results

        # Search for "transform position"
        result = self.scraper.search_docs("transform position", "6000.0")

        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["results"]), 3)
        # Transform.position should be in results
        titles = [r["title"] for r in result["results"]]
        self.assertIn("Transform.position", titles)

    @patch("unity_docs_mcp.search_index.UnitySearchIndex.load_index")
    def test_search_with_index_loading(self, mock_load_index):
        """Test search triggers index loading if needed."""
        # Create a real UnitySearchIndex instance for this test
        real_index = UnitySearchIndex()
        self.scraper.search_index = real_index

        # Mock successful index loading
        mock_load_index.return_value = True
        real_index.pages = [["GameObject", "GameObject"]]
        real_index.page_info = [["Base class for all entities.", 0]]
        real_index.search_index = {"gameobject": [0]}
        real_index.common_words = set()

        # Perform search (should trigger index loading)
        result = self.scraper.search_docs("gameobject", "6000.0")

        # Verify index was loaded
        mock_load_index.assert_called_once_with("6000.0")

        # Verify search worked
        self.assertEqual(result["status"], "success")
        self.assertGreater(len(result["results"]), 0)

    def test_search_different_versions(self):
        """Test search with different Unity versions."""
        mock_results = [{"title": "Test", "url": "test.html", "description": "Test"}]
        self.mock_search_index.search.return_value = mock_results

        # Test different versions
        versions = ["6000.0", "2023.3", "2022.3"]
        for version in versions:
            result = self.scraper.search_docs("test", version)
            self.assertEqual(result["status"], "success")

        # Verify each version was searched
        self.assertEqual(self.mock_search_index.search.call_count, len(versions))


if __name__ == "__main__":
    unittest.main()
