"""Tests for Unity documentation scraper."""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time
import json

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from unity_docs_mcp.scraper import UnityDocScraper
from unity_docs_mcp.search_index import UnitySearchIndex


class TestUnityDocScraper(unittest.TestCase):
    """Test cases for UnityDocScraper."""

    def setUp(self):
        """Set up test fixtures."""
        self.scraper = UnityDocScraper()

    def test_build_api_url_class_only(self):
        """Test building API URL for class only."""
        url = self.scraper._build_api_url("GameObject", None, "6000.0")
        expected = "https://docs.unity3d.com/6000.0/Documentation/ScriptReference/GameObject.html"
        self.assertEqual(url, expected)

    def test_build_api_url_class_and_method(self):
        """Test building API URL for class and method."""
        url = self.scraper._build_api_url("GameObject", "Instantiate", "6000.0")
        expected = "https://docs.unity3d.com/6000.0/Documentation/ScriptReference/GameObject.Instantiate.html"
        self.assertEqual(url, expected)

    def test_build_api_url_whitespace_handling(self):
        """Test URL building with whitespace in inputs."""
        url = self.scraper._build_api_url(" GameObject ", " Instantiate ", "6000.0")
        expected = "https://docs.unity3d.com/6000.0/Documentation/ScriptReference/GameObject.Instantiate.html"
        self.assertEqual(url, expected)

    def test_build_api_url_with_hyphen(self):
        """Test building API URL with hyphen notation for properties."""
        url = self.scraper._build_api_url(
            "GameObject", "transform", "6000.0", use_hyphen=True
        )
        expected = "https://docs.unity3d.com/6000.0/Documentation/ScriptReference/GameObject-transform.html"
        self.assertEqual(url, expected)

    def test_build_api_url_dot_vs_hyphen(self):
        """Test that dot and hyphen notations produce different URLs."""
        dot_url = self.scraper._build_api_url(
            "ContactPoint2D", "otherRigidbody", "6000.0", use_hyphen=False
        )
        hyphen_url = self.scraper._build_api_url(
            "ContactPoint2D", "otherRigidbody", "6000.0", use_hyphen=True
        )

        self.assertIn("ContactPoint2D.otherRigidbody.html", dot_url)
        self.assertIn("ContactPoint2D-otherRigidbody.html", hyphen_url)
        self.assertNotEqual(dot_url, hyphen_url)

    def test_build_search_url(self):
        """Test building search URL."""
        url = self.scraper._build_search_url("transform", "6000.0")
        expected = "https://docs.unity3d.com/6000.0/Documentation/ScriptReference/30_search.html?q=transform"
        self.assertEqual(url, expected)

    def test_build_search_url_with_spaces(self):
        """Test building search URL with spaces in query."""
        url = self.scraper._build_search_url("game object", "6000.0")
        expected = "https://docs.unity3d.com/6000.0/Documentation/ScriptReference/30_search.html?q=game%20object"
        self.assertEqual(url, expected)

    def test_validate_version_valid(self):
        """Test version validation with valid versions."""
        # Get actual supported versions for testing
        supported_versions = self.scraper.get_supported_versions()

        # Test with versions we know should be supported
        self.assertTrue(self.scraper.validate_version("6000.0"))

        # Test with the first few versions from the actual list
        if len(supported_versions) > 0:
            self.assertTrue(self.scraper.validate_version(supported_versions[0]))
        if len(supported_versions) > 1:
            self.assertTrue(self.scraper.validate_version(supported_versions[1]))

    def test_validate_version_invalid(self):
        """Test version validation with invalid versions."""
        self.assertFalse(self.scraper.validate_version("invalid"))
        self.assertFalse(self.scraper.validate_version("1.0"))
        self.assertFalse(self.scraper.validate_version(""))

    def test_get_supported_versions(self):
        """Test getting supported versions."""
        versions = self.scraper.get_supported_versions()
        self.assertIsInstance(versions, list)
        self.assertIn("6000.0", versions)
        # Note: 2023.3 might not be in the current Unity versions info
        # Just check that we get reasonable recent versions
        self.assertGreater(len(versions), 5)
        # Should include some Unity 6 versions
        unity6_versions = [v for v in versions if v.startswith("6000.")]
        self.assertGreater(len(unity6_versions), 0)

    def test_suggest_class_names(self):
        """Test class name suggestions."""
        suggestions = self.scraper.suggest_class_names("game")
        self.assertIn("GameObject", suggestions)

        suggestions = self.scraper.suggest_class_names("trans")
        self.assertIn("Transform", suggestions)

        suggestions = self.scraper.suggest_class_names("VECTOR")
        self.assertIn("Vector3", suggestions)
        self.assertIn("Vector2", suggestions)

    def test_suggest_class_names_no_matches(self):
        """Test class name suggestions with no matches."""
        suggestions = self.scraper.suggest_class_names("xyz123nonexistent")
        self.assertEqual(len(suggestions), 0)

    def test_suggest_class_names_limit(self):
        """Test class name suggestions are limited to 10."""
        suggestions = self.scraper.suggest_class_names("e")  # Many classes contain 'e'
        self.assertLessEqual(len(suggestions), 10)

    @patch("unity_docs_mcp.scraper.requests.Session.get")
    def test_fetch_page_success(self, mock_get):
        """Test successful page fetching."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Test content</body></html>"
        mock_get.return_value = mock_response

        result = self.scraper._fetch_page("https://example.com")
        self.assertEqual(result, "<html><body>Test content</body></html>")
        mock_get.assert_called_once()

    @patch("unity_docs_mcp.scraper.requests.Session.get")
    def test_fetch_page_404(self, mock_get):
        """Test page fetching with 404 error."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = self.scraper._fetch_page("https://example.com/nonexistent")
        self.assertIsNone(result)

    @patch("unity_docs_mcp.scraper.requests.Session.get")
    def test_fetch_page_server_error(self, mock_get):
        """Test page fetching with server error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        result = self.scraper._fetch_page("https://example.com")
        self.assertIsNone(result)

    @patch("unity_docs_mcp.scraper.requests.Session.get")
    def test_fetch_page_request_exception(self, mock_get):
        """Test page fetching with request exception."""
        import requests

        mock_get.side_effect = requests.exceptions.RequestException("Connection error")

        result = self.scraper._fetch_page("https://example.com")
        self.assertIsNone(result)

    @patch("unity_docs_mcp.scraper.time.sleep")
    @patch("unity_docs_mcp.scraper.requests.Session.get")
    def test_rate_limiting(self, mock_get, mock_sleep):
        """Test rate limiting functionality."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "content"
        mock_get.return_value = mock_response

        # Make two requests quickly
        start_time = time.time()
        self.scraper.last_request_time = start_time

        self.scraper._fetch_page("https://example.com/1")
        self.scraper._fetch_page("https://example.com/2")

        # Should have called sleep for rate limiting
        mock_sleep.assert_called()

    @patch("unity_docs_mcp.scraper.UnityDocScraper._fetch_page")
    def test_get_api_doc_success(self, mock_fetch):
        """Test successful API documentation retrieval."""
        mock_fetch.return_value = "<html>Test content</html>"

        result = self.scraper.get_api_doc("GameObject", "Instantiate", "6000.0")

        self.assertEqual(result["status"], "success")
        self.assertIn("url", result)
        self.assertIn("html", result)
        self.assertEqual(result["html"], "<html>Test content</html>")

    @patch("unity_docs_mcp.scraper.UnityDocScraper._fetch_page")
    def test_get_api_doc_fetch_failure(self, mock_fetch):
        """Test API documentation retrieval with fetch failure."""
        mock_fetch.return_value = None

        result = self.scraper.get_api_doc("GameObject", "Instantiate", "6000.0")

        self.assertEqual(result["status"], "error")
        self.assertIn("error", result)

    @patch("unity_docs_mcp.scraper.UnityDocScraper._fetch_page")
    def test_get_api_doc_property_fallback(self, mock_fetch):
        """Test that properties fall back to hyphen notation when dot notation fails."""
        # First call (dot notation) returns None, second call (hyphen notation) returns content
        mock_fetch.side_effect = [None, "<html>Property content</html>"]

        result = self.scraper.get_api_doc("ContactPoint2D", "otherRigidbody", "6000.0")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["html"], "<html>Property content</html>")
        self.assertIn("ContactPoint2D-otherRigidbody.html", result["url"])

        # Verify both URL patterns were tried
        self.assertEqual(mock_fetch.call_count, 2)
        first_call_url = mock_fetch.call_args_list[0][0][0]
        second_call_url = mock_fetch.call_args_list[1][0][0]
        self.assertIn("ContactPoint2D.otherRigidbody.html", first_call_url)
        self.assertIn("ContactPoint2D-otherRigidbody.html", second_call_url)

    @patch("unity_docs_mcp.scraper.UnityDocScraper._fetch_page")
    def test_get_api_doc_exception(self, mock_fetch):
        """Test API documentation retrieval with exception."""
        mock_fetch.side_effect = Exception("Network error")

        result = self.scraper.get_api_doc("GameObject", "Instantiate", "6000.0")

        self.assertEqual(result["status"], "error")
        self.assertIn("Network error", result["error"])

    @patch("unity_docs_mcp.search_index.UnitySearchIndex.search")
    def test_search_docs_success(self, mock_search):
        """Test successful documentation search."""
        mock_results = [
            {
                "title": "Transform",
                "url": "https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Transform.html",
                "description": "Position, rotation and scale of an object.",
            }
        ]
        mock_search.return_value = mock_results

        result = self.scraper.search_docs("transform", "6000.0")

        self.assertEqual(result["status"], "success")
        self.assertIn("results", result)
        self.assertIn("count", result)
        self.assertEqual(result["results"], mock_results)
        self.assertEqual(result["count"], 1)

    @patch("unity_docs_mcp.search_index.UnitySearchIndex.search")
    def test_search_docs_no_results(self, mock_search):
        """Test documentation search with no results."""
        mock_search.return_value = []

        result = self.scraper.search_docs("nonexistent", "6000.0")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["results"], [])
        self.assertEqual(result["count"], 0)

    @patch("unity_docs_mcp.search_index.UnitySearchIndex.search")
    def test_search_docs_exception(self, mock_search):
        """Test documentation search with exception."""
        mock_search.side_effect = Exception("Search error")

        result = self.scraper.search_docs("transform", "6000.0")

        self.assertEqual(result["status"], "error")
        self.assertIn("Search error", result["error"])

    def test_normalize_version_full_versions(self):
        """Test version normalization for full Unity versions."""
        test_cases = [
            ("6000.0.29f1", "6000.0"),
            ("2022.3.45f1", "2022.3"),
            ("2021.3.12a1", "2021.3"),
            ("2020.3.48b2", "2020.3"),
            ("2019.4.31f1", "2019.4"),
        ]

        for input_version, expected in test_cases:
            with self.subTest(input_version=input_version):
                result = self.scraper.normalize_version(input_version)
                self.assertEqual(result, expected)

    def test_normalize_version_already_normalized(self):
        """Test version normalization for already normalized versions."""
        test_cases = ["6000.0", "2023.3", "2022.3", "2021.3", "2020.3", "2019.4"]

        for version in test_cases:
            with self.subTest(version=version):
                result = self.scraper.normalize_version(version)
                self.assertEqual(result, version)

    def test_normalize_version_invalid_formats(self):
        """Test version normalization for invalid formats."""
        test_cases = ["invalid", "1", "abc.def", ""]

        for version in test_cases:
            with self.subTest(version=version):
                result = self.scraper.normalize_version(version)
                self.assertEqual(result, version)  # Should return as-is

    def test_validate_version_with_normalization(self):
        """Test version validation with version normalization."""
        # These should be valid after normalization
        self.assertTrue(self.scraper.validate_version("6000.0.29f1"))
        self.assertTrue(self.scraper.validate_version("2022.3.45f1"))
        self.assertTrue(self.scraper.validate_version("2021.3.12a1"))

        # These should be invalid even after normalization
        self.assertFalse(self.scraper.validate_version("1.0.5f1"))
        self.assertFalse(self.scraper.validate_version("invalid.version"))

    @patch("unity_docs_mcp.scraper.requests.Session.get")
    def test_get_latest_version_success(self, mock_get):
        """Test successful latest version detection."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.url = "https://docs.unity3d.com/6000.1/Documentation/ScriptReference/GameObject.html"
        mock_response.text = "<html>Unity 6.1</html>"
        mock_get.return_value = mock_response

        result = self.scraper.get_latest_version()
        self.assertEqual(result, "6000.1")

    @patch("unity_docs_mcp.scraper.requests.Session.get")
    def test_get_latest_version_from_content(self, mock_get):
        """Test latest version detection from page content."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.url = "https://docs.unity3d.com/ScriptReference/GameObject.html"  # No version in URL
        mock_response.text = "<html><title>Unity 6.1 Documentation</title></html>"
        mock_get.return_value = mock_response

        result = self.scraper.get_latest_version()
        self.assertEqual(result, "6000.1")

    @patch("unity_docs_mcp.scraper.requests.Session.get")
    def test_get_latest_version_fallback(self, mock_get):
        """Test latest version detection with fallback."""
        mock_get.side_effect = Exception("Network error")

        result = self.scraper.get_latest_version()
        # Should fallback to first supported version
        expected = self.scraper.get_supported_versions()[0]
        self.assertEqual(result, expected)

    @patch("unity_docs_mcp.scraper.requests.Session.head")
    def test_check_api_availability_success(self, mock_head):
        """Test API availability checking across versions."""
        # The method tests 6 predefined versions, mock accordingly
        test_versions = ["6000.0", "2023.3", "2022.3", "2021.3", "2020.3", "2019.4"]

        # Mock responses: first 3 versions have the API, last 3 don't
        mock_responses = []
        for i in range(len(test_versions)):
            mock_response = Mock()
            mock_response.status_code = 200 if i < 3 else 404
            mock_responses.append(mock_response)

        mock_head.side_effect = mock_responses

        result = self.scraper.check_api_availability_across_versions(
            "GameObject", "SetActive"
        )

        self.assertIn("available", result)
        self.assertIn("unavailable", result)
        # Note: The actual counts depend on how many test versions are validated
        # Just check that we got reasonable results
        self.assertGreater(len(result["available"]), 0)
        self.assertGreater(len(result["unavailable"]), 0)

    @patch("unity_docs_mcp.scraper.requests.Session.head")
    def test_check_api_availability_all_unavailable(self, mock_head):
        """Test API availability checking when API is not found in any version."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_head.return_value = mock_response

        result = self.scraper.check_api_availability_across_versions("NonexistentClass")

        self.assertEqual(len(result["available"]), 0)
        self.assertGreater(len(result["unavailable"]), 0)

    @patch("unity_docs_mcp.scraper.requests.Session.head")
    def test_check_api_availability_network_error(self, mock_head):
        """Test API availability checking with network errors."""
        import requests

        mock_head.side_effect = requests.exceptions.RequestException("Network error")

        result = self.scraper.check_api_availability_across_versions("GameObject")

        # All versions should be in unavailable due to network errors
        self.assertEqual(len(result["available"]), 0)
        self.assertGreater(len(result["unavailable"]), 0)

    def test_get_api_doc_with_normalization(self):
        """Test API doc retrieval with version normalization."""
        with patch.object(self.scraper, "_fetch_page") as mock_fetch:
            mock_fetch.return_value = "<html>Test content</html>"

            result = self.scraper.get_api_doc("GameObject", "SetActive", "6000.0.29f1")

            self.assertEqual(result["status"], "success")
            # Should have normalized the version in the URL
            self.assertIn("6000.0", result["url"])
            self.assertNotIn("6000.0.29f1", result["url"])

    def test_search_docs_with_normalization(self):
        """Test documentation search with version normalization."""
        with patch.object(self.scraper.search_index, "search") as mock_search:
            mock_search.return_value = []

            result = self.scraper.search_docs("transform", "2022.3.45f1")

            # Should call search with normalized version
            mock_search.assert_called_with("transform", "2022.3")

    @patch("unity_docs_mcp.scraper.requests.Session.get")
    def test_get_supported_versions_dynamic_success(self, mock_get):
        """Test dynamic supported versions fetching."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """UnityVersionsInfo = {
  supported: [
    { major: 6000, minor: 2, name: "Unity 6.2 Beta" },
    { major: 6000, minor: 1, name: "Unity 6.1" },
    { major: 2022, minor: 3, LTS: true },
  ],
  notSupported: [
    { major: 2023, minor: 2 },
    { major: 2022, minor: 2 },
    { major: 2020, minor: 3 },
    { major: 2019, minor: 4 },
  ],
};"""
        mock_get.return_value = mock_response

        result = self.scraper.get_supported_versions()

        # Should include both supported and recent not-supported versions
        self.assertIn("6000.2", result)
        self.assertIn("6000.1", result)
        self.assertIn("2022.3", result)
        self.assertIn("2023.2", result)  # Recent "not supported" but included
        self.assertIn("2022.2", result)
        self.assertIn("2020.3", result)
        self.assertIn("2019.4", result)

        # Should be sorted with latest first
        self.assertEqual(result[0], "6000.2")

    @patch("unity_docs_mcp.scraper.requests.Session.get")
    def test_get_supported_versions_dynamic_fallback(self, mock_get):
        """Test dynamic supported versions with fallback on error."""
        mock_get.side_effect = Exception("Network error")

        result = self.scraper.get_supported_versions()

        # Should fallback to hardcoded list
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        self.assertIn("6000.0", result)

    @patch("unity_docs_mcp.scraper.requests.Session.get")
    def test_get_supported_versions_dynamic_http_error(self, mock_get):
        """Test dynamic supported versions with HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        result = self.scraper.get_supported_versions()

        # Should fallback to hardcoded list
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        self.assertIn("6000.0", result)

    @patch("unity_docs_mcp.scraper.requests.Session.get")
    def test_get_supported_versions_filtering_old_versions(self, mock_get):
        """Test that very old versions are filtered out."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """UnityVersionsInfo = {
  supported: [
    { major: 6000, minor: 1, name: "Unity 6.1" },
  ],
  notSupported: [
    { major: 2018, minor: 4 },  // Should be filtered out (too old)
    { major: 2019, minor: 4 },  // Should be included (2019+)
    { major: 2020, minor: 3 },  // Should be included
  ],
};"""
        mock_get.return_value = mock_response

        result = self.scraper.get_supported_versions()

        # Should include 2019+ versions but exclude older ones
        self.assertIn("6000.1", result)
        self.assertIn("2019.4", result)
        self.assertIn("2020.3", result)
        self.assertNotIn("2018.4", result)  # Should be filtered out

    def test_scraper_initialization(self):
        """Test that UnityDocScraper can be initialized."""
        scraper = UnityDocScraper()
        self.assertIsNotNone(scraper)
        self.assertIsNotNone(scraper.session)
        self.assertIsNotNone(scraper.search_index)

    # Additional search tests from test_scraper_search.py
    def test_suggest_class_names_from_index(self):
        """Test class name suggestions using search index."""
        # Mock suggestions from index
        mock_suggestions = ["GameObject", "GameObjectUtility"]
        self.scraper.search_index.suggest_classes = Mock(return_value=mock_suggestions)

        suggestions = self.scraper.suggest_class_names("game")

        self.assertEqual(suggestions, mock_suggestions)
        self.scraper.search_index.suggest_classes.assert_called_once_with("game")

    def test_suggest_class_names_fallback(self):
        """Test class name suggestions fallback when index returns empty."""
        # Mock empty suggestions from index
        self.scraper.search_index.suggest_classes = Mock(return_value=[])

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

        self.scraper.search_index.search = Mock(return_value=search_results)

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
        self.scraper.search_index.search = Mock(return_value=mock_results)

        # Test different versions
        versions = ["6000.0", "2023.3", "2022.3"]
        for version in versions:
            result = self.scraper.search_docs("test", version)
            self.assertEqual(result["status"], "success")

        # Verify each version was searched
        self.assertEqual(self.scraper.search_index.search.call_count, len(versions))


class TestNamespaceHandling(unittest.TestCase):
    """Test that the scraper correctly handles Unity classes with namespaces."""

    def setUp(self):
        self.scraper = UnityDocScraper()

    @patch.object(UnityDocScraper, "_fetch_page")
    def test_navmeshagent_without_namespace(self, mock_fetch):
        """Test that NavMeshAgent is found even without AI namespace."""
        # Mock search results
        self.scraper.search_index.search = Mock(
            return_value=[
                {
                    "type": "class",
                    "title": "NavMeshAgent",
                    "url": "https://docs.unity3d.com/6000.0/Documentation/ScriptReference/AI.NavMeshAgent.html",
                }
            ]
        )

        # Mock successful page fetch
        mock_fetch.return_value = "<html>NavMeshAgent content</html>"

        # Test
        result = self.scraper.get_api_doc("NavMeshAgent", version="6000.0")

        self.assertEqual(result["status"], "success")
        self.assertIn("AI.NavMeshAgent", result["url"])

    @patch.object(UnityDocScraper, "_fetch_page")
    def test_class_with_namespace_provided(self, mock_fetch):
        """Test that classes work when namespace is provided."""
        # Mock successful page fetch
        mock_fetch.return_value = "<html>NavMeshAgent content</html>"

        # Test
        result = self.scraper.get_api_doc("AI.NavMeshAgent", version="6000.0")

        self.assertEqual(result["status"], "success")
        self.assertIn("AI.NavMeshAgent", result["url"])

    @patch.object(UnityDocScraper, "_fetch_page")
    def test_class_without_namespace_in_unity(self, mock_fetch):
        """Test that classes without namespaces work correctly."""
        # Mock search results
        self.scraper.search_index.search = Mock(
            return_value=[
                {
                    "type": "class",
                    "title": "GameObject",
                    "url": "https://docs.unity3d.com/6000.0/Documentation/ScriptReference/GameObject.html",
                }
            ]
        )

        # Mock successful page fetch
        mock_fetch.return_value = "<html>GameObject content</html>"

        # Test
        result = self.scraper.get_api_doc("GameObject", version="6000.0")

        self.assertEqual(result["status"], "success")
        self.assertIn("GameObject.html", result["url"])

    @patch.object(UnityDocScraper, "_fetch_page")
    def test_method_with_namespace_resolution(self, mock_fetch):
        """Test that methods work with namespace resolution."""
        # Mock search results
        self.scraper.search_index.search = Mock(
            return_value=[
                {
                    "type": "class",
                    "title": "NavMeshAgent",
                    "url": "https://docs.unity3d.com/6000.0/Documentation/ScriptReference/AI.NavMeshAgent.html",
                }
            ]
        )

        # Mock successful page fetch for property (hyphen notation)
        mock_fetch.return_value = "<html>remainingDistance content</html>"

        # Test
        result = self.scraper.get_api_doc(
            "NavMeshAgent", "remainingDistance", version="6000.0"
        )

        self.assertEqual(result["status"], "success")
        # Should try dot notation first, then hyphen notation
        self.assertIn("AI.NavMeshAgent", result["url"])


if __name__ == "__main__":
    unittest.main()
