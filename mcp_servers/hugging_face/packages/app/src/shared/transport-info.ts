import type { TransportType } from './constants.js';

/**
 * Unified TransportInfo interface used for both server storage and client display
 */
export interface TransportInfo {
	transport: TransportType;
	port?: number;
	defaultHfTokenSet: boolean;
	hfTokenMasked?: string;
	jsonResponseEnabled?: boolean;
	externalApiMode?: boolean;
	stdioClient?: {
		name: string;
		version: string;
	} | null;
}

/**
 * Get the appropriate display text for the HF token status based on transport mode
 *
 * @param info - The transport information
 * @returns Object with display text and whether it's a warning
 */
export function getTokenDisplayText(info: TransportInfo): { text: string; isWarning: boolean } {
	if (info.transport === 'stdio') {
		// STDIO mode: show masked token or warning if not set
		if (info.defaultHfTokenSet && info.hfTokenMasked) {
			return { text: info.hfTokenMasked, isWarning: false };
		} else {
			return { text: 'Warning: No token set', isWarning: true };
		}
	} else {
		// Other modes (HTTP): different logic
		if (!info.defaultHfTokenSet) {
			return { text: 'Using Authorization Headers', isWarning: false };
		} else {
			return {
				text: `⚠️ Using ${info.hfTokenMasked || 'token'} as default`,
				isWarning: true,
			};
		}
	}
}
