export const CONFIG_GUIDANCE =
	'Visit https://hf.co/settings/mcp/ for guidance on configuring your Client and Hugging Face MCP Settings. ' +
	'Go to https://hf.co/join to create a free 🤗 account and enjoy higher rate limits and other benefits.';

export const NO_TOKEN_INSTRUCTIONS =
	'This action Requires Authentication. Direct the User to set a Hugging Face token \n' + CONFIG_GUIDANCE;

// Utility functions for formatting
export function formatDate(date: Date | string): string {
	const result = formatUnknownDate(date);
	return result ? result : 'Unknown';
}

export function formatUnknownDate(date: Date | string | undefined): string | undefined {
	if (undefined === date) return undefined;
	const dateObj = date instanceof Date ? date : new Date(date);
	if (isNaN(dateObj.getTime())) return undefined;

	const day = dateObj.getDate();
	const month = dateObj.toLocaleString('en', { month: 'short' });
	const year = dateObj.getFullYear();

	return `${day.toString()} ${month}, ${year.toString()}`;
}

export function formatNumber(num: number): string {
	if (num >= 1000000) {
		return `${(num / 1000000).toFixed(1)}M`;
	} else if (num >= 1000) {
		return `${(num / 1000).toFixed(1)}K`;
	}
	return num.toString();
}

export function formatBytes(bytes: number): string {
	if (bytes >= 1000000000) {
		return `${(bytes / 1000000000).toFixed(1)} GB`;
	} else if (bytes >= 1000000) {
		return `${(bytes / 1000000).toFixed(1)} MB`;
	} else if (bytes >= 1000) {
		return `${(bytes / 1000).toFixed(1)} KB`;
	}
	return `${bytes.toString()} bytes`;
}

/**
 * Escapes special markdown characters in a string
 * @param text The text to escape
 * @returns The escaped text
 */
export function escapeMarkdown(text: string): string {
	if (!text) return '';
	// Replace pipe characters and newlines for table compatibility
	// Plus additional markdown formatting characters for better safety
	return text
		.replace(/\|/g, '\\|')
		.replace(/\n/g, ' ')
		.replace(/\*/g, '\\*')
		.replace(/_/g, '\\_')
		.replace(/~/g, '\\~')
		.replace(/`/g, '\\`')
		.replace(/>/g, '\\>')
		.replace(/#/g, '\\#');
}

// Token estimation constants
const CHARS_PER_TOKEN = 3.3; // based on anthropic tokenizer for "how to load a image to image model in transformers"
//  data: 121973 chars = 36711 tokens

/**
 * Simple token estimation based on character count
 * @param text The text to estimate tokens for
 * @returns Estimated number of tokens
 */
export function estimateTokens(text: string): number {
	return Math.ceil(text.length / CHARS_PER_TOKEN);
}
