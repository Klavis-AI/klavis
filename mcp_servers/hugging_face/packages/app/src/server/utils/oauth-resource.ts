import type { Request } from 'express';
import { OAUTH_RESOURCE_BASE_URL } from '../../shared/constants.js';

export const buildOAuthResourceHeader = (req: Request): string => {
	const rawUrl =
		typeof req.originalUrl === 'string' && req.originalUrl.length > 0 ? req.originalUrl : req.url ?? '';
	const queryIndex = rawUrl.indexOf('?');
	let query = queryIndex === -1 ? '' : rawUrl.slice(queryIndex);

	if (!query && req.query && Object.keys(req.query).length > 0) {
		const searchParams = new URLSearchParams();

		for (const [key, value] of Object.entries(req.query)) {
			if (Array.isArray(value)) {
				value.forEach((entry) => {
					if (entry === undefined || entry === null) {
						searchParams.append(key, '');
						return;
					}

					searchParams.append(key, String(entry));
				});
				continue;
			}

			if (value === undefined || value === null) {
				searchParams.append(key, '');
				continue;
			}

			searchParams.append(key, String(value));
		}

		const paramsString = searchParams.toString();
		if (paramsString) {
			query = `?${paramsString}`;
		}
	}

	return `Bearer resource_metadata="${OAUTH_RESOURCE_BASE_URL}${query}"`;
};
