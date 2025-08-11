/**
 * Custom error classes for Fireflies MCP Server
 */

export class FirefliesError extends Error {
  public readonly code: string;
  public readonly statusCode: number | undefined;
  public readonly details: any | undefined;

  constructor(
    message: string,
    code: string = 'FIREFLIES_ERROR',
    statusCode?: number,
    details?: any,
  ) {
    super(message);
    this.name = 'FirefliesError';
    this.code = code;
    this.statusCode = statusCode;
    this.details = details;

    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, FirefliesError);
    }
  }
}

export class FirefliesAPIError extends FirefliesError {
  constructor(message: string, statusCode?: number, details?: any) {
    super(message, 'FIREFLIES_API_ERROR', statusCode, details);
    this.name = 'FirefliesAPIError';
  }
}

export class FirefliesAuthError extends FirefliesError {
  constructor(message: string = 'Authentication failed') {
    super(message, 'FIREFLIES_AUTH_ERROR', 401);
    this.name = 'FirefliesAuthError';
  }
}

export class FirefliesValidationError extends FirefliesError {
  constructor(message: string, field?: string) {
    super(message, 'FIREFLIES_VALIDATION_ERROR', 400, { field });
    this.name = 'FirefliesValidationError';
  }
}

export class FirefliesNotFoundError extends FirefliesError {
  constructor(resource: string, id?: string) {
    const message = id ? `${resource} with ID '${id}' not found` : `${resource} not found`;
    super(message, 'FIREFLIES_NOT_FOUND_ERROR', 404, { resource, id });
    this.name = 'FirefliesNotFoundError';
  }
}

export class FirefliesRateLimitError extends FirefliesError {
  constructor(retryAfter?: number) {
    super('Rate limit exceeded', 'FIREFLIES_RATE_LIMIT_ERROR', 429, { retryAfter });
    this.name = 'FirefliesRateLimitError';
  }
}

export class FirefliesConnectionError extends FirefliesError {
  constructor(message: string = 'Connection to Fireflies API failed') {
    super(message, 'FIREFLIES_CONNECTION_ERROR', 503);
    this.name = 'FirefliesConnectionError';
  }
}

export class FirefliesTimeoutError extends FirefliesError {
  constructor(timeout: number) {
    super(`Request timed out after ${timeout}ms`, 'FIREFLIES_TIMEOUT_ERROR', 408, { timeout });
    this.name = 'FirefliesTimeoutError';
  }
}

/**
 * Type for formatted error response
 */
interface FormattedError {
  success: false;
  error: {
    message: string;
    code: string;
    statusCode?: number;
    details?: any;
  };
  timestamp: string;
}

/**
 * Error handler utility functions
 */
export class ErrorHandler {
  /**
   * Convert unknown error to FirefliesError
   */
  static toFirefliesError(error: unknown): FirefliesError {
    if (error instanceof FirefliesError) {
      return error;
    }

    if (error instanceof Error) {
      if (error.message.includes('GraphQL')) {
        return new FirefliesAPIError(`GraphQL Error: ${error.message}`);
      }

      const httpMatch = error.message.match(/(\d{3})/);
      if (httpMatch) {
        const statusCode = parseInt(httpMatch[1]);
        switch (statusCode) {
          case 401:
            return new FirefliesAuthError(error.message);
          case 404:
            return new FirefliesNotFoundError('Resource');
          case 429:
            return new FirefliesRateLimitError();
          default:
            return new FirefliesAPIError(error.message, statusCode);
        }
      }

      return new FirefliesError(error.message);
    }

    if (typeof error === 'string') {
      return new FirefliesError(error);
    }

    return new FirefliesError('An unknown error occurred', 'UNKNOWN_ERROR');
  }

  /**
   * Format error for MCP response with explicit type handling
   */
  static formatForMCP(error: FirefliesError | Error): FormattedError {
    const firefliesError =
      error instanceof FirefliesError ? error : ErrorHandler.toFirefliesError(error);

    const errorResponse: FormattedError = {
      success: false,
      error: {
        message: firefliesError.message,
        code: firefliesError.code,
      },
      timestamp: new Date().toISOString(),
    };

    if (firefliesError.statusCode !== undefined) {
      errorResponse.error.statusCode = firefliesError.statusCode;
    }

    if (firefliesError.details !== undefined) {
      errorResponse.error.details = firefliesError.details;
    }

    return errorResponse;
  }

  /**
   * Check if error is retryable
   */
  static isRetryable(error: FirefliesError): boolean {
    const retryableCodes = [
      'FIREFLIES_CONNECTION_ERROR',
      'FIREFLIES_TIMEOUT_ERROR',
      'FIREFLIES_RATE_LIMIT_ERROR',
    ];

    const retryableStatusCodes = [429, 500, 502, 503, 504];

    return (
      retryableCodes.includes(error.code) ||
      (error.statusCode !== undefined && retryableStatusCodes.includes(error.statusCode))
    );
  }

  /**
   * Get retry delay for retryable errors
   */
  static getRetryDelay(error: FirefliesError, attempt: number = 1): number {
    if (error instanceof FirefliesRateLimitError && error.details?.retryAfter) {
      return error.details.retryAfter * 1000;
    }

    return Math.min(1000 * Math.pow(2, attempt - 1), 30000);
  }
}

/**
 * Error code constants
 */
export const ERROR_CODES = {
  UNKNOWN: 'UNKNOWN_ERROR',
  VALIDATION: 'FIREFLIES_VALIDATION_ERROR',

  API_ERROR: 'FIREFLIES_API_ERROR',
  AUTH_ERROR: 'FIREFLIES_AUTH_ERROR',
  NOT_FOUND: 'FIREFLIES_NOT_FOUND_ERROR',
  RATE_LIMIT: 'FIREFLIES_RATE_LIMIT_ERROR',

  CONNECTION: 'FIREFLIES_CONNECTION_ERROR',
  TIMEOUT: 'FIREFLIES_TIMEOUT_ERROR',

  TRANSCRIPT_NOT_FOUND: 'TRANSCRIPT_NOT_FOUND',
  MEETING_NOT_FOUND: 'MEETING_NOT_FOUND',
  EXPORT_FAILED: 'EXPORT_FAILED',
  SEARCH_FAILED: 'SEARCH_FAILED',
} as const;

/**
 * HTTP status code constants
 */
export const HTTP_STATUS = {
  OK: 200,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  TIMEOUT: 408,
  TOO_MANY_REQUESTS: 429,
  INTERNAL_SERVER_ERROR: 500,
  BAD_GATEWAY: 502,
  SERVICE_UNAVAILABLE: 503,
  GATEWAY_TIMEOUT: 504,
} as const;

/**
 * Utility function to create standardized error responses
 */
export function createErrorResponse(error: unknown, tool?: string) {
  const firefliesError = ErrorHandler.toFirefliesError(error);
  const formattedError = ErrorHandler.formatForMCP(firefliesError);

  const response = {
    content: [
      {
        type: 'text' as const,
        text: JSON.stringify(
          {
            ...formattedError,
            ...(tool !== undefined && { tool }),
          },
          null,
          2,
        ),
      },
    ],
    isError: true,
  };

  return response;
}
