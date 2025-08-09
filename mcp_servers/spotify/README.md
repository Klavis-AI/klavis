# Spotify MCP Server

A **Model Context Protocol (MCP)** server for Spotify, enabling access to music data such as artists, albums, tracks, and audio features through the Spotify Web API.

---

## Features

- **Artist Search & Info**: Search for artists by name or ID and retrieve details such as genres, popularity, followers, and Spotify profile links.  
- **Top Tracks**: Fetch the top tracks for a given artist by name or ID.  
- **Albums**: Get albums by artist name or ID, including release dates.  
- **Track Search & Details**: Search for tracks by keywords or get detailed track information by ID.   

---

## Prerequisites

- Python **3.10** or higher  
- A **Spotify API Access Token** (You can obtain this via [Spotify Developer Dashboard](https://developer.spotify.com/dashboard))  
- Spotify Web API endpoint base URL: `https://api.spotify.com/v1`  

---

## Installation

1. Clone the repository and navigate to the Spotify MCP server directory:

```bash
cd klavis-ai-spotify-mcp
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with your Spotify credentials:
```env
SPOTIFY_API_BASE=https://api.spotify.com/v1
SPOTIFY_ACCESS_TOKEN="YOUR_SPOTIFY_ACCESS_TOKEN"
```


## How to Get a Spotify Access Token (via Postman)  (spotify access token valids 3600 seconds)

1. **Get your Client ID and Client Secret**  
   - Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)  
   - Create an app and copy:  
     - **Client ID** → acts like your username  
     - **Client Secret** → acts like your password  

2. **Open Postman**  
   - Method: **POST**  
   - URL:  
     ```
     https://accounts.spotify.com/api/token
     ```

3. **Set Authorization**  
   - In Postman, go to **Authorization** tab  
   - **Type**: Basic Auth  
   - **Username** = Your **Client ID**  
   - **Password** = Your **Client Secret**

4. **Set Body**  
   - Go to **Body** tab  
   - Select **x-www-form-urlencoded**  
   - Add:  
     ```
     grant_type    client_credentials
     ```

5. **Send Request & Get Token**  
   - Click **Send**  
   - Copy the `"access_token"` from the response  

6. **Add to `.env` file**  
   ```env
   SPOTIFY_API_BASE=https://api.spotify.com/v1
   SPOTIFY_ACCESS_TOKEN=YOUR_ACCESS_TOKEN

---

## Running the Server

Run the MCP server:
```bash
uv run main.py
```

This will start the server with all registered Spotify tools.

---

## Available Tools

| Tool Name | Description | Example Usage |
|-----------|-------------|---------------|
| `get_artist_top_tracks_by_artist_name_tool` | Search tracks by artist name | "Search for top 5 tracks of Karan Aujla." |
| `get_artist_info_by_artist_name_tool` | Get artist info by artist name | "Get artist info for Taylor Swift" |
| `get_artist_albums_by_artist_name_tool` | Get artist album by artist name | "Get albums by artist name Yo Yo honey singh" |
| `get_artist_info_by_name` | Get artist info by name | "Get artist info for Justin Bieber" |
| `get_artist_info_tool` | Get artist info by artist ID | "get artist info by this artist id 4YRxDV8wJFPHPTeXepOstw" |
| `get_artist_top_tracks_tool` | Get top tracks for artist ID | "Get top tracks for artist ID 4YRxDV8wJFPHPTeXepOstw" |
| `get_artist_albums_tool` | Get albums by artist ID | "Get albums for artist ID 1uNFoZAHBGtllmzznpCI3s" |

---

## Example Claude Prompts

- "Search for top 5 tracks of Karan Aujla."  
- "Get artist info for Taylor Swift"  
- "Get albums by artist name Yo Yo honey singh"  
- "get artist info by this artist id 4YRxDV8wJFPHPTeXepOstw"
- "Get top tracks for artist ID 4YRxDV8wJFPHPTeXepOstw"
- "Get albums for artist ID 1uNFoZAHBGtllmzznpCI3s"
- "Get artist info for ID 1uNFoZAHBGtllmzznpCI3s"
- "Get track details for ID 4uLU6hMCjMI75M1A2tKUQC"
- "Get album details for ID 3KuXEGcqLcnEYWnn3OEGy0"
