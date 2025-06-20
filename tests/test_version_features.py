"""Tests for version-related features in Unity Docs MCP Server."""

import unittest
from unittest.mock import Mock, patch, AsyncMock
import asyncio

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from unity_docs_mcp.server import UnityDocsMCPServer
from mcp.types import TextContent


class TestVersionFeatures(unittest.TestCase):
    """Test cases for version-related functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.server = UnityDocsMCPServer()

    def test_default_version_detection(self):
        """Test that default version is detected dynamically."""
        with patch.object(self.server.scraper, "get_latest_version") as mock_latest:
            mock_latest.return_value = "6000.1"

            # Test with None version (should trigger latest version detection)
            with patch.object(self.server.scraper, "validate_version") as mock_validate:
                mock_validate.return_value = True
                with patch.object(self.server.scraper, "get_api_doc") as mock_get_api:
                    mock_get_api.return_value = {"status": "error"}
                    with patch.object(
                        self.server.scraper, "check_api_availability_across_versions"
                    ) as mock_check:
                        mock_check.return_value = {"available": [], "unavailable": []}

                        # Run async method
                        async def run_test():
                            result = await self.server._get_unity_api_doc(
                                "GameObject", None, None
                            )
                            return result

                        result = asyncio.run(run_test())

                        # Should have called get_latest_version
                        mock_latest.assert_called_once()

    def test_version_normalization_in_api_doc(self):
        """Test version normalization in API documentation retrieval."""
        with patch.object(self.server.scraper, "validate_version") as mock_validate:
            mock_validate.return_value = True
            with patch.object(
                self.server.scraper, "normalize_version"
            ) as mock_normalize:
                mock_normalize.return_value = "6000.0"
                with patch.object(self.server.scraper, "get_api_doc") as mock_get_api:
                    mock_get_api.return_value = {
                        "status": "success",
                        "html": "<html>Test</html>",
                        "url": "https://example.com",
                    }
                    with patch.object(
                        self.server.parser, "parse_api_doc"
                    ) as mock_parse:
                        mock_parse.return_value = {
                            "title": "GameObject",
                            "content": "Test content",
                            "url": "https://example.com",
                        }

                        async def run_test():
                            result = await self.server._get_unity_api_doc(
                                "GameObject", None, "6000.0.29f1"
                            )
                            return result

                        result = asyncio.run(run_test())

                        # Should show normalized version info
                        content = result[0].text
                        self.assertIn("6000.0 (normalized from 6000.0.29f1)", content)

    def test_version_normalization_in_search(self):
        """Test version normalization in documentation search."""
        with patch.object(self.server.scraper, "validate_version") as mock_validate:
            mock_validate.return_value = True
            with patch.object(
                self.server.scraper, "normalize_version"
            ) as mock_normalize:
                mock_normalize.return_value = "2022.3"
                with patch.object(self.server.scraper, "search_docs") as mock_search:
                    mock_search.return_value = {
                        "status": "success",
                        "results": [
                            {
                                "title": "Transform",
                                "url": "test.html",
                                "description": "Test",
                            }
                        ],
                        "count": 1,
                    }

                    async def run_test():
                        result = await self.server._search_unity_docs(
                            "transform", "2022.3.45f1"
                        )
                        return result

                    result = asyncio.run(run_test())

                    # Should show normalized version info
                    content = result[0].text
                    self.assertIn("2022.3 (normalized from 2022.3.45f1)", content)

    def test_error_with_version_availability_info(self):
        """Test error handling with version availability information."""
        with patch.object(self.server.scraper, "validate_version") as mock_validate:
            mock_validate.return_value = True
            with patch.object(
                self.server.scraper, "normalize_version"
            ) as mock_normalize:
                mock_normalize.return_value = "2019.4"
                with patch.object(self.server.scraper, "get_api_doc") as mock_get_api:
                    mock_get_api.return_value = {"status": "error"}
                    with patch.object(
                        self.server.scraper, "check_api_availability_across_versions"
                    ) as mock_check:
                        mock_check.return_value = {
                            "available": ["6000.0", "2022.3", "2021.3"],
                            "unavailable": ["2020.3", "2019.4"],
                        }

                        async def run_test():
                            result = await self.server._get_unity_api_doc(
                                "AsyncGPUReadback", None, "2019.4"
                            )
                            return result

                        result = asyncio.run(run_test())

                        content = result[0].text
                        self.assertIn("not found in Unity 2019.4", content)
                        self.assertIn(
                            "**Available in versions:** 6000.0, 2022.3, 2021.3", content
                        )
                        self.assertIn("**Not available in:** 2020.3, 2019.4", content)

    def test_unsupported_version_with_normalization_info(self):
        """Test unsupported version error with normalization information."""
        with patch.object(self.server.scraper, "validate_version") as mock_validate:
            mock_validate.return_value = False
            with patch.object(
                self.server.scraper, "normalize_version"
            ) as mock_normalize:
                mock_normalize.return_value = "1.0"
                with patch.object(
                    self.server.scraper, "get_supported_versions"
                ) as mock_supported:
                    mock_supported.return_value = ["6000.0", "2022.3", "2021.3"]

                    async def run_test():
                        result = await self.server._get_unity_api_doc(
                            "GameObject", None, "1.0.5f1"
                        )
                        return result

                    result = asyncio.run(run_test())

                    content = result[0].text
                    self.assertIn(
                        "Unsupported Unity version '1.0.5f1' (normalized to '1.0')",
                        content,
                    )
                    self.assertIn("Supported versions: 6000.0, 2022.3, 2021.3", content)

    def test_api_availability_network_error_fallback(self):
        """Test API availability checking with network error fallback."""
        with patch.object(self.server.scraper, "validate_version") as mock_validate:
            mock_validate.return_value = True
            with patch.object(
                self.server.scraper, "normalize_version"
            ) as mock_normalize:
                mock_normalize.return_value = "6000.0"
                with patch.object(self.server.scraper, "get_api_doc") as mock_get_api:
                    mock_get_api.return_value = {"status": "error"}
                    with patch.object(
                        self.server.scraper, "check_api_availability_across_versions"
                    ) as mock_check:
                        mock_check.side_effect = Exception("Network error")

                        async def run_test():
                            result = await self.server._get_unity_api_doc(
                                "GameObject", None, "6000.0"
                            )
                            return result

                        result = asyncio.run(run_test())

                        content = result[0].text
                        # Should fallback to basic error message
                        self.assertIn("not found in Unity 6000.0", content)
                        self.assertNotIn("Available in versions", content)


class TestDynamicVersionDetection(unittest.TestCase):
    """Test cases for dynamic version detection."""

    def setUp(self):
        """Set up test fixtures."""
        from unity_docs_mcp.scraper import UnityDocScraper

        self.scraper = UnityDocScraper()

    @patch("unity_docs_mcp.scraper.requests.Session.get")
    def test_latest_version_from_url(self, mock_get):
        """Test extracting latest version from redirected URL."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.url = "https://docs.unity3d.com/6000.1/Documentation/ScriptReference/GameObject.html"
        mock_response.text = "Some content"
        mock_get.return_value = mock_response

        result = self.scraper.get_latest_version()
        self.assertEqual(result, "6000.1")

    @patch("unity_docs_mcp.scraper.requests.Session.get")
    def test_latest_version_from_content_format_conversion(self, mock_get):
        """Test extracting and converting version format from content."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.url = "https://docs.unity3d.com/ScriptReference/GameObject.html"
        mock_response.text = "<html><h1>Unity 6.1 Documentation</h1></html>"
        mock_get.return_value = mock_response

        result = self.scraper.get_latest_version()
        self.assertEqual(result, "6000.1")

    @patch("unity_docs_mcp.scraper.requests.Session.get")
    def test_latest_version_standard_format(self, mock_get):
        """Test extracting version that's already in standard format."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.url = "https://docs.unity3d.com/ScriptReference/GameObject.html"
        mock_response.text = "<html><h1>Unity 2022.3 Documentation</h1></html>"
        mock_get.return_value = mock_response

        result = self.scraper.get_latest_version()
        self.assertEqual(result, "2022.3")

    @patch("unity_docs_mcp.scraper.requests.Session.get")
    def test_latest_version_no_match(self, mock_get):
        """Test latest version detection when no version is found."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.url = "https://docs.unity3d.com/ScriptReference/GameObject.html"
        mock_response.text = "<html>No version info</html>"
        mock_get.return_value = mock_response

        result = self.scraper.get_latest_version()
        # Should fallback to first supported version
        expected = self.scraper.get_supported_versions()[0]
        self.assertEqual(result, expected)

    @patch("unity_docs_mcp.scraper.requests.Session.get")
    def test_latest_version_http_error(self, mock_get):
        """Test latest version detection with HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        result = self.scraper.get_latest_version()
        # Should fallback to first supported version
        expected = self.scraper.get_supported_versions()[0]
        self.assertEqual(result, expected)


