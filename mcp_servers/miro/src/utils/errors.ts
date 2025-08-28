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
