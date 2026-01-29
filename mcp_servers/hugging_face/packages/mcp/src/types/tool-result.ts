/**
 * Standard response format for all tools to enable consistent query logging
 */
export interface ToolResult {
	/**
	 * The formatted output string to be returned to the MCP client
	 */
	formatted: string;

	/**
	 * Total number of results found (before any limits applied)
	 * For detail tools: 1 if found, 0 if not found
	 * For prompts: 1 if generated successfully
	 */
	totalResults: number;

	/**
	 * Number of results actually included in the formatted response
	 * Usually limited by the 'limit' parameter for search tools
	 * For detail tools: same as totalResults
	 * For prompts: 1 if generated successfully
	 */
	resultsShared: number;

	/**
	 * Indicates whether this result represents an error condition
	 * When true, formatted contains an error message
	 */
	isError?: boolean;
}