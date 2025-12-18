# get_channel_history 軽量化 実装仕様書

## 概要

`get_channel_history` ツールに `response_format` パラメーターを追加し、レスポンスを軽量化する。

## 現状の問題点

- `conversations.history` API のレスポンスをそのまま返しており、不要なフィールドが多い
- `search_messages` で実装済みの `response_format` パターンが未適用

## 現状の API レスポンス構造

```json
{
  "ok": true,
  "messages": [
    {
      "type": "message",
      "user": "U123456",
      "text": "メッセージ本文",
      "ts": "1234567890.123456",
      "blocks": [...],
      "attachments": [...],
      "reactions": [
        {
          "name": "thumbsup",
          "users": ["U123456", "U789012"],
          "count": 2
        }
      ],
      "edited": {
        "user": "U123456",
        "ts": "1234567890.234567"
      },
      "thread_ts": "1234567890.123456",
      "reply_count": 3,
      "reply_users_count": 2,
      "latest_reply": "1234567890.345678",
      "reply_users": ["U123456", "U789012"],
      "is_starred": true,
      "client_msg_id": "...",
      "team": "T123456"
    }
  ],
  "has_more": true,
  "pin_count": 0,
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
      "text": "メッセージ本文",
      "thread_ts": "1234567890.123456",
      "reply_count": 3,
      "is_thread_parent": true
    }
  ],
  "has_more": true,
  "summary": "Found 10 messages. Use next_cursor for more results.",
  "response_metadata": {
    "next_cursor": "..."
  }
}
```

### フィールド選定理由

| フィールド | 理由 |
|-----------|------|
| `user_id` | 誰が投稿したかの特定に必須 |
| `ts` | メッセージ識別子。リアクション追加、返信、編集等の引数として必須 |
| `text` | メッセージ内容 |
| `thread_ts` | スレッドの親メッセージを示す。返信時の引数として必要 |
| `reply_count` | スレッドの返信数（スレッド親メッセージのみ） |
| `is_thread_parent` | スレッドの親メッセージかどうかの判別用 |

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

- [conversations.history API](https://docs.slack.dev/reference/methods/conversations.history/)
- [Retrieving messages](https://api.slack.com/messaging/retrieving)
