import { google } from 'googleapis';
import { PlaylistParams, PlaylistItemsParams, SearchParams } from '../types.js';
import { removeThumbnails, createErrorMessage } from '../utils/dataUtils.js';

/**
 * Service for interacting with YouTube playlists
 */
export class PlaylistService {
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
    
    const apiKey = process.env.YOUTUBE_API_KEY;
    if (!apiKey) {
      throw new Error('YOUTUBE_API_KEY environment variable is not set.');
    }

    this.youtube = google.youtube({
      version: "v3",
      auth: apiKey
    });
    
    this.initialized = true;
  }

  /**
   * Get information about a YouTube playlist
   */
  async getPlaylist({ 
    playlistId 
  }: PlaylistParams): Promise<any> {
    try {
      this.initialize();
      
      const response = await this.youtube.playlists.list({
        part: ['snippet', 'contentDetails', 'status'],
        id: [playlistId]
      });
      
      const playlist = response.data.items?.[0] || null;
      return removeThumbnails(playlist);
    } catch (error) {
      throw new Error(createErrorMessage('get playlist', error));
    }
  }

  /**
   * Get videos in a YouTube playlist with enhanced data and pagination support
   */
  async getPlaylistItems({ 
    playlistId, 
    maxResults = 50 
  }: PlaylistItemsParams): Promise<any> {
    try {
      this.initialize();
      
      const playlistResponse = await this.youtube.playlistItems.list({
        part: ['snippet', 'contentDetails', 'status'],
        playlistId,
        maxResults
      });

      const items = playlistResponse.data.items || [];
      
      // Get detailed video information for better data
      const videoIds = items
        .map(item => item.contentDetails?.videoId)
        .filter(Boolean);

      let videosWithDetails = [];
      if (videoIds.length > 0) {
        const videosResponse = await this.youtube.videos.list({
          part: ['snippet', 'statistics', 'contentDetails'],
          id: videoIds
        });
        videosWithDetails = videosResponse.data.items || [];
      }

      // Combine playlist item info with detailed video info
      const enhancedItems = items.map(playlistItem => {
        const videoDetails = videosWithDetails.find(
          video => video.id === playlistItem.contentDetails?.videoId
        );
        
        return {
          playlistItem: removeThumbnails(playlistItem),
          videoDetails: removeThumbnails(videoDetails) || null
        };
      });

      return {
        items: enhancedItems,
        totalResults: playlistResponse.data.pageInfo?.totalResults || items.length,
        nextPageToken: playlistResponse.data.nextPageToken,
        prevPageToken: playlistResponse.data.prevPageToken
      };
    } catch (error) {
      throw new Error(createErrorMessage('get playlist items', error));
    }
  }

  /**
   * Search for playlists on YouTube
   */
  async searchPlaylists({ 
    query, 
    maxResults = 10 
  }: SearchParams): Promise<any[]> {
    try {
      this.initialize();
      
      const response = await this.youtube.search.list({
        part: ['snippet'],
        q: query,
        maxResults,
        type: ['playlist']
      });
      
      const items = response.data.items || [];
      return removeThumbnails(items);
    } catch (error) {
      throw new Error(createErrorMessage('search playlists', error));
    }
  }
}