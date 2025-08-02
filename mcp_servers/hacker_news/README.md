# 📰 Hacker News Tools

Async tools for the official Hacker News API, perfect for building custom clients, data analysis scripts, or AI-powered applications.

This library provides simple, high-level functions that wrap the official Hacker News API, returning clean Python dictionaries. This document covers both the tools themselves and the underlying API data structures you'll be working with.

---

## 📦 Available Tools

These functions provide direct access to Hacker News data.

### `hackerNews_item`
Fetches a single Hacker News item (story, comment, job, etc.) by its unique ID.

* **Parameters:**
    * `item_id` (int): The unique numeric identifier for the item (e.g., `8863`).

---

### `hackerNews_user`
Retrieves a Hacker News user's profile information.

* **Parameters:**
    * `username` (str): The user's case-sensitive username (e.g., `'pg'`).

---

### Story & Update Lists
These tools retrieve the full details for items in a specific category.

* **`hackerNews_topstories`**: Fetches the current top stories.
* **`hackerNews_beststories`**: Fetches the all-time best stories.
* **`hackerNews_newstories`**: Fetches the most recent stories.
* **`hackerNews_showstories`**: Fetches the latest "Show HN" stories.
* **`hackerNews_askstories`**: Fetches the latest "Ask HN" stories.
* **`hackerNews_jobstories`**: Fetches the latest job postings.
* **`hackerNews_updates`**: Fetches recent updates, including new items and changed profiles.

* **Common Parameter:**
    * `count` (int): The number of stories to fetch. (Default: `5`)

---

## ⚙️ API Reference & Data Models

The tools above are wrappers for the official Hacker News API. Understanding the underlying API can help you know what data to expect in return. For complete details, see the official [Hacker News API documentation](https://github.com/HackerNews/API).

* **Base URL**: The tools make calls to `https://hacker-news.firebaseio.com/v0/`.
* **Format**: All data is retrieved as **JSON** and parsed into Python dictionaries.
* **Core Concept**: Nearly everything—stories, comments, jobs, and polls—is considered an **item**.
---

## ✅ Common Features

-   **Asynchronous:** All tool functions are `async` and built for non-blocking I/O operations.
-   **Parsed Output:** Tools return ready-to-use Python dictionaries (`dict`) or lists of dictionaries (`list[dict]`), not raw JSON strings.
-   **Simplified Interface:** Complex API calls for fetching lists are simplified to a single function with a `count` parameter.