"""Unity Docs MCP Server - Main server implementation."""

import sys
import asyncio
from typing import Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

try:
    from .scraper import UnityDocScraper
    from .parser import UnityDocParser
except ImportError:
    # Handle direct execution
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from unity_docs_mcp.scraper import UnityDocScraper
    from unity_docs_mcp.parser import UnityDocParser


class UnityDocsMCPServer:
    """MCP Server for Unity documentation."""
    
    def __init__(self):
        self.server = Server("unity-docs-mcp")
        self.scraper = UnityDocScraper()
        self.parser = UnityDocParser()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup MCP server handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="get_unity_api_doc",
                    description="Get Unity API documentation for a specific class or method",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "class_name": {
                                "type": "string",
                                "description": "Unity class name (e.g., 'GameObject', 'Transform')"
                            },
                            "method_name": {
                                "type": "string",
                                "description": "Optional method name (e.g., 'Instantiate', 'SetActive')"
                            },
                            "version": {
                                "type": "string",
                                "description": "Unity version (default: '6000.0')",
                                "default": "6000.0"
                            }
                        },
                        "required": ["class_name"]
                    }
                ),
                Tool(
                    name="search_unity_docs",
                    description="Search Unity documentation",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query (e.g., 'transform', 'rigidbody physics')"
                            },
                            "version": {
                                "type": "string",
                                "description": "Unity version (default: '6000.0')",
                                "default": "6000.0"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="list_unity_versions",
                    description="List supported Unity versions",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="suggest_unity_classes",
                    description="Get suggestions for Unity class names",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "partial_name": {
                                "type": "string",
                                "description": "Partial class name to get suggestions for"
                            }
                        },
                        "required": ["partial_name"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            """Handle tool calls."""
            
            if name == "get_unity_api_doc":
                return await self._get_unity_api_doc(
                    arguments.get("class_name"),
                    arguments.get("method_name"),
                    arguments.get("version", "6000.0")
                )
            
            elif name == "search_unity_docs":
                return await self._search_unity_docs(
                    arguments.get("query"),
                    arguments.get("version", "6000.0")
                )
            
            elif name == "list_unity_versions":
                return await self._list_unity_versions()
            
            elif name == "suggest_unity_classes":
                return await self._suggest_unity_classes(
                    arguments.get("partial_name")
                )
            
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    async def _get_unity_api_doc(self, class_name: str, method_name: str = None, version: str = "6000.0") -> list[TextContent]:
        """Get Unity API documentation."""
        if not class_name:
            return [TextContent(type="text", text="Error: class_name is required")]
        
        if not self.scraper.validate_version(version):
            return [TextContent(type="text", text=f"Error: Unsupported Unity version '{version}'. Supported versions: {', '.join(self.scraper.get_supported_versions())}")]
        
        # Fetch the documentation
        result = self.scraper.get_api_doc(class_name, method_name, version)
        
        if result.get("status") == "error":
            return [TextContent(type="text", text=f"Error: {result.get('error')}")]
        
        # Parse the HTML content
        parsed_result = self.parser.parse_api_doc(result["html"], result["url"])
        
        if "error" in parsed_result:
            return [TextContent(type="text", text=f"Error parsing documentation: {parsed_result['error']}")]
        
        # Format the response
        content = f"# {parsed_result['title']}\n\n"
        content += f"Source: {parsed_result['url']}\n\n"
        content += parsed_result['content']
        
        return [TextContent(type="text", text=content)]
    
    async def _search_unity_docs(self, query: str, version: str = "6000.0") -> list[TextContent]:
        """Search Unity documentation."""
        if not query:
            return [TextContent(type="text", text="Error: query is required")]
        
        if not self.scraper.validate_version(version):
            return [TextContent(type="text", text=f"Error: Unsupported Unity version '{version}'. Supported versions: {', '.join(self.scraper.get_supported_versions())}")]
        
        # Perform the search
        result = self.scraper.search_docs(query, version)
        
        if result.get("status") == "error":
            return [TextContent(type="text", text=f"Error: {result.get('error')}")]
        
        # Get search results directly from scraper
        search_results = result.get("results", [])
        
        if not search_results:
            return [TextContent(type="text", text=f"No results found for query: '{query}'")]
        
        # Format the response
        content = f"# Unity Documentation Search Results\n\n"
        content += f"**Query:** {query}\n"
        content += f"**Version:** {version}\n"
        content += f"**Results:** {result.get('count', len(search_results))} found\n\n"
        
        for i, res in enumerate(search_results[:10], 1):  # Show top 10 results
            content += f"## {i}. {res['title']}\n"
            if res.get("url"):
                content += f"**URL:** {res['url']}\n"
            if res.get("description"):
                content += f"**Description:** {res['description']}\n"
            content += "\n"
        
        return [TextContent(type="text", text=content)]
    
    async def _list_unity_versions(self) -> list[TextContent]:
        """List supported Unity versions."""
        versions = self.scraper.get_supported_versions()
        content = "# Supported Unity Versions\n\n"
        for version in versions:
            content += f"- {version}\n"
        
        return [TextContent(type="text", text=content)]
    
    async def _suggest_unity_classes(self, partial_name: str) -> list[TextContent]:
        """Suggest Unity class names."""
        if not partial_name:
            return [TextContent(type="text", text="Error: partial_name is required")]
        
        suggestions = self.scraper.suggest_class_names(partial_name)
        
        if not suggestions:
            return [TextContent(type="text", text=f"No suggestions found for '{partial_name}'")]
        
        content = f"# Unity Class Suggestions for '{partial_name}'\n\n"
        for suggestion in suggestions:
            content += f"- {suggestion}\n"
        
        return [TextContent(type="text", text=content)]
    
    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """Main entry point."""
    server = UnityDocsMCPServer()
    await server.run()


def cli_main():
    """CLI entry point for setuptools."""
    asyncio.run(main())


if __name__ == "__main__":
    cli_main()