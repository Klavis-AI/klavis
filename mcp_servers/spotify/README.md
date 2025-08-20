# Spotify Music Explorer MCP

An AI agent server built with **FastMCP** that turns your Spotify listening data into interactive insights, tools, and personalized music intelligence — **even without Spotify Premium**.

Get dynamic tools to **search**, **analyze**, **build playlists**, and **explore your taste** through the power of the Spotify Web API.

---

## 🚀 What It Can Do

* 🔍 **Search Explorer**
  Find tracks, albums, and artists with natural-language queries or keywords.

* 🧠 **Taste Analysis Tools**
  Understand your genre leanings, mood tendencies, and discover how your preferences evolve.

* 🔄 **Listening Shift Insights**
  Compare your music energy, valence, and vibe between different periods.

* 🔮 **Taste Prediction Engine**
  Forecast the direction your music taste might head based on past trends.

* 📈 **Top Tracks & Artists Viewer**
  View your most-played artists and tracks across different timeframes.

* 🗃 **Playlist Explorer & Builder**
  Explore your playlists or create new ones via agent-powered tools.

* 🧪 **Track Audio Feature Inspector**
  Dive into danceability, tempo, valence, acousticness, and other hidden traits.

* 🤖 **AI-Generated Recommendations**
  Use Spotify’s engine to get tailored suggestions based on seeds (genre, artist, track).

* ▶️ **Now Playing Tool**
  See what's currently playing on your Spotify account.

* ❤️ **Follow/Unfollow Artists**
  Manage the artists you follow.

* 🧹 **Playlist Cleanup**
  Remove tracks or delete playlists with ease.

---

## 🔧 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/your-username/spotify-music-explorer-mcp.git
cd spotify-music-explorer-mcp
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up your environment variables

```bash
cp .env.example .env
```

Update `.env` with your Spotify API credentials:

* Create an app at [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
* Generate a **Refresh Token** using the Authorization Code Flow if you want full access

### 4. Run the MCP server

```bash
python spotify_music_explorer_mcp.py
```

By default, your server will be available at:
`http://localhost:9090`

---

## 🔐 Authentication

This server uses **Bearer Token Auth**. By default, it expects:

```
Authorization: Bearer shadow-spotify-token
```

You can configure this via `.env`:

```env
MCP_BEARER_TOKEN=your_custom_token
```

---

## 🧰 Available Tools

Here are some of the tools exposed through the MCP agent system:

| Tool Name                       | What It Does                                                              |
| ------------------------------- | ------------------------------------------------------------------------- |
| `search_tracks`                 | Search for tracks by keyword                                              |
| `search_artists`                | Search for artists by keyword                                             |
| `search_albums`                 | Search for albums by keyword                                              |
| `get_playlist`                  | Get playlist metadata                                                     |
| `get_playlist_tracks`           | View the tracks inside a playlist                                         |
| `create_playlist`               | Create a new playlist on your account                                     |
| `add_tracks_to_playlist`        | Add tracks to a playlist                                                  |
| `remove_tracks_from_playlist`   | Remove selected tracks from a playlist                                    |
| `delete_playlist`               | Delete a playlist entirely                                                |
| `get_top_tracks`                | View your top tracks                                                      |
| `get_top_artists`               | View your top artists                                                     |
| `get_currently_playing`         | See what’s currently playing                                              |
| `get_audio_features`            | Retrieve technical audio features for tracks                              |
| `get_audio_analysis`            | Get detailed audio analysis for a track                                   |
| `get_recommendations`           | Get track recommendations via Spotify’s AI engine                         |
| `get_user_playlists`            | List all playlists under your account                                     |
| `get_artist`, `get_album`, etc. | View metadata for artists, albums, and individual tracks                  |
| `get_related_artists`           | Discover artists similar to a given artist                                |
| `get_genre_seeds`               | View available genre seeds for recommendations                            |
| `compare_tracks`                | Compare multiple tracks based on key features like valence, tempo, energy |

---

## 🛠 Built With

* 🧠 [FastMCP](https://github.com/fixie-ai/fastmcp) – AI Agent Framework
* 🎧 [Spotify Web API](https://developer.spotify.com/documentation/web-api/)
* 🔐 Bearer Token Auth (via custom RSA implementation)

---

## 📝 License

MIT License

---

Made with ❤️ by music & data nerds.
**Not affiliated with Spotify.**

