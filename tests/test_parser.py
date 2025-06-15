"""Tests for Unity documentation parser."""

import unittest
from unittest.mock import Mock, patch
from bs4 import BeautifulSoup

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from unity_docs_mcp.parser import UnityDocParser


class TestUnityDocParser(unittest.TestCase):
    """Test cases for UnityDocParser."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = UnityDocParser()
        
        # Sample HTML content for testing
        self.sample_api_html = """
        <html>
        <head><title>GameObject.Instantiate - Unity</title></head>
        <body>
            <div class="content">
                <h1>GameObject.Instantiate</h1>
                <p>Creates a new object that is a copy of the original.</p>
                <h2>Parameters</h2>
                <div class="subsection">
                    <table>
                        <tr><th>Parameter</th><th>Description</th></tr>
                        <tr><td>original</td><td>An existing object that you want to make a copy of.</td></tr>
                    </table>
                </div>
                <h2>Returns</h2>
                <p>The instantiated clone.</p>
                <pre><code>
public static Object Instantiate(Object original);
                </code></pre>
                <a href="/ScriptReference/Object.html">Object</a>
                <script>console.log('test');</script>
                <style>.hidden { display: none; }</style>
            </div>
        </body>
        </html>
        """
        
        self.sample_search_html = """
        <html>
        <body>
            <div class="search-results">
                <div class="search-result">
                    <h3><a href="/ScriptReference/Transform.html">Transform</a></h3>
                    <p>Position, rotation and scale of an object.</p>
                </div>
                <div class="search-result">
                    <h3><a href="/ScriptReference/GameObject.html">GameObject</a></h3>
                    <p>Base class for all entities in Unity Scenes.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def test_parse_api_doc_success(self):
        """Test successful API documentation parsing."""
        url = "https://docs.unity3d.com/6000.0/Documentation/ScriptReference/GameObject.Instantiate.html"
        result = self.parser.parse_api_doc(self.sample_api_html, url)
        
        self.assertIn("title", result)
        self.assertIn("content", result)
        self.assertIn("url", result)
        self.assertEqual(result["url"], url)
        self.assertEqual(result["title"], "GameObject.Instantiate")
        
        # Check that content contains expected elements
        content = result["content"]
        self.assertIn("GameObject.Instantiate", content)
        self.assertIn("Creates a new object", content)
        self.assertIn("Parameters", content)
        self.assertIn("Returns", content)
        
        # Check that scripts and styles are removed
        self.assertNotIn("console.log", content)
        self.assertNotIn(".hidden", content)
    
    def test_parse_api_doc_no_content(self):
        """Test parsing when main content div is not found."""
        html = "<html><body><p>No main content</p></body></html>"
        url = "https://example.com"
        result = self.parser.parse_api_doc(html, url)
        
        self.assertIn("error", result)
    
    def test_parse_search_results_success(self):
        """Test successful search results parsing."""
        result = self.parser.parse_search_results(self.sample_search_html)
        
        self.assertIn("results", result)
        self.assertIn("count", result)
        self.assertEqual(result["count"], 2)
        
        results = result["results"]
        self.assertEqual(len(results), 2)
        
        # Check first result
        first_result = results[0]
        self.assertEqual(first_result["title"], "Transform")
        self.assertIn("Transform.html", first_result["url"])
        self.assertIn("Position, rotation", first_result["description"])
        
        # Check second result
        second_result = results[1]
        self.assertEqual(second_result["title"], "GameObject")
        self.assertIn("GameObject.html", second_result["url"])
    
    def test_parse_search_results_empty(self):
        """Test parsing empty search results."""
        html = "<html><body><div>No results found</div></body></html>"
        result = self.parser.parse_search_results(html)
        
        self.assertEqual(result["count"], 0)
        self.assertEqual(len(result["results"]), 0)
    
    def test_extract_title_h1(self):
        """Test title extraction from h1 tag."""
        soup = BeautifulSoup("<html><body><h1>Test Title - Unity Manual</h1></body></html>", 'html.parser')
        title = self.parser._extract_title(soup)
        self.assertEqual(title, "Test Title")
    
    def test_extract_title_title_tag(self):
        """Test title extraction from title tag."""
        soup = BeautifulSoup("<html><head><title>Page Title - Unity</title></head></html>", 'html.parser')
        title = self.parser._extract_title(soup)
        self.assertEqual(title, "Page Title")
    
    def test_extract_title_fallback(self):
        """Test title extraction fallback."""
        soup = BeautifulSoup("<html><body><p>No title</p></body></html>", 'html.parser')
        title = self.parser._extract_title(soup)
        self.assertEqual(title, "Unity Documentation")
    
    def test_clean_markdown(self):
        """Test markdown cleaning functionality."""
        messy_markdown = """
# Title


Content here



| Column 1 |  |
|  | Column 2 |


[]()

```

```

More content
        """
        
        cleaned = self.parser._clean_markdown(messy_markdown)
        
        # Should remove excessive newlines
        self.assertNotIn("\n\n\n", cleaned)
        
        # Should remove empty links
        self.assertNotIn("[]()", cleaned)
        
        # Should remove empty code blocks
        self.assertNotIn("```\n\n```", cleaned)
    
    def test_relative_link_conversion(self):
        """Test conversion of relative links to absolute URLs."""
        html_with_relative_links = """
        <div class="content">
            <a href="/ScriptReference/Transform.html">Transform</a>
            <a href="../Manual/GameObjects.html">GameObjects</a>
            <a href="https://unity.com">Unity</a>
        </div>
        """
        
        url = "https://docs.unity3d.com/6000.0/Documentation/ScriptReference/GameObject.html"
        result = self.parser.parse_api_doc(html_with_relative_links, url)
        
        content = result["content"]
        
        # Absolute URL from root should be converted
        self.assertIn("https://docs.unity3d.com/ScriptReference/Transform.html", content)
        
        # External URLs should remain unchanged
        self.assertIn("https://unity.com", content)


if __name__ == '__main__':
    unittest.main()