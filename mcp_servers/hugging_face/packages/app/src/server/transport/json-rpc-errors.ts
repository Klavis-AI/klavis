// json-rpc-errors.ts
export const JSON_RPC_ERROR_CODES = {
	// Standard JSON-RPC 2.0 error codes
	PARSE_ERROR: -32700,
	INVALID_REQUEST: -32600,
	METHOD_NOT_FOUND: -32601,
	INVALID_PARAMS: -32602,
	INTERNAL_ERROR: -32603,

	// Server error codes (-32000 to -32099)
	SERVER_ERROR: -32000,
	SESSION_NOT_FOUND: -32001,
	SERVER_SHUTTING_DOWN: -32002,
	SESSION_ALREADY_EXISTS: -32003,
	STALE_CONNECTION: -32004,
	AUTHENTICATION_FAILED: -32005,
} as const;

export type JsonRpcErrorCode = (typeof JSON_RPC_ERROR_CODES)[keyof typeof JSON_RPC_ERROR_CODES];

export interface JsonRpcError {
	jsonrpc: '2.0';
	error: {
		code: JsonRpcErrorCode;
		message: string;
		data?: unknown;
	};
	id: string | number | null;
}

/**
 * Create a JSON-RPC 2.0 error response
 */
export function createJsonRpcError(
	code: JsonRpcErrorCode,
	message: string,
	id: string | number | null = null,
	data?: unknown
): JsonRpcError {
	const error: JsonRpcError = {
		jsonrpc: '2.0',
		error: {
			code,
			message,
		},
		id,
	};

	if (data !== undefined) {
		error.error.data = data;
	}

	return error;
}

/**
 * Safely extract JSON-RPC ID from request body
 */
export function extractJsonRpcId(body: unknown): string | number | null {
	if (body && typeof body === 'object' && 'id' in body) {
		const id = (body as { id: unknown }).id;
		if (typeof id === 'string') {
			return id;
		}
		if (typeof id === 'number') {
			return id;
		}
		if (id === null) {
			return null;
		}
	}
	return null;
}

/**
 * Common error response factories
 */
export const JsonRpcErrors = {
	internalError: (id: string | number | null = null, details?: string) =>
		createJsonRpcError(JSON_RPC_ERROR_CODES.INTERNAL_ERROR, details || 'Internal server error', id),

	invalidParams: (message: string, id: string | number | null = null) =>
		createJsonRpcError(JSON_RPC_ERROR_CODES.INVALID_PARAMS, `Invalid params: ${message}`, id),

	sessionNotFound: (sessionId: string, id: string | number | null = null) =>
		createJsonRpcError(JSON_RPC_ERROR_CODES.SESSION_NOT_FOUND, 'Session not found', id, { sessionId }),

	serverShuttingDown: (id: string | number | null = null) =>
		createJsonRpcError(JSON_RPC_ERROR_CODES.SERVER_SHUTTING_DOWN, 'Server is shutting down', id),

	sessionAlreadyExists: (sessionId: string, id: string | number | null = null) =>
		createJsonRpcError(JSON_RPC_ERROR_CODES.SESSION_ALREADY_EXISTS, 'Session already exists', id, { sessionId }),

	methodNotAllowed: (id: string | number | null = null, message: string = 'Method not allowed') =>
		createJsonRpcError(JSON_RPC_ERROR_CODES.SERVER_ERROR, message, id),

	invalidRequest: (id: string | number | null = null, message: string = 'Invalid request') =>
		createJsonRpcError(JSON_RPC_ERROR_CODES.INVALID_REQUEST, message, id),

	authenticationFailed: (id: string | number | null = null, message: string = 'Authentication failed') =>
		createJsonRpcError(JSON_RPC_ERROR_CODES.AUTHENTICATION_FAILED, message, id),
} as const;
