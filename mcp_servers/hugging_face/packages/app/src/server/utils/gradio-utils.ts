/**
 * Utility functions for handling Gradio endpoint detection and configuration
 */
import type { SpaceTool } from '../../shared/settings.js';
import { GRADIO_PREFIX, GRADIO_PRIVATE_PREFIX } from '../../shared/constants.js';
import { logger } from './logger.js';
import { getGradioSpaces } from './gradio-discovery.js';

/**
 * Determines if a tool name represents a Gradio endpoint
 * Gradio tools follow the pattern: gr<number>_<name> or grp<number>_<name>
 *
 * @param toolName - The name of the tool to check
 * @returns true if the tool is a Gradio endpoint, false otherwise
 *
 * @example
 * isGradioTool('gr1_evalstate_flux1_schnell') // true
 * isGradioTool('grp2_private_tool') // true
 * isGradioTool('hf_doc_search') // false
 * isGradioTool('regular_tool') // false
 */
export function isGradioTool(toolName: string): boolean {
	// Gradio tools follow pattern: gr<number>_<name> or grp<number>_<name>
	return /^grp?\d+_/.test(toolName);
}

/**
 * Creates a Gradio tool name based on tool name, index, and privacy status
 * This is the core logic used throughout the application for generating tool names
 *
 * @param toolName - The tool name (e.g., "flux1_schnell", "EasyGhibli")
 * @param index - Zero-based index position (will be converted to 1-based)
 * @param isPrivate - Whether this is a private space (determines gr vs grp prefix)
 * @param toolIndex - Optional tool index within the endpoint for uniqueness when truncating
 * @returns The generated tool name following Gradio naming convention
 *
 * @example
 * createGradioToolName('flux1_schnell', 0, false) // 'gr1_flux1_schnell'
 * createGradioToolName('EasyGhibli', 1, false) // 'gr2_easyghibli'
 * createGradioToolName('private.model', 2, true) // 'grp3_private_model'
 */
export function createGradioToolName(
	toolName: string,
	index: number,
	isPrivate: boolean | undefined,
	toolIndex?: number
): string {
	// Choose prefix based on privacy status
	const prefix = isPrivate ? GRADIO_PRIVATE_PREFIX : GRADIO_PREFIX;
	const indexStr = (index + 1).toString();

	// Calculate available space for the sanitized name (49 - prefix - index - underscore)
	const maxNameLength = 49 - prefix.length - indexStr.length - 1;

	// Sanitize the tool name: replace special characters with underscores, normalize multiple underscores, and lowercase
	let sanitizedName = toolName
		? toolName
				.replace(/[-\s.]+/g, '_') // Replace special chars with underscores
				.toLowerCase()
		: 'unknown';

	// Handle based on length
	if (sanitizedName.length > maxNameLength) {
		// Over limit: insert tool index at beginning if provided, then truncate
		if (toolIndex !== undefined) {
			// Insert tool index after the underscore: gr1_0_toolname
			const toolIndexPrefix = `${toolIndex}_`;
			const availableForName = maxNameLength - toolIndexPrefix.length;

			// Keep first 20 chars, add underscore, then keep as many chars from the end as possible
			const keepFromEnd = availableForName - 20 - 1; // -1 for the underscore
			sanitizedName = toolIndexPrefix + sanitizedName.substring(0, 20) + '_' + sanitizedName.slice(-keepFromEnd);
		} else {
			// No tool index, just do middle truncation as before
			const keepFromEnd = maxNameLength - 20 - 1; // -1 for the underscore
			sanitizedName = sanitizedName.substring(0, 20) + '_' + sanitizedName.slice(-keepFromEnd);
		}
	}
	// Under limit: keep as-is, no normalization

	// Create tool name: {prefix}{1-based-index}_{sanitized_name}
	return `${prefix}${indexStr}_${sanitizedName}`;
}

/**
 * Parsed Gradio space ID before subdomain resolution
 */
export interface ParsedGradioSpace {
	name: string; // e.g., "microsoft/Florence-2-large"
}

/**
 * Parses the gradio parameter to extract space IDs.
 * Does NOT construct subdomains - they must be fetched from the HuggingFace API.
 *
 * @param gradioParam - Comma-separated list of space IDs (e.g., "microsoft/Florence-2-large,acme/foo")
 * @returns Array of parsed space IDs
 *
 * @example
 * parseGradioSpaceIds('microsoft/Florence-2-large') // [{ name: 'microsoft/Florence-2-large' }]
 * parseGradioSpaceIds('microsoft/Florence-2-large,acme/foo') // [{ name: 'microsoft/Florence-2-large' }, { name: 'acme/foo' }]
 * parseGradioSpaceIds('none') // []
 */
