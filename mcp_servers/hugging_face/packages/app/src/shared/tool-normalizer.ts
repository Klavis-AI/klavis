import { HUB_INSPECT_TOOL_ID, MODEL_DETAIL_TOOL_ID, DATASET_DETAIL_TOOL_ID } from '@llmindset/hf-mcp';

/**
 * Normalizes built-in tool lists coming from UI/API clients.
 * - Deduplicates entries while preserving original order where possible.
 * - Replaces legacy detail tools with the newer hub aggregate tool.
 */
export function normalizeBuiltInTools(ids: readonly string[]): string[] {
	const seen = new Set<string>();
	const normalized: string[] = [];
	let addHubInspect = false;

	for (const rawId of ids) {
		if (rawId === MODEL_DETAIL_TOOL_ID || rawId === DATASET_DETAIL_TOOL_ID) {
			addHubInspect = true;
			continue;
		}

		if (!seen.has(rawId)) {
			seen.add(rawId);
			normalized.push(rawId);
		}
	}

	if (addHubInspect && !seen.has(HUB_INSPECT_TOOL_ID)) {
		seen.add(HUB_INSPECT_TOOL_ID);
		normalized.push(HUB_INSPECT_TOOL_ID);
	}

	return normalized;
}
