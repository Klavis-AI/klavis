# get_thread_replies 軽量化 実装仕様書

## 概要

`get_thread_replies` ツールに `response_format` パラメーターを追加し、レスポンスを軽量化する。

## 現状の問題点

- `conversations.replies` API のレスポンスをそのまま返しており、不要なフィールドが多い
- `search_messages` で実装済みの `response_format` パターンが未適用

## 現状の API レスポンス構造

```json
{
  "ok": true,
  "messages": [
    {
      "type": "message",
      "user": "U123456",
      "text": "親メッセージ本文",
      "thread_ts": "1234567890.123456",
      "reply_count": 5,
      "subscribed": true,
      "last_read": "1234567890.123456",
      "unread_count": 0,
      "ts": "1234567890.123456",
      "blocks": [...],
      "reactions": [...],
      "files": [...],
      "attachments": [...],
      "edited": {...},
      "client_msg_id": "...",
      "team": "T123456"
    },
    {
      "type": "message",
      "user": "U789012",
      "text": "返信本文",
      "thread_ts": "1234567890.123456",
      "parent_user_id": "U123456",
      "ts": "1234567890.234567",
      "blocks": [...],
      "reactions": [...],
      "client_msg_id": "...",
      "team": "T123456"
    }
  ],
  "has_more": false,
  "response_metadata": {
    "next_cursor": "..."
  }
}
```

## 実装方針

### response_format パラメーター

- **`concise`（デフォルト）**: 必要最小限のフィールドのみ返す
- **`detailed`**: API レスポンスをそのまま返す（従来の動作）

### concise フォーマットで返すフィールド

```json
{
  "ok": true,
  "messages": [
    {
      "user_id": "U123456",
      "ts": "1234567890.123456",
      "text": "親メッセージ本文",
      "thread_ts": "1234567890.123456",
      "reply_count": 5,
      "is_parent": true
    },
    {
      "user_id": "U789012",
      "ts": "1234567890.234567",
      "text": "返信本文",
      "thread_ts": "1234567890.123456",
      "parent_user_id": "U123456",
      "is_parent": false
    }
  ],
  "has_more": false,
  "summary": "Found 6 messages in thread. Use next_cursor for more results.",
  "response_metadata": {
    "next_cursor": "..."
  }
}
```

### フィールド選定理由

| フィールド | 理由 |
|-----------|------|
| `user_id` | 誰が投稿したかの特定に必須 |
| `ts` | メッセージ識別子。リアクション追加や返信時の引数として必須 |
| `text` | メッセージ内容 |
| `thread_ts` | スレッド識別子。返信時の引数として必須 |
| `reply_count` | 親メッセージの返信数把握（親メッセージのみ） |
| `parent_user_id` | 親投稿者の特定（返信メッセージのみ） |
| `is_parent` | 親メッセージか返信かを簡単に判別するため |

### summary フィールド

- メッセージ数のサマリー
- `has_more` が true の場合、`next_cursor` の利用案内を含める

## 必要なスコープ

変更なし（既存スコープで対応可能）
- `channels:history`
- `groups:history`
- `im:history`
- `mpim:history`

## 参考資料

- [conversations.replies API](https://docs.slack.dev/reference/methods/conversations.replies/)
- [Retrieving messages](https://api.slack.com/messaging/retrieving)
