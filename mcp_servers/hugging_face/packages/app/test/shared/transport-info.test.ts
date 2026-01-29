import { describe, it, expect } from 'vitest';
import { getTokenDisplayText } from '../../src/shared/transport-info.js';
import type { TransportInfo } from '../../src/shared/transport-info.js';

describe('getTokenDisplayText', () => {
	describe('STDIO mode', () => {
		it('should show masked token when token is set', () => {
			const info: TransportInfo = {
				transport: 'stdio',
				defaultHfTokenSet: true,
				hfTokenMasked: 'hf_ab...xyz',
				stdioClient: null,
			};

			const result = getTokenDisplayText(info);

			expect(result.text).toBe('hf_ab...xyz');
			expect(result.isWarning).toBe(false);
		});

		it('should show warning when token is not set', () => {
			const info: TransportInfo = {
				transport: 'stdio',
				defaultHfTokenSet: false,
				stdioClient: null,
			};

			const result = getTokenDisplayText(info);

			expect(result.text).toBe('Warning: No token set');
			expect(result.isWarning).toBe(true);
		});

		it('should show warning when token is set but mask is missing', () => {
			const info: TransportInfo = {
				transport: 'stdio',
				defaultHfTokenSet: true,
				hfTokenMasked: undefined,
				stdioClient: null,
			};

			const result = getTokenDisplayText(info);

			expect(result.text).toBe('Warning: No token set');
			expect(result.isWarning).toBe(true);
		});
	});

	describe('Non-STDIO modes (HTTP)', () => {
		const nonStdioModes: Array<TransportInfo['transport']> = ['streamableHttp', 'streamableHttpJson'];

		nonStdioModes.forEach((transport) => {
			describe(`${transport} mode`, () => {
				it('should show "Using Authorization Headers" when token is not set', () => {
					const info: TransportInfo = {
						transport,
						defaultHfTokenSet: false,
						stdioClient: null,
					};

					const result = getTokenDisplayText(info);

					expect(result.text).toBe('Using Authorization Headers');
					expect(result.isWarning).toBe(false);
				});

				it('should show warning with masked token when token is set', () => {
					const info: TransportInfo = {
						transport,
						defaultHfTokenSet: true,
						hfTokenMasked: 'hf_ab...xyz',
						stdioClient: null,
					};

					const result = getTokenDisplayText(info);

					expect(result.text).toBe('⚠️ Using hf_ab...xyz as default');
					expect(result.isWarning).toBe(true);
				});

				it('should show warning with fallback when token is set but mask is missing', () => {
					const info: TransportInfo = {
						transport,
						defaultHfTokenSet: true,
						hfTokenMasked: undefined,
						stdioClient: null,
					};

					const result = getTokenDisplayText(info);

					expect(result.text).toBe('⚠️ Using token as default');
					expect(result.isWarning).toBe(true);
				});
			});
		});
	});

	describe('Unknown transport mode', () => {
		it('should handle unknown transport as non-STDIO mode', () => {
			const info: TransportInfo = {
				transport: 'unknown',
				defaultHfTokenSet: false,
				stdioClient: null,
			};

			const result = getTokenDisplayText(info);

			expect(result.text).toBe('Using Authorization Headers');
			expect(result.isWarning).toBe(false);
		});
	});
});
