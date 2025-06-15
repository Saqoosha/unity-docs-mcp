# Unity Docs MCP Server

A Model Context Protocol (MCP) server that provides Unity documentation retrieval capabilities. This server allows you to fetch Unity API documentation and search Unity docs directly through MCP-compatible clients.

## Features

- 🔍 **Fast Local Search**: Search Unity documentation using a local index - no JavaScript execution needed
- 📖 **API Documentation Retrieval**: Get detailed API documentation for Unity classes and methods  
- 🔄 **Smart Version Handling**: Automatic version normalization and latest version detection
- 🎯 **Version Accuracy**: Strict version-specific results with helpful availability context
- 🚀 **Auto-Latest Detection**: Automatically uses Unity's latest version when none specified
- 🔧 **Full Version Support**: Accepts complete Unity versions like `6000.0.29f1`, `2022.3.45a1`
- 🧠 **Smart Suggestions**: Get class name suggestions based on partial input
- 📝 **Clean Markdown Output**: Formatted markdown with Unity-specific formatting issues resolved
- ⚡ **Rate Limited**: Respectful web scraping with built-in rate limiting
- 💾 **Advanced Caching**: Multi-level caching system with 6-hour API availability cache
- 🧪 **Well Tested**: Comprehensive unit and integration tests (88 total tests)

## Quick Start

### For End Users (Simplest)

If you just want to use the MCP server with Claude Desktop or other MCP clients:

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Run directly with uvx (no installation needed!)
uvx --from git+https://github.com/your-username/unity-docs-mcp unity-docs-mcp
```

### For Claude Desktop Users

Add this to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "unity-docs": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/your-username/unity-docs-mcp", "unity-docs-mcp"]
    }
  }
}
```

**Configuration File Locations:**
- **Windows:** `%APPDATA%/Claude/claude_desktop_config.json`
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

## Installation

### Prerequisites

- Python 3.8 or higher
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- MCP-compatible client (like Claude Desktop)

### Method 1: Install with uvx (Recommended for Users)

```bash
# Install directly from GitHub (replace with actual repository URL)
uvx --from git+https://github.com/your-username/unity-docs-mcp unity-docs-mcp

# Or install from PyPI (when published)
uvx unity-docs-mcp
```

### Method 2: Install with uv (For Development)

```bash
# Clone the repository
git clone <repository-url>
cd unity-docs-mcp

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install runtime dependencies
uv pip install -r requirements.txt

# Install in development mode
uv pip install -e .
```

### Method 3: Install with pip (Traditional)

```bash
# Clone the repository
git clone <repository-url>
cd unity-docs-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Development Setup

```bash
# Install development dependencies
uv pip install -r requirements-dev.txt

# Run tests
python run_tests.py
# or without coverage:
python -m unittest discover tests -v

# Validate project structure
python validate_structure.py
```

## Configuration

### Claude Desktop Configuration

Add the following to your Claude Desktop configuration file:

**Windows:** `%APPDATA%/Claude/claude_desktop_config.json`
**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "unity-docs": {
      "command": "python",
      "args": ["/path/to/unity-docs-mcp/src/unity_docs_mcp/server.py"],
      "env": {}
    }
  }
}
```

### Command Line Usage

You can also run the server directly:

```bash
python src/unity_docs_mcp/server.py
```

## Usage

Once configured, you can use the following tools through your MCP client:

### 1. Get Unity API Documentation

Retrieve documentation for a specific Unity class or method:

```
get_unity_api_doc:
- class_name: "GameObject" (required)
- method_name: "Instantiate" (optional)
- version: "6000.0" (optional, auto-detects latest if not specified)
```

**Examples:**
- Get latest Unity docs: `class_name: "GameObject"` (auto-detects Unity 6.1)
- Get specific method: `class_name: "GameObject", method_name: "Instantiate"`
- Use full version: `class_name: "Transform", version: "2022.3.45f1"` (normalizes to 2022.3)
- Version-specific docs: `class_name: "AsyncGPUReadback", version: "2019.4"` (shows availability info if not found)

### 2. Search Unity Documentation

Search through Unity documentation:

```
search_unity_docs:
- query: "rigidbody physics" (required)
- version: "6000.0" (optional, auto-detects latest if not specified)
```

**Examples:**
- Search latest Unity: `query: "rigidbody physics"` (uses Unity 6.1 automatically)
- Search UI components: `query: "button UI canvas"`
- Search with full version: `query: "transform", version: "2021.3.12a1"` (normalizes to 2021.3)

### 3. List Unity Versions

Get a list of supported Unity versions:

```
list_unity_versions
```

### 4. Suggest Unity Classes

Get suggestions for Unity class names:

```
suggest_unity_classes:
- partial_name: "game" (required)
```

**Examples:**
- `partial_name: "game"` → Returns GameObject, etc.
- `partial_name: "trans"` → Returns Transform, etc.

## Supported Unity Versions

The MCP server supports all major Unity versions with intelligent version handling:

### Version Format Support
- **Latest Auto-Detection**: When no version specified, automatically uses Unity's latest (currently 6.1)
- **Full Version Normalization**: `6000.0.29f1` → `6000.0`, `2022.3.45a1` → `2022.3`
- **All Release Types**: Supports alpha (`a`), beta (`b`), final (`f`), and patch versions

### Supported Version Ranges
Dynamically fetched from Unity's official version info (auto-updated):
- **6000.x** (Unity 6.2 Beta, 6.1, 6.0)
- **2023.x** (2023.2, 2023.1)  
- **2022.x** (2022.3 LTS, 2022.2, 2022.1)
- **2021.x** (2021.3 LTS, 2021.2, 2021.1)
- **2020.x** (2020.3, 2020.2, 2020.1)
- **2019.x** (2019.4)

### Enhanced Error Handling
When an API is not found in the requested version, the server provides:
- **Available Versions**: Lists exactly which versions contain the API
- **Upgrade Guidance**: Specific version recommendations
- **Context Information**: Clear explanation of version compatibility

## Architecture

The server consists of four main components:

### 1. Scraper (`scraper.py`)
- Handles web requests to Unity documentation
- Implements rate limiting to be respectful to Unity's servers
- Validates Unity versions and builds appropriate URLs
- Uses search index for search operations instead of web scraping

### 2. Parser (`parser.py`)
- Converts HTML content to clean markdown
- Removes Unity-specific formatting issues (link brackets, UI elements)
- Handles Unity-specific HTML structures
- Uses Trafilatura for content extraction with custom preprocessing

### 3. Search Index (`search_index.py`)
- Downloads and caches Unity's JavaScript search index
- Implements client-side search logic in Python
- Provides fast, reliable search without JavaScript execution
- Caches index files with configurable expiration (default 24 hours)
- Supports exact matches, prefix matches, and substring matches

### 4. Server (`server.py`)
- Implements the MCP server protocol
- Provides tool definitions and handlers
- Orchestrates scraper, parser, and search index components
- Returns formatted responses to MCP clients

## Development

### Project Structure

```
unity-docs-mcp/
├── src/unity_docs_mcp/
│   ├── __init__.py          # Package initialization
│   ├── server.py            # MCP server implementation
│   ├── scraper.py           # Web scraping utilities
│   ├── parser.py            # HTML parsing and markdown conversion
│   └── search_index.py      # Local search index handler
├── tests/
│   ├── __init__.py
│   ├── test_server.py       # Server component tests
│   ├── test_scraper.py      # Scraper component tests
│   ├── test_parser.py       # Parser component tests
│   ├── test_search_index.py # Search index tests
│   ├── test_scraper_search.py # Scraper search functionality tests
│   └── test_integration.py  # Integration tests
├── requirements.txt         # Runtime dependencies
├── requirements-dev.txt     # Development dependencies
├── pyproject.toml          # Project configuration
├── run_tests.py            # Test runner script
└── README.md               # This file
```

### Running Tests

The project includes comprehensive unit tests (45 total) covering all functionality:

```bash
# Run all tests with coverage
python run_tests.py

# Run specific test modules
python tests/test_scraper.py          # Core scraper functionality (41 tests)
python tests/test_version_features.py # Version handling features (11 tests)

# Run specific test file
python -m unittest tests.test_parser

# Run tests with pytest (if installed)
pytest tests/ --cov=src/unity_docs_mcp --cov-report=html
```

### Test Coverage Areas
- **Version Normalization**: Full Unity version format support
- **Dynamic Version Detection**: Latest Unity version auto-detection
- **Dynamic Version List**: Unity's official version list fetching with fallback
- **API Availability Checking**: Cross-version API existence verification
- **Error Handling**: Comprehensive error scenarios with version context
- **Server Integration**: End-to-end MCP server functionality
- **Mock Network Calls**: All external Unity API calls are mocked for reliability

### Code Quality

The project follows Python best practices:

- **Type hints**: Full type annotation support
- **Documentation**: Comprehensive docstrings
- **Testing**: High test coverage with unit and integration tests
- **Error handling**: Robust error handling throughout
- **Rate limiting**: Respectful web scraping practices

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## Rate Limiting and Ethics

This server implements respectful web scraping practices:

- **Rate limiting**: 0.5 second delay between requests
- **User agent**: Proper user agent identification
- **Error handling**: Graceful handling of server errors
- **Caching**: Intelligent request caching (future enhancement)

Please use this tool responsibly and in accordance with Unity's terms of service.

## Troubleshooting

### Common Issues

1. **"Module not found" errors**
   - Ensure you've installed all dependencies including trafilatura: `pip install -r requirements.txt`
   - Check your Python path includes the src directory

2. **"Unsupported Unity version" errors**
   - Use `list_unity_versions` to see supported versions
   - Version format should be like "6000.0" or "2023.3"

3. **Network timeout errors**
   - Check your internet connection
   - Unity's servers might be temporarily unavailable
   - Try again after a few minutes
   - Search index will be cached after first download

4. **Empty search results**
   - The search index may need to be downloaded first (happens automatically)
   - Try different search terms - the search supports partial matches
   - Common Unity words like "the", "is", "in" are ignored
   - Search is case-insensitive

5. **Search index cache issues**
   - The search index is cached in `~/.unity_docs_mcp/cache/`
   - Cache expires after 24 hours by default
   - Delete cache files to force a fresh download

### Debug Mode

For debugging, you can run the server with additional logging:

```bash
PYTHONPATH=src python -m unity_docs_mcp.server --debug
```

### Testing Connection

To test if the server is working correctly:

```bash
# Test basic functionality
python -c "
import asyncio
from src.unity_docs_mcp.server import UnityDocsMCPServer
server = UnityDocsMCPServer()
result = asyncio.run(server._list_unity_versions())
print(result[0].text)
"
```

### Testing with MCP Inspector

You can test the MCP server functionality using the MCP Inspector tool:

1. **Install MCP Inspector:**
   ```bash
   npm install -g @modelcontextprotocol/inspector
   ```

2. **Test the server:**
   ```bash
   # Run the server and inspect it
   mcp-inspector src/unity_docs_mcp/server.py
   ```

3. **Interactive testing:**
   The MCP Inspector will open a web interface where you can:
   - View available tools and their schemas
   - Test tool calls interactively
   - See real responses from the server
   - Debug any issues with tool implementations

4. **Example test calls:**
   ```json
   {
     "method": "tools/call",
     "params": {
       "name": "list_unity_versions",
       "arguments": {}
     }
   }
   ```
   
   ```json
   {
     "method": "tools/call", 
     "params": {
       "name": "get_unity_api_doc",
       "arguments": {
         "class_name": "GameObject",
         "version": "6000.0"
       }
     }
   }
   ```

The MCP Inspector is particularly useful for:
- Validating tool schemas
- Testing error handling
- Debugging response formats
- Ensuring compatibility with MCP clients

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

### v0.3.0 (Latest) - Smart Version Handling Update
- **Dynamic Latest Version Detection**: Automatically detects and uses Unity's latest version when none specified
- **Dynamic Version List**: Fetches supported Unity versions from Unity's official `UnityVersionsInfo.js`
- **Full Version Normalization**: Supports complete Unity versions like `6000.0.29f1`, `2022.3.45a1` with automatic normalization
- **Enhanced Error Handling**: When API not found, shows exactly which versions have it available
- **Cross-Version API Checking**: Fast HEAD requests to determine API availability across major Unity versions
- **Intelligent Defaults**: No version specified = latest Unity version (currently 6.1)
- **Transparent Version Info**: Shows both original and normalized versions in responses
- **Comprehensive Test Coverage**: Added 15 new unit tests for version handling features (45 total tests)
- **Zero Maintenance**: Both latest version detection and supported version list require no manual updates

### v0.2.1
- Added automatic property/method type detection
- Search results now show type information [property], [method], [class], [constructor]
- Optimized URL construction to use correct format on first try
- Fixed property documentation fetching (e.g., ContactPoint2D.otherRigidbody)
- Reduced HTTP requests by 50% with type-aware URL patterns

### v0.2.0
- Implemented local search index for fast, reliable search
- Added search index caching with configurable expiration
- Fixed Unity documentation formatting issues (brackets, UI elements)
- Improved search with exact, prefix, and substring matching
- Added comprehensive search index tests

### v0.1.0 (Initial Release)
- Basic Unity documentation retrieval
- Search functionality via web scraping
- Support for multiple Unity versions
- Class name suggestions
- Comprehensive test suite
- MCP server implementation

## Support

For issues, questions, or contributions, please [create an issue](link-to-issues) on the project repository.

---

**Note**: This project is not officially affiliated with Unity Technologies. It's a community tool that helps developers access Unity documentation more efficiently.