import { z } from 'zod';
import { HfApiCall } from './hf-api-call.js';
import { explain } from './error-messages.js';
import { NO_TOKEN_INSTRUCTIONS } from './utilities.js';

export interface SpaceInfo {
	runtime?: {
		hardware?:
			| {
					current?: string;
					requested?: string;
			  }
			| string;
	};
	gated?: boolean;
	models?: string[];
}

export interface SpaceVariable {
	key: string;
	value: string;
	description?: string;
}

export interface DuplicateSpaceParams {
	sourceSpaceId: string;
	newSpaceName?: string;
	hardware?: 'freecpu' | 'zerogpu';
	private?: boolean;
}

export interface DuplicateSpaceResult {
	url: string;
	spaceId: string;
	hardware: string;
	private: boolean;
	variablesCopied: number;
	instructions: string;
	hardwareWarning?: string;
}

export const DUPLICATE_SPACE_TOOL_CONFIG = {
	name: 'duplicate_space',
	description: '', // This will be dynamically set with username
	schema: z.object({
		sourceSpaceId: z.string().min(1).describe("Space ID to copy (e.g., 'username/space-name')"),
		newSpaceId: z.string().optional().describe('Name for the new space (optional, defaults to source space-name)'),
		hardware: z
			.enum(['freecpu', 'zerogpu'])
			.optional()
			.describe('Either "freecpu" or "zerogpu" (defaults based on source). Both options are in the free tier.'),
		private: z
			.boolean()
			.optional()
			.default(true)
			.describe('Check with User whether the new space should be public or private.'),
	}),
	annotations: {
		title: 'Duplicate Hugging Face Space',
		destructiveHint: false,
		readOnlyHint: false,
		openWorldHint: true,
	},
} as const;

// Hardware mapping constants
const HARDWARE_MAP = {
	freecpu: 'cpu-basic',
	zerogpu: 'zero-a10g',
} as const;

const FREE_HARDWARE = ['cpu-basic', 'zero-a10g'];

export class DuplicateSpaceTool extends HfApiCall<DuplicateSpaceParams, DuplicateSpaceResult> {
	private username?: string;

	constructor(hfToken?: string, username?: string) {
		super('https://huggingface.co/api', hfToken);
		this.username = username;
	}

	static createToolConfig(
		username?: string
	): Omit<typeof DUPLICATE_SPACE_TOOL_CONFIG, 'description'> & { description: string } {
		const description = username
			? `Duplicate a Hugging Face Space. Target space will be created as ${username}/<new-space-name>.`
			: NO_TOKEN_INSTRUCTIONS;
		return {
			...DUPLICATE_SPACE_TOOL_CONFIG,
			description,
		};
	}

	normalizeSpaceName(spaceName: string): string {
		// If already has a slash, check if it's trying to use a different username
		if (spaceName.includes('/')) {
			const [providedUser, spaceNamePart] = spaceName.split('/');
			if (providedUser !== this.username) {
				throw new Error(
					`Invalid space ID: ${spaceName}. You can only create spaces in your own namespace. Try "${this.username || 'your-username'}/${spaceNamePart || 'space-name'}"`
				);
			}
			return spaceName;
		}
		// Otherwise, prepend with username
		return `${this.username || 'unknown'}/${spaceName}`;
	}

	async getSpaceInfo(spaceId: string): Promise<SpaceInfo> {
		const url = `${this.apiUrl}/spaces/${spaceId}`;
		return this.fetchFromApi(url);
	}

	async getSpaceVariables(spaceId: string): Promise<Record<string, { value: string; description?: string }>> {
		const url = `${this.apiUrl}/spaces/${spaceId}/variables`;
		try {
			return await this.fetchFromApi(url);
		} catch {
			// If we can't access variables (private space or no permissions), return empty
			return {};
		}
	}

