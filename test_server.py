#!/usr/bin/env python3
"""Simple test script for Unity Docs MCP Server."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from unity_docs_mcp.scraper import UnityDocScraper
from unity_docs_mcp.parser import UnityDocParser

def test_scraper():
    """Test the scraper functionality."""
    print("🔍 Testing Unity Doc Scraper...")
    
    scraper = UnityDocScraper()
    
    # Test supported versions
    print(f"✅ Supported versions: {scraper.get_supported_versions()}")
    
    # Test class suggestions
    suggestions = scraper.suggest_class_names("game")
    print(f"✅ Class suggestions for 'game': {suggestions}")
    
    # Test API doc fetch
    print("🌐 Testing API doc fetch for GameObject...")
    result = scraper.get_api_doc("GameObject", version="6000.0")
    
    if result.get("status") == "success":
        print(f"✅ Successfully fetched GameObject doc")
        print(f"   URL: {result['url']}")
        print(f"   HTML length: {len(result['html'])} chars")
        
        # Test parser
        print("📄 Testing HTML parser...")
        parser = UnityDocParser()
        parsed = parser.parse_api_doc(result["html"], result["url"])
        
        if "error" not in parsed:
            print(f"✅ Successfully parsed documentation")
            print(f"   Title: {parsed['title']}")
            print(f"   Content length: {len(parsed['content'])} chars")
            print(f"   First 200 chars: {parsed['content'][:200]}...")
        else:
            print(f"❌ Parser error: {parsed['error']}")
    else:
        print(f"❌ Scraper error: {result.get('error')}")
    
    # Test search
    print("🔍 Testing search functionality...")
    search_result = scraper.search_docs("transform", version="6000.0")
    
    if search_result.get("status") == "success":
        print(f"✅ Successfully performed search")
        print(f"   URL: {search_result['url']}")
        print(f"   HTML length: {len(search_result['html'])} chars")
    else:
        print(f"❌ Search error: {search_result.get('error')}")

if __name__ == "__main__":
    test_scraper()