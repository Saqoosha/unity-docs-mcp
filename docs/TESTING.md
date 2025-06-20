# Testing Unity Docs MCP Server

This document describes how to test the Unity Docs MCP Server to ensure it's working correctly.

## Prerequisites

Make sure you have installed the server correctly:

```bash
# With uv (recommended)
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
uv pip install -e .

# Verify installation
which unity-docs-mcp
```

## Quick Functionality Test

### 1. Project Structure Validation

```bash
python validate_structure.py
```

**Expected output:**
```
✅ All required files are present!
✅ All Python files have valid syntax!
✅ All files have reasonable sizes!
🎉 Project structure validation passed!
```

### 2. Basic Functionality Demo

```bash
python demo_test.py
```

**Expected output:**
- List of supported Unity versions
- Class suggestions for different queries
- Successful API documentation retrieval
- Working search functionality

## Detailed Testing

### 1. Unit Tests

```bash
# Run all tests with coverage
python run_tests.py

# Run with pytest (recommended)
python -m pytest tests/ -v

# Or run specific test files
python -m pytest tests/test_parser.py -v
python -m pytest tests/test_scraper.py -v
python -m pytest tests/test_server.py -v
python -m pytest tests/test_search_index.py -v
python -m pytest tests/test_scraper_search.py -v

# Run only search-related tests
python -m pytest tests/test_search_index.py tests/test_scraper_search.py -v
```

### 2. MCP Inspector Testing

The MCP Inspector provides a web interface to test the MCP server:

```bash
# Install MCP Inspector
npm install -g @modelcontextprotocol/inspector

# Run the inspector
mcp-inspector src/unity_docs_mcp/server.py
```

**What to test in MCP Inspector:**

1. **List Tools** - Should show 4 available tools:
   - `get_unity_api_doc`
   - `search_unity_docs`
   - `list_unity_versions`
   - `suggest_unity_classes`

2. **Test Tool Calls:**

   ```json
   // List Unity versions
   {
     "method": "tools/call",
     "params": {
       "name": "list_unity_versions",
       "arguments": {}
     }
   }
   ```

   ```json
   // Get API documentation
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

   ```json
   // Search documentation
   {
     "method": "tools/call",
     "params": {
       "name": "search_unity_docs",
       "arguments": {
         "query": "rigidbody physics",
         "version": "6000.0"
       }
     }
   }
   ```

   ```json
   // Get class suggestions
   {
     "method": "tools/call",
     "params": {
       "name": "suggest_unity_classes",
       "arguments": {
         "partial_name": "transform"
       }
     }
   }
   ```

### 3. Command Line Testing

```bash
# Test the CLI entry point
timeout 5s unity-docs-mcp

# Test with uvx (if available)
uvx --from . unity-docs-mcp &
sleep 2
kill %1
```

### 4. Claude Desktop Integration Testing

1. **Add to Claude Desktop config:**

   **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   **Windows:** `%APPDATA%/Claude/claude_desktop_config.json`

   ```json
   {
     "mcpServers": {
       "unity-docs": {
         "command": "uvx",
         "args": ["--from", "/path/to/unity-docs-mcp", "unity-docs-mcp"]
       }
     }
   }
   ```

2. **Test in Claude Desktop:**
   - Ask: "What Unity versions are supported?"
   - Ask: "How do I use GameObject.Instantiate?"
   - Ask: "Search for transform documentation"

## Expected Results

### Successful Test Indicators

✅ **Structure validation passes**
✅ **MCP Inspector shows 4 tools**
✅ **API documentation returns formatted markdown**
✅ **Search returns relevant results quickly (using local index)**
✅ **Class suggestions work for partial names**
✅ **Error handling works gracefully**
✅ **Rate limiting prevents server overload**
✅ **Search index is cached and reused**
✅ **Search works offline after initial index download**

### Example Successful Outputs

**Unity Versions:**
```markdown
# Supported Unity Versions

- 6000.0
- 2023.3
- 2023.2
- 2023.1
- 2022.3
- 2022.2
- 2022.1
- 2021.3
```

**Class Suggestions:**
```markdown
# Unity Class Suggestions for 'game'

- GameObject
```

**API Documentation:**
```markdown
# GameObject

**Source:** https://docs.unity3d.com/6000.0/Documentation/ScriptReference/GameObject.html

Base class for all entities in Unity Scenes...
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure all dependencies are installed
   uv pip install -r requirements.txt
   # Trafilatura is required
   uv pip install trafilatura
   ```

2. **Network Timeouts**
   - Check internet connection
   - Unity servers might be temporarily unavailable
   - Rate limiting is working correctly
   - Search index will be cached after first download

3. **Search Index Issues**
   ```bash
   # Clear search index cache if needed
   rm -rf ~/.unity_docs_mcp/cache/
   # Test will download fresh index
   ```

3. **MCP Inspector Won't Connect**
   ```bash
   # Check if Node.js and npm are installed
   node --version
   npm --version
   
   # Reinstall MCP Inspector
   npm uninstall -g @modelcontextprotocol/inspector
   npm install -g @modelcontextprotocol/inspector
   ```

4. **Claude Desktop Integration Issues**
   - Verify config file path and syntax
   - Check that uvx is installed: `curl -LsSf https://astral.sh/uv/install.sh | sh`
   - Restart Claude Desktop after config changes

### Debug Mode

For detailed debugging, run with debug logging:

```bash
PYTHONPATH=src python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from unity_docs_mcp.server import UnityDocsMCPServer
import asyncio

async def debug_test():
    server = UnityDocsMCPServer()
    result = await server._list_unity_versions()
    print('Debug result:', result)

asyncio.run(debug_test())
"
```

## Performance Testing

### Search Index Performance Test

```bash
python -c "
import time
from unity_docs_mcp.search_index import UnitySearchIndex

# Test search performance
index = UnitySearchIndex()
print('Loading index...')
start = time.time()
if index.load_index('6000.0'):
    load_time = time.time() - start
    print(f'Index loaded in {load_time:.2f}s')
    
    # Test search speed
    queries = ['GameObject', 'transform', 'rigidbody physics', 'ui button']
    for query in queries:
        start = time.time()
        results = index.search(query)
        search_time = time.time() - start
        print(f'Search \"{query}\": {len(results)} results in {search_time:.3f}s')
else:
    print('Failed to load index')
"
```

### Rate Limiting Test

```bash
python -c "
import asyncio
import time
from unity_docs_mcp.scraper import UnityDocScraper

async def rate_test():
    scraper = UnityDocScraper()
    
    start = time.time()
    # Make multiple requests
    for i in range(3):
        result = scraper.get_api_doc('GameObject', None, '6000.0')
        print(f'Request {i+1}: {result.get(\"status\", \"unknown\")}')
    
    elapsed = time.time() - start
    print(f'Total time: {elapsed:.2f}s (should be >1s due to rate limiting)')

asyncio.run(rate_test())
"
```

## Integration Test Checklist

- [ ] Project structure validates successfully
- [ ] All unit tests pass (some minor failures expected)
- [ ] MCP Inspector connects and shows tools
- [ ] Can list Unity versions
- [ ] Can get API documentation
- [ ] Can search documentation using local index
- [ ] Search index downloads and caches correctly
- [ ] Search index cache expires after 24 hours
- [ ] Can get class suggestions from index
- [ ] Error handling works for invalid inputs
- [ ] Rate limiting prevents request flooding
- [ ] Claude Desktop integration works
- [ ] uvx installation works

## Search Index Testing

### Manual Search Index Test

```bash
# Test search index directly
python test_search_final.py

# Expected output:
# - Index loads successfully
# - Search returns relevant results
# - Performance is fast (< 0.1s per search)
```

### Cache Testing

```bash
# Check cache directory
ls -la ~/.unity_docs_mcp/cache/

# Should see files like:
# search_index_6000.0.pkl
# search_index_2023.3.pkl
```

## Next Steps

After successful testing:

1. **Publish to GitHub** with proper repository URL
2. **Update README** with correct installation URLs
3. **Create release** with version tag
4. **Submit to MCP registry** (if available)
5. **Share with Unity community**

The Unity Docs MCP Server is ready for production use! 🚀