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

// Define VideoFormat type
type VideoFormat = 'mp4' | 'mp3' | 'wav';

export class VideoDownloader implements MCPFunctionGroup {
  @MCPFunction({
    description: 'Download video in specified format',
    parameters: {
      type: 'object',
      properties: {
        videoId: { type: 'string' },
        format: { type: 'string', enum: ['mp4', 'mp3', 'wav'] },
        quality: { type: 'string', enum: ['highest', 'lowest', '1080p', '720p', '480p', '360p'] }
      },
      required: ['videoId', 'format']
    }
  })
  async downloadVideo({ 
    videoId, 
    format = 'mp4', 
    quality = 'highest' 
  }: { 
    videoId: string, 
    format?: VideoFormat, 
    quality?: string 
  }): Promise<string> {
    try {
      const info = await ytdl.getInfo(videoId);
      const outputDir = path.join(process.cwd(), 'downloads');
      await fs.mkdir(outputDir, { recursive: true });
      
      const outputPath = path.join(
        outputDir,
        `${videoId}-${Date.now()}.${format}`
      );
      
      if (format === 'mp4') {
        await this.downloadVideoFormat(info, outputPath, quality);
      } else {
        await this.downloadAudioFormat(info, outputPath, format);
      }
      
      return outputPath;
    } catch (error) {
      throw new Error(`Failed to download video: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  @MCPFunction({
    description: 'Extract video thumbnail',
    parameters: {
      type: 'object',
      properties: {
        videoId: { type: 'string' },
        timestamp: { type: 'number' }
      },
      required: ['videoId']
    }
  })
  async extractThumbnail({ 
    videoId, 
    timestamp = 0 
  }: { 
    videoId: string, 
    timestamp?: number 
  }): Promise<string> {
    try {
      const outputDir = path.join(process.cwd(), 'thumbnails');
      await fs.mkdir(outputDir, { recursive: true });
      
      const outputPath = path.join(
        outputDir,
        `${videoId}-${timestamp}-${Date.now()}.jpg`
      );
      
      await this.extractFrameAtTimestamp(videoId, timestamp, outputPath);
      return outputPath;
    } catch (error) {
      throw new Error(`Failed to extract thumbnail: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  @MCPFunction({
    description: 'Get video download options',
    parameters: {
      type: 'object',
      properties: {
        videoId: { type: 'string' }
      },
      required: ['videoId']
    }
  })
  async getDownloadOptions({ 
    videoId 
  }: { 
    videoId: string 
  }): Promise<any> {
    try {
      const info = await ytdl.getInfo(videoId);
      const videoFormats = info.formats
        .filter(f => f.container === 'mp4')
        .map(format => ({
          quality: `${format.height}p`,
          fps: format.fps,
          filesize: format.contentLength ? parseInt(format.contentLength) : null,
          mimeType: format.mimeType
        }))
        .sort((a, b) => (b.quality ? parseInt(b.quality) : 0) - (a.quality ? parseInt(a.quality) : 0));

      const audioFormats = info.formats
        .filter(f => f.mimeType.includes('audio'))
        .map(format => ({
          audioQuality: format.audioBitrate,
          mimeType: format.mimeType
        }));

      return {
        videoDetails: {
          title: info.videoDetails.title,
          lengthSeconds: parseInt(info.videoDetails.lengthSeconds),
          thumbnails: info.videoDetails.thumbnails
        },
        videoFormats,
        audioFormats
      };
    } catch (error) {
      throw new Error(`Failed to get download options: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  private async downloadVideoFormat(info: ytdl.videoInfo, outputPath: string, quality: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const format = this.getBestFormat(info, quality);
      const video = ytdl(info.videoDetails.videoId, { format });
      
      ffmpeg(video)
        .toFormat('mp4')
        .on('end', () => resolve())
        .on('error', (err) => reject(err))
        .save(outputPath);
    });
  }

  private async downloadAudioFormat(info: ytdl.videoInfo, outputPath: string, format: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const video = ytdl(info.videoDetails.videoId, {
        quality: 'highestaudio',
        filter: 'audioonly'
      });
      
      ffmpeg(video)
        .toFormat(format)
        .on('end', () => resolve())
        .on('error', (err) => reject(err))
        .save(outputPath);
    });
  }

  private async extractFrameAtTimestamp(videoId: string, timestamp: number, outputPath: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const video = ytdl(videoId);
      
      ffmpeg(video)
        .screenshots({
          timestamps: [timestamp],
          filename: path.basename(outputPath),
          folder: path.dirname(outputPath)
        })
        .on('end', () => resolve())
        .on('error', (err) => reject(err));
    });
  }

  private getBestFormat(info: ytdl.videoInfo, quality: string): ytdl.videoFormat {
    const formats = info.formats.filter(f => f.container === 'mp4');
    
    if (quality === 'highest') {
      return formats.sort((a, b) => (b.height || 0) - (a.height || 0))[0];
    }
    
    if (quality === 'lowest') {
      return formats.sort((a, b) => (a.height || 0) - (b.height || 0))[0];
    }
    
    const targetHeight = parseInt(quality);
    return formats
      .sort((a, b) => 
        Math.abs((a.height || 0) - targetHeight) - Math.abs((b.height || 0) - targetHeight)
      )[0];
  }
}