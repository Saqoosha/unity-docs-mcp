#!/usr/bin/env python3
"""Test MCP tools directly without Inspector."""

import sys
import os
import asyncio
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from unity_docs_mcp.server import UnityDocsMCPServer

async def test_tools():
    """Test MCP tools."""
    print("🚀 Testing Unity Docs MCP Tools")
    print("=" * 40)
    
    server = UnityDocsMCPServer()
    
    # Test 1: List Unity versions
    print("\n1️⃣ Testing list_unity_versions...")
    result = await server._list_unity_versions()
    content = result[0].text if result else "No result"
    print(content)
    
    # Test 2: Suggest Unity classes
    print("\n2️⃣ Testing suggest_unity_classes...")
    result = await server._suggest_unity_classes("game")
    content = result[0].text if result else "No result"
    print(content)
    
    # Test 3: Get Unity API doc
    print("\n3️⃣ Testing get_unity_api_doc...")
    result = await server._get_unity_api_doc("GameObject", version="6000.0")
    content = result[0].text if result else "No result"
    print(content[:500] + "..." if len(content) > 500 else content)
    
    # Test 4: Search Unity docs
    print("\n4️⃣ Testing search_unity_docs...")
    result = await server._search_unity_docs("transform", version="6000.0")
    content = result[0].text if result else "No result"
    print(content[:500] + "..." if len(content) > 500 else content)
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(test_tools())