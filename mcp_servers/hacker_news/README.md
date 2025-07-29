### Hacker News API Cheat Sheet

***

## 🌐 API Basics

* **Base URL**: All API calls are prefixed with `https://hacker-news.firebaseio.com/v0/`.
* **Versioning**: The current and only version is `v0`.
* **Format**: All endpoints return data in JSON format. Append `?print=pretty` to any endpoint URL for human-readable output.
* **Core Concept**: Stories, comments, jobs, polls, and poll options are all considered **items** and are identified by a unique integer `id`.

***

## 🔗 API Endpoints

The API provides endpoints for retrieving items, user profiles, and lists of item IDs.

| Endpoint | Description |
| :--- | :--- |
| `/item/<id>.json` | Fetches a single item (story, comment, job, etc.) by its unique ID. |
| `/user/<id>.json` | Fetches a user's profile by their case-sensitive username. |
| `/maxitem.json` | Returns the ID of the most recent item. |
| `/topstories.json` | Returns a list of up to 500 top story IDs. |
| `/newstories.json` | Returns a list of up to 500 new story IDs. |
| `/beststories.json`| Returns a list of up to 500 "best" story IDs. |
| `/askstories.json` | Returns a list of up to 200 latest "Ask HN" story IDs. |
| `/showstories.json` | Returns a list of up to 200 latest "Show HN" story IDs. |
| `/jobstories.json` | Returns a list of up to 200 latest job story IDs. |
| `/updates.json` | Returns a list of item and profile IDs that have changed. |

***

## 📦 Data Models

Here are the data structures for the main objects available through the API. **Bold** fields are required and will always be present.

### Item Object
An `item` can be one of the following types: `"story"`, `"comment"`, `"job"`, `"poll"`, or `"pollopt"`.

| Field | Type | Description |
| :--- | :--- | :--- |
| **`id`** | Integer | The item's unique ID. |
| **`type`** | String | The type of item. |
| `deleted` | Boolean | `true` if the item is deleted. |
| `by` | String | The username of the item's author. |
| `time` | Integer | Creation date in Unix Time. |
| `text` | String | The comment, story, or poll text (HTML). |
| `dead` | Boolean | `true` if the item is dead. |
| `parent` | Integer | The parent item's ID (for comments). |
| `kids` | Array | A list of comment IDs, in ranked display order. |
| `url` | String | The URL of the story. |
| `score` | Integer | The story's score or poll option's votes. |
| `title` | String | The title of the story, poll, or job (HTML). |
| `parts` | Array | A list of poll option IDs (for polls). |
| `descendants`| Integer | The total comment count for a story or poll. |

### User Object
A user's public profile.

| Field | Type | Description |
| :--- | :--- | :--- |
| **`id`** | String | The user's unique, case-sensitive username. |
| **`created`**| Integer | Creation date of the user in Unix Time. |
| **`karma`** | Integer | The user's karma score. |
| `about` | String | The user's optional self-description (HTML). |
| `submitted`| Array | A list of IDs for the user's submissions (stories, comments, etc.). |