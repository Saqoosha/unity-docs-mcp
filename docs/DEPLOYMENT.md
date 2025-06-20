# Unity Docs MCP Server - Deployment Guide

## For End Users

### Quick Installation with uv

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Configure Claude Desktop
# Add to ~/Library/Application Support/Claude/claude_desktop_config.json (macOS)
# or %APPDATA%/Claude/claude_desktop_config.json (Windows)
{
  "mcpServers": {
    "unity-docs": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/saqoosha/unity-docs-mcp", "unity-docs-mcp"]
    }
  }
}
```

## For Developers

### Local Development Setup

1. **Clone and Setup**
```bash
git clone https://github.com/saqoosha/unity-docs-mcp
cd unity-docs-mcp
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

2. **Configure Claude Desktop**
```json
{
  "mcpServers": {
    "unity-docs": {
      "command": "/absolute/path/to/unity-docs-mcp/venv/bin/unity-docs-mcp"
    }
  }
}
```

**Important:** Use the full absolute path to avoid Python module errors.

### Common Issues

**"ModuleNotFoundError: No module named 'mcp'"**
- Solution: Use the full path to the virtual environment's executable
- Wrong: `"command": "python", "args": ["src/unity_docs_mcp/server.py"]`
- Right: `"command": "/path/to/venv/bin/unity-docs-mcp"`

**Stack traces on Ctrl+C**
- Fixed in v0.2.1+ with graceful shutdown handling
- Shows: `🛑 Shutting down Unity Docs MCP Server...`

## Publishing to PyPI (Maintainers)

```bash
# Update version in pyproject.toml and __init__.py
# Build and upload
pip install build twine
python -m build
python -m twine upload dist/*
```

After publishing, users can install with:
```bash
uvx unity-docs-mcp
# or
pip install unity-docs-mcp
```