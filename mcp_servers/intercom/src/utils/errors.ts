export interface JsonRpcError {
  jsonrpc: '2.0';
  error: {
    code: number;
    message: string;
    data?: any;
  };
  id: null;
}

export function createErrorResponse(code: number, message: string, data?: any): JsonRpcError {
  return {
    jsonrpc: '2.0',
    error: {
      code,
      message,
      data,
    },
    id: null,
  };
}

// Intercom-specific error codes and helpers
export const IntercomErrorCodes = {
  // Authentication errors
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,

  // Resource errors
  NOT_FOUND: 404,
  CONFLICT: 409,

  // Rate limiting
  RATE_LIMITED: 429,

  // Server errors
  INTERNAL_SERVER_ERROR: 500,
  SERVICE_UNAVAILABLE: 503,

  // Client errors
  BAD_REQUEST: 400,
  UNPROCESSABLE_ENTITY: 422,

  // Custom MCP errors
  INVALID_CONTACT_ID: 1001,
  INVALID_CONVERSATION_ID: 1002,
  INVALID_COMPANY_ID: 1003,
  INVALID_MESSAGE_ID: 1004,
  INVALID_TAG_ID: 1005,
  INVALID_ARTICLE_ID: 1006,
  MISSING_REQUIRED_FIELD: 1007,
  INVALID_SEARCH_QUERY: 1008,
} as const;

// Helper functions for common Intercom errors
export function createUnauthorizedError(message = 'Invalid Intercom access token'): JsonRpcError {
  return createErrorResponse(IntercomErrorCodes.UNAUTHORIZED, message);
}

export function createNotFoundError(resource: string, id?: string): JsonRpcError {
  const message = id ? `${resource} with ID ${id} not found` : `${resource} not found`;
  return createErrorResponse(IntercomErrorCodes.NOT_FOUND, message);
}

export function createRateLimitError(message = 'Intercom API rate limit exceeded'): JsonRpcError {
  return createErrorResponse(IntercomErrorCodes.RATE_LIMITED, message);
}

export function createValidationError(field: string, message?: string): JsonRpcError {
  const errorMessage = message || `Invalid or missing required field: ${field}`;
  return createErrorResponse(IntercomErrorCodes.MISSING_REQUIRED_FIELD, errorMessage, { field });
}

export function createIntercomApiError(
  status: number,
  statusText: string,
  details?: any,
): JsonRpcError {
  return createErrorResponse(status, `Intercom API error: ${status} ${statusText}`, details);
}
