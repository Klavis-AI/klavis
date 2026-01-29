export function isBrowser(headers: Record<string, string | string[] | undefined>): boolean {
	const acceptHeader = headers['accept'];

	if (!acceptHeader) {
		return false;
	}

	const accept = Array.isArray(acceptHeader) ? acceptHeader.join(',') : acceptHeader;

	// If accept contains text/event-stream or application/json, it's not a browser
	if (accept.includes('text/event-stream') || accept.includes('application/json')) {
		return false;
	}

	// If accept contains */* it's likely a browser
	if (accept.includes('*/*')) {
		return true;
	}

	// Otherwise assume it's not a browser
	return false;
}
