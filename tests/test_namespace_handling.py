"""Test namespace handling for Unity classes."""

import unittest
from unittest.mock import Mock, patch
from src.unity_docs_mcp.scraper import UnityDocScraper


class TestNamespaceHandling(unittest.TestCase):
    """Test that the scraper correctly handles Unity classes with namespaces."""
    
    def setUp(self):
        self.scraper = UnityDocScraper()
    
    @patch.object(UnityDocScraper, '_fetch_page')
    def test_navmeshagent_without_namespace(self, mock_fetch):
        """Test that NavMeshAgent is found even without AI namespace."""
        # Mock search results
        self.scraper.search_index.search = Mock(return_value=[
            {
                'type': 'class',
                'title': 'NavMeshAgent',
                'url': 'https://docs.unity3d.com/6000.0/Documentation/ScriptReference/AI.NavMeshAgent.html'
            }
        ])
        
        # Mock successful page fetch
        mock_fetch.return_value = "<html>NavMeshAgent content</html>"
        
        # Test
        result = self.scraper.get_api_doc("NavMeshAgent", version="6000.0")
        
        self.assertEqual(result['status'], 'success')
        self.assertIn('AI.NavMeshAgent', result['url'])
    
    @patch.object(UnityDocScraper, '_fetch_page')
    def test_class_with_namespace_provided(self, mock_fetch):
        """Test that classes work when namespace is provided."""
        # Mock successful page fetch
        mock_fetch.return_value = "<html>NavMeshAgent content</html>"
        
        # Test
        result = self.scraper.get_api_doc("AI.NavMeshAgent", version="6000.0")
        
        self.assertEqual(result['status'], 'success')
        self.assertIn('AI.NavMeshAgent', result['url'])
    
    @patch.object(UnityDocScraper, '_fetch_page')
    def test_class_without_namespace_in_unity(self, mock_fetch):
        """Test that classes without namespaces work correctly."""
        # Mock search results
        self.scraper.search_index.search = Mock(return_value=[
            {
                'type': 'class',
                'title': 'GameObject',
                'url': 'https://docs.unity3d.com/6000.0/Documentation/ScriptReference/GameObject.html'
            }
        ])
        
        # Mock successful page fetch
        mock_fetch.return_value = "<html>GameObject content</html>"
        
        # Test
        result = self.scraper.get_api_doc("GameObject", version="6000.0")
        
        self.assertEqual(result['status'], 'success')
        self.assertIn('GameObject.html', result['url'])
    
    @patch.object(UnityDocScraper, '_fetch_page')
    def test_method_with_namespace_resolution(self, mock_fetch):
        """Test that methods work with namespace resolution."""
        # Mock search results
        self.scraper.search_index.search = Mock(return_value=[
            {
                'type': 'class',
                'title': 'NavMeshAgent',
                'url': 'https://docs.unity3d.com/6000.0/Documentation/ScriptReference/AI.NavMeshAgent.html'
            }
        ])
        
        # Mock successful page fetch for property (hyphen notation)
        mock_fetch.return_value = "<html>remainingDistance content</html>"
        
        # Test
        result = self.scraper.get_api_doc("NavMeshAgent", "remainingDistance", version="6000.0")
        
        self.assertEqual(result['status'], 'success')
        # Should try dot notation first, then hyphen notation
        self.assertIn('AI.NavMeshAgent', result['url'])


if __name__ == '__main__':
    unittest.main()