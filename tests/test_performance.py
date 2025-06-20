"""Performance and stress tests for Unity Docs MCP Server."""

import unittest
from unittest.mock import Mock, patch
import time
import threading
import asyncio
import gc
import psutil
import os

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from unity_docs_mcp.scraper import UnityDocScraper
from unity_docs_mcp.parser import UnityDocParser
from unity_docs_mcp.search_index import UnitySearchIndex
from unity_docs_mcp.server import UnityDocsMCPServer


class TestPerformance(unittest.TestCase):
    """Test performance characteristics of the system."""

    def setUp(self):
        """Set up test fixtures."""
        self.scraper = UnityDocScraper()
        self.parser = UnityDocParser()
        self.process = psutil.Process()

    def test_parse_large_document_performance(self):
        """Test parsing performance with large HTML documents."""
        # Generate large HTML document (5MB)
        large_content = []
        for i in range(1000):
            large_content.append(f"""
            <div class="section">
                <h2>Section {i}</h2>
                <p>This is a paragraph with some content. {'X' * 1000}</p>
                <table>
                    <tr><th>Header 1</th><th>Header 2</th><th>Header 3</th></tr>
                    {"".join(f'<tr><td>Cell {j}-1</td><td>Cell {j}-2</td><td>Cell {j}-3</td></tr>' for j in range(50))}
                </table>
                <pre><code>
                public class Example{i} : MonoBehaviour {{
                    void Start() {{
                        Debug.Log("Hello from section {i}");
                    }}
                }}
                </code></pre>
            </div>
            """)
        
        large_html = f"""
        <html>
        <body>
            <div class="content">
                <h1>Large Document</h1>
                {''.join(large_content)}
            </div>
        </body>
        </html>
        """
        
        # Measure parsing time
        start_time = time.time()
        result = self.parser.parse_api_doc(large_html, "https://example.com")
        parse_time = time.time() - start_time
        
        # Should parse large document in reasonable time
        self.assertLess(parse_time, 5.0)  # Should complete within 5 seconds
        self.assertIn("title", result)
        self.assertIn("content", result)

    def test_search_index_loading_performance(self):
        """Test search index loading performance."""
        search_index = UnitySearchIndex()
        
        # Mock large index data
        with patch("requests.get") as mock_get:
            # Create large mock index (10k entries)
            pages = [[f"Class{i}", f"Class {i} Title"] for i in range(10000)]
            info = [[f"Description for class {i}", i] for i in range(10000)]
            search_index_data = {str(i): [i] for i in range(10000)}
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = f"""
var pages = {pages};
var info = {info};
var common = {{}};
var searchIndex = {search_index_data};
"""
            mock_get.return_value = mock_response
            
            # Measure loading time
            start_time = time.time()
            success = search_index.load_index("6000.0", force_refresh=True)
            load_time = time.time() - start_time
            
            self.assertTrue(success)
            self.assertLess(load_time, 2.0)  # Should load within 2 seconds

    def test_search_performance_with_large_index(self):
        """Test search performance with large index."""
        search_index = UnitySearchIndex()
        
        # Create large mock index in memory
        search_index.pages = [[f"Class{i}", f"Class {i} Title"] for i in range(10000)]
        search_index.page_info = [[f"Description for class {i}", i] for i in range(10000)]
        search_index.search_index = {f"class{i}": [i] for i in range(10000)}
        search_index.common_words = set()
        search_index._loaded = True
        
        # Measure search time
        start_time = time.time()
        results = search_index.search("class500", "6000.0", max_results=20)
        search_time = time.time() - start_time
        
        # Search should be fast even with large index
        self.assertLess(search_time, 0.1)  # Should complete within 100ms
        self.assertGreater(len(results), 0)

    def test_memory_usage_with_multiple_versions(self):
        """Test memory usage when loading multiple version indices."""
        search_index = UnitySearchIndex()
        initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        # Mock loading multiple versions
        versions = ["6000.0", "2023.3", "2022.3", "2021.3", "2020.3"]
        
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = """
var pages = [["GameObject", "GameObject"], ["Transform", "Transform"]];
var info = [["Base class", 0], ["Position", 1]];
var common = {};
var searchIndex = {"gameobject": [0], "transform": [1]};
"""
            mock_get.return_value = mock_response
            
            # Load multiple versions
            for version in versions:
                search_index.load_index(version, force_refresh=True)
        
        # Check memory usage
        final_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB for 5 versions)
        self.assertLess(memory_increase, 100)

    @patch("unity_docs_mcp.scraper.requests.Session.get")
    def test_rate_limiting_performance(self, mock_get):
        """Test rate limiting doesn't significantly impact performance."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html>Content</html>"
        mock_get.return_value = mock_response
        
        # Make multiple sequential requests
        num_requests = 10
        start_time = time.time()
        
        for i in range(num_requests):
            self.scraper._fetch_page(f"https://example.com/page{i}")
        
        total_time = time.time() - start_time
        
        # With 0.5s rate limit, 10 requests should take about 4.5-5 seconds
        # (9 delays of 0.5s each)
        self.assertGreater(total_time, 4.0)
        self.assertLess(total_time, 6.0)

    def test_concurrent_thread_safety(self):
        """Test thread safety with concurrent operations."""
        results = []
        errors = []
        
        def worker(thread_id):
            try:
                # Each thread performs various operations
                scraper = UnityDocScraper()
                
                # Test cache operations
                for i in range(5):
                    cache_key = scraper._get_cache_key(f"Class{thread_id}", f"method{i}")
                    scraper._api_cache[cache_key] = {"test": thread_id}
                
                # Test search suggestions
                suggestions = scraper.suggest_class_names(f"test{thread_id}")
                
                results.append({
                    "thread_id": thread_id,
                    "cache_size": len(scraper._api_cache),
                    "suggestions": len(suggestions)
                })
            except Exception as e:
                errors.append((thread_id, str(e)))
        
        # Create multiple threads
        threads = []
        for i in range(10):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        # Verify no errors occurred
        self.assertEqual(len(errors), 0, f"Thread errors: {errors}")
        
        # Verify all threads completed
        self.assertEqual(len(results), 10)

    def test_cache_performance_improvement(self):
        """Test that caching provides significant performance improvement."""
        with patch("requests.Session.head") as mock_head:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_head.return_value = mock_response
            
            # First call (no cache)
            start_time = time.time()
            self.scraper.check_api_availability_across_versions("TestClass")
            uncached_time = time.time() - start_time
            
            # Second call (cached)
            start_time = time.time()
            self.scraper.check_api_availability_across_versions("TestClass")
            cached_time = time.time() - start_time
            
            # Cached should be at least 10x faster
            self.assertLess(cached_time * 10, uncached_time)

    def test_stress_search_index_operations(self):
        """Stress test search index with many operations."""
        search_index = UnitySearchIndex()
        
        # Create a moderate-sized index
        search_index.pages = [[f"Class{i}", f"Class {i}"] for i in range(1000)]
        search_index.page_info = [[f"Description {i}", i] for i in range(1000)]
        search_index.search_index = {f"class{i}": [i] for i in range(1000)}
        search_index.common_words = set()
        search_index._loaded = True
        
        # Perform many searches
        start_time = time.time()
        for i in range(100):
            results = search_index.search(f"class{i % 10}", "6000.0")
        total_time = time.time() - start_time
        
        # 100 searches should complete quickly
        self.assertLess(total_time, 1.0)

    def test_memory_cleanup(self):
        """Test that memory is properly cleaned up."""
        initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        # Create and destroy many objects
        for _ in range(10):
            scraper = UnityDocScraper()
            parser = UnityDocParser()
            search_index = UnitySearchIndex()
            
            # Do some operations
            scraper._api_cache = {f"key{i}": f"value{i}" for i in range(1000)}
            parser.parse_api_doc("<html><body>Test</body></html>", "test.html")
            
            # Clear references
            del scraper
            del parser
            del search_index
        
        # Force garbage collection
        gc.collect()
        
        # Check memory didn't increase significantly
        final_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Should not leak more than 10MB
        self.assertLess(memory_increase, 10)


class TestAsyncPerformance(unittest.TestCase):
    """Test async performance characteristics."""

    def setUp(self):
        """Set up test fixtures."""
        self.server = UnityDocsMCPServer()

    async def test_concurrent_request_performance(self):
        """Test performance of concurrent async requests."""
        with patch("unity_docs_mcp.scraper.UnityDocScraper._fetch_page") as mock_fetch:
            mock_fetch.return_value = "<html><h1>Test</h1></html>"
            
            # Create many concurrent requests
            num_requests = 20
            tasks = []
            for i in range(num_requests):
                task = self.server._get_unity_api_doc(f"Class{i}", None, "6000.0")
                tasks.append(task)
            
            # Measure concurrent execution time
            start_time = time.time()
            results = await asyncio.gather(*tasks)
            concurrent_time = time.time() - start_time
            
            # Verify all completed
            self.assertEqual(len(results), num_requests)
            
            # Concurrent execution should be faster than sequential
            # With rate limiting, sequential would take ~10s (20 * 0.5s)
            # Concurrent should be significantly faster
            self.assertLess(concurrent_time, 5.0)

    async def test_async_memory_usage(self):
        """Test memory usage with many async operations."""
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        with patch("unity_docs_mcp.scraper.UnityDocScraper._fetch_page") as mock_fetch:
            mock_fetch.return_value = "<html><h1>Test</h1></html>"
            
            # Create many async tasks
            tasks = []
            for i in range(100):
                task = self.server._get_unity_api_doc(f"Class{i}", None, "6000.0")
                tasks.append(task)
            
            # Run all tasks
            await asyncio.gather(*tasks)
        
        # Check memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Should not use excessive memory
        self.assertLess(memory_increase, 50)


# Helper to run async tests
def run_async_test(test_func):
    """Helper to run async test functions."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(test_func())
    finally:
        loop.close()


# Wrap async test methods
for test_class in [TestAsyncPerformance]:
    for attr_name in dir(test_class):
        attr = getattr(test_class, attr_name)
        if callable(attr) and attr_name.startswith("test_") and asyncio.iscoroutinefunction(attr):
            def make_wrapper(async_func):
                def wrapper(self):
                    return run_async_test(lambda: async_func(self))
                return wrapper
            
            setattr(test_class, attr_name, make_wrapper(attr))


if __name__ == "__main__":
    unittest.main()