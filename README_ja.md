# Unity Docs MCP Server

ClaudeでUnityのドキュメントに直接アクセスできるようにします。

**⚠️ 免責事項**: これは非公式のコミュニティプロジェクトです。Unity Technologiesは本プロジェクトと提携しておらず、支援や承認も行っていません。

[English README](README.md)

## インストール

### Claude Code の場合
```bash
claude mcp add unity-docs -s user -- uvx --from git+https://github.com/Saqoosha/unity-docs-mcp unity-docs-mcp
```

### Claude Desktop の場合
`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) または `%APPDATA%\Claude\claude_desktop_config.json` (Windows) に追加:

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

## 使い方

ClaudeにUnity APIについて質問してください：
- 「GameObjectについて教えて」
- 「NavMeshAgentの使い方は？」
- 「transformメソッドを検索して」

## 機能

- 🔍 高速ローカル検索
- 📖 完全なAPIドキュメント
- 🎯 バージョン別ドキュメント (2019.1 - 6000.2)
- 💾 スマートキャッシュ (API 6時間 + 検索 24時間)
- ✅ 88個のテスト

## 開発

```bash
git clone https://github.com/Saqoosha/unity-docs-mcp
cd unity-docs-mcp
python -m venv venv
source venv/bin/activate
pip install -e .
```

## ドキュメント

詳細なドキュメントは [docs](docs/) ディレクトリを参照してください。

## ライセンス

MIT