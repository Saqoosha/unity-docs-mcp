"""Tests for Unity documentation scraper."""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from unity_docs_mcp.scraper import UnityDocScraper


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
        url = self.scraper._build_api_url("GameObject", "transform", "6000.0", use_hyphen=True)
        expected = "https://docs.unity3d.com/6000.0/Documentation/ScriptReference/GameObject-transform.html"
        self.assertEqual(url, expected)
    
    def test_build_api_url_dot_vs_hyphen(self):
        """Test that dot and hyphen notations produce different URLs."""
        dot_url = self.scraper._build_api_url("ContactPoint2D", "otherRigidbody", "6000.0", use_hyphen=False)
        hyphen_url = self.scraper._build_api_url("ContactPoint2D", "otherRigidbody", "6000.0", use_hyphen=True)
        
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
        self.assertTrue(self.scraper.validate_version("6000.0"))
        self.assertTrue(self.scraper.validate_version("2023.3"))
        self.assertTrue(self.scraper.validate_version("2022.1"))
    
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
        self.assertIn("2023.3", versions)
        self.assertGreater(len(versions), 0)
    
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
    
    @patch('unity_docs_mcp.scraper.requests.Session.get')
    def test_fetch_page_success(self, mock_get):
        """Test successful page fetching."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Test content</body></html>"
        mock_get.return_value = mock_response
        
        result = self.scraper._fetch_page("https://example.com")
        self.assertEqual(result, "<html><body>Test content</body></html>")
        mock_get.assert_called_once()
    
    @patch('unity_docs_mcp.scraper.requests.Session.get')
    def test_fetch_page_404(self, mock_get):
        """Test page fetching with 404 error."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        result = self.scraper._fetch_page("https://example.com/nonexistent")
        self.assertIsNone(result)
    
    @patch('unity_docs_mcp.scraper.requests.Session.get')
    def test_fetch_page_server_error(self, mock_get):
        """Test page fetching with server error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        result = self.scraper._fetch_page("https://example.com")
        self.assertIsNone(result)
    
    @patch('unity_docs_mcp.scraper.requests.Session.get')
    def test_fetch_page_request_exception(self, mock_get):
        """Test page fetching with request exception."""
        import requests
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")
        
        result = self.scraper._fetch_page("https://example.com")
        self.assertIsNone(result)
    
    @patch('unity_docs_mcp.scraper.time.sleep')
    @patch('unity_docs_mcp.scraper.requests.Session.get')
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
    
    @patch('unity_docs_mcp.scraper.UnityDocScraper._fetch_page')
    def test_get_api_doc_success(self, mock_fetch):
        """Test successful API documentation retrieval."""
        mock_fetch.return_value = "<html>Test content</html>"
        
        result = self.scraper.get_api_doc("GameObject", "Instantiate", "6000.0")
        
        self.assertEqual(result["status"], "success")
        self.assertIn("url", result)
        self.assertIn("html", result)
        self.assertEqual(result["html"], "<html>Test content</html>")
    
    @patch('unity_docs_mcp.scraper.UnityDocScraper._fetch_page')
    def test_get_api_doc_fetch_failure(self, mock_fetch):
        """Test API documentation retrieval with fetch failure."""
        mock_fetch.return_value = None
        
        result = self.scraper.get_api_doc("GameObject", "Instantiate", "6000.0")
        
        self.assertEqual(result["status"], "error")
        self.assertIn("error", result)
    
    @patch('unity_docs_mcp.scraper.UnityDocScraper._fetch_page')
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
    
    @patch('unity_docs_mcp.scraper.UnityDocScraper._fetch_page')
    def test_get_api_doc_exception(self, mock_fetch):
        """Test API documentation retrieval with exception."""
        mock_fetch.side_effect = Exception("Network error")
        
        result = self.scraper.get_api_doc("GameObject", "Instantiate", "6000.0")
        
        self.assertEqual(result["status"], "error")
        self.assertIn("Network error", result["error"])
    
    @patch('unity_docs_mcp.search_index.UnitySearchIndex.search')
    def test_search_docs_success(self, mock_search):
        """Test successful documentation search."""
        mock_results = [
            {
                'title': 'Transform',
                'url': 'https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Transform.html',
                'description': 'Position, rotation and scale of an object.'
            }
        ]
        mock_search.return_value = mock_results
        
        result = self.scraper.search_docs("transform", "6000.0")
        
        self.assertEqual(result["status"], "success")
        self.assertIn("results", result)
        self.assertIn("count", result)
        self.assertEqual(result["results"], mock_results)
        self.assertEqual(result["count"], 1)
    
    @patch('unity_docs_mcp.search_index.UnitySearchIndex.search')
    def test_search_docs_no_results(self, mock_search):
        """Test documentation search with no results."""
        mock_search.return_value = []
        
        result = self.scraper.search_docs("nonexistent", "6000.0")
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["results"], [])
        self.assertEqual(result["count"], 0)
    
    @patch('unity_docs_mcp.search_index.UnitySearchIndex.search')
    def test_search_docs_exception(self, mock_search):
        """Test documentation search with exception."""
        mock_search.side_effect = Exception("Search error")
        
        result = self.scraper.search_docs("transform", "6000.0")
        
        self.assertEqual(result["status"], "error")
        self.assertIn("Search error", result["error"])


if __name__ == '__main__':
    unittest.main()