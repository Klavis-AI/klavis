import { google } from 'googleapis';
import { ChannelParams, ChannelVideosParams, ChannelVideosNavParams } from '../types.js';
import { ListManager } from './listManager.js';
import { removeThumbnails, createErrorMessage } from '../utils/dataUtils.js';
import { getApiKey } from '../auth.js';

/**
 * Service for interacting with YouTube channels
 */
export class ChannelService {
  private youtube;
  private initialized = false;
  private listManager = ListManager.getInstance();

  constructor() {
    // Don't initialize in constructor
  }

  /**
   * Initialize the YouTube client only when needed
   */
  private initialize() {
    if (this.initialized) return;

    const apiKey = getApiKey();
    if (!apiKey) {
      throw new Error('YouTube API key is missing. Provide it via AUTH_DATA env var or x-auth-data header.');
    }

    this.youtube = google.youtube({
      version: 'v3',
      auth: apiKey
    });

    this.initialized = true;
  }

  /**
   * Get channel details
   */
  async getChannel({ 
    channelId 
  }: ChannelParams): Promise<any> {
    try {
      this.initialize();
      
      const response = await this.youtube.channels.list({
        part: ['snippet', 'statistics', 'contentDetails'],
        id: [channelId]
      });

      const channel = response.data.items?.[0] || null;
      return removeThumbnails(channel);
    } catch (error) {
      throw new Error(createErrorMessage('get channel', error));
    }
  }

  /**
   * Get channel playlists
   */
  async getPlaylists({ 
    channelId, 
    maxResults = 50 
  }: ChannelVideosParams): Promise<any[]> {
    try {
      this.initialize();
      
      const response = await this.youtube.playlists.list({
        part: ['snippet', 'contentDetails'],
        channelId,
        maxResults
      });

      const playlists = response.data.items || [];
      return removeThumbnails(playlists);
    } catch (error) {
      throw new Error(createErrorMessage('get channel playlists', error));
    }
  }

  /**
   * Start a new channel videos list (creates a new list session)
   */
  async listVideos({ 
    channelId, 
    maxResults = 20,
    sortOrder = 'newest'
  }: ChannelVideosParams): Promise<any> {
    try {
      this.initialize();
      
      // Get channel details to find uploads playlist and total video count
      const channelResponse = await this.youtube.channels.list({
        part: ['contentDetails', 'snippet', 'statistics'],
        id: [channelId]
      });

      const channelData = channelResponse.data.items?.[0];
      if (!channelData) {
        throw new Error(`Channel not found: ${channelId}`);
      }

      const uploadsPlaylistId = channelData.contentDetails?.relatedPlaylists?.uploads;
      const channelTitle = channelData.snippet?.title || 'Unknown Channel';
      const totalVideoCount = parseInt(channelData.statistics?.videoCount || '0');

      if (!uploadsPlaylistId) {
        throw new Error(`No uploads playlist found for channel: ${channelId}`);
      }

      // Create list session
      const listId = this.listManager.createSession(
        channelId,
        maxResults,
        sortOrder,
        uploadsPlaylistId,
        channelTitle,
        totalVideoCount
      );

      // Get first page
      const firstPageResult = await this.getVideosPage(listId, 1);

      return {
        listId,
        channelId,
        channelTitle,
        sortOrder,
        currentPage: 1,
        totalPages: Math.ceil(totalVideoCount / maxResults),
        pageSize: maxResults,
        totalVideos: totalVideoCount,
        ...firstPageResult
      };
    } catch (error) {
      throw new Error(createErrorMessage('list channel videos', error));
    }
  }

  /**
   * Navigate within an existing list session
   */
  async navigateList({
    listId,
    page
  }: ChannelVideosNavParams): Promise<any> {
    try {
      this.initialize();
      
      const session = this.listManager.getSession(listId);
      if (!session) {
        throw new Error(`List session expired or not found: ${listId}`);
      }

      if (page < 1 || page > session.totalPages) {
        throw new Error(`Invalid page number: ${page}. Valid range: 1-${session.totalPages}`);
      }

      const pageResult = await this.getVideosPage(listId, page);

      return {
        listId,
        channelId: session.channelId,
        channelTitle: session.channelTitle,
        sortOrder: session.sortOrder,
        currentPage: page,
        totalPages: session.totalPages,
        pageSize: session.maxResults,
        ...pageResult
      };
    } catch (error) {
      throw new Error(createErrorMessage('navigate list', error));
    }
  }

