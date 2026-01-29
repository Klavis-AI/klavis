import type { Request } from 'express';

/**
 * Extracts supported query parameters from the request and sets corresponding headers
 * This centralizes the logic for converting URL query parameters to internal headers
 * used by the tool selection strategy.
 */
export function extractQueryParamsToHeaders(req: Request, headers: Record<string, string>): void {
	const bouquet = req.query.bouquet as string | undefined;
	const mix = Array.isArray(req.query.mix) ? req.query.mix.join(',') : (req.query.mix as string | undefined);
	const gradio = req.query.gradio as string | undefined;
	const streamable = req.query.streamable as string | undefined;
	const forceauth = req.query.forceauth as string | undefined;
	const login = req.query.login;
	const auth = req.query.auth;
	const noImageContent = Array.isArray(req.query.no_image_content)
		? req.query.no_image_content[0]
		: req.query.no_image_content;

	if (bouquet) {
		headers['x-mcp-bouquet'] = bouquet;
	}
	if (mix) {
		headers['x-mcp-mix'] = mix;
	}
	if (gradio) {
		headers['x-mcp-gradio'] = gradio;
	}
	if (streamable) {
		headers['x-mcp-streamable'] = streamable;
	}

	if (typeof noImageContent === 'string') {
		const normalized = noImageContent.trim().toLowerCase();
		if (normalized === 'true' || normalized === '1' || normalized === 'yes' || normalized === '') {
			headers['x-mcp-no-image-content'] = 'true';
		}
}

	// Check if forceauth, login, or auth appears in the URL (with or without values)
	if (forceauth || login !== undefined || auth !== undefined) {
		headers['x-mcp-force-auth'] = 'true';
	}
}
