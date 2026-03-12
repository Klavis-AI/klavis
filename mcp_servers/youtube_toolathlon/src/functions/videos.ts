import { google } from 'googleapis';
// @ts-ignore - We know the SDK exists
import { MCPFunction, MCPFunctionGroup } from "@modelcontextprotocol/sdk";

function safelyExecute<T>(fn: () => Promise<T>): Promise<T> {
  return fn().catch(error => {
    throw new Error(`Operation failed: ${error instanceof Error ? error.message : String(error)}`);
  });
}

export class VideoManagement implements MCPFunctionGroup {
  private youtube;

  constructor() {
    const apiKey = process.env.YOUTUBE_API_KEY;
    if (!apiKey) {
      throw new Error('YOUTUBE_API_KEY environment variable is not set. Please set it before running the application.');
    }

    // @ts-ignore - The Google API works this way
    this.youtube = google.youtube({
      version: 'v3',
      auth: apiKey
    });
  }

  // @ts-ignore - We know the SDK exists
  @MCPFunction({
    description: 'Get detailed information about a YouTube video',
    parameters: {
      type: 'object',
      properties: {
        videoId: { type: 'string' },
        parts: { 
          type: 'array',
          items: { type: 'string' }
        }
      },
      required: ['videoId']
    }
  })
  async getVideo({ 
    videoId, 
    parts = ['snippet', 'contentDetails', 'statistics'] 
  }: { 
    videoId: string, 
    parts?: string[] 
  }): Promise<any> {
    return safelyExecute(async () => {
      const response = await this.youtube.videos.list({
        part: parts,
        id: [videoId]
      });
      
      return response.data.items?.[0] || null;
    });
  }

  // @ts-ignore - We know the SDK exists
  @MCPFunction({
    description: 'Search for videos on YouTube',
    parameters: {
      type: 'object',
      properties: {
        query: { type: 'string' },
        maxResults: { type: 'number' }
      },
      required: ['query']
    }
  })
  async searchVideos({ 
    query, 
    maxResults = 10 
  }: { 
    query: string, 
    maxResults?: number 
  }): Promise<any[]> {
    return safelyExecute(async () => {
      const response = await this.youtube.search.list({
        part: ['snippet'],
        q: query,
        maxResults,
        type: ['video']
      });
      
      return response.data.items || [];
    });
  }

  // @ts-ignore - We know the SDK exists
  @MCPFunction({
    description: 'Get video statistics like views, likes, and comments',
    parameters: {
      type: 'object',
      properties: {
        videoId: { type: 'string' }
      },
      required: ['videoId']
    }
  })
  async getVideoStats({ 
    videoId 
  }: { 
    videoId: string 
  }): Promise<any> {
    return safelyExecute(async () => {
      const response = await this.youtube.videos.list({
        part: ['statistics'],
        id: [videoId]
      });
      
      return response.data.items?.[0]?.statistics || null;
    });
  }
}