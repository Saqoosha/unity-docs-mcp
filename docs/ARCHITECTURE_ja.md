# Unity Docs MCP Server - アーキテクチャドキュメント

## 📋 プロジェクト概要

**目的**: Unity公式APIドキュメントをMCP (Model Context Protocol)経由で取得し、クリーンなMarkdown形式で提供するサーバー

**主な機能**:
- Unity APIドキュメントの取得（クラス、メソッド）
- ドキュメント検索機能
- 複数Unityバージョン対応
- クリーンなテキスト出力（UI要素、フォーマット除去）

## 🏗️ アーキテクチャ

### ディレクトリ構造
```
unity-docs-mcp/
├── src/unity_docs_mcp/
│   ├── __init__.py
│   ├── server.py          # MCPサーバーメイン (UnityDocsMCPServer)
│   ├── scraper.py         # Webスクレイピング (UnityDocScraper)
│   ├── parser.py          # HTML解析&クリーニング (UnityDocParser)
│   └── search_index.py    # ローカル検索インデックス (UnitySearchIndex)
├── tests/
│   ├── test_*.py          # ユニットテスト
│   └── test_search_index.py # 検索インデックステスト
├── pyproject.toml         # 依存関係&プロジェクト設定
├── config.json           # MCP Inspector設定
├── start_inspector.sh    # 起動スクリプト
├── CLAUDE.md            # プロジェクト固有の指示
└── venv/                # Python仮想環境
```

### コアコンポーネント

#### 1. **server.py** - MCPサーバー
```python
class UnityDocsMCPServer:
    # MCPツール:
    - list_unity_versions()      # サポートされているUnityバージョン
    - suggest_unity_classes()    # クラス名提案
    - get_unity_api_doc()       # APIドキュメント取得
    - search_unity_docs()       # ドキュメント検索
```

#### 2. **scraper.py** - Webスクレイパー
```python
class UnityDocScraper:
    # UnityドキュメントからHTMLを取得
    - get_api_doc(class_name, method_name, version)
    - search_docs(query, version)  # 現在はsearch_indexを使用
    - suggest_class_names(partial)  # search_indexを使用
    - URLパターン:
      - メソッド: https://docs.unity3d.com/{version}/Documentation/ScriptReference/{Class}.{method}.html
      - プロパティ: https://docs.unity3d.com/{version}/Documentation/ScriptReference/{Class}-{property}.html
      - 自動フォールバック: まずドット記法を試し、次にプロパティ用のハイフン記法を試す
```

#### 3. **parser.py** - HTMLパーサー
```python
class UnityDocParser:
    # 重要な処理パイプライン:
    1. _remove_link_tags()          # <a>タグを削除（超重要！）
    2. _remove_unity_ui_elements()  # フィードバック/UI要素を削除
    3. trafilatura.extract()        # メインコンテンツを抽出
    4. _clean_trafilatura_content() # コードフォーマットを修正
    5. _remove_markdown_formatting() # 太字、リンクを削除
```

#### 4. **search_index.py** - ローカル検索インデックス
```python
class UnitySearchIndex:
    # Unityの検索インデックスをダウンロードしてキャッシュ
    - load_index(version, force_refresh)  # キャッシュからインデックスを読み込むかダウンロード
    - search(query, version, max_results) # ローカルインデックスを使用して検索
    - suggest_classes(partial_name)       # クラス名を提案
    - clear_cache(version)                # キャッシュされたインデックスをクリア
    
    # キャッシュ管理:
    - ファイルキャッシュ: ~/.unity_docs_mcp/cache/search_index_{version}.pkl
    - メモリキャッシュ: 現在のセッション用
    - 有効期限: デフォルトで24時間
```

## 🔧 主要な依存関係

```toml
dependencies = [
    "mcp>=1.0.0",              # MCPプロトコル
    "requests>=2.31.0",        # HTTPリクエスト
    "beautifulsoup4>=4.12.0",  # HTML解析
    "trafilatura>=1.8.0",      # コンテンツ抽出
    "lxml>=4.9.0",            # XML/HTML処理
    "markdownify>=0.11.6",    # HTMLからMarkdownへの変換
]
```

## 🐛 問題と解決策

### 問題0: 検索ページのJavaScript実行
**症状**: Unity検索ページが「Searching Script Reference, please wait.」とローディングスピナーを返す

**原因**: Unityの検索ページはJavaScriptを使用してローカルインデックスから動的に結果をロードする

**解決策**: UnityのJavaScript検索インデックスを直接ダウンロードして使用
```python
# UnityドキュメントからIndex.jsをダウンロード
# JavaScript変数を解析: pages, info, searchIndex, common
# Pythonで検索ロジックを実装
# パフォーマンスのためインデックスをキャッシュ
```

### 問題1: コードのブラケット問題
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

### 問題2: コンテンツ内のUI要素
**症状**: 「Leave feedback」、「Success!」、「Submission failed」がAPIドキュメントに混入

**解決策**: 特定のUI要素を除去
```python
feedback_text_patterns = [
    'Leave feedback', 'Suggest a change', 'Success!', 
    'Thank you for helping us improve', 'Submission failed'
]
```

### 問題3: 太字フォーマット
**症状**: `**GameObject[]**`のような太字フォーマット

**解決策**: HTMLの`<strong>`/`<b>`タグとMarkdownの`**`を除去

