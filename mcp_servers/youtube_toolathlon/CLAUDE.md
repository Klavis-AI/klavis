# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

```bash
# Install dependencies
npm install

# Build the project (compiles TypeScript to dist/)
npm run build

# Development mode with auto-rebuild and restart
npm run dev

# Start the server (requires build first)
npm start

# Prepare for publishing (runs build)
npm run prepublishOnly
```

## Environment Setup

Required environment variables:
- `YOUTUBE_API_KEY`: YouTube Data API v3 key (required for all operations)
- `YOUTUBE_TRANSCRIPT_LANG`: Default transcript language (optional, defaults to 'en')

## Project Architecture

This is a Model Context Protocol (MCP) server that provides YouTube integration for AI language models. The architecture follows a service-oriented pattern:

### Core Structure
- **Entry Points**: `src/index.ts` (main server), `src/cli.ts` (CLI binary)
- **Server Setup**: `src/server.ts` - MCP server initialization and tool registration
- **Services Layer**: `src/services/` - Business logic for YouTube operations
  - `VideoService`: Video details, search, and statistics
  - `TranscriptService`: Video transcript retrieval and search
  - `PlaylistService`: Playlist management and content
  - `ChannelService`: Channel information and video listings
- **Types**: `src/types.ts` - TypeScript interfaces for all parameters

### MCP Tools Architecture
The server exposes 7 MCP tools following the pattern `{category}_{action}`:
- `videos_getVideo` / `videos_searchVideos`
- `transcripts_getTranscript`
- `channels_getChannel` / `channels_listVideos`
- `playlists_getPlaylist` / `playlists_getPlaylistItems`

### Service Pattern
All services use lazy initialization to validate the YouTube API key only when tools are called, not during server startup. Services follow a consistent error handling pattern with try/catch blocks.

### Build Configuration
- **TypeScript**: ES2022 target with ESNext modules
- **Module System**: ES modules with `.js` extensions in imports
- **Output**: Compiled to `dist/` directory
- **Entry Points**: `dist/index.js` (server), `dist/cli.js` (binary)

### Key Dependencies
- `@modelcontextprotocol/sdk`: MCP protocol implementation
- `googleapis`: YouTube Data API v3 client
- `youtube-transcript`: Transcript extraction (no API key needed)
- `ytdl-core`: YouTube video information

The `functions/` directory contains additional functionality that is excluded from the main build via tsconfig.json.