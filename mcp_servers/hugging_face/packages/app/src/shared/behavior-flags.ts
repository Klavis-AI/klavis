export const README_INCLUDE_FLAG = 'ALLOW_README_INCLUDE' as const;
export const GRADIO_IMAGE_FILTER_FLAG = 'NO_GRADIO_IMAGE_CONTENT' as const;

export function hasReadmeFlag(ids: readonly string[]): boolean {
	return ids.includes(README_INCLUDE_FLAG);
}