### 問題4: Markdownリンク
**症状**: `[ComputeBuffer](ComputeBuffer.html)`がパラメータに残る

**解決策**: 正規表現でMarkdownリンクを除去
```python
content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)
```

### 問題5: プロパティvsメソッドのURLパターン
**症状**: `ContactPoint2D.otherRigidbody`が404エラーを返す

**原因**: Unityはプロパティとメソッドで異なるURLパターンを使用
- メソッドはドット記法を使用: `GameObject.SetActive.html`
- プロパティはハイフン記法を使用: `GameObject-transform.html`

**解決策**: 自動フォールバック機構
```python
# まずドット記法を試す（メソッド用）
url = build_api_url(class_name, method_name)  # GameObject.SetActive.html
if not found and method_name:
    # ハイフン記法を試す（プロパティ用）
    url = build_api_url(class_name, method_name, use_hyphen=True)  # GameObject-transform.html
```

## 🚀 起動とテスト

### MCP Inspectorの起動
```bash
./start_inspector.sh
# http://localhost:6274 を開く
```

### テスト例
```json
// GameObjectドキュメントを取得
{"class_name": "GameObject", "version": "6000.0"}

// 特定のメソッドを取得
{"class_name": "GameObject", "method_name": "SetActive", "version": "6000.0"}

// ドキュメントを検索
{"query": "transform", "version": "6000.0"}

// クラス提案を取得
{"partial_name": "game"}
```

### 直接Pythonテスト
```python
source venv/bin/activate
python test_mcp_tools.py
```

## 💡 重要な洞察

1. **Trafilaturaの`include_links=False`は不十分**
   - URL部分`(url)`のみを削除し、`[text]`を残す
   - HTMLレベルで`<a>`タグを削除する必要がある

2. **処理順序が重要**
   ```
   HTML → リンク削除 → UI削除 → Trafilatura → コードクリーン → フォーマット削除
   ```

3. **Unity HTML構造**
   - メインコンテンツ: `#content-wrap .content`
   - コード例には多くのインラインリンクが含まれる
   - フィードバックフォームが全体に埋め込まれている

4. **検索インデックス構造**
   ```javascript
   var pages = [["ClassName", "Class Title"], ...];
   var info = [["Description", type_id], ...];
   var searchIndex = {"term": [page_indices], ...};
   var common = {"the": 1, "is": 1, ...};  // 無視する単語
   ```

5. **検索アルゴリズム**
   - 完全一致: 5.0ポイント
   - 前方一致: 3.0ポイント
   - 部分一致: 1.0ポイント
   - 一般的な単語は無視される
   - 結合された用語（スペースなし）も検索される

6. **仮想環境が必要**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # または venv/bin/activate.fish
   pip install -e .
   ```

## 🔍 デバッグのヒント

1. **inspector.log**でMCP接続の問題を確認
2. **スクレイパーを直接テスト**: `python test_server.py`
3. **問題のあるHTMLを保存**: `debug_gameobject.html`
4. **スタックしたプロセスを終了**: 
   ```bash
   pkill -f mcp-inspector
   lsof -ti :6274 :6277 | xargs kill -9
   ```

## 📝 将来の改善点

1. Unityドキュメントをローカルにキャッシュ
2. より多くのUnityバージョンを追加
3. Unity Packageドキュメントのサポート
4. オフラインモード
5. より良いエラーメッセージ

## ⚠️ 重要な注意事項

- **常にvenvをアクティベート**してから実行
- **MCP Inspector認証無効化**: `DANGEROUSLY_OMIT_AUTH=true`
- **使用ポート**: 6274（Web UI）、6277（プロキシ）
- **Python 3.8以上**が必要

---

**覚えておくこと**: クリーンな出力の鍵は、マークダウン変換の前に問題のあるHTML要素を削除することです！🎯

## クイックリファレンス

### ファイルの場所
- **メインサーバー**: `src/unity_docs_mcp/server.py`
- **HTMLスクレイパー**: `src/unity_docs_mcp/scraper.py`
- **パーサー/クリーナー**: `src/unity_docs_mcp/parser.py`
- **検索インデックス**: `src/unity_docs_mcp/search_index.py`
- **テストスクリプト**: `test_mcp_tools.py`
- **Inspectorスクリプト**: `start_inspector.sh`
- **キャッシュディレクトリ**: `~/.unity_docs_mcp/cache/`

### 主要関数
```python
# parser.py - 処理パイプライン
_remove_link_tags()           # 最初でなければならない！
_remove_unity_ui_elements()   # フィードバックUIを削除
trafilatura.extract()         # コンテンツを抽出
_clean_trafilatura_content()  # コードフォーマットを修正
_remove_markdown_formatting() # 太字、リンクを削除
```

### テストURL例
- クラス: `https://docs.unity3d.com/6000.0/Documentation/ScriptReference/GameObject.html`
- メソッド: `https://docs.unity3d.com/6000.0/Documentation/ScriptReference/GameObject.SetActive.html`
- プロパティ: `https://docs.unity3d.com/6000.0/Documentation/ScriptReference/GameObject-transform.html`
- 検索インデックス: `https://docs.unity3d.com/6000.0/Documentation/ScriptReference/docdata/index.js`
- ~~検索ページ~~: `https://docs.unity3d.com/6000.0/Documentation/ScriptReference/30_search.html?q=transform` (もう使用されていません)