class TestVersionFormatEdgeCases(unittest.TestCase):
    """Test edge cases for Unity version format handling."""

    def setUp(self):
        """Set up test fixtures."""
        from unity_docs_mcp.scraper import UnityDocScraper

        self.scraper = UnityDocScraper()

    def test_normalize_alpha_versions(self):
        """Test normalization of alpha versions."""
        test_cases = [
            ("6000.0.1a1", "6000.0"),
            ("2023.3.0a12", "2023.3"),
            ("2022.2.15a20", "2022.2"),
        ]

        for input_version, expected in test_cases:
            with self.subTest(version=input_version):
                result = self.scraper.normalize_version(input_version)
                self.assertEqual(result, expected)

    def test_normalize_beta_versions(self):
        """Test normalization of beta versions."""
        test_cases = [
            ("6000.0.1b1", "6000.0"),
            ("2023.3.0b5", "2023.3"),
            ("2022.2.15b12", "2022.2"),
        ]

        for input_version, expected in test_cases:
            with self.subTest(version=input_version):
                result = self.scraper.normalize_version(input_version)
                self.assertEqual(result, expected)

    def test_normalize_release_candidate_versions(self):
        """Test normalization of release candidate versions."""
        test_cases = [
            ("6000.0.1rc1", "6000.0"),
            ("2023.3.0rc2", "2023.3"),
            ("2022.2.15rc3", "2022.2"),
        ]

        for input_version, expected in test_cases:
            with self.subTest(version=input_version):
                result = self.scraper.normalize_version(input_version)
                self.assertEqual(result, expected)

    def test_normalize_patch_versions(self):
        """Test normalization of patch versions."""
        test_cases = [
            ("6000.0.1p1", "6000.0"),
            ("2023.3.5p2", "2023.3"),
            ("2022.2.15p10", "2022.2"),
        ]

        for input_version, expected in test_cases:
            with self.subTest(version=input_version):
                result = self.scraper.normalize_version(input_version)
                self.assertEqual(result, expected)

    def test_normalize_special_characters(self):
        """Test normalization with special characters."""
        test_cases = [
            ("6000.0-alpha", "6000.0"),
            ("2023.3_beta", "2023.3"),
            ("2022.2 LTS", "2022.2"),
            ("2021.3(LTS)", "2021.3"),
            ("Unity 2020.3", "2020.3"),
        ]

        for input_version, expected in test_cases:
            with self.subTest(version=input_version):
                result = self.scraper.normalize_version(input_version)
                self.assertEqual(result, expected)

    def test_normalize_edge_case_formats(self):
        """Test normalization of edge case version formats."""
        test_cases = [
            ("6000", "6000"),  # No minor version
            ("2023", "2023"),  # No minor version
            ("6000.0.0.0", "6000.0"),  # Too many parts
            ("v6000.0", "6000.0"),  # v prefix
            ("6000.0final", "6000.0"),  # suffix without separator
        ]

        for input_version, expected in test_cases:
            with self.subTest(version=input_version):
                result = self.scraper.normalize_version(input_version)
                self.assertEqual(result, expected)

    def test_normalize_invalid_formats(self):
        """Test normalization preserves invalid formats."""
        test_cases = [
            "invalid",
            "abc.def",
            ".",
            "..",
            "2023.",
            ".2023",
            "",
            "   ",
            "!@#$",
        ]

        for version in test_cases:
            with self.subTest(version=version):
                result = self.scraper.normalize_version(version)
                self.assertEqual(result, version)  # Should return as-is

    def test_validate_version_with_edge_cases(self):
        """Test version validation with edge case formats."""
        # These should be valid after normalization (assuming 6000.0 is supported)
        valid_cases = [
            "6000.0.29f1",
            "6000.0.1a1",
            "6000.0.1b2",
            "6000.0.1rc3",
            "6000.0.1p4",
        ]

        for version in valid_cases:
            with self.subTest(version=version):
                # Only test if 6000.0 is in supported versions
                if "6000.0" in self.scraper.get_supported_versions():
                    self.assertTrue(self.scraper.validate_version(version))

    def test_normalize_whitespace_handling(self):
        """Test normalization handles whitespace correctly."""
        test_cases = [
            ("  6000.0  ", "6000.0"),
            ("\t2023.3\t", "2023.3"),
            (" 2022.2.15f1 ", "2022.2"),
            ("6000.0\n", "6000.0"),
            ("2023.3\r\n", "2023.3"),
        ]

        for input_version, expected in test_cases:
            with self.subTest(version=input_version):
                result = self.scraper.normalize_version(input_version)
                self.assertEqual(result, expected)

    def test_normalize_case_sensitivity(self):
        """Test normalization with case variations."""
        test_cases = [
            ("6000.0.29F1", "6000.0"),
            ("2023.3.1A5", "2023.3"),
            ("2022.2.15B10", "2022.2"),
            ("2021.3.5P2", "2021.3"),
            ("2020.3.1RC1", "2020.3"),
        ]

        for input_version, expected in test_cases:
            with self.subTest(version=input_version):
                result = self.scraper.normalize_version(input_version)
                self.assertEqual(result, expected)

    @patch("unity_docs_mcp.scraper.requests.Session.get")
    def test_get_supported_versions_with_mixed_formats(self, mock_get):
        """Test parsing supported versions with mixed formats."""
        mock_response = Mock()
        mock_response.status_code = 200
        # The current parser expects numeric values, not strings
        mock_response.text = """UnityVersionsInfo = {
          supported: [
            { major: 6000, minor: 2, name: "Unity 6.2 Beta", patch: 1, release: "b5" },
            { major: 6000, minor: 1, build: "29f1" },
            { major: 2022, minor: 3, LTS: true, patch: 45 },
          ],
          notSupported: [
            { major: 2023, minor: 2, extra: "data" },
            { major: 2022, minor: 2 },
            { major: 2020, minor: 3 },
          ],
        };"""
        mock_get.return_value = mock_response

        result = self.scraper.get_supported_versions()

        # Should handle all variations correctly
        self.assertIn("6000.2", result)
        self.assertIn("6000.1", result)
        self.assertIn("2022.3", result)
        self.assertIn("2023.2", result)
        self.assertIn("2022.2", result)
        self.assertIn("2020.3", result)

    def test_version_comparison_consistency(self):
        """Test that normalized versions compare consistently."""
        versions = [
            "6000.0.29f1",
            "6000.0.1a1",
            "6000.0.15b3",
            "6000.0",
            "6000.0.5p2",
        ]

        # All should normalize to the same version
        normalized = [self.scraper.normalize_version(v) for v in versions]
        self.assertEqual(len(set(normalized)), 1)  # All should be "6000.0"

    def test_empty_and_none_version_handling(self):
        """Test handling of empty and None version values."""
        # Test empty string
        result = self.scraper.normalize_version("")
        self.assertEqual(result, "")

        # Test None handling - normalize_version now handles None gracefully
        result = self.scraper.normalize_version(None)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
