// @ts-ignore - We know the SDK exists
import { MCPFunction, MCPFunctionGroup } from "@modelcontextprotocol/sdk";
import { YoutubeTranscript } from "youtube-transcript";

export class TranscriptManagement implements MCPFunctionGroup {
  constructor() {
    // No constructor arguments needed for YouTube transcript
  }

  // @ts-ignore - We know the SDK exists
  @MCPFunction({
    description: 'Get the transcript of a YouTube video',
    parameters: {
      type: 'object',
      properties: {
        videoId: { type: 'string' },
        language: { type: 'string' }
      },
      required: ['videoId']
    }
  })
  async getTranscript({ 
    videoId, 
    language = process.env.YOUTUBE_TRANSCRIPT_LANG || 'en' 
  }: { 
    videoId: string, 
    language?: string 
  }): Promise<any> {
    try {
      // @ts-ignore - Library may not match types exactly
      const transcript = await YoutubeTranscript.fetchTranscript(videoId);
      
      return {
        videoId,
        language,
        transcript
      };
    } catch (error) {
      throw new Error(`Failed to get transcript: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  // @ts-ignore - We know the SDK exists
  @MCPFunction({
    description: 'Search within a transcript',
    parameters: {
      type: 'object',
      properties: {
        videoId: { type: 'string' },
        query: { type: 'string' },
        language: { type: 'string' }
      },
      required: ['videoId', 'query']
    }
  })
  async searchTranscript({ 
    videoId, 
    query,
    language = process.env.YOUTUBE_TRANSCRIPT_LANG || 'en' 
  }: { 
    videoId: string,
    query: string, 
    language?: string 
  }): Promise<any> {
    try {
      // @ts-ignore - Library may not match types exactly
      const transcript = await YoutubeTranscript.fetchTranscript(videoId);
      
      // Search through transcript for the query
      const matches = transcript.filter(item => 
        item.text.toLowerCase().includes(query.toLowerCase())
      );
      
      return {
        videoId,
        query,
        matches,
        totalMatches: matches.length
      };
    } catch (error) {
      throw new Error(`Failed to search transcript: ${error instanceof Error ? error.message : String(error)}`);
    }
  }
}