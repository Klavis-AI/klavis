import { randomBytes } from 'crypto';

export interface ListSession {
  listId: string;
  channelId: string;
  maxResults: number;
  sortOrder: 'newest' | 'oldest' | 'popular';
  totalPages: number;
  uploadsPlaylistId: string;
  channelTitle: string;
  createdAt: Date;
  pageTokens: Map<number, string>; // page number -> pageToken
}

export class ListManager {
  private static instance: ListManager;
  private sessions: Map<string, ListSession> = new Map();
  private readonly sessionTimeout = 30 * 60 * 1000; // 30 minutes

  private constructor() {
    // Clean up expired sessions every 10 minutes
    setInterval(() => this.cleanupExpiredSessions(), 10 * 60 * 1000);
  }

  static getInstance(): ListManager {
    if (!ListManager.instance) {
      ListManager.instance = new ListManager();
    }
    return ListManager.instance;
  }

  /**
   * Create a new list session
   */
  createSession(
    channelId: string,
    maxResults: number,
    sortOrder: 'newest' | 'oldest' | 'popular',
    uploadsPlaylistId: string,
    channelTitle: string,
    totalResults: number
  ): string {
    const listId = this.generateListId();
    const totalPages = Math.ceil(totalResults / maxResults);
    
    const session: ListSession = {
      listId,
      channelId,
      maxResults,
      sortOrder,
      totalPages,
      uploadsPlaylistId,
      channelTitle,
      createdAt: new Date(),
      pageTokens: new Map([[1, '']]) // First page has no token
    };

    this.sessions.set(listId, session);
    return listId;
  }

  /**
   * Get session by list ID
   */
  getSession(listId: string): ListSession | null {
    const session = this.sessions.get(listId);
    if (!session) return null;

    // Check if session is expired
    if (Date.now() - session.createdAt.getTime() > this.sessionTimeout) {
      this.sessions.delete(listId);
      return null;
    }

    return session;
  }

  /**
   * Update session with page token
   */
  updatePageToken(listId: string, pageNumber: number, pageToken: string): void {
    const session = this.sessions.get(listId);
    if (session) {
      session.pageTokens.set(pageNumber, pageToken);
    }
  }

  /**
   * Get page token for specific page
   */
  getPageToken(listId: string, pageNumber: number): string | null {
    const session = this.sessions.get(listId);
    if (!session) return null;
    
    return session.pageTokens.get(pageNumber) || null;
  }

  /**
   * Delete session
   */
  deleteSession(listId: string): void {
    this.sessions.delete(listId);
  }

  private generateListId(): string {
    return 'list_' + randomBytes(8).toString('hex');
  }

  private cleanupExpiredSessions(): void {
    const now = Date.now();
    for (const [listId, session] of this.sessions.entries()) {
      if (now - session.createdAt.getTime() > this.sessionTimeout) {
        this.sessions.delete(listId);
      }
    }
  }
}