	async duplicate(params: DuplicateSpaceParams): Promise<DuplicateSpaceResult> {
		const { sourceSpaceId, newSpaceName, hardware, private: isPrivate = true } = params;

		if (!this.username) throw new Error(NO_TOKEN_INSTRUCTIONS);

		try {
			// Step 1: Get source space info
			let sourceInfo: SpaceInfo;
			try {
				sourceInfo = await this.getSpaceInfo(sourceSpaceId);
			} catch (error) {
				// Explain the error and rethrow
				throw explain(error, `Could not access source space "${sourceSpaceId}"`);
			}

			// Step 2: Get variables from source space
			const sourceVars = await this.getSpaceVariables(sourceSpaceId);
			const variables: SpaceVariable[] = Object.entries(sourceVars).map(([key, varInfo]) => ({
				key,
				value: varInfo.value,
				description: varInfo.description,
			}));

			// Step 3: Determine hardware
			// Extract hardware string from either object or string format
			let sourceHardwareStr: string | undefined;
			if (typeof sourceInfo.runtime?.hardware === 'object') {
				sourceHardwareStr = sourceInfo.runtime.hardware.current || sourceInfo.runtime.hardware.requested;
			} else {
				sourceHardwareStr = sourceInfo.runtime?.hardware;
			}

			let selectedHardware: string;
			let hardwareKey: 'freecpu' | 'zerogpu';

			if (hardware) {
				selectedHardware = HARDWARE_MAP[hardware];
				hardwareKey = hardware;
			} else {
				// Auto-detect based on source
				if (sourceHardwareStr === 'zero-a10g') {
					selectedHardware = 'zero-a10g';
					hardwareKey = 'zerogpu';
				} else if (sourceHardwareStr === 'cpu-basic' || !sourceHardwareStr) {
					selectedHardware = 'cpu-basic';
					hardwareKey = 'freecpu';
				} else {
					// For any paid hardware, default to ZeroGPU (free tier)
					selectedHardware = 'zero-a10g';
					hardwareKey = 'zerogpu';
				}
			}

			// Step 4: Determine target space ID
			let targetId: string;
			if (newSpaceName) {
				targetId = this.normalizeSpaceName(newSpaceName);
			} else {
				// Use same name as source
				const sourceName = sourceSpaceId.split('/')[1];
				targetId = `${this.username}/${sourceName || ''}`;
			}

			// Step 5: Check for warnings
			let hardwareWarning: string | undefined;
			if (sourceHardwareStr && !FREE_HARDWARE.includes(sourceHardwareStr)) {
				hardwareWarning = `Note: The source space uses '${sourceHardwareStr}' which is paid hardware. Your duplicated space is set to '${hardwareKey}'. "+ 
				"You may need to upgrade in Settings to run this space or achieve the same performance.`;
			}

			let gatedWarning: string | undefined;
			if (sourceInfo.gated) {
				gatedWarning = `🔐 The model in this space is 'gated' - you may need to accept the licensing conditions before  use.`;
			}

			// Step 6: Make the duplication request
			const url = `${this.apiUrl}/spaces/${sourceSpaceId}/duplicate`;
			const payload = {
				repository: targetId,
				private: isPrivate,
				hardware: selectedHardware,
				variables: variables.length > 0 ? variables : undefined,
			};

			const response = await this.fetchFromApi<{ url: string }>(url, {
				method: 'POST',
				body: JSON.stringify(payload),
			});

			// Step 7: Construct response
			const warnings: string[] = [];
			if (hardwareWarning) warnings.push(hardwareWarning);
			if (gatedWarning) warnings.push(gatedWarning);

			const result: DuplicateSpaceResult = {
				url: response.url,
				spaceId: targetId,
				hardware: hardwareKey,
				private: isPrivate,
				variablesCopied: variables.length,
				instructions: this.formatInstructions(response.url, hardwareKey, isPrivate, warnings),
			};

			if (hardwareWarning) {
				result.hardwareWarning = hardwareWarning;
			}

			return result;
		} catch (error) {
			// Explain the error and rethrow
			throw explain(error, 'Failed to duplicate space');
		}
	}

	private formatInstructions(url: string, hardware: string, isPrivate: boolean, warnings: string[]): string {
		let instructions = `✅ 🤗 Space successfully duplicated! 

🔗 Your new space: ${url}

⚙️ To configure your space:
1. Go to ${url}
2. Click on 'Settings' in the top right
3. Configure any additional settings as needed

Hardware: ${hardware} | Visibility: ${isPrivate ? 'Private' : 'Public'}`;

		if (warnings.length > 0) {
			instructions += '\n\n⚠️ Warnings:';
			warnings.forEach((warning) => {
				instructions += `\n- ${warning}`;
			});
		}

		return instructions;
	}
}

export const formatDuplicateResult = (result: DuplicateSpaceResult): string => {
	return result.instructions;
};
