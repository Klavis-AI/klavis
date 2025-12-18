# search_messages 軽量化・機能追加 実装仕様書

## 概要

`user_search_messages` ツールのレスポンスを軽量化し、トークン消費を削減する。
また、`to_me` パラメーターを追加し、ログインユーザー宛のメッセージを簡単に検索できるようにする。

## 現状の問題点

- `search.messages` API のレスポンスをそのまま返しており、不要なフィールドが多くトークン消費が大きい
- `list_channels` や `list_users` で実装済みの `response_format` パターンが未適用
- 自分宛のメッセージを検索するには、ユーザーが自分のユーザーIDを把握している必要がある

## 調査結果

### search.messages API レスポンス構造

```json
{
  "ok": true,
  "query": "検索クエリ",
  "messages": {
    "total": 123,
    "pagination": {
      "total_count": 123,
      "page": 1,
      "per_page": 20,
      "page_count": 7,
      "first": 1,
      "last": 20
    },
    "paging": {
      "count": 20,
      "total": 123,
      "page": 1,
      "pages": 7
    },
    "matches": [
      {
        "iid": "xxx",
        "team": "T12345678",
        "channel": {
          "id": "C12345678",
          "is_channel": true,
          "is_group": false,
          "is_im": false,
          "is_mpim": false,
          "is_shared": false,
          "is_private": false,
          "is_ext_shared": false,
          "is_org_shared": false,
          "is_pending_ext_shared": false,
          "name": "general",
          "name_normalized": "general"
          // ... 他にも多数のフィールド
        },
        "type": "message",
        "user": "U12345678",
        "username": "john.doe",
        "ts": "1234567890.123456",
        "text": "メッセージ本文",
        "permalink": "https://workspace.slack.com/archives/C12345678/p1234567890123456",
        "blocks": [...],  // リッチテキストブロック
        "attachments": [...],  // 添付ファイル情報
        "no_reactions": true,
        "score": 0.95
        // ... その他多数のフィールド
      }
    ]
  }
}
```

### 利用可能な検索モディファイア

| モディファイア | 説明 | 例 |
|---------------|------|-----|
| `from:@user` | 特定ユーザーからのメッセージ | `from:@john` |
| `to:@user` | 特定ユーザー宛のメッセージ（メンション含む） | `to:@john` |
| `in:#channel` | 特定チャンネル内の検索 | `in:#general` |
| `in:@user` | 特定ユーザーとのDM内の検索 | `in:@john` |
| `before:YYYY-MM-DD` | 指定日より前 | `before:2024-01-01` |
| `after:YYYY-MM-DD` | 指定日より後 | `after:2024-01-01` |
| `on:YYYY-MM-DD` | 指定日当日 | `on:2024-06-15` |
| `during:month` | 指定月中 | `during:january` |
| `has::emoji:` | 特定リアクションを持つメッセージ | `has::thumbsup:` |
| `is:thread` | スレッド内のメッセージ | `is:thread` |
| `with:@user` | 特定ユーザーを含むスレッド/DM | `with:@john` |

### auth.test API

- **必要スコープ**: ユーザートークンの場合は**スコープ不要**
- **レスポンス**:
  ```json
  {
    "ok": true,
    "url": "https://workspace.slack.com/",
    "team": "Workspace Name",
    "user": "username",
    "team_id": "T12345678",
    "user_id": "U12345678"
  }
  ```
- **用途**: ログインユーザーの `user_id` を取得するために使用

## 実装方針

### 1. response_format パラメーターの追加

`list_channels` と同様のパターンで実装する。

- **`concise`（デフォルト）**: 必要最小限のフィールドのみ返す
- **`detailed`**: APIレスポンスをそのまま返す（従来の動作）

#### concise フォーマットで返すフィールド

```python
{
    "ok": True,
    "query": "search query",
    "messages": {
        "total": 123,
        "matches": [
            {
                "channel_id": "C12345678",
                "channel_name": "general",  # None for DMs
                "user_id": "U12345678",
                "username": "john.doe",
                "ts": "1234567890.123456",
                "text": "message body",
                "permalink": "https://workspace.slack.com/archives/...",
                "thread_ts": "1234567890.123456"  # Only for threaded messages
            }
        ]
    },
    "summary": "Found 123 messages, showing 20. Use next_cursor for more results. To get full message details, use slack_get_channel_history with channel_id and latest=ts, inclusive=true, limit=1. For threaded messages, use slack_get_thread_replies.",
    "response_metadata": {
        "next_cursor": "xxx"  # Only if more results available
    }
}
```

**選定理由**:
- `channel_id` / `channel_name`: どこで発言されたかの特定に必須
- `user_id` / `username`: 誰が発言したかの特定に必須
- `ts`: メッセージの時刻特定、返信やリアクション追加時の引数として必須
- `text`: メッセージ内容
- `permalink`: Slackで直接開く際のリンク
- `thread_ts`: スレッドへの返信時に必要

### 2. to_me パラメーターの追加

```python
async def user_search_messages(
    query: str,
    to_me: bool = False,  # 新規追加
    # ... 他のパラメーター
) -> Dict[str, Any]:
```

#### 実装フロー

1. `to_me=True` の場合:
   1. `auth.test` API を呼び出してログインユーザーの `user_id` を取得
   2. 検索クエリに `to:@<user_id>` を追加
   3. `search.messages` API を呼び出す

2. `to_me=False` の場合（デフォルト）:
   - 従来通りの動作

#### auth.test 呼び出しの実装

```python
async def get_current_user_id() -> str:
    """auth.test を呼び出してログインユーザーのuser_idを取得"""
    response = await make_slack_user_request("GET", "auth.test")
    if not response.get("ok"):
        raise Exception("Failed to get current user info")
    return response.get("user_id")
```

### 3. ファイル変更箇所

#### search.py

```python
import logging
from typing import Any, Dict, Optional, List
from .base import make_slack_user_request

logger = logging.getLogger(__name__)


async def get_current_user_id() -> str:
    """Get the user ID of the authenticated user using auth.test."""
    response = await make_slack_user_request("GET", "auth.test")
    if not response.get("ok"):
        raise Exception("Failed to get current user info")
    return response.get("user_id")


def format_message_response(
    match: dict[str, Any],
    response_format: str = "concise",
) -> dict[str, Any]:
    """Format a single message match based on response_format."""
    if response_format == "detailed":
        return match

    channel = match.get("channel", {})

    formatted = {
        "channel_id": channel.get("id"),
        "channel_name": channel.get("name"),  # None for DMs
        "user_id": match.get("user"),
        "username": match.get("username"),
        "ts": match.get("ts"),
        "text": match.get("text"),
        "permalink": match.get("permalink"),
    }

    # Add thread_ts if this is a threaded message
    if match.get("thread_ts"):
        formatted["thread_ts"] = match.get("thread_ts")

    return formatted


def generate_summary(
    total: int,
    returned: int,
    has_more: bool,
    include_hint: bool = True,
) -> str:
    """Generate summary string for the response."""
    parts = [f"Found {total} messages"]

    if total > returned:
        parts.append(f"showing {returned}")

    summary = ", ".join(parts) + "."

    if has_more:
        summary += " Use next_cursor for more results."

    if include_hint:
        summary += (
            " To get full message details, use slack_get_channel_history with "
            "channel_id and latest=ts, inclusive=true, limit=1. "
            "For threaded messages, use slack_get_thread_replies."
        )

    return summary


async def user_search_messages(
    query: str,
    channel_ids: Optional[List[str]] = None,
    to_me: bool = False,  # 新規追加
    sort: Optional[str] = None,
    sort_dir: Optional[str] = None,
    count: Optional[int] = None,
    cursor: Optional[str] = None,
    highlight: Optional[bool] = None,
    response_format: Optional[str] = None,  # 新規追加
) -> Dict[str, Any]:
    """Search for messages in the workspace."""
    # ... 実装
```

#### server.py のツール定義更新

```python
types.Tool(
    name="slack_user_search_messages",
    description="Searches for messages matching a query. Supports filtering by channel and searching for messages mentioning the authenticated user.",
    inputSchema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query string. Supports Slack search operators like 'in:#channel', 'from:@user', 'before:YYYY-MM-DD', 'after:YYYY-MM-DD', etc.",
            },
            "channel_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional list of channel IDs to search within.",
            },
            "to_me": {
                "type": "boolean",
                "description": "If true, searches for messages that mention the authenticated user. Automatically adds 'to:@<user_id>' to the query.",
                "default": False,
            },
            "sort": {
                "type": "string",
                "enum": ["score", "timestamp"],
                "description": "Sort results by relevance (score) or date (timestamp). Default is score.",
                "default": "score",
            },
            "sort_dir": {
                "type": "string",
                "enum": ["asc", "desc"],
                "description": "Sort direction. Default is desc.",
                "default": "desc",
            },
            "count": {
                "type": "number",
                "description": "Number of results to return per page (default 20, max 100)",
                "default": 20,
            },
            "cursor": {
                "type": "string",
                "description": "Pagination cursor for next page of results",
            },
            "highlight": {
                "type": "boolean",
                "description": "Whether to include highlighting of matched terms",
                "default": True,
            },
            "response_format": {
                "type": "string",
                "enum": ["concise", "detailed"],
                "description": "Response format. 'concise' (default) returns only essential fields. 'detailed' returns complete API response.",
                "default": "concise",
            },
        },
        "required": ["query"],
    },
    annotations=types.ToolAnnotations(
        **{"category": "SLACK_MESSAGE", "readOnlyHint": True}
    ),
),
```

### 4. summary フィールドの設計

`summary` は単一の文字列として以下の情報を含める：

1. **検索結果の概要**: `Found X messages, showing Y.`
2. **ページネーション案内**: `Use next_cursor for more results.`（次ページがある場合のみ）
3. **詳細取得ヒント**: concise の場合のみ追加

#### concise の場合の summary 例

```
"Found 123 messages, showing 20. Use next_cursor for more results. To get full message details, use slack_get_channel_history with channel_id and latest=ts, inclusive=true, limit=1. For threaded messages, use slack_get_thread_replies."
```

#### detailed の場合の summary 例

```
"Found 123 messages, showing 20. Use next_cursor for more results."
```

#### 実装ポイント

```python
# In user_search_messages function
include_hint = response_format == "concise"
summary = generate_summary(total, returned, has_more, include_hint=include_hint)
```

## 必要なスコープ

### 既存スコープ（変更なし）
- `search:read`: メッセージ検索に必要

### 追加スコープ
**なし** - `auth.test` はユーザートークンの場合スコープ不要

## レスポンスサイズの比較（推定）

| フォーマット | 1メッセージあたりの推定サイズ | 20メッセージの場合 |
|-------------|---------------------------|------------------|
| detailed（現状） | ~2,000-5,000 bytes | ~40,000-100,000 bytes |
| concise（新規） | ~200-400 bytes | ~4,000-8,000 bytes |

**削減率**: 約80-90%

## 実装順序

1. `search.py` に `get_current_user_id()` 関数を追加
2. `search.py` に `format_message_response()` 関数を追加
3. `search.py` に `generate_summary()` 関数を追加
4. `user_search_messages()` に `to_me` と `response_format` パラメーターを追加
5. `server.py` のツール定義を更新
6. `server.py` の `call_tool` ハンドラを更新

## テスト観点

1. **response_format テスト**
   - `concise` がデフォルトで適用されること
   - `detailed` で従来通りの全フィールドが返ること
   - `concise` で必要なフィールドのみ返ること

2. **summary テスト**
   - `concise` の場合、summary に詳細取得ヒントが含まれること
   - `detailed` の場合、summary に詳細取得ヒントが含まれないこと
   - next_cursor がある場合、summary に `Use next_cursor for more results.` が含まれること

3. **to_me テスト**
   - `to_me=True` で自分宛のメッセージが検索されること
   - `to_me=False` で従来通りの検索が行われること
   - `to_me=True` と他のフィルターの組み合わせが正常に動作すること

4. **エラーハンドリング**
   - `auth.test` が失敗した場合の適切なエラーメッセージ

## 参考資料

- [search.messages API](https://docs.slack.dev/reference/methods/search.messages/)
- [auth.test API](https://docs.slack.dev/reference/methods/auth.test/)
- [conversations.history API](https://docs.slack.dev/reference/methods/conversations.history/) - 特定メッセージの詳細取得に使用
- [Slack Search Modifiers](https://slack.com/help/articles/202528808-Search-in-Slack)
