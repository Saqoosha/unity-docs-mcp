# Unity Docs MCP Server - Architecture Documentation

## 📋 Project Overview

**Purpose**: Unity公式APIドキュメントをMCP (Model Context Protocol)経由で取得し、クリーンなMarkdown形式で提供するサーバー

**Key Features**:
- Unity APIドキュメントの取得（クラス、メソッド）
- ドキュメント検索機能
- 複数Unityバージョン対応
- クリーンなテキスト出力（UI要素、フォーマット除去）

## 🏗️ Architecture

### Directory Structure
```
unity-docs-mcp/
├── src/unity_docs_mcp/
│   ├── __init__.py
│   ├── server.py          # MCP server main (UnityDocsMCPServer)
│   ├── scraper.py         # Web scraping (UnityDocScraper)
│   ├── parser.py          # HTML parsing & cleaning (UnityDocParser)
│   └── search_index.py    # Local search index (UnitySearchIndex)
├── tests/
│   ├── test_*.py          # Unit tests
│   └── test_search_index.py # Search index tests
├── pyproject.toml         # Dependencies & project config
├── config.json           # MCP Inspector config
├── start_inspector.sh    # Launch script
├── CLAUDE.md            # Project-specific instructions
└── venv/                # Python virtual environment
```

### Core Components

#### 1. **server.py** - MCP Server
```python
class UnityDocsMCPServer:
    # MCP tools:
    - list_unity_versions()      # Supported Unity versions
    - suggest_unity_classes()    # Class name suggestions
    - get_unity_api_doc()       # Get API documentation
    - search_unity_docs()       # Search documentation
```

#### 2. **scraper.py** - Web Scraper
```python
class UnityDocScraper:
    # Fetches HTML from Unity docs
    - get_api_doc(class_name, method_name, version)
    - search_docs(query, version)  # Now uses search_index
    - suggest_class_names(partial)  # Uses search_index
    - URL patterns:
      - Methods: https://docs.unity3d.com/{version}/Documentation/ScriptReference/{Class}.{method}.html
      - Properties: https://docs.unity3d.com/{version}/Documentation/ScriptReference/{Class}-{property}.html
      - Automatic fallback: Tries dot notation first, then hyphen for properties
```

#### 3. **parser.py** - HTML Parser
```python
class UnityDocParser:
    # Critical processing pipeline:
    1. _remove_link_tags()          # Remove <a> tags (CRUCIAL!)
    2. _remove_unity_ui_elements()  # Remove feedback/UI elements
    3. trafilatura.extract()        # Extract main content
    4. _clean_trafilatura_content() # Fix code formatting
    5. _remove_markdown_formatting() # Remove bold, links
```

#### 4. **search_index.py** - Local Search Index
```python
class UnitySearchIndex:
    # Downloads and caches Unity's search index
    - load_index(version, force_refresh)  # Load index from cache or download
    - search(query, version, max_results) # Search using local index
    - suggest_classes(partial_name)       # Suggest class names
    - clear_cache(version)                # Clear cached index
    
    # Cache management:
    - File cache: ~/.unity_docs_mcp/cache/search_index_{version}.pkl
    - Memory cache: For current session
    - Expiration: 24 hours by default
```

## 🔧 Key Dependencies

```toml
dependencies = [
    "mcp>=1.0.0",              # MCP protocol
    "requests>=2.31.0",        # HTTP requests
    "beautifulsoup4>=4.12.0",  # HTML parsing
    "trafilatura>=1.8.0",      # Content extraction
    "lxml>=4.9.0",            # XML/HTML processing
    "markdownify>=0.11.6",    # HTML to Markdown conversion
]
```

## 🐛 Problems & Solutions

### Problem 0: Search Page JavaScript Execution
**症状**: Unity search page returns "Searching Script Reference, please wait." with loading spinner

**原因**: Unity's search page uses JavaScript to dynamically load results from a local index

**解決策**: Download and use Unity's JavaScript search index directly
```python
# Download index.js from Unity docs
# Parse JavaScript variables: pages, info, searchIndex, common
# Implement search logic in Python
# Cache the index for performance
```

### Problem 1: Code Bracket Issues
**症状**: 
```csharp
public class Example :[MonoBehaviour]{ 
    private[GameObject][] cubes = new[GameObject][10];
```

**原因**: HTMLの`<a>`タグがTrafilaturaによって`[text]`形式に変換される

**解決策**: HTMLレベルでリンクタグを事前除去
```python
for link in soup.find_all('a'):
    link.replace_with(link.get_text())
```

### Problem 2: UI Elements in Content
**症状**: "Leave feedback", "Success!", "Submission failed" がAPIドキュメントに混入

**解決策**: 特定のUI要素を除去
```python
feedback_text_patterns = [
    'Leave feedback', 'Suggest a change', 'Success!', 
    'Thank you for helping us improve', 'Submission failed'
]
```

