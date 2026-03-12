// @ts-ignore - We know the SDK exists
import { MCPFunction, MCPFunctionGroup } from "@modelcontextprotocol/sdk";
import { google } from 'googleapis';

// Utility functions
function safeGet<T>(obj: any, path: string, defaultValue?: T): T | undefined {
  return path.split('.').reduce((acc, part) => 
    acc && acc[part] !== undefined ? acc[part] : defaultValue, obj);
}

function safeParse(value: string | number | null | undefined, defaultValue = 0): number {
  if (value === null || value === undefined) return defaultValue;
  const parsed = Number(value);
  return isNaN(parsed) ? defaultValue : parsed;
}

export class ChannelManagement implements MCPFunctionGroup {
  private youtube;

  constructor() {
    const apiKey = process.env.YOUTUBE_API_KEY;
    if (!apiKey) {
      throw new Error('YOUTUBE_API_KEY environment variable is not set.');
    }

    // @ts-ignore - The Google API works this way
    this.youtube = google.youtube({
      version: 'v3',
      auth: apiKey
    });
  }

  // @ts-ignore - We know the SDK exists
  @MCPFunction({
    description: 'Get channel details',
    parameters: {
      type: 'object',
      properties: {
        channelId: { type: 'string' }
      },
      required: ['channelId']
    }
  })
  async getChannel({ 
    channelId 
  }: { 
    channelId: string 
  }): Promise<any> {
    try {
      const response = await this.youtube.channels.list({
        part: ['snippet', 'statistics', 'contentDetails'],
        id: [channelId]
      });

      return response.data.items?.[0] || null;
    } catch (error) {
      throw new Error(`Failed to get channel: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  // @ts-ignore - We know the SDK exists
  @MCPFunction({
    description: 'Get channel videos',
    parameters: {
      type: 'object',
      properties: {
        channelId: { type: 'string' },
        maxResults: { type: 'number' }
      },
      required: ['channelId']
    }
  })
  async getChannelVideos({ 
    channelId, 
    maxResults = 50 
  }: { 
    channelId: string, 
    maxResults?: number 
  }): Promise<any[]> {
    try {
      const response = await this.youtube.search.list({
        part: ['snippet'],
        channelId,
        maxResults,
        order: 'date',
        type: ['video']
      });

      return response.data.items || [];
    } catch (error) {
      throw new Error(`Failed to get channel videos: ${error instanceof Error ? error.message : String(error)}`);
    }
  }
}