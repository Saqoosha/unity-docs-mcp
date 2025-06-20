# Unity Docs MCP Server

Provides Unity documentation access directly in Claude.

**⚠️ Disclaimer**: This is an unofficial community project. Unity Technologies Corp. is not affiliated with and does not endorse or support this project.

[日本語版 README](README_ja.md)

## Installation

### Claude Code
```bash
claude mcp add unity-docs -s user -- uvx --from git+https://github.com/Saqoosha/unity-docs-mcp unity-docs-mcp
```

### Claude Desktop
Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "unity-docs": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/Saqoosha/unity-docs-mcp", "unity-docs-mcp"]
    }
  }
}
```

## Usage

Ask Claude about Unity APIs:
- "Tell me about GameObject"
- "How do I use NavMeshAgent?"
- "Search for transform methods"

## Features

- 🔍 Fast local search
- 📖 Full API documentation
- 🎯 Version-specific docs (2019.1 - 6000.2)
- 💾 Smart caching (6h API + 24h search)
- ✅ 88 tests

## Development

```bash
git clone https://github.com/Saqoosha/unity-docs-mcp
cd unity-docs-mcp
python -m venv venv
source venv/bin/activate
pip install -e .
```

## Documentation

For detailed documentation, see the [docs](docs/) directory.

## License

MIT