# YouTube MCP Server
A Model Context Protocol (MCP) server implementation for YouTube, enabling AI language models to interact with YouTube content through a standardized interface.

## Features

### Video Information
* Get video details (title, description, duration, etc.)
* List channel videos
* Get video statistics (views, likes, comments)
* Search videos across YouTube

### Transcript Management
* Retrieve video transcripts
* Support for multiple languages
* Get timestamped captions
* Search within transcripts

### Channel Management
* Get channel details
* List channel playlists
* Get channel statistics
* Search within channel content

### Playlist Management
* List playlist items
* Get playlist details
* Search within playlists
* Get playlist video transcripts

## Installation

```bash
npm install @modelcontextprotocol/server-youtube
```

## Configuration
Set the following environment variables:
* `YOUTUBE_API_KEY`: Your YouTube Data API key
* `YOUTUBE_TRANSCRIPT_LANG`: Default language for transcripts (optional, defaults to 'en')

## Using with MCP Client
Add this to your MCP client configuration (e.g. Claude Desktop):

```json
{
  "mcpServers": {
    "youtube": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-youtube"],
      "env": {
        "YOUTUBE_API_KEY": "<YOUR_API_KEY>"
      }
    }
  }
}
```

### Using with VS Code

For one-click installation, click one of the install buttons below:

[![Install with NPX in VS Code](https://img.shields.io/badge/VS_Code-NPM-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=youtube&config=%7B%22command%22%3A%22npx%22%2C%22args%22%3A%5B%22-y%22%2C%22%40modelcontextprotocol%2Fserver-youtube%22%5D%2C%22env%22%3A%7B%22YOUTUBE_API_KEY%22%3A%22%24%7Binput%3AapiKey%7D%22%7D%7D&inputs=%5B%7B%22type%22%3A%22promptString%22%2C%22id%22%3A%22apiKey%22%2C%22description%22%3A%22YouTube+API+Key%22%2C%22password%22%3Atrue%7D%5D) [![Install with NPX in VS Code Insiders](https://img.shields.io/badge/VS_Code_Insiders-NPM-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=youtube&config=%7B%22command%22%3A%22npx%22%2C%22args%22%3A%5B%22-y%22%2C%22%40modelcontextprotocol%2Fserver-youtube%22%5D%2C%22env%22%3A%7B%22YOUTUBE_API_KEY%22%3A%22%24%7Binput%3AapiKey%7D%22%7D%7D&inputs=%5B%7B%22type%22%3A%22promptString%22%2C%22id%22%3A%22apiKey%22%2C%22description%22%3A%22YouTube+API+Key%22%2C%22password%22%3Atrue%7D%5D&quality=insiders)

### Manual Installation

If you prefer manual installation, first check the install buttons at the top of this section. Otherwise, follow these steps:

Add the following JSON block to your User Settings (JSON) file in VS Code. You can do this by pressing `Ctrl + Shift + P` and typing `Preferences: Open User Settings (JSON)`.

```json
{
  "mcp": {
    "inputs": [
      {
        "type": "promptString",
        "id": "apiKey",
        "description": "YouTube API Key",
        "password": true
      }
    ],
    "servers": {
      "youtube": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-youtube"],
        "env": {
          "YOUTUBE_API_KEY": "${input:apiKey}"
        }
      }
    }
  }
}
```

Optionally, you can add it to a file called `.vscode/mcp.json` in your workspace:

```json
{
  "inputs": [
    {
      "type": "promptString",
      "id": "apiKey",
      "description": "YouTube API Key",
      "password": true
    }
  ],
  "servers": {
    "youtube": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-youtube"],
      "env": {
        "YOUTUBE_API_KEY": "${input:apiKey}"
      }
    }
  }
}
```

## YouTube API Setup
1. Go to Google Cloud Console
2. Create a new project or select an existing one
3. Enable the YouTube Data API v3
4. Create API credentials (API key)
5. Copy the API key for configuration

## Examples

### Managing Videos

```javascript
// Get video details
const video = await youtube.videos.getVideo({
  videoId: "video-id"
});

// Get video transcript
const transcript = await youtube.transcripts.getTranscript({
  videoId: "video-id",
  language: "en"
});

// Search videos
const searchResults = await youtube.videos.searchVideos({
  query: "search term",
  maxResults: 10
});
```

### Managing Channels

```javascript
// Get channel details
const channel = await youtube.channels.getChannel({
  channelId: "channel-id"
});

// List channel videos
const videos = await youtube.channels.listVideos({
  channelId: "channel-id",
  maxResults: 50
});
```

### Managing Playlists

```javascript
// Get playlist items
const playlistItems = await youtube.playlists.getPlaylistItems({
  playlistId: "playlist-id",
  maxResults: 50
});

// Get playlist details
const playlist = await youtube.playlists.getPlaylist({
  playlistId: "playlist-id"
});
```

## Development

```bash
# Install dependencies
npm install

# Run tests
npm test

# Build
npm run build

# Lint
npm run lint
```

## Contributing
See CONTRIBUTING.md for information about contributing to this repository.

## License
This project is licensed under the MIT License - see the LICENSE file for details.
