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
                                "description": "Unity version (optional - defaults to latest available version if not specified)"
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
                                "description": "Unity version (optional - defaults to latest available version if not specified)"
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
                    arguments.get("version")
                )
            
            elif name == "search_unity_docs":
                return await self._search_unity_docs(
                    arguments.get("query"),
                    arguments.get("version")
                )
            
            elif name == "list_unity_versions":
                return await self._list_unity_versions()
            
            elif name == "suggest_unity_classes":
                return await self._suggest_unity_classes(
                    arguments.get("partial_name")
                )
            
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    async def _get_unity_api_doc(self, class_name: str, method_name: str = None, version: str = None) -> list[TextContent]:
        """Get Unity API documentation for the specified version only."""
        if not class_name:
            return [TextContent(type="text", text="Error: class_name is required")]
        
        # If no version specified, get latest dynamically
        if version is None:
            version = self.scraper.get_latest_version()
        
        # Store original version for display purposes
        original_version = version
        
        # Validate version (this will automatically normalize it)
        if not self.scraper.validate_version(version):
            normalized = self.scraper.normalize_version(version)
            if normalized != version:
                return [TextContent(type="text", text=f"Error: Unsupported Unity version '{version}' (normalized to '{normalized}'). Supported versions: {', '.join(self.scraper.get_supported_versions())}")]
            else:
                return [TextContent(type="text", text=f"Error: Unsupported Unity version '{version}'. Supported versions: {', '.join(self.scraper.get_supported_versions())}")]
        
        # Normalize version for API calls
        version = self.scraper.normalize_version(version)
        
        # Try to detect member type using search index if available
        member_type = None
        if method_name and hasattr(self.scraper, 'search_index'):
            query = f"{class_name} {method_name}"
            search_results = self.scraper.search_docs(query, version)
            
            if search_results.get("status") == "success" and search_results.get("results"):
                # Look for exact match to get type info
                for result in search_results["results"]:
                    if (result.get("title") == f"{class_name}.{method_name}" or 
                        result.get("title") == f"{class_name}-{method_name}"):
                        member_type = result.get("type")
                        break
        
        # Fetch the documentation for the exact version requested
        result = self.scraper.get_api_doc(class_name, method_name, version, member_type=member_type)
        
        # If error, check availability across versions and provide helpful info
        if result.get("status") == "error":
            if method_name:
                base_error = f"'{class_name}.{method_name}' not found in Unity {version} documentation."
            else:
                base_error = f"'{class_name}' not found in Unity {version} documentation."
            
            # Check availability across other versions
            try:
                version_info = self.scraper.check_api_availability_across_versions(class_name, method_name)
                
                if version_info["available"]:
                    error_msg = f"{base_error}\n\n**Available in versions:** {', '.join(version_info['available'])}"
                    if version_info["unavailable"]:
                        error_msg += f"\n**Not available in:** {', '.join(version_info['unavailable'])}"
                else:
                    error_msg = f"{base_error}\n\nThis API was not found in any tested Unity versions."
                    
            except Exception:
                # Fallback to basic error if version checking fails
                error_msg = base_error
            
            return [TextContent(type="text", text=error_msg)]
        
        # Parse the HTML content
        parsed_result = self.parser.parse_api_doc(result["html"], result["url"])
        
        if "error" in parsed_result:
            return [TextContent(type="text", text=f"Error parsing documentation: {parsed_result['error']}")]
        
        # Format the response
        content = f"# {parsed_result['title']}\n\n"
        
        # Show version info (including normalization if different)
        if original_version != version:
            content += f"**Unity Version:** {version} (normalized from {original_version})\n"
        else:
            content += f"**Unity Version:** {version}\n"
            
        content += f"**Source:** {parsed_result['url']}\n\n"
        content += parsed_result['content']
        
        return [TextContent(type="text", text=content)]
    
    async def _search_unity_docs(self, query: str, version: str = None) -> list[TextContent]:
        """Search Unity documentation."""
        if not query:
            return [TextContent(type="text", text="Error: query is required")]
        
        # If no version specified, get latest dynamically
        if version is None:
            version = self.scraper.get_latest_version()
        
        # Store original version for display purposes
        original_version = version
        
        if not self.scraper.validate_version(version):
            normalized = self.scraper.normalize_version(version)
            if normalized != version:
                return [TextContent(type="text", text=f"Error: Unsupported Unity version '{version}' (normalized to '{normalized}'). Supported versions: {', '.join(self.scraper.get_supported_versions())}")]
            else:
                return [TextContent(type="text", text=f"Error: Unsupported Unity version '{version}'. Supported versions: {', '.join(self.scraper.get_supported_versions())}")]
        
        # Normalize version for API calls
        version = self.scraper.normalize_version(version)
        
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
        
        # Show version info (including normalization if different)
        if original_version != version:
            content += f"**Version:** {version} (normalized from {original_version})\n"
        else:
            content += f"**Version:** {version}\n"
            
        content += f"**Results:** {result.get('count', len(search_results))} found\n\n"
        content += "💡 **Tip:** For detailed documentation with our advanced caching, use `get_unity_api_doc` with the exact class name from results below.\n\n"
        
        for i, res in enumerate(search_results[:10], 1):  # Show top 10 results
            content += f"## {i}. {res['title']}\n"
            if res.get("type"):
                content += f"**Type:** {res['type']}\n"
            
            # Extract class name for get_unity_api_doc suggestion
            title = res.get('title', '')
            if res.get("type") == "class" and '.' in title:
                content += f"**📋 Use:** `get_unity_api_doc(class_name: \"{title}\", version: \"{version}\")`\n"
            
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
    # Print startup info to stderr (stdout is reserved for MCP protocol)
    import sys
    from . import __version__
    
    # Get actual supported Unity versions
    scraper = UnityDocScraper()
    supported_versions = scraper.get_supported_versions()
    version_range = f"{supported_versions[-1]} - {supported_versions[0]}" if supported_versions else "Unknown"
    
    print(f"🚀 Unity Docs MCP Server v{__version__}", file=sys.stderr)
    print(f"📚 Supporting Unity versions {version_range}", file=sys.stderr)
    print("💾 Advanced caching enabled (6h API + 24h search index)", file=sys.stderr)
    print("🔌 Starting MCP server...", file=sys.stderr)
    print("", file=sys.stderr)  # Empty line
    
    server = UnityDocsMCPServer()
    await server.run()


def cli_main():
    """CLI entry point for setuptools."""
    asyncio.run(main())


if __name__ == "__main__":
    cli_main()