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
# Via entry point (after installation)
unity-docs-mcp

# Direct module execution
python -m unity_docs_mcp.server
```

### Architecture Overview

The project consists of four main modules that process Unity documentation:

1. **server.py** - MCP server implementation providing 4 tools:
   - `list_unity_versions` - Lists supported Unity versions
   - `suggest_unity_classes` - Provides class name suggestions  
   - `get_unity_api_doc` - Fetches API documentation
   - `search_unity_docs` - Searches Unity documentation

2. **scraper.py** - Handles web requests to Unity's documentation site:
   - Implements rate limiting (0.5s between requests)
   - Builds URLs for API docs
   - Validates Unity versions
   - **Uses search_index.py for search instead of web scraping**

3. **parser.py** - Critical HTML processing pipeline:
   - **MUST remove `<a>` tags BEFORE Trafilatura** (prevents bracket issues)
   - Removes Unity UI elements (feedback forms, etc.)
   - Converts to clean Markdown

4. **search_index.py** - Local search index implementation:
   - Downloads and caches Unity's JavaScript search index
   - Implements client-side search logic in Python
   - Provides fast, reliable search without JavaScript execution
   - Caches index files with configurable expiration

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
// Get GameObject documentation
{"class_name": "GameObject", "version": "6000.0"}

// Get specific method
{"class_name": "GameObject", "method_name": "SetActive", "version": "6000.0"}

// Search documentation
{"query": "transform", "version": "6000.0"}

// Get class suggestions
{"partial_name": "game"}
```

### Supported Unity Versions

- 6000.0 (latest)
- 2023.3, 2023.2, 2023.1
- 2022.3
- 2021.3

### Project Structure

```
src/unity_docs_mcp/
├── server.py       # MCP server implementation
├── scraper.py      # Web scraping logic
├── parser.py       # HTML parsing and cleaning
└── search_index.py # Local search index handler
```

### Important Notes

- Always activate virtual environment before development
- MCP Inspector runs on ports 6274 (UI) and 6277 (proxy)
- Update docs after significant changes to remember what was done
- See ARCHITECTURE.md for complete technical details
- See TESTING.md for comprehensive testing guide