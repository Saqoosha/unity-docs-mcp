#!/usr/bin/env python3
"""
Local testing script for Unity Docs MCP Server.
This script allows you to interactively test all MCP tools without needing Claude Desktop.
"""

import asyncio
import json
from unity_docs_mcp.server import UnityDocsMCPServer


class LocalMCPTester:
    """Local tester for Unity Docs MCP Server."""
    
    def __init__(self):
        self.server = UnityDocsMCPServer()
    
    async def test_tool(self, tool_name: str, arguments: dict):
        """Test a specific MCP tool."""
        print(f"\n🔧 Testing tool: {tool_name}")
        print(f"📥 Arguments: {json.dumps(arguments, indent=2)}")
        print("-" * 50)
        
        try:
            if tool_name == "list_unity_versions":
                result = await self.server._list_unity_versions()
            elif tool_name == "suggest_unity_classes":
                result = await self.server._suggest_unity_classes(arguments.get("partial_name"))
            elif tool_name == "get_unity_api_doc":
                result = await self.server._get_unity_api_doc(
                    arguments.get("class_name"),
                    arguments.get("method_name"),
                    arguments.get("version", "6000.0")
                )
            elif tool_name == "search_unity_docs":
                result = await self.server._search_unity_docs(
                    arguments.get("query"),
                    arguments.get("version", "6000.0")
                )
            else:
                print(f"❌ Unknown tool: {tool_name}")
                return
            
            print("📤 Result:")
            if result and len(result) > 0:
                content = result[0].text
                # Truncate long content for readability
                if len(content) > 500:
                    print(content[:500] + "\n... (truncated)")
                else:
                    print(content)
            else:
                print("No result returned")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def interactive_test(self):
        """Run interactive test session."""
        print("🎮 Unity Docs MCP Server - Local Interactive Test")
        print("=" * 60)
        
        test_cases = [
            # Test 1: List versions
            {
                "name": "list_unity_versions",
                "args": {},
                "description": "List all supported Unity versions"
            },
            
            # Test 2: Class suggestions
            {
                "name": "suggest_unity_classes", 
                "args": {"partial_name": "transform"},
                "description": "Get class suggestions for 'transform'"
            },
            
            # Test 3: More class suggestions
            {
                "name": "suggest_unity_classes",
                "args": {"partial_name": "physics"},
                "description": "Get class suggestions for 'physics'"
            },
            
            # Test 4: Get API documentation
            {
                "name": "get_unity_api_doc",
                "args": {"class_name": "Transform", "version": "6000.0"},
                "description": "Get Transform class documentation"
            },
            
            # Test 5: Get specific method documentation
            {
                "name": "get_unity_api_doc", 
                "args": {"class_name": "GameObject", "method_name": "Find", "version": "6000.0"},
                "description": "Get GameObject.Find method documentation"
            },
            
            # Test 6: Search documentation
            {
                "name": "search_unity_docs",
                "args": {"query": "rigidbody", "version": "6000.0"},
                "description": "Search for 'rigidbody' in documentation"
            },
            
            # Test 7: Search with multiple terms
            {
                "name": "search_unity_docs",
                "args": {"query": "animation controller", "version": "6000.0"},
                "description": "Search for 'animation controller'"
            },
            
            # Test 8: Error handling - invalid version
            {
                "name": "get_unity_api_doc",
                "args": {"class_name": "GameObject", "version": "invalid"},
                "description": "Test error handling with invalid version"
            },
            
            # Test 9: Error handling - empty query
            {
                "name": "search_unity_docs",
                "args": {"query": "", "version": "6000.0"},
                "description": "Test error handling with empty search query"
            }
        ]
        
        print(f"Running {len(test_cases)} test cases...\n")
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"📝 Test {i}/{len(test_cases)}: {test_case['description']}")
            await self.test_tool(test_case["name"], test_case["args"])
            
            # Pause between tests for readability
            if i < len(test_cases):
                print("\n" + "⏸️  Press Enter to continue to next test...")
                input()
        
        print("\n✅ All tests completed!")
        print("\n🎯 Test Summary:")
        print("- If you see Unity documentation content, the server is working!")
        print("- Network errors are normal if Unity servers are unreachable")
        print("- Error handling tests should show appropriate error messages")


async def quick_test():
    """Run a quick test without user interaction."""
    print("🚀 Unity Docs MCP Server - Quick Test")
    print("=" * 45)
    
    tester = LocalMCPTester()
    
    # Quick functional tests
    tests = [
        ("list_unity_versions", {}),
        ("suggest_unity_classes", {"partial_name": "game"}),
        ("get_unity_api_doc", {"class_name": "GameObject", "version": "6000.0"})
    ]
    
    for tool_name, args in tests:
        await tester.test_tool(tool_name, args)
    
    print("\n✅ Quick test completed!")


def main():
    """Main function with user choice."""
    print("Unity Docs MCP Server - Local Testing")
    print("=" * 40)
    print("Choose test mode:")
    print("1. Quick test (automated)")
    print("2. Interactive test (step by step)")
    print("3. Custom test (manual)")
    
    try:
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            asyncio.run(quick_test())
        elif choice == "2":
            tester = LocalMCPTester()
            asyncio.run(tester.interactive_test())
        elif choice == "3":
            print("\nCustom test mode:")
            print("Available tools: list_unity_versions, suggest_unity_classes, get_unity_api_doc, search_unity_docs")
            
            tool_name = input("Tool name: ").strip()
            print("Arguments (JSON format, or press Enter for empty):")
            args_input = input().strip()
            
            try:
                args = json.loads(args_input) if args_input else {}
            except json.JSONDecodeError:
                args = {}
                print("Invalid JSON, using empty arguments")
            
            tester = LocalMCPTester()
            asyncio.run(tester.test_tool(tool_name, args))
        else:
            print("Invalid choice")
    
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    main()