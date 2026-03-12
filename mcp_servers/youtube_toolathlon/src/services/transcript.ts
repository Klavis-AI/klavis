import { YoutubeTranscript } from "youtube-transcript";
import { TranscriptParams, SearchTranscriptParams } from '../types.js';

/**
 * Service for interacting with YouTube video transcripts
 */
export class TranscriptService {
  // No YouTube API key needed for transcripts, but we'll implement the same pattern
  private initialized = false;

  constructor() {
    // No initialization needed
  }

  private initialize() {
    if (this.initialized) return;
    // No API key needed for transcripts, but we'll check if language is set
    this.initialized = true;
  }

  /**
   * Get the transcript of a YouTube video
   */
  async getTranscript({ 
    videoId, 
    language = process.env.YOUTUBE_TRANSCRIPT_LANG || 'en' 
  }: TranscriptParams): Promise<any> {
    try {
      this.initialize();
      
      // YoutubeTranscript.fetchTranscript only accepts videoId
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

  /**
   * Search within a transcript
   */
  async searchTranscript({ 
    videoId, 
    query,
    language = process.env.YOUTUBE_TRANSCRIPT_LANG || 'en' 
  }: SearchTranscriptParams): Promise<any> {
    try {
      this.initialize();
      
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
  
  /**
   * Get transcript with timestamps
   */
  async getTimestampedTranscript({ 
    videoId, 
    language = process.env.YOUTUBE_TRANSCRIPT_LANG || 'en' 
  }: TranscriptParams): Promise<any> {
    try {
      this.initialize();
      
      const transcript = await YoutubeTranscript.fetchTranscript(videoId);
      
      // Format timestamps in human-readable format
      const timestampedTranscript = transcript.map(item => {
        const seconds = item.offset / 1000;
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.floor(seconds % 60);
        const formattedTime = `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
        
        return {
          timestamp: formattedTime,
          text: item.text,
          startTimeMs: item.offset,
          durationMs: item.duration
        };
      });
      
      return {
        videoId,
        language,
        timestampedTranscript
      };
    } catch (error) {
      throw new Error(`Failed to get timestamped transcript: ${error instanceof Error ? error.message : String(error)}`);
    }
  }
}