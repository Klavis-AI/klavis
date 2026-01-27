/**
 * @fileoverview Defines the interface for a communication transport.
 * @module src/mcp-server/transports/ITransport
 */
import type { ServerType } from '@hono/node-server';
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';

export type TransportServer = ServerType | McpServer;

export interface ITransport {
  start(): Promise<TransportServer>;
  stop(): Promise<void>;
}
