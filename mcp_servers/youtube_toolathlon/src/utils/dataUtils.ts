/**
 * Utility functions for data formatting and error handling
 */

/**
 * Remove thumbnails from YouTube API response data
 */
export function removeThumbnails(data: any): any {
  if (!data) return data;
  
  if (Array.isArray(data)) {
    return data.map(item => removeThumbnails(item));
  }
  
  if (typeof data === 'object') {
    const cleaned = { ...data };
    
    // Remove thumbnails from snippet
    if (cleaned.snippet?.thumbnails) {
      delete cleaned.snippet.thumbnails;
    }
    
    // Recursively clean nested objects
    for (const key in cleaned) {
      if (typeof cleaned[key] === 'object' && cleaned[key] !== null) {
        cleaned[key] = removeThumbnails(cleaned[key]);
      }
    }
    
    return cleaned;
  }
  
  return data;
}

/**
 * Standardized error message format
 */
export function createErrorMessage(operation: string, error: unknown): string {
  const message = error instanceof Error ? error.message : String(error);
  return `Failed to ${operation}: ${message}`;
}

/**
 * Standard response wrapper for consistent data structure
 */
export interface StandardResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  timestamp: string;
}

/**
 * Create a standardized success response
 */
export function createSuccessResponse<T>(data: T): StandardResponse<T> {
  return {
    success: true,
    data: removeThumbnails(data),
    timestamp: new Date().toISOString()
  };
}

/**
 * Create a standardized error response
 */
export function createErrorResponse(operation: string, error: unknown): StandardResponse {
  return {
    success: false,
    error: createErrorMessage(operation, error),
    timestamp: new Date().toISOString()
  };
}