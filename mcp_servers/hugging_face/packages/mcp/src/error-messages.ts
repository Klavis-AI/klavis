/**
 * Common HTTP error messages for Hugging Face API operations
 */

import { HfApiError } from './hf-api-call.js';

/**
 * Friendly explanations for common HTTP error codes
 */
export const FRIENDLY_ERROR_EXPLANATIONS: Record<number, string> = {
	400: 'The request was invalid. Check your HF_TOKEN permissions, or that you have not exceeded the maximum number of spaces allowed..',
	401: 'Authentication failed. Please check that your Hugging Face token is valid. Check your Hugging Face token permissions.',
	403: 'You do not have permission to access this resource. Check your Hugging Face token permissions.',
	404: 'The requested resource does not exist.',
	409: 'A resource with this name already exists.',
	422: 'The provided configuration is invalid.',
	429: 'Duplication failed due to rate limits.',
	500: 'Hugging Face is experiencing issues. Please try again later.',
	502: 'The server gateway is temporarily unavailable.',
	503: 'The service is temporarily down for maintenance.',
};

/**
 * Get friendly explanation for a given HTTP status code
 */
export function getFriendlyExplanation(status: number): string {
	// Check for exact match first
	if (FRIENDLY_ERROR_EXPLANATIONS[status]) {
		return FRIENDLY_ERROR_EXPLANATIONS[status];
	}

	// Handle 5xx errors generically
	if (status >= 500) {
		return 'Hugging Face is experiencing issues. Please try again later.';
	}

	// Default for unknown errors
	return 'An unexpected error occurred. Please try again.';
}

/**
 * Explain an error by enhancing it with friendly explanation if it's an HfApiError
 * Otherwise returns the original error unchanged
 * @param error - The error to explain
 * @param context - Optional context about what was being attempted
 * @returns The enhanced HfApiError or original error
 */
export function explain(error: unknown, context?: string): unknown {
	// Only enhance HfApiError instances
	if (error instanceof HfApiError) {
		const friendlyExplanation = getFriendlyExplanation(error.status);
		return error.withImprovedMessage(friendlyExplanation, context);
	}

	// Return any other error unchanged
	return error;
}
