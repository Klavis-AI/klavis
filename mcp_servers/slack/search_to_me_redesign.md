# Slack検索ツール `to_me`パラメーター再設計

## 現状の問題

### 現在の実装
```python
if to_me:
    user_id = await get_current_user_id()
    search_query = f"{search_query} to:<@{user_id}>"
```

### 問題点

1. **`to:`修飾子の制約**
   - `to:<@userId>`はDMで送信されたメッセージのみを検索対象とする
   - チャンネル内での@mentionsは検索できない

2. **OR検索が機能しない**
   - `query to:<@userId>` のような形式でOR検索を試みても、`to:`修飾子が優先されDMのみが返される

3. **ユーザー混乱**
   - `to_me=True`という名前から、自分宛のメンションも含まれると期待するが、実際はDMのみ

## Slack検索修飾子の調査結果

### 主な検索修飾子

| 修飾子 | 用途 | 対象 |
|--------|------|------|
| `to:<@userId>` | 自分宛のDM検索 | DMのみ |
| `from:@user` / `from:<@userId>` | 特定ユーザーからのメッセージ | 全て |
| `in:#channel` / `in:<@userId>` | 特定チャンネル/DM内検索 | 指定場所 |
| `<@userId>` (クエリ内) | ユーザーメンションを含むメッセージ | 全て |

### 重要な発見

1. **メンション検索**: `<@U12345678>`をクエリに含めることで、そのユーザーへのメンションを検索可能
2. **`to:`と`from:`の違い**:
   - `to:` → DM宛先（DMのみ対象）
   - `from:` → 送信者（全メッセージ対象）
3. **結果フィルタリング**: APIレスポンスの`type`フィールドで`"im"`（DM）かどうか判別可能

## 設計案

### `to_me`パラメーターをLiteral型に変更

`to_me`（boolean）を`to_me`（Literal型）に変更する。パラメーター名はそのまま維持。

```python
from typing import Literal

to_me: Literal["dm", "mention", "off"] = "off"
```

#### オプション詳細

| 値 | クエリ追加 | 検索対象 | ユースケース |
|----|----------|----------|-------------|
| `"off"`（デフォルト） | なし | 全メッセージ | 一般検索（自分宛以外のメッセージも含む） |
| `"dm"` | `to:<@{user_id}>` | DMで自分宛のメッセージ | 「自分へのDMを探したい」 |
| `"mention"` | `<@{user_id}>` | チャンネルで自分への@mentions | 「チャンネルで自分がメンションされたメッセージを探したい」 |

#### 実装例（search.py）

```python
async def user_search_messages(
    query: str,
    channel_ids: Optional[List[str]] = None,
    to_me: Literal["dm", "mention", "off"] = "off",
    # ... 他のパラメーター
) -> Dict[str, Any]:
    search_query = query

    if to_me == "dm":
        # DMで自分宛のメッセージを検索
        user_id = await get_current_user_id()
        search_query = f"{search_query} to:<@{user_id}>"
    elif to_me == "mention":
        # チャンネルで自分へのメンションを検索
        user_id = await get_current_user_id()
        search_query = f"{search_query} <@{user_id}>"

    # ... 以降の処理
```

#### ツール定義（server.py）

```python
"to_me": {
    "type": "string",
    "enum": ["dm", "mention", "off"],
    "description": (
        "Filter messages addressed to the authenticated user. "
        "'dm': Search only direct messages sent to you. "
        "'mention': Search messages where you are @mentioned in channels. "
        "'off': No recipient filtering, searches all accessible messages (default)."
    ),
    "default": "off",
}
```

#### LLMへのガイダンス

ツールのdescriptionで以下のようにLLMが判断しやすいよう記載:

```
to_me: Filter for messages addressed to you.
  - 'dm': Only DMs sent directly to you (use when user asks for "messages sent to me in DMs")
  - 'mention': Only @mentions of you in channels (use when user asks for "messages mentioning me" or "messages addressed to me in channels")
  - 'off': All messages (default, use for general search)
```

### 変更点まとめ

| 項目 | Before | After |
|------|--------|-------|
| パラメーター名 | `to_me` | `to_me`（維持） |
| 型 | `bool` | `Literal["dm", "mention", "off"]` |
| デフォルト | `False` | `"off"` |
| DM検索 | `to_me=True` | `to_me="dm"` |
| チャンネルメンション検索 | 不可 | `to_me="mention"` |
| フィルターなし | `to_me=False` | `to_me="off"` |

## 参考資料

- [Slack search.messages API](https://docs.slack.dev/reference/methods/search.messages/)
- [Search in Slack](https://slack.com/help/articles/202528808-Search-in-Slack)
- [Shrinking the haystack: how to narrow search results in Slack](https://slack.com/blog/productivity/shrinking-the-haystack-how-to-narrow-search-results-in-slack)

## 補足: Slack検索の制約

1. **search.messages API**はユーザートークン使用時、Slack UIで設定された検索フィルターの影響を受ける
2. **最大取得件数**: count最大100、page最大100
3. **近接メッセージ**: 近接したメッセージが複数マッチする場合、1件のみ返される