  /**
   * Get videos for a specific page within a list session
   */
  private async getVideosPage(listId: string, page: number): Promise<any> {
    const session = this.listManager.getSession(listId);
    if (!session) {
      throw new Error(`List session not found: ${listId}`);
    }

    // Check if we already have the page token for this page
    let pageToken = this.listManager.getPageToken(listId, page);
    
    // If we don't have the token for this exact page, we need to calculate it
    if (pageToken === null && page > 1) {
      // We need to navigate through pages to get the correct token
      pageToken = await this.calculatePageToken(session, page);
    }

    const playlistResponse = await this.youtube.playlistItems.list({
      part: ['snippet', 'contentDetails'],
      playlistId: session.uploadsPlaylistId,
      maxResults: session.maxResults,
      pageToken: pageToken || undefined,
    });

    // Store next page token if available
    if (playlistResponse.data.nextPageToken && page < session.totalPages) {
      this.listManager.updatePageToken(listId, page + 1, playlistResponse.data.nextPageToken);
    }

    const videoIds = playlistResponse.data.items?.map(item => 
      item.contentDetails?.videoId
    ).filter(Boolean) || [];

    let videosWithDetails = [];
    if (videoIds.length > 0) {
      const videosResponse = await this.youtube.videos.list({
        part: ['snippet', 'statistics', 'contentDetails'],
        id: videoIds
      });
      videosWithDetails = videosResponse.data.items || [];
    }

    // Apply sorting based on session sortOrder
    videosWithDetails = this.sortVideos(videosWithDetails, session.sortOrder);

    // Remove thumbnails from video data
    const cleanedVideos = removeThumbnails(videosWithDetails);

    return {
      videos: cleanedVideos,
      hasNextPage: page < session.totalPages,
      hasPrevPage: page > 1
    };
  }

  /**
   * Calculate page token for a specific page by navigating through previous pages
   */
  private async calculatePageToken(session: any, targetPage: number): Promise<string> {
    let currentPage = 1;
    let pageToken = '';

    while (currentPage < targetPage) {
      // Check if we have a cached token for the next page
      const cachedToken = this.listManager.getPageToken(session.listId, currentPage + 1);
      if (cachedToken !== null) {
        pageToken = cachedToken;
        currentPage++;
        continue;
      }

      // Fetch current page to get next page token
      const response = await this.youtube.playlistItems.list({
        part: ['contentDetails'],
        playlistId: session.uploadsPlaylistId,
        maxResults: session.maxResults,
        pageToken: pageToken || undefined,
      });

      if (response.data.nextPageToken) {
        pageToken = response.data.nextPageToken;
        this.listManager.updatePageToken(session.listId, currentPage + 1, pageToken);
      } else {
        break; // No more pages
      }
      currentPage++;
    }

    return pageToken;
  }

  /**
   * Sort videos based on sort order
   */
  private sortVideos(videos: any[], sortOrder: 'newest' | 'oldest' | 'popular'): any[] {
    switch (sortOrder) {
      case 'newest':
        // Default order from uploads playlist is already newest first
        return videos;
      case 'oldest':
        return videos.reverse();
      case 'popular':
        return videos.sort((a, b) => {
          const aViews = parseInt(a.statistics?.viewCount || '0');
          const bViews = parseInt(b.statistics?.viewCount || '0');
          return bViews - aViews; // Most views first
        });
      default:
        return videos;
    }
  }

  /**
   * Get channel statistics
   */
  async getStatistics({ 
    channelId 
  }: ChannelParams): Promise<any> {
    try {
      this.initialize();
      
      const response = await this.youtube.channels.list({
        part: ['statistics'],
        id: [channelId]
      });

      return response.data.items?.[0]?.statistics || null;
    } catch (error) {
      throw new Error(createErrorMessage('get channel statistics', error));
    }
  }
}