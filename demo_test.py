#!/usr/bin/env python3
"""Demo script to test Unity Docs MCP Server functionality."""

import asyncio
import json
from unity_docs_mcp.server import UnityDocsMCPServer


async def demo_unity_docs_mcp():
    """Demonstrate Unity Docs MCP Server capabilities."""
    print("🎮 Unity Docs MCP Server Demo")
    print("=" * 50)
    
    server = UnityDocsMCPServer()
    
    # Demo 1: List supported Unity versions
    print("\n📋 1. Supported Unity Versions:")
    print("-" * 30)
    result = await server._list_unity_versions()
    print(result[0].text)
    
    # Demo 2: Get class suggestions
    print("\n💡 2. Class Suggestions for 'game':")
    print("-" * 35)
    result = await server._suggest_unity_classes("game")
    print(result[0].text)
    
    # Demo 3: More suggestions
    print("\n💡 3. Class Suggestions for 'vector':")
    print("-" * 37)
    result = await server._suggest_unity_classes("vector")
    print(result[0].text)
    
    # Demo 4: Test API doc retrieval (will show error handling)
    print("\n📖 4. API Documentation Test (GameObject):")
    print("-" * 45)
    try:
        result = await server._get_unity_api_doc("GameObject", None, "6000.0")
        if "Error" in result[0].text:
            print("⚠️  Network request not made (expected in offline demo)")
            print("   This would fetch real Unity documentation online")
        else:
            print(result[0].text[:200] + "...")
    except Exception as e:
        print(f"⚠️  Expected error: {e}")
    
    # Demo 5: Test search functionality
    print("\n🔍 5. Search Documentation Test:")
    print("-" * 35)
    try:
        result = await server._search_unity_docs("transform", "6000.0")
        if "Error" in result[0].text:
            print("⚠️  Network request not made (expected in offline demo)")
            print("   This would search real Unity documentation online")
        else:
            print(result[0].text[:200] + "...")
    except Exception as e:
        print(f"⚠️  Expected error: {e}")
    
    print("\n✅ Demo completed successfully!")
    print("\n🚀 How to use in production:")
    print("   1. Install: uvx --from git+<repo-url> unity-docs-mcp")
    print("   2. Configure Claude Desktop with the uvx command")
    print("   3. Use MCP Inspector: mcp-inspector src/unity_docs_mcp/server.py")
    print("   4. Ask Claude about Unity APIs!")


if __name__ == "__main__":
    asyncio.run(demo_unity_docs_mcp())