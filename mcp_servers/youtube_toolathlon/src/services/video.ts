import { google } from 'googleapis';
import { VideoParams, SearchParams, TrendingParams, RelatedVideosParams } from '../types.js';
import { removeThumbnails, createErrorMessage } from '../utils/dataUtils.js';
import { getAccessToken } from '../auth.js';

/**
 * Service for interacting with YouTube videos
 */
export class VideoService {
  private youtube;
  private initialized = false;

  constructor() {
    // Don't initialize in constructor
  }

  /**
   * Initialize the YouTube client only when needed
   */
  private initialize() {
    if (this.initialized) return;

    const accessToken = getAccessToken();
    if (!accessToken) {
      throw new Error('OAuth access token is missing. Provide it via AUTH_DATA env var or x-auth-data header.');
    }

    const oauth2Client = new google.auth.OAuth2();
    oauth2Client.setCredentials({ access_token: accessToken });

    this.youtube = google.youtube({
      version: 'v3',
      auth: oauth2Client,
    });

    this.initialized = true;
  }

  /**
   * Get detailed information about a YouTube video
   */
  async getVideo({ 
    videoId, 
    parts = ['snippet', 'contentDetails', 'statistics'] 
  }: VideoParams): Promise<any> {
    try {
      this.initialize();
      
      const response = await this.youtube.videos.list({
        part: parts,
        id: [videoId]
      });
      
      const video = response.data.items?.[0] || null;
      return removeThumbnails(video);
    } catch (error) {
      throw new Error(createErrorMessage('get video', error));
    }
  }

  /**
   * Search for videos on YouTube
   */
  async searchVideos({ 
    query, 
    maxResults = 10 
  }: SearchParams): Promise<any[]> {
    try {
      this.initialize();
      
      const response = await this.youtube.search.list({
        part: ['snippet'],
        q: query,
        maxResults,
        type: ['video']
      });
      
      const searchItems = response.data.items || [];
      
      // Get detailed video information including statistics and duration
      const videoIds = searchItems
        .map(item => item.id?.videoId)
        .filter(Boolean);

      if (videoIds.length === 0) {
        return [];
      }

      const videosResponse = await this.youtube.videos.list({
        part: ['snippet', 'statistics', 'contentDetails'],
        id: videoIds
      });

      const detailedVideos = videosResponse.data.items || [];
      return removeThumbnails(detailedVideos);
    } catch (error) {
      throw new Error(createErrorMessage('search videos', error));
    }
  }

  /**
   * Get video statistics like views, likes, and comments
   */
  async getVideoStats({ 
    videoId 
  }: { videoId: string }): Promise<any> {
    try {
      this.initialize();
      
      const response = await this.youtube.videos.list({
        part: ['statistics'],
        id: [videoId]
      });
      
      return response.data.items?.[0]?.statistics || null;
    } catch (error) {
      throw new Error(createErrorMessage('get video stats', error));
    }
  }

  /**
   * Get trending videos
   */
  async getTrendingVideos({ 
    regionCode = 'US', 
    maxResults = 10,
    videoCategoryId = ''
  }: TrendingParams): Promise<any[]> {
    try {
      this.initialize();
      
      const params: any = {
        part: ['snippet', 'contentDetails', 'statistics'],
        chart: 'mostPopular',
        regionCode,
        maxResults
      };
      
      if (videoCategoryId) {
        params.videoCategoryId = videoCategoryId;
      }
      
      const response = await this.youtube.videos.list(params);
      const items = response.data.items || [];
      return removeThumbnails(items);
    } catch (error) {
      throw new Error(createErrorMessage('get trending videos', error));
    }
  }

  /**
   * Get related videos for a specific video
   */
  async getRelatedVideos({ 
    videoId, 
    maxResults = 10 
  }: RelatedVideosParams): Promise<any[]> {
    try {
      this.initialize();
      
      const response = await this.youtube.search.list({
        part: ['snippet'],
        relatedToVideoId: videoId,
        maxResults,
        type: ['video']
      });
      
      const items = response.data.items || [];
      return removeThumbnails(items);
    } catch (error) {
      throw new Error(createErrorMessage('get related videos', error));
    }
  }
}