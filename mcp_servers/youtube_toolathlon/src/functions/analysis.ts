import { MCPFunction, MCPFunctionGroup } from "@modelcontextprotocol/sdk";
import { YoutubeTranscript } from "youtube-transcript";
import * as ytdl from "ytdl-core";
import * as fs from "fs/promises";

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

function safelyExecute<T>(fn: () => T): T | null {
  try {
    return fn();
  } catch (error: unknown) {
    console.error('Execution error:', error instanceof Error ? error.message : 'Unknown error');
    return null;
  }
}

export class ContentAnalysis implements MCPFunctionGroup {
  private youtube: any;
  private languageClient: any;

  constructor() {
    this.youtube = google.youtube({
      version: 'v3',
      auth: process.env.YOUTUBE_API_KEY
    });
    this.languageClient = new google.cloud.LanguageServiceClient();
  }

  @MCPFunction({
    description: 'Generate video summary from transcript',
    parameters: {
      type: 'object',
      properties: {
        videoId: { type: 'string' },
        maxLength: { type: 'number' }
      },
      required: ['videoId']
    }
  })
  async generateSummary({ 
    videoId, 
    maxLength = 250 
  }: { 
    videoId: string, 
    maxLength?: number 
  }): Promise<string> {
    try {
      const transcript = await YoutubeTranscript.fetchTranscript(videoId);
      const text = transcript.map(t => t.text).join(' ');
      
      const [result] = await this.languageClient.summarize({
        document: {
          content: text,
          type: 'PLAIN_TEXT'
        },
        maxOutputTokens: maxLength
      });

      return result.summary || '';
    } catch (error) {
      throw new Error(`Failed to generate summary: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  @MCPFunction({
    description: 'Analyze video sentiment',
    parameters: {
      type: 'object',
      properties: {
        videoId: { type: 'string' }
      },
      required: ['videoId']
    }
  })
  async analyzeSentiment({ 
    videoId 
  }: { 
    videoId: string 
  }): Promise<any> {
    try {
      const transcript = await YoutubeTranscript.fetchTranscript(videoId);
      const text = transcript.map(t => t.text).join(' ');

      const [result] = await this.languageClient.analyzeSentiment({
        document: {
          content: text,
          type: 'PLAIN_TEXT'
        }
      });

      return {
        sentiment: result.documentSentiment,
        segments: result.sentences.map(s => ({
          text: s.text?.content,
          sentiment: s.sentiment
        }))
      };
    } catch (error) {
      throw new Error(`Failed to analyze sentiment: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  @MCPFunction({
    description: 'Extract key topics from video',
    parameters: {
      type: 'object',
      properties: {
        videoId: { type: 'string' }
      },
      required: ['videoId']
    }
  })
  async extractTopics({ 
    videoId 
  }: { 
    videoId: string 
  }): Promise<any[]> {
    try {
      const transcript = await YoutubeTranscript.fetchTranscript(videoId);
      const text = transcript.map(t => t.text).join(' ');

      const [result] = await this.languageClient.analyzeEntities({
        document: {
          content: text,
          type: 'PLAIN_TEXT'
        }
      });

      return result.entities || [];
    } catch (error) {
      throw new Error(`Failed to extract topics: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  @MCPFunction({
    description: 'Generate key moment timestamps',
    parameters: {
      type: 'object',
      properties: {
        videoId: { type: 'string' }
      },
      required: ['videoId']
    }
  })
  async generateTimestamps({ 
    videoId 
  }: { 
    videoId: string 
  }): Promise<any[]> {
    try {
      const transcript = await YoutubeTranscript.fetchTranscript(videoId);
      const [result] = await this.languageClient.classifyText({
        document: {
          content: transcript.map(t => t.text).join(' '),
          type: 'PLAIN_TEXT'
        }
      });

      const keyMoments = [];
      let currentSegment = { text: [], timestamp: 0 };

      for (const item of transcript) {
        currentSegment.text.push(item.text);
        
        if (this.isSignificantChange(item.text) || item.offset >= currentSegment.timestamp + 30000) {
          keyMoments.push({
            timestamp: currentSegment.timestamp / 1000,
            text: currentSegment.text.join(' '),
            categories: result.categories
          });
          currentSegment = { text: [], timestamp: item.offset };
        }
      }

      return keyMoments;
    } catch (error) {
      throw new Error(`Failed to generate timestamps: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  private isSignificantChange(text: string): boolean {
    const indicators = [
      'next', 'now', 'let\'s', 'moving on',
      'first', 'second', 'finally',
      'but', 'however', 'although'
    ];
    return indicators.some(i => text.toLowerCase().includes(i));
  }

  @MCPFunction({
    description: 'Get personalized video recommendations',
    parameters: {
      type: 'object',
      properties: {
        videoId: { type: 'string' },
        maxResults: { type: 'number' }
      },
      required: ['videoId']
    }
  })
  async getRecommendations({ 
    videoId, 
    maxResults = 10 
  }: { 
    videoId: string, 
    maxResults?: number 
  }): Promise<any[]> {
    try {
      const [videoDetails, topics] = await Promise.all([
        this.youtube.videos.list({
          part: ['snippet', 'topicDetails'],
          id: [videoId]
        }),
        this.extractTopics({ videoId })
      ]);

      const video = videoDetails.data.items?.[0];
      const topicIds = video.topicDetails?.topicIds || [];
      const categoryId = video.snippet?.categoryId;

      const response = await this.youtube.search.list({
        part: ['snippet'],
        relatedToVideoId: videoId,
        type: ['video'],
        videoCategoryId: categoryId,
        maxResults,
        topicId: topicIds[0] // Use primary topic
      });

      const recommendations = response.data.items?.map(item => {
        const relevanceScore = this.calculateRelevance(
          item.snippet?.title || '',
          item.snippet?.description || '',
          topics
        );
        return {
          ...item,
          relevanceScore
        };
      }) || [];

      return recommendations.sort((a, b) => b.relevanceScore - a.relevanceScore);
    } catch (error) {
      throw new Error(`Failed to get recommendations: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  private calculateRelevance(title: string, description: string, topics: any[]): number {
    let score = 0;
    const content = (title + ' ' + description).toLowerCase();
    
    topics.forEach(topic => {
      if (content.includes(topic.name.toLowerCase())) {
        score += topic.salience * 2;
      }
    });

    return score;
  }
}