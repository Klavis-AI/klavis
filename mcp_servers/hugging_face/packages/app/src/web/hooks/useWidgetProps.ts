import { useOpenAiGlobal } from './useOpenAiGlobal';

export function useWidgetProps<T extends Record<string, unknown>>(
	defaultState?: T | (() => T)
): T {
	const props = useOpenAiGlobal('toolOutput') as T;

	const fallback =
		typeof defaultState === 'function'
			? (defaultState as () => T | null)()
			: defaultState ?? null;

	return props ?? fallback;
}