### Problem 3: Bold Formatting
**症状**: `**GameObject[]**` のような太字フォーマット

**解決策**: HTMLの`<strong>`/`<b>`タグとMarkdownの`**`を除去

### Problem 4: Markdown Links
**症状**: `[ComputeBuffer](ComputeBuffer.html)` がパラメータに残る

**解決策**: 正規表現でMarkdownリンクを除去
```python
content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)
```

### Problem 5: Property vs Method URL Patterns
**症状**: `ContactPoint2D.otherRigidbody` returns 404 error

**原因**: Unity uses different URL patterns for properties vs methods
- Methods use dot notation: `GameObject.SetActive.html`
- Properties use hyphen notation: `GameObject-transform.html`

**解決策**: Automatic fallback mechanism
```python
# First try dot notation (for methods)
url = build_api_url(class_name, method_name)  # GameObject.SetActive.html
if not found and method_name:
    # Try hyphen notation (for properties)
    url = build_api_url(class_name, method_name, use_hyphen=True)  # GameObject-transform.html
```

## 🚀 Launch & Test

### Start MCP Inspector
```bash
./start_inspector.sh
# Opens http://localhost:6274
```

### Test Examples
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

### Direct Python Test
```python
source venv/bin/activate
python test_mcp_tools.py
```

## 💡 Critical Insights

1. **Trafilatura's `include_links=False` is not enough**
   - Only removes URL part `(url)`, leaves `[text]`
   - Must remove `<a>` tags at HTML level

2. **Processing Order Matters**
   ```
   HTML → Remove Links → Remove UI → Trafilatura → Clean Code → Remove Formatting
   ```

3. **Unity HTML Structure**
   - Main content: `#content-wrap .content`
   - Code examples contain many inline links
   - Feedback forms embedded throughout

4. **Search Index Structure**
   ```javascript
   var pages = [["ClassName", "Class Title"], ...];
   var info = [["Description", type_id], ...];
   var searchIndex = {"term": [page_indices], ...};
   var common = {"the": 1, "is": 1, ...};  // Words to ignore
   ```

5. **Search Algorithm**
   - Exact match: 5.0 points
   - Prefix match: 3.0 points 
   - Substring match: 1.0 point
   - Common words are ignored
   - Combined terms (no spaces) are also searched

6. **Virtual Environment Required**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # or venv/bin/activate.fish
   pip install -e .
   ```

## 🔍 Debugging Tips

1. **Check inspector.log** for MCP connection issues
2. **Test scraper directly** with `python test_server.py`
3. **Save problematic HTML** with `debug_gameobject.html`
4. **Kill stuck processes**: 
   ```bash
   pkill -f mcp-inspector
   lsof -ti :6274 :6277 | xargs kill -9
   ```

## 📝 Future Improvements

1. Cache Unity docs locally
2. Add more Unity versions
3. Support for Unity Package docs
4. Offline mode
5. Better error messages

## ⚠️ Important Notes

- **Always activate venv** before running
- **MCP Inspector auth disabled** with `DANGEROUSLY_OMIT_AUTH=true`
- **Ports used**: 6274 (web UI), 6277 (proxy)
- **Python 3.8+** required

---

**Remember**: The key to clean output is removing problematic HTML elements BEFORE any markdown conversion! 🎯

## Quick Reference

### File Locations
- **Main server**: `src/unity_docs_mcp/server.py`
- **HTML scraper**: `src/unity_docs_mcp/scraper.py`
- **Parser/cleaner**: `src/unity_docs_mcp/parser.py`
- **Search index**: `src/unity_docs_mcp/search_index.py`
- **Test script**: `test_mcp_tools.py`
- **Inspector script**: `start_inspector.sh`
- **Cache directory**: `~/.unity_docs_mcp/cache/`

### Key Functions
```python
# parser.py - Processing pipeline
_remove_link_tags()           # Must be FIRST!
_remove_unity_ui_elements()   # Remove feedback UI
trafilatura.extract()         # Extract content
_clean_trafilatura_content()  # Fix code formatting
_remove_markdown_formatting() # Remove bold, links
```

### Test URL Examples
- Class: `https://docs.unity3d.com/6000.0/Documentation/ScriptReference/GameObject.html`
- Method: `https://docs.unity3d.com/6000.0/Documentation/ScriptReference/GameObject.SetActive.html`
- Property: `https://docs.unity3d.com/6000.0/Documentation/ScriptReference/GameObject-transform.html`
- Search Index: `https://docs.unity3d.com/6000.0/Documentation/ScriptReference/docdata/index.js`
- ~~Search Page~~: `https://docs.unity3d.com/6000.0/Documentation/ScriptReference/30_search.html?q=transform` (Not used anymore)