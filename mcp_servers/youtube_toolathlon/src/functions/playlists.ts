// @ts-ignore - We know the SDK exists
import { MCPFunction, MCPFunctionGroup } from "@modelcontextprotocol/sdk";
import { google } from 'googleapis';

// Utility function for safe execution with error handling
function safelyExecute<T>(fn: () => Promise<T>): Promise<T> {
  return fn().catch(error => {
    throw new Error(`Operation failed: ${error instanceof Error ? error.message : String(error)}`);
  });
}

export class PlaylistManagement implements MCPFunctionGroup {
  private youtube;

  constructor() {
    const apiKey = process.env.YOUTUBE_API_KEY;
    if (!apiKey) {
      throw new Error('YOUTUBE_API_KEY environment variable is not set.');
    }

    // @ts-ignore - The Google API works this way
    this.youtube = google.youtube({
      version: "v3",
      auth: apiKey
    });
  }

  // @ts-ignore - We know the SDK exists
  @MCPFunction({
    description: 'Get information about a YouTube playlist',
    parameters: {
      type: 'object',
      properties: {
        playlistId: { type: 'string' }
      },
      required: ['playlistId']
    }
  })
  async getPlaylist({ 
    playlistId 
  }: { 
    playlistId: string 
  }): Promise<any> {
    return safelyExecute(async () => {
      const response = await this.youtube.playlists.list({
        part: ['snippet', 'contentDetails'],
        id: [playlistId]
      });
      
      return response.data.items?.[0] || null;
    });
  }

  // @ts-ignore - We know the SDK exists
  @MCPFunction({
    description: 'Get videos in a YouTube playlist',
    parameters: {
      type: 'object',
      properties: {
        playlistId: { type: 'string' },
        maxResults: { type: 'number' }
      },
      required: ['playlistId']
    }
  })
  async getPlaylistItems({ 
    playlistId, 
    maxResults = 50 
  }: { 
    playlistId: string, 
    maxResults?: number 
  }): Promise<any[]> {
    return safelyExecute(async () => {
      const response = await this.youtube.playlistItems.list({
        part: ['snippet', 'contentDetails'],
        playlistId,
        maxResults
      });
      
      return response.data.items || [];
    });
  }
}