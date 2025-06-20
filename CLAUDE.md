# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Unity Docs MCP Server - Development Guide

### Commands

**Testing & Development**:
```bash
# Start MCP Inspector for interactive testing
./start_inspector.sh

# Run full test suite with coverage
python run_tests.py

# Direct test without Inspector
source venv/bin/activate && python test_mcp_tools.py

# Validate project structure
python validate_structure.py

# Install development dependencies
pip install -e .
```

**Running the Server**:
```bash
# Via entry point (after installation) - shows startup info
unity-docs-mcp
# Output:
# 🚀 Unity Docs MCP Server v0.2.1
# 📚 Supporting Unity versions 2019.1 - 6000.2
# 💾 Advanced caching enabled (6h API + 24h search index)
# 🔌 Starting MCP server...

# IMPORTANT: For Claude Desktop, use the full path to avoid "module not found" errors:
# /path/to/unity-docs-mcp/venv/bin/unity-docs-mcp

# Direct module execution
python -m unity_docs_mcp.server
```

### Architecture Overview

The project consists of four main modules that process Unity documentation:

1. **server.py** - MCP server implementation providing 4 tools:
   - `list_unity_versions` - Lists supported Unity versions
   - `suggest_unity_classes` - Provides class name suggestions  
   - `get_unity_api_doc` - Fetches API documentation for **exact version only**
   - `search_unity_docs` - Searches Unity documentation in specified version

2. **scraper.py** - Handles web requests to Unity's documentation site:
   - Implements rate limiting (0.5s between requests)
   - Builds URLs for API docs
   - Validates Unity versions
   - **Advanced caching system for API availability checks (6-hour cache)**
   - **Uses search_index.py for search instead of web scraping**

3. **parser.py** - Critical HTML processing pipeline:
   - **MUST remove `<a>` tags BEFORE Trafilatura** (prevents bracket issues)
   - Removes Unity UI elements (feedback forms, etc.)
   - Converts to clean Markdown

4. **search_index.py** - Local search index implementation:
   - Downloads and caches Unity's JavaScript search index per version
   - Each version has its own index file and cache (24-hour cache)
   - Implements client-side search logic in Python
   - Provides fast, reliable search without JavaScript execution

### Version-Specific Behavior

**Important**: The MCP server provides intelligent version handling:

#### Version Normalization
- **Automatic normalization**: `6000.0.29f1` → `6000.0`, `2022.3.45f1` → `2022.3`
- **Full version support**: Accepts any Unity version format (alpha, beta, final)
- **Transparent conversion**: Shows original and normalized versions in results

#### Dynamic Latest Version Detection
- **Smart defaults**: When no version specified, automatically uses latest available
- **Unity redirect detection**: Leverages Unity's own version redirection
- **No maintenance required**: Always up-to-date with Unity releases

#### Version Availability Information
- **404 with context**: When API not found, shows which versions have it
- **Cross-version checking**: Fast HEAD requests to determine availability with intelligent caching
- **Helpful suggestions**: "Available in versions: 6000.0, 2022.3" for upgrade decisions
- **Performance optimized**: API availability checks are cached for 6 hours to minimize web requests

#### Strict Version Accuracy
- **No fallback**: Searches only in the exact specified (normalized) version
- **Clear error messages**: Precise information about version availability
- **User control**: Developers get docs for their exact Unity version

### Critical Implementation Details

1. **HTML Link Removal is CRUCIAL** - Must remove `<a>` tags BEFORE Trafilatura
2. **Processing Pipeline Order**: HTML → Remove Links → Remove UI → Trafilatura → Clean
3. **Trafilatura's `include_links=False` is NOT enough** - it leaves `[text]` brackets

### Common Issues & Solutions

- **Brackets in code**: `[GameObject]` → Remove `<a>` tags at HTML level
- **UI elements**: "Leave feedback" → Remove with `_remove_unity_ui_elements()`
- **Bold text**: `**text**` → Remove `<strong>`, `<b>` tags and markdown formatting
- **Markdown links**: `[ComputeBuffer](ComputeBuffer.html)` → Strip with regex
- **Search waiting page**: Unity search page loads dynamically → Use local search index instead

### Testing MCP Tools

Use the MCP Inspector to test tools with these example inputs:

```json
// Get latest Unity documentation (auto-detects latest version)
{"class_name": "GameObject"}

// Get documentation for specific full version (auto-normalizes)
{"class_name": "GameObject", "version": "6000.0.29f1"}

// Get specific method with version normalization
{"class_name": "GameObject", "method_name": "SetActive", "version": "2022.3.45f1"}

// Search in latest version (no version = latest)
{"query": "transform"}

// Search in specific version with normalization
{"query": "rigidbody physics", "version": "2021.3.12a1"}

// Get class suggestions (version independent)
{"partial_name": "game"}

// Test 404 with version availability info
{"class_name": "AsyncGPUReadback", "version": "2019.4"}
```

### Supported Unity Versions

The MCP server dynamically fetches supported Unity versions from Unity's official version info:

#### Dynamic Version Detection
- **Automatic Updates**: Fetches version list from Unity's `UnityVersionsInfo.js`
- **No Manual Maintenance**: Version list updates automatically with Unity releases
- **Intelligent Filtering**: Includes supported + recent versions (2019+), excludes very old versions
- **Robust Fallback**: Uses hardcoded list if Unity's server is unavailable

#### Current Supported Versions
Based on Unity's official data (auto-updated):
- **6000.x** (Unity 6.2 Beta, 6.1, 6.0)
- **2023.x** (2023.2, 2023.1)
- **2022.x** (2022.3 LTS, 2022.2, 2022.1)
- **2021.x** (2021.3 LTS, 2021.2, 2021.1)
- **2020.x** (2020.3, 2020.2, 2020.1)
- **2019.x** (2019.4)

#### Version Support Features

- **Dynamic Latest Detection**: Automatically detects and uses Unity's latest version when no version specified
- **Full Version Normalization**: Supports complete version strings like `6000.0.29f1`, `2022.3.45a1`
- **Format Flexibility**: Accepts any Unity version format (alpha, beta, final, patch versions)
- **Zero Maintenance**: Both latest version detection and supported version list require no code maintenance

### Enhanced Error Handling

The MCP server provides intelligent error handling with version context:

1. **Version Availability Context**: When API not found, shows exactly which versions have it
2. **Cross-Version Checking**: Fast HEAD requests to check API availability across major versions
3. **Upgrade Guidance**: Provides specific version recommendations for missing APIs
4. **Transparent Normalization**: Shows both original and normalized versions in responses
5. **No Silent Failures**: Clear messaging about version compatibility issues

#### Example Error Output
```
'AsyncGPUReadback' not found in Unity 2019.4 documentation.

**Available in versions:** 6000.0, 2022.3, 2021.3
**Not available in:** 2020.3, 2019.4
```

### Project Structure

```
src/unity_docs_mcp/
├── server.py       # MCP server implementation
├── scraper.py      # Web scraping logic with caching
├── parser.py       # HTML parsing and cleaning
└── search_index.py # Local search index handler

tests/
├── test_scraper.py       # Core scraper tests (41 tests)
├── test_search_index.py  # Search functionality tests (15 tests)
├── test_version_features.py # Version handling tests (11 tests)
├── test_parser.py        # HTML parsing tests (9 tests)
├── test_scraper_search.py # Search integration tests (8 tests)
├── test_integration.py   # End-to-end tests (3 tests)
└── test_server.py        # MCP server tests (1 test)
```

### Testing

The project includes comprehensive unit tests covering all version-related functionality:

```bash
# Run all tests
source venv/bin/activate && python -m unittest discover tests/

# Run specific test modules
python tests/test_scraper.py          # Core scraper functionality (41 tests)
python tests/test_version_features.py # Version handling features (11 tests)
python tests/test_search_index.py     # Search index functionality (15 tests)  
python tests/test_parser.py           # HTML parsing functionality (9 tests)
python tests/test_integration.py      # Integration tests (3 tests)

# Run with coverage
python run_tests.py
```

#### Test Coverage

- **Version Normalization**: Full Unity version format support (`6000.0.29f1` → `6000.0`)
- **Dynamic Version Detection**: Latest Unity version auto-detection
- **Dynamic Version List**: Unity's official version list fetching with fallback
- **API Availability Checking**: Cross-version API existence verification with caching
- **Error Handling**: Comprehensive error scenarios with version context
- **Server Integration**: End-to-end MCP server functionality
- **Mock Network Calls**: All external Unity API calls are mocked for reliability
- **Caching Performance**: Validates 6-hour API availability cache functionality

Total: **88 unit tests** ensuring robust functionality across all components.

### Performance & Caching

The MCP server implements a comprehensive caching strategy to minimize web requests:

#### Multi-Level Caching System
- **Search Index Cache**: 24-hour cache for Unity's search index files (per version)
- **API Availability Cache**: 6-hour cache for cross-version API existence checks
- **Memory Cache**: In-process caching for same-session requests
- **File Cache**: Persistent cache stored in user's home directory (`~/.unity_docs_mcp/cache/`)

#### Cache Benefits
- **Dramatic Speed Improvement**: API availability checks go from 3+ seconds to <0.01 seconds
- **Reduced Server Load**: Minimizes requests to Unity's documentation servers
- **Offline Capability**: Previously cached data remains available during network issues
- **Automatic Cleanup**: Cache files expire automatically to stay current

#### Cache Locations
```
~/.unity_docs_mcp/cache/
├── search_index_6000.0.pkl      # Search index for Unity 6000.0
├── search_index_2022.3.pkl      # Search index for Unity 2022.3
└── api_availability_cache.pkl   # API availability results
```

### Startup Information

The server displays helpful information on startup (via stderr, safe for MCP protocol):

```
🚀 Unity Docs MCP Server v0.2.1              # From __init__.py __version__
📚 Supporting Unity versions 2019.1 - 6000.2  # Dynamically fetched from Unity
💾 Advanced caching enabled (6h API + 24h search index)
🔌 Starting MCP server...

# When stopping with Ctrl+C (graceful shutdown):
🛑 Shutting down Unity Docs MCP Server...
```

**Server Features:**
- **Graceful Shutdown**: Handles Ctrl+C (SIGINT) and SIGTERM signals cleanly
- **No Stack Traces**: Signal trapping prevents ugly error output on exit
- **Server Version**: Automatically reads from `src/unity_docs_mcp/__init__.py`
- **Unity Versions**: Dynamically fetched from Unity's official version list
- **No Hardcoding**: All version information updates automatically

### Important Notes

- Always activate virtual environment before development
- MCP Inspector runs on ports 6274 (UI) and 6277 (proxy)  
- Update docs after significant changes to remember what was done
- All new version-related features are fully tested
- Startup messages appear in Claude Desktop logs for debugging
- See ARCHITECTURE.md for complete technical details