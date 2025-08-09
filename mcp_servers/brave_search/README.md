# 🦁 Brave Search Tools

Async tools to access the Brave Search API for building AI assistants, dashboards, or apps.

These tools cover web, image, news, and video search with essential filtering and pagination options.

---

## 📦 Available Tools

### `brave_web_search`
Performs a general Brave web search.

* **Parameters:**
    * `query` (str): The user's search query.
    * `count` (int): Number of results. (Default: `5`, Max: `20`)
    * `offset` (int): The number of results to skip for pagination.
    * `country` (str): A 2-letter country code (e.g., `US`).
    * `search_lang` (str): A 2-letter language code (e.g., `en`).
    * `safesearch` (str): Safety filter (`off`, `moderate`, or `strict`).

---

### `brave_image_search`
Searches for images on Brave.

* **Parameters:**
    * `query` (str): The image search query.
    * `count` (int): Number of image results. (Default: `5`, Max: `200`)
    * `offset` (int): The number of results to skip for pagination.
    * `country` (str): A 2-letter country code (e.g., `US`).
    * `search_lang` (str): A 2-letter language code (e.g., `en`).
    * `safesearch` (str): Safety filter (`off` or `strict`).

---

### `brave_news_search`
Searches for news articles.

* **Parameters:**
    * `query` (str): The news search query.
    * `count` (int): Number of news articles. (Default: `5`, Max: `50`)
    * `offset` (int): The number of results to skip for pagination.
    * `country` (str): A 2-letter country code (e.g., `US`).
    * `search_lang` (str): A 2-letter language code (e.g., `en`).
    * `safesearch` (str): Safety filter (`off`, `moderate`, or `strict`).
    * `freshness` (str): Filter by date: `pd` (day), `pw` (week), `pm` (month), or `py` (year).

---

### `brave_video_search`
Searches for videos.

* **Parameters:**
    * `query` (str): The video search query.
    * `count` (int): Number of video results. (Default: `5`, Max: `50`)
    * `offset` (int): The number of results to skip for pagination.
    * `country` (str): A 2-letter country code (e.g., `US`).
    * `search_lang` (str): A 2-letter language code (e.g., `en`).
    * `safesearch` (str): Safety filter (`off`, `moderate`, or `strict`). Defaults to `off`.
    * `freshness` (str): Filter by date: `pd` (day), `pw` (week), `pm` (month), or `py` (year).

---

## ✅ Common Features

-   **Asynchronous:** All tool functions are `async` and designed for non-blocking I/O.
-   **JSON Output:** Each tool returns a `dict` parsed directly from the API's JSON response.
-   **Logging:** Built-in logging provides useful information about outgoing requests and incoming responses.
-   **Pagination:** All tools support pagination using a combination of the `offset` and `count` parameters.