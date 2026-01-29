import { describe, it, expect } from 'vitest';
import { isInitializeRequest } from '../../src/shared/transport-metrics.js';

describe('isInitializeRequest', () => {
	it('should identify initialize requests', () => {
		expect(isInitializeRequest('initialize')).toBe(true);
		expect(isInitializeRequest('notifications/initialized')).toBe(false);
		expect(isInitializeRequest('tools/list')).toBe(false);
	});
});