export function parseGradioSpaceIds(gradioParam: string): ParsedGradioSpace[] {
	const spaces: ParsedGradioSpace[] = [];
	const trimmed = gradioParam.trim();

	// Treat special sentinel "none" as "disable gradio"
	if (trimmed.toLowerCase() === 'none') {
		return spaces;
	}

	const entries = gradioParam
		.split(',')
		.map((s) => s.trim())
		.filter((s) => s.length > 0);

	for (const entry of entries) {
		// Skip explicit "none" entries within a list
		if (entry.toLowerCase() === 'none') {
			continue;
		}

		// Validate exactly one slash in the middle (username/space-name format)
		const slashCount = (entry.match(/\//g) || []).length;
		const slashIndex = entry.indexOf('/');
		const isValidFormat = slashCount === 1 && slashIndex > 0 && slashIndex < entry.length - 1;

		if (!isValidFormat) {
			logger.warn(
				`Skipping invalid gradio entry "${entry}": must contain exactly one slash with content on both sides (format: username/space-name)`
			);
			continue;
		}

		spaces.push({ name: entry });
		logger.debug(`Parsed gradio space ID: ${entry}`);
	}

	return spaces;
}

/**
 * Fetches real subdomains from the HuggingFace API for the given space IDs.
 * Now uses the optimized discovery API with caching for better performance.
 *
 * @param spaceIds - Array of space IDs to fetch subdomains for
 * @param hfToken - Optional HuggingFace token for authentication
 * @param hubUrl - Optional hub URL for custom HuggingFace instances (not used with new API)
 * @returns Array of SpaceTool objects with real subdomains from the API
 *
 * @example
 * const spaces = [{ name: 'microsoft/Florence-2-large' }];
 * const tools = await fetchGradioSubdomains(spaces, 'hf_token');
 * // Returns: [{ _id: 'gradio_...', name: 'microsoft/Florence-2-large', subdomain: 'microsoft-florence-2-large', emoji: '🔧' }]
 */
export async function fetchGradioSubdomains(spaceIds: ParsedGradioSpace[], hfToken?: string): Promise<SpaceTool[]> {
	if (spaceIds.length === 0) {
		return [];
	}

	const spaceNames = spaceIds.map((s) => s.name);

	// Use the new optimized discovery API with caching
	// Skip schemas since we only need metadata here
	const spaces = await getGradioSpaces(spaceNames, hfToken, { skipSchemas: true });

	// Convert to SpaceTool format
	const spaceTools: SpaceTool[] = spaces.map((space) => ({
		_id: space._id,
		name: space.name,
		subdomain: space.subdomain,
		emoji: space.emoji,
	}));

	logger.debug(
		{
			requested: spaceIds.length,
			successful: spaceTools.length,
		},
		'Fetched Gradio subdomains'
	);

	return spaceTools;
}

/**
 * Parses gradio parameter and fetches real subdomains from HuggingFace API.
 * This is the main entry point that combines parsing and API fetching.
 *
 * @param gradioParam - Comma-separated list of space IDs
 * @param hfToken - Optional HuggingFace token for authentication
 * @param hubUrl - Optional hub URL for custom HuggingFace instances
 * @returns Array of SpaceTool objects with real subdomains
 *
 * @example
 * const tools = await parseAndFetchGradioEndpoints('microsoft/Florence-2-large', 'hf_token');
 * // Returns array of SpaceTool objects with real subdomains from HuggingFace API
 */
export async function parseAndFetchGradioEndpoints(gradioParam: string, hfToken?: string): Promise<SpaceTool[]> {
	const parsedSpaces = parseGradioSpaceIds(gradioParam);

	if (parsedSpaces.length === 0) {
		return [];
	}

	return fetchGradioSubdomains(parsedSpaces, hfToken);
}

/**
 * Input parameters for determining if gradio_files tool should be registered
 */
export interface GradioFilesEligibilityParams {
	/** Number of configured Gradio spaces */
	gradioSpaceCount: number;
	/** List of enabled built-in tool IDs */
	builtInTools: string[];
	/** The tool ID that represents dynamic_space */
	dynamicSpaceToolId: string;
	/** Whether the user's gradio-files dataset exists */
	datasetExists: boolean;
}

/**
 * Pure function to determine if the gradio_files tool should be registered.
 *
 * The tool should be registered when:
 * 1. The user's gradio-files dataset exists, AND
 * 2. Either Gradio spaces are configured OR dynamic_space tool is enabled
 *
 * @param params - The eligibility parameters
 * @returns true if gradio_files tool should be registered
 *
 * @example
 * shouldRegisterGradioFilesTool({
 *   gradioSpaceCount: 0,
 *   builtInTools: ['dynamic_space'],
 *   dynamicSpaceToolId: 'dynamic_space',
 *   datasetExists: true,
 * }) // true - dynamic_space enabled with existing dataset
 *
 * @example
 * shouldRegisterGradioFilesTool({
 *   gradioSpaceCount: 2,
 *   builtInTools: [],
 *   dynamicSpaceToolId: 'dynamic_space',
 *   datasetExists: true,
 * }) // true - Gradio spaces configured with existing dataset
 *
 * @example
 * shouldRegisterGradioFilesTool({
 *   gradioSpaceCount: 0,
 *   builtInTools: [],
 *   dynamicSpaceToolId: 'dynamic_space',
 *   datasetExists: true,
 * }) // false - no Gradio spaces and dynamic_space not enabled
 */
export function shouldRegisterGradioFilesTool(params: GradioFilesEligibilityParams): boolean {
	const { gradioSpaceCount, builtInTools, dynamicSpaceToolId, datasetExists } = params;

	if (!datasetExists) {
		return false;
	}

	const hasGradioSpaces = gradioSpaceCount > 0;
	const isDynamicSpaceEnabled = builtInTools.includes(dynamicSpaceToolId);

	return hasGradioSpaces || isDynamicSpaceEnabled;
}
