import { type Express } from 'express';
import { type TransportType } from '../../shared/constants.js';
import type { BaseTransport, ServerFactory } from './base-transport.js';
import { StdioTransport } from './stdio-transport.js';
import { StreamableHttpTransport } from './streamable-http-transport.js';
import { StatelessHttpTransport } from './stateless-http-transport.js';

/**
 * Utility for creating transport instances
 */
export const createTransport = (type: TransportType, serverFactory: ServerFactory, app: Express): BaseTransport => {
		switch (type) {
			case 'stdio':
				return new StdioTransport(serverFactory, app);
			case 'streamableHttp':
				return new StreamableHttpTransport(serverFactory, app);
		case 'streamableHttpJson':
			return new StatelessHttpTransport(serverFactory, app);
		default:
			throw new Error(`Unsupported transport type: ${type}`);
	}
};
