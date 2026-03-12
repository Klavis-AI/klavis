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