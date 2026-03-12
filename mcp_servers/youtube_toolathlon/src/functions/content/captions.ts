import { MCPFunction, MCPFunctionGroup } from "@modelcontextprotocol/sdk";
import { YoutubeTranscript } from "youtube-transcript";
import * as ytdl from "ytdl-core";
import * as fs from "fs/promises";
import * as path from 'path';
import ffmpeg from 'fluent-ffmpeg';

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

export class CaptionManager implements MCPFunctionGroup {
  // [Previous methods remain the same]

  private async uploadCaptions(videoId: string, captions: string, language: string): Promise<void> {
    const name = `${language}_${Date.now()}.srt`;
    const tmpPath = path.join(process.cwd(), 'temp', name);
    
    await fs.mkdir(path.dirname(tmpPath), { recursive: true });
    await fs.writeFile(tmpPath, captions);

    await this.youtube.captions.insert({
      part: ['snippet'],
      requestBody: {
        snippet: {
          videoId,
          language,
          name,
          isDraft: false
        }
      },
      media: {
        body: fs.createReadStream(tmpPath)
      }
    });

    await fs.unlink(tmpPath);
  }

  private async getCaptionTracks(videoId: string): Promise<any[]> {
    const response = await this.youtube.captions.list({
      part: ['snippet'],
      videoId
    });
    return response.data.items || [];
  }

  private async generateTranslations(videoId: string, languages: string[], sourceCaptions: string): Promise<void> {
    for (const language of languages) {
      const translated = await this.translateCaptions(sourceCaptions, language);
      await this.uploadCaptions(videoId, translated, language);
    }
  }

  private async translateCaptions(captions: string, targetLanguage: string): Promise<string> {
    const lines = captions.split('\n');
    let output = '';
    let isText = false;

    for (const line of lines) {
      if (line.trim() === '') {
        output += '\n';
        isText = false;
        continue;
      }

      if (/^\d+$/.test(line.trim()) || /^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$/.test(line.trim())) {
        output += line + '\n';
        isText = false;
      } else if (isText || !line.includes('-->')) {
        const [translation] = await this.translateClient.translate(line, targetLanguage);
        output += translation + '\n';
        isText = true;
      } else {
        output += line + '\n';
      }
    }

    return output;
  }

  private formatTime(seconds: number): string {
    const pad = (n: number) => n.toString().padStart(2, '0');
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    const ms = Math.floor((seconds % 1) * 1000);
    return `${pad(h)}:${pad(m)}:${pad(s)},${ms.toString().padStart(3, '0')}`;
  }

  private calculateSimilarity(str1: string, str2: string): number {
    const len1 = str1.length;
    const len2 = str2.length;
    const matrix = Array(len1 + 1).fill(null).map(() => Array(len2 + 1).fill(0));

    for (let i = 0; i <= len1; i++) matrix[i][0] = i;
    for (let j = 0; j <= len2; j++) matrix[0][j] = j;

    for (let i = 1; i <= len1; i++) {
      for (let j = 1; j <= len2; j++) {
        const cost = str1[i - 1] === str2[j - 1] ? 0 : 1;
        matrix[i][j] = Math.min(
          matrix[i - 1][j] + 1,      // deletion
          matrix[i][j - 1] + 1,      // insertion
          matrix[i - 1][j - 1] + cost // substitution
        );
      }
    }

    const maxLen = Math.max(len1, len2);
    return 1 - matrix[len1][len2] / maxLen;
  }

  // Optional additional methods for advanced caption management
  @MCPFunction({
    description: 'Analyze caption quality and complexity',
    parameters: {
      type: 'object',
      properties: {
        videoId: { type: 'string' }
      },
      required: ['videoId']
    }
  })
  async analyzeCaptionQuality({ 
    videoId 
  }: { 
    videoId: string 
  }): Promise<any> {
    try {
      const captionTracks = await this.getCaptionTracks(videoId);
      
      const qualityAnalysis = await Promise.all(captionTracks.map(async (track) => {
        const captionContent = await this.downloadCaptionTrack(track);
        return {
          language: track.snippet.language,
          complexity: this.calculateCaptionComplexity(captionContent),
          readingSpeed: this.calculateReadingSpeed(captionContent),
          wordCount: this.countWords(captionContent)
        };
      }));

      return {
        videoId,
        captionQuality: qualityAnalysis
      };
    } catch (error) {
      throw new Error(`Failed to analyze caption quality: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  private async downloadCaptionTrack(track: any): Promise<string> {
    const response = await this.youtube.captions.download({
      id: track.id,
      tfmt: 'srt'
    });
    return response.data;
  }

  private calculateCaptionComplexity(captions: string): number {
    const lines = captions.split('\n').filter(line => 
      !line.trim().match(/^\d+$/) && 
      !line.trim().match(/^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$/)
    );

    const totalChars = lines.join(' ').length;
    const uniqueWords = new Set(lines.join(' ').toLowerCase().split(/\s+/));
    
    return (uniqueWords.size / totalChars) * 1000; // Lexical density metric
  }

  private calculateReadingSpeed(captions: string): number {
    const lines = captions.split('\n').filter(line => 
      !line.trim().match(/^\d+$/) && 
      !line.trim().match(/^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$/)
    );

    const wordCount = lines.join(' ').split(/\s+/).length;
    const estimatedReadTime = lines.length * 2; // Assume 2 seconds per caption line

    return wordCount / estimatedReadTime; // Words per second
  }

  private countWords(captions: string): number {
    const lines = captions.split('\n').filter(line => 
      !line.trim().match(/^\d+$/) && 
      !line.trim().match(/^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$/)
    );

    return lines.join(' ').split(/\s+/).length;
  }
}