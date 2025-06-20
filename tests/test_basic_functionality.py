"""Basic functionality tests to ensure code is not broken."""

import unittest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestBasicFunctionality(unittest.TestCase):
    """Test that all modules can be imported and basic functionality works."""

    def test_imports(self):
        """Test that all modules can be imported without errors."""
        try:
            from unity_docs_mcp import __version__
            from unity_docs_mcp.server import UnityDocsMCPServer
            from unity_docs_mcp.scraper import UnityDocScraper
            from unity_docs_mcp.parser import UnityDocParser
            from unity_docs_mcp.search_index import UnitySearchIndex

            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Import failed: {e}")
        except IndentationError as e:
            self.fail(f"Indentation error: {e}")
        except SyntaxError as e:
            self.fail(f"Syntax error: {e}")

    def test_scraper_initialization(self):
        """Test that UnityDocScraper can be initialized."""
        from unity_docs_mcp.scraper import UnityDocScraper

        scraper = UnityDocScraper()
        self.assertIsNotNone(scraper)
        self.assertIsNotNone(scraper.session)
        self.assertIsNotNone(scraper.search_index)

    def test_parser_initialization(self):
        """Test that UnityDocParser can be initialized."""
        from unity_docs_mcp.parser import UnityDocParser

        parser = UnityDocParser()
        self.assertIsNotNone(parser)

    def test_search_index_initialization(self):
        """Test that UnitySearchIndex can be initialized."""
        from unity_docs_mcp.search_index import UnitySearchIndex

        index = UnitySearchIndex()
        self.assertIsNotNone(index)
        self.assertEqual(index._loaded, False)

    def test_get_supported_versions(self):
        """Test that get_supported_versions returns a list."""
        from unity_docs_mcp.scraper import UnityDocScraper

        scraper = UnityDocScraper()
        versions = scraper.get_supported_versions()
        self.assertIsInstance(versions, list)
        self.assertGreater(len(versions), 0)
        # Should include at least Unity 6000.0
        self.assertIn("6000.0", versions)

    def test_normalize_version(self):
        """Test version normalization."""
        from unity_docs_mcp.scraper import UnityDocScraper

        scraper = UnityDocScraper()

        # Test various version formats
        self.assertEqual(scraper.normalize_version("6000.0.29f1"), "6000.0")
        self.assertEqual(scraper.normalize_version("2022.3.45f1"), "2022.3")
        self.assertEqual(scraper.normalize_version("2021.3.12a1"), "2021.3")
        self.assertEqual(scraper.normalize_version("6000.0"), "6000.0")

    def test_search_without_crash(self):
        """Test that search can be called without crashing."""
        from unity_docs_mcp.search_index import UnitySearchIndex

        index = UnitySearchIndex()
        # Even without loading, should return empty list, not crash
        results = index.search("GameObject", "6000.0", max_results=5)
        self.assertIsInstance(results, list)


if __name__ == "__main__":
    unittest.main()
