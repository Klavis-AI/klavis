# Google Docs MCP Server - ツール設計ドキュメント

> **設計原則**: すべての操作を本質的な単位に統合し、ツール数を最小化する

## 1. 調査結果サマリー

### 1.1 Google Docs APIの主要機能

#### テキスト操作
| リクエストタイプ | 説明 |
|-----------------|------|
| `insertText` | 指定位置にテキストを挿入 |
| `deleteContentRange` | 指定範囲のコンテンツを削除 |
| `replaceAllText` | テキストの検索・置換 |

#### 装飾（フォーマット）操作
| リクエストタイプ | 説明 |
|-----------------|------|
| `updateTextStyle` | 文字スタイル（太字、斜体、下線など）を適用 |
| `updateParagraphStyle` | 段落スタイル（見出し、配置など）を適用 |
| `createParagraphBullets` | 箇条書きを作成 |
| `deleteParagraphBullets` | 箇条書きを削除 |

### 1.2 利用可能なスタイルプロパティ

#### TextStyle（文字スタイル）
```python
{
    "bold": bool,              # 太字
    "italic": bool,            # 斜体
    "underline": bool,         # 下線
    "strikethrough": bool,     # 取り消し線
    "smallCaps": bool,         # 小型英大文字
    "backgroundColor": {...},  # 背景色
    "foregroundColor": {...},  # 文字色
    "fontSize": {"magnitude": float, "unit": "PT"},  # フォントサイズ
    "weightedFontFamily": {"fontFamily": str},       # フォントファミリー
    "baselineOffset": "NONE|SUPERSCRIPT|SUBSCRIPT",  # 上付き/下付き
    "link": {"url": str}       # ハイパーリンク
}
```

#### ParagraphStyle（段落スタイル）
```python
{
    "namedStyleType": "NORMAL_TEXT|TITLE|SUBTITLE|HEADING_1|...|HEADING_6",
    "alignment": "START|CENTER|END|JUSTIFIED",
    "lineSpacing": float,      # 行間（100 = 1.0）
    "direction": "LEFT_TO_RIGHT|RIGHT_TO_LEFT",
    "spaceAbove": {"magnitude": float, "unit": "PT"},  # 段落前の余白
    "spaceBelow": {"magnitude": float, "unit": "PT"},  # 段落後の余白
    "indentFirstLine": {...},  # 最初の行のインデント
    "indentStart": {...},      # 開始インデント
    "indentEnd": {...}         # 終了インデント
}
```

#### NamedStyleType（見出しスタイル）
| スタイル | 説明 |
|----------|------|
| `NORMAL_TEXT` | 通常のテキスト |
| `TITLE` | ドキュメントタイトル |
| `SUBTITLE` | サブタイトル |
| `HEADING_1` | 見出し1（H1） |
| `HEADING_2` | 見出し2（H2） |
| `HEADING_3` | 見出し3（H3） |
| `HEADING_4` | 見出し4（H4） |
| `HEADING_5` | 見出し5（H5） |
| `HEADING_6` | 見出し6（H6） |

### 1.3 装飾情報の取得について

**結論: 装飾情報はAPI経由で取得可能**

`documents.get()` で取得するドキュメント構造には、各 `TextRun` ごとに `textStyle` と `paragraphStyle` が含まれる。

```json
{
  "paragraph": {
    "elements": [{
      "startIndex": 1,
      "endIndex": 75,
      "textRun": {
        "content": "Example text...",
        "textStyle": {
          "bold": true,
          "foregroundColor": {...}
        }
      }
    }],
    "paragraphStyle": {
      "namedStyleType": "HEADING_1",
      "direction": "LEFT_TO_RIGHT"
    }
  }
}
```

### 1.4 重要な技術的制約

1. **テキスト追加と装飾は別操作**: プレーンテキストを挿入後、装飾を適用する必要がある
2. **batchUpdateでアトミック実行**: 複数の操作を1回のAPI呼び出しで実行可能
3. **インデックスはUTF-16コードユニット**: サロゲートペアは2インデックス消費
4. **後ろから前へ操作**: インデックスの再計算を避けるため、高いインデックスから処理

