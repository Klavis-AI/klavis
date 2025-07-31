# 🦁 Brave Search Tools

Async tools to access the Brave Search API for building AI assistants, dashboards, or apps.

These tools cover web, image, news, and video search — all with rich filtering and personalization options.

---

## 📦 Available Tools

| Tool | Description | Key Parameters | Notes |
|-----|--------------|----------------|------|
| **`brave_web_search`** | Perform a general Brave web search with rich filters and personalization. | - `query` (str): Search term<br>- `count` (int): Number of results (max 20)<br>- `country`, `search_lang`, `ui_lang`<br>- `safesearch`: off / moderate / strict<br>- `spellcheck`, `freshness`, `offset`<br>- `text_decorations`, `result_filter`, `units`<br>- `goggles` (custom re-ranking)<br>- `extra_snippets`, `summary`<br>- Location headers: `x_loc_lat`, `x_loc_long`, etc. | Supports result filtering (`news`, `videos`, `web`, etc.). Goggles allow custom ranking. Returns mixed web results including type breakdown. |
| **`brave_image_search`** | Search for images on Brave. | - `query` (str): Search term<br>- `count` (int): Number of images (max 200)<br>- `search_lang`, `country`<br>- `safesearch`: off / strict<br>- `spellcheck` | Default safesearch is stricter. Returns list of image results plus altered query if spellcheck changed input. |
| **`brave_news_search`** | Search for news articles. | - `query` (str): Search term<br>- `count` (int): Number of articles (max 50)<br>- `search_lang`, `ui_lang`, `country`<br>- `safesearch`: off / moderate / strict<br>- `offset` (pagination)<br>- `spellcheck`, `freshness`<br>- `extra_snippets`<br>- `goggles` (custom re-ranking) | Supports freshness filtering (last day, week, month, year, or date range). Extra snippets require certain plans. |
| **`brave_video_search`** | Search for videos. | - `query` (str): Search term<br>- `count` (int): Number of videos (max 50)<br>- `safesearch`: off / moderate / strict<br>- `search_lang`, `ui_lang`, `country`<br>- `offset` (pagination)<br>- `spellcheck`, `freshness` | Default safesearch is "off". Returns list of video results and supports freshness & spellcheck. |

---

## ✅ Common Features

- All tools support:
  - Async requests.
  - JSON response ready to use.
  - Logging for request & response info.
  - Optional spellcheck to correct queries.
  - Pagination (using `offset` and `count` where available).
- Location headers personalize search results:
  - `x_loc_lat`, `x_loc_long`
  - `x_loc_city`, `x_loc_state`, `x_loc_country`, etc.

---
