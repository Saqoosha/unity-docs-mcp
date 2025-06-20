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

    def test_search_without_crash(self):
        """Test that search can be called without crashing."""
        from unity_docs_mcp.search_index import UnitySearchIndex

        index = UnitySearchIndex()
        # Even without loading, should return empty list, not crash
        results = index.search("GameObject", "6000.0", max_results=5)
        self.assertIsInstance(results, list)


if __name__ == "__main__":
    unittest.main()