---

## 2. Anthropicツール設計ベストプラクティス

[Writing Tools for Agents](https://www.anthropic.com/engineering/writing-tools-for-agents) に基づく設計原則:

### 2.1 名前空間と命名
- 関連ツールには共通プレフィックスを使用（例: `google_docs_*`）
- パラメータ名は明確に（`user` ではなく `user_id`）

### 2.2 ツール説明
- 新入社員に説明するように詳細に記述
- 暗黙的なコンテキストを明示的にする
- 専門用語やクエリフォーマットを説明

### 2.3 レスポンス設計
- 低レベルの技術的識別子（UUID、MIMEタイプ）を避ける
- 人間が読める情報を返す（`name`、`url`、`file_type`）
- `response_format` オプションで "concise" と "detailed" を選択可能に

### 2.4 トークン効率
- ページネーション、フィルタリング、トランケーションを実装
- デフォルトの制限値を設定（Claude Codeは25,000トークン）

### 2.5 エラーハンドリング
- 具体的で行動可能なエラーメッセージを返す
- スタックトレースやエラーコードではなく、何をすべきかを伝える

### 2.6 ツール選択戦略
- すべてのAPIエンドポイントをラップしない
- 高インパクトなワークフローに焦点を当てる
- 関連する操作を1つのツールに統合することを検討

---

## 3. ツール設計

### 3.1 設計原則

**統合の原則**: 本質的に同じ操作は1つのツールに統合する

| 操作の本質 | 統合ツール |
|-----------|-----------|
| テキスト編集（挿入/削除/置換） | `edit_text` |
| スタイル適用（文字/段落） | `apply_style` |

**後方互換性の原則**: 既存ツールの名前・パラメータは維持する
- ツール名の変更は禁止
- パラメータの削除は禁止
- パラメータの追加は許可
- 内部実装の改善は許可

---

### 3.2 ツール一覧（8つ）

#### 既存ツール（維持）
| ツール名 | 説明 | 変更内容 |
|---------|------|----------|
| `google_docs_get_document_by_id` | ドキュメント取得 | `response_format` パラメータ追加 |
| `google_docs_get_all_documents` | ドキュメント一覧取得 | 変更なし |
| `google_docs_insert_text_at_end` | 末尾にテキスト挿入 | 変更なし（互換性維持） |
| `google_docs_create_blank_document` | 空ドキュメント作成 | 変更なし |
| `google_docs_create_document_from_text` | テキスト付きドキュメント作成 | 変更なし |

#### 新規ツール
| ツール名 | 説明 |
|---------|------|
| `google_docs_edit_text` | テキスト編集（置換ベース） |
| `google_docs_apply_style` | スタイル適用（文字・段落統合） |
| `google_docs_insert_formatted_text` | マークダウン風テキスト挿入（高レベルAPI） |

---

### 3.3 詳細ツール設計

---

## 3.3.A 既存ツール（維持・拡張）

#### 3.3.1 `google_docs_get_document_by_id`（既存・拡張）

**目的**: ドキュメント内容を取得

**変更内容**: `response_format` パラメータを追加（既存パラメータは維持）

```python
{
    "name": "google_docs_get_document_by_id",
    "description": """Retrieve a Google Docs document by ID.

Response formats:
- 'raw': Full API response with all metadata (default, backward compatible)
- 'plain_text': Text content only, no formatting
- 'markdown': Text with formatting converted to markdown syntax
- 'structured': JSON with text runs and style information, including character indices
""",
    "inputSchema": {
        "type": "object",
        "required": ["document_id"],
        "properties": {
            "document_id": {
                "type": "string",
                "description": "The ID of the Google Docs document to retrieve."
            },
            "response_format": {
                "type": "string",
                "enum": ["raw", "plain_text", "markdown", "structured"],
                "description": "Output format. Default: 'raw' (for backward compatibility)",
                "default": "raw"
            }
        }
    }
}
```

**後方互換性**:
- `response_format` 省略時は従来通り生のAPI応答を返す（`raw`）
- 既存の呼び出しコードは変更不要

**レスポンス例（raw形式 = デフォルト）**:
```python
# 従来通りのGoogle Docs API応答
dict(response)  # 現在の実装と同じ
```

**レスポンス例（markdown形式）**:
```json
{
    "document_id": "1abc...",
    "title": "Meeting Notes",
    "content": "# Meeting Notes\n\n**Important**: This is a _critical_ update.",
    "word_count": 15
}
```

**レスポンス例（structured形式）**:
```json
{
    "document_id": "1abc...",
    "title": "Meeting Notes",
    "elements": [
        {
            "type": "paragraph",
            "start_index": 1,
            "end_index": 15,
            "content": "Meeting Notes",
            "paragraph_style": {"heading_type": "HEADING_1"},
            "text_runs": [
                {"content": "Meeting Notes", "start_index": 1, "end_index": 14, "style": {}}
            ]
        }
    ]
}
```

---

#### 3.3.2 `google_docs_get_all_documents`（既存・維持）

**目的**: ユーザーのDriveからGoogle Docsドキュメント一覧を取得

**変更内容**: なし（現状維持）

```python
{
    "name": "google_docs_get_all_documents",
    "description": "Get all Google Docs documents from the user's Drive.",
    "inputSchema": {
        "type": "object",
        "properties": {}
    }
}
```

---

#### 3.3.3 `google_docs_insert_text_at_end`（既存・維持）

**目的**: ドキュメント末尾にテキストを挿入

**変更内容**: なし（現状維持、互換性のため `edit_text` と併存）

```python
{
    "name": "google_docs_insert_text_at_end",
    "description": "Insert text at the end of a Google Docs document.",
    "inputSchema": {
        "type": "object",
        "required": ["document_id", "text"],
        "properties": {
            "document_id": {
                "type": "string",
                "description": "The ID of the Google Docs document to modify."
            },
            "text": {
                "type": "string",
                "description": "The text content to insert at the end of the document."
            }
        }
    }
}
```

**注記**: より柔軟なテキスト編集には新規の `edit_text` ツールを推奨

---

#### 3.3.4 `google_docs_create_blank_document`（既存・維持）

**目的**: 空のドキュメントを作成

**変更内容**: なし（現状維持）

```python
{
    "name": "google_docs_create_blank_document",
    "description": "Create a new blank Google Docs document with a title.",
    "inputSchema": {
        "type": "object",
        "required": ["title"],
        "properties": {
            "title": {
                "type": "string",
                "description": "The title for the new document."
            }
        }
    }
}
```

---

#### 3.3.5 `google_docs_create_document_from_text`（既存・維持）

**目的**: テキスト内容付きのドキュメントを作成

**変更内容**: なし（現状維持）

```python
{
    "name": "google_docs_create_document_from_text",
    "description": "Create a new Google Docs document with specified text content.",
    "inputSchema": {
        "type": "object",
        "required": ["title", "text_content"],
        "properties": {
            "title": {
                "type": "string",
                "description": "The title for the new document."
            },
            "text_content": {
                "type": "string",
                "description": "The text content to include in the new document."
            }
        }
    }
}
```

---

## 3.3.B 新規ツール

#### 3.3.6 `google_docs_edit_text`（新規）

**目的**: テキストの編集（挿入・削除・置換を統一的に扱う）

**設計思想**:
- **挿入** = `"アンカーテキスト"` → `"アンカーテキスト + 新規テキスト"`
- **削除** = `"削除対象テキスト"` → `""`
- **置換** = `"旧テキスト"` → `"新テキスト"`

すべて「テキスト置換」という単一の操作に帰結する（Claude CodeのEditツールと同じ設計思想）。

```python
{
    "name": "google_docs_edit_text",
    "description": """Edit text in a Google Docs document by replacing old text with new text.

This single operation handles insert, delete, and replace:

- **Insert after anchor**:
  old_text: "# Introduction"
  new_text: "# Introduction\n\nThis is the new paragraph."

- **Delete**:
  old_text: "Remove this sentence."
  new_text: ""

- **Replace**:
  old_text: "old word"
  new_text: "new word"

- **Insert at end**:
  old_text: "" (empty)
  new_text: "Appended text"
  append_to_end: true
""",
    "inputSchema": {
        "type": "object",
        "required": ["document_id", "old_text", "new_text"],
        "properties": {
            "document_id": {
                "type": "string",
                "description": "The ID of the Google Docs document"
            },
            "old_text": {
                "type": "string",
                "description": "The text to find and replace. Use empty string with append_to_end=true to insert at end."
            },
            "new_text": {
                "type": "string",
                "description": "The replacement text. Use empty string to delete."
            },
            "match_case": {
                "type": "boolean",
                "description": "Whether to match case when finding old_text. Default: true",
                "default": true
            },
            "replace_all": {
                "type": "boolean",
                "description": "Replace all occurrences or just the first one. Default: false",
                "default": false
            },
            "append_to_end": {
                "type": "boolean",
                "description": "If true and old_text is empty, append new_text to the end of document. Default: false",
                "default": false
            }
        }
    }
}
```

**レスポンス例**:
```json
{
    "success": true,
    "document_id": "1abc...",
    "replacements_made": 1,
    "message": "Replaced 'old text' with 'new text' at 1 location(s)"
}
```

**エラーハンドリング例**:
```json
{
    "success": false,
    "error": "Text not found: 'old text' does not exist in the document.",
    "hint": "Check for typos or use get_document to view current content."
}
```

---

#### 3.3.7 `google_docs_apply_style`（新規）

**目的**: 指定範囲にスタイルを適用（文字スタイルと段落スタイルを統合）

**設計思想**:
- 文字スタイル（bold, italic等）と段落スタイル（heading, alignment等）は、どちらも「範囲にスタイルを適用する」という本質的に同じ操作
- 1つのツールで両方を扱える

```python
{
    "name": "google_docs_apply_style",
    "description": """Apply formatting styles to a specified range in a Google Docs document.

Supports both character-level styles (bold, italic, etc.) and paragraph-level styles (headings, alignment, etc.).

To find the correct indices, use get_document with response_format='structured'.
""",
    "inputSchema": {
        "type": "object",
        "required": ["document_id", "start_index", "end_index"],
        "properties": {
            "document_id": {
                "type": "string",
                "description": "The ID of the Google Docs document"
            },
            "start_index": {
                "type": "integer",
                "description": "Start position of the range (1-based, inclusive)"
            },
            "end_index": {
                "type": "integer",
                "description": "End position of the range (exclusive)"
            },

            "// Character Styles": "---",
            "bold": {
                "type": "boolean",
                "description": "Apply bold formatting"
            },
            "italic": {
                "type": "boolean",
                "description": "Apply italic formatting"
            },
            "underline": {
                "type": "boolean",
                "description": "Apply underline formatting"
            },
            "strikethrough": {
                "type": "boolean",
                "description": "Apply strikethrough formatting"
            },
            "font_size": {
                "type": "number",
                "description": "Font size in points (e.g., 12, 14, 18)"
            },
            "font_family": {
                "type": "string",
                "description": "Font family name (e.g., 'Arial', 'Times New Roman')"
            },
            "foreground_color": {
                "type": "string",
                "description": "Text color in hex format (e.g., '#FF0000' for red)"
            },
            "background_color": {
                "type": "string",
                "description": "Background/highlight color in hex format"
            },
            "link_url": {
                "type": "string",
                "description": "URL to create a hyperlink"
            },

            "// Paragraph Styles": "---",
            "heading_type": {
                "type": "string",
                "enum": ["NORMAL_TEXT", "TITLE", "SUBTITLE", "HEADING_1", "HEADING_2", "HEADING_3", "HEADING_4", "HEADING_5", "HEADING_6"],
                "description": "Paragraph heading style"
            },
            "alignment": {
                "type": "string",
                "enum": ["START", "CENTER", "END", "JUSTIFIED"],
                "description": "Text alignment"
            },
            "line_spacing": {
                "type": "number",
                "description": "Line spacing (100 = single, 150 = 1.5, 200 = double)"
            },
            "space_above": {
                "type": "number",
                "description": "Space above paragraph in points"
            },
            "space_below": {
                "type": "number",
                "description": "Space below paragraph in points"
            }
        }
    }
}
```

**実装時の注意**:
- 文字スタイルは `updateTextStyle` リクエストで適用
- 段落スタイルは `updateParagraphStyle` リクエストで適用
- 両方指定された場合は、1つの `batchUpdate` で両方を実行

**レスポンス例**:
```json
{
    "success": true,
    "document_id": "1abc...",
    "styled_range": {
        "start_index": 1,
        "end_index": 25
    },
    "applied_styles": ["bold", "heading_type:HEADING_1"],
    "message": "Applied 2 style(s) to range [1, 25)"
}
```

---

#### 3.3.8 `google_docs_insert_formatted_text`（新規）

**目的**: マークダウン風の記法で装飾付きテキストを挿入（高レベルAPI）

**設計思想**:
- LLMはマークダウン形式のテキストを生成しやすい
- 「テキスト挿入 + スタイル適用」を1回の呼び出しで完結
- 低レベルAPI（`edit_text` + `apply_style`）の組み合わせを内部で実行

```python
{
    "name": "google_docs_insert_formatted_text",
    "description": """Insert formatted text into a Google Docs document using markdown-like syntax.

Supported markup:
- **bold** or __bold__ for bold text
- *italic* or _italic_ for italic text
- ~~strikethrough~~ for strikethrough
- [link text](url) for hyperlinks
- # Heading 1, ## Heading 2, ... ###### Heading 6 (must be at line start)
- - item or * item for bullet points

Example:
'''
# Meeting Notes

**Important**: This is a _critical_ update.

## Action Items
- Review the ~~old~~ new proposal
- Contact [John](mailto:john@example.com)
'''

This is a high-level API that internally:
1. Parses the markdown syntax
2. Inserts plain text using insertText
3. Applies styles using updateTextStyle/updateParagraphStyle
4. Executes all as a single atomic batchUpdate
""",
    "inputSchema": {
        "type": "object",
        "required": ["document_id", "formatted_text"],
        "properties": {
            "document_id": {
                "type": "string",
                "description": "The ID of the Google Docs document"
            },
            "formatted_text": {
                "type": "string",
                "description": "Text with markdown-like syntax for formatting"
            },
            "position": {
                "type": "string",
                "enum": ["end", "beginning"],
                "description": "Where to insert the text. Default: 'end'",
                "default": "end"
            }
        }
    }
}
```

**レスポンス例**:
```json
{
    "success": true,
    "document_id": "1abc...",
    "inserted_range": {
        "start_index": 50,
        "end_index": 150
    },
    "styles_applied": {
        "headings": 2,
        "bold_ranges": 1,
        "italic_ranges": 1,
        "links": 1,
        "bullet_items": 2
    },
    "message": "Inserted 100 characters with formatting at end of document"
}
```

---

### 3.4 ツール間の関係

```
┌─────────────────────────────────────────────────────────────────┐
│                        読み取り系                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  google_docs_get_all_documents     →  一覧取得           │   │
│  │  google_docs_get_document_by_id    →  内容取得（拡張済） │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        作成系                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  google_docs_create_blank_document      →  空で作成      │   │
│  │  google_docs_create_document_from_text  →  テキスト付き  │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     高レベル編集API（推奨）                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  google_docs_insert_formatted_text  [新規]              │   │
│  │  - マークダウン風記法で装飾付きテキストを一括挿入         │   │
│  │  - 内部で edit_text + apply_style を実行                │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↓ 内部で使用 / 精密操作用
┌─────────────────────────────────────────────────────────────────┐
│                     低レベル編集API                              │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  google_docs_edit_text   [新規]  →  テキスト置換         │ │
│  │  google_docs_apply_style [新規]  →  スタイル適用         │ │
│  │  google_docs_insert_text_at_end  →  末尾追加（互換維持） │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 3.5 既存ツールと新規ツールの使い分け

| ユースケース | 推奨ツール | 理由 |
|-------------|-----------|------|
| 単純な末尾追加 | `insert_text_at_end` | 既存互換、シンプル |
| 任意位置への挿入・削除・置換 | `edit_text` | 柔軟性が高い |
| 装飾付きテキストの挿入 | `insert_formatted_text` | マークダウン記法で直感的 |
| 既存テキストへの装飾適用 | `apply_style` | インデックス指定で精密 |
| ドキュメント内容の取得（生） | `get_document_by_id` | デフォルトで互換 |
| ドキュメント内容の取得（整形） | `get_document_by_id` + `response_format` | markdown/structured形式 |

---

## 4. 実装時の注意事項

### 4.1 インデックス管理

```python
# 複数の操作を行う場合、後ろから前へ処理
# 例: インデックス10と50に挿入する場合
requests = [
    # 先に50に挿入
    {'insertText': {'location': {'index': 50}, 'text': 'Second'}},
    # 次に10に挿入（50のインデックスはずれない）
    {'insertText': {'location': {'index': 10}, 'text': 'First'}},
]
```

### 4.2 batchUpdateのアトミック性

```python
# すべての操作が成功するか、すべて失敗するか
# 1つでもエラーがあれば変更は適用されない
response = service.documents().batchUpdate(
    documentId=document_id,
    body={'requests': requests}
).execute()
```

### 4.3 エラーハンドリング例

```python
# 良い例
return {
    "success": False,
    "error": "Cannot delete the last newline character. Try selecting a range that ends before the final newline (index < end_of_document).",
    "hint": f"Document ends at index {end_index}. Try end_index={end_index - 1}"
}

# 悪い例
return {"error": "400 Bad Request"}
```

### 4.4 Hex色からRGBへの変換

```python
def hex_to_rgb(hex_color: str) -> dict:
    """Convert hex color to Google Docs RGB format."""
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    return {"red": r, "green": g, "blue": b}
```

---

## 5. 実装計画

### Phase 1: 既存ツールの拡張
1. `get_document_by_id` に `response_format` パラメータを追加
   - デフォルトは `raw`（後方互換性維持）
   - `plain_text`, `markdown`, `structured` 形式のレスポンス生成ロジックを実装

### Phase 2: 新規ツールの追加（低レベルAPI）
2. `edit_text` を実装
   - テキスト検索・置換ロジック
   - `append_to_end` オプション
3. `apply_style` を実装
   - `updateTextStyle` と `updateParagraphStyle` の統合
   - Hex色からRGBへの変換

### Phase 3: 新規ツールの追加（高レベルAPI）
4. `insert_formatted_text` を実装
   - マークダウンパーサーの実装
   - プレーンテキスト抽出 + スタイル範囲の計算
   - `batchUpdate` での一括実行

### 後方互換性の保証
- 既存の5つのツールは名前・パラメータを変更しない
- 既存の呼び出しコードは修正不要で動作する

---

## 6. 参考資料

- [Google Docs API - Format Text](https://developers.google.com/workspace/docs/api/how-tos/format-text)
- [Google Docs API - Insert, delete, and move text](https://developers.google.com/workspace/docs/api/how-tos/move-text)
- [Google Docs API - Document Structure](https://developers.google.com/workspace/docs/api/concepts/structure)
- [Google Docs API - batchUpdate Reference](https://developers.google.com/workspace/docs/api/reference/rest/v1/documents/batchUpdate)
- [Anthropic - Writing Tools for Agents](https://www.anthropic.com/engineering/writing-tools-for-agents)
