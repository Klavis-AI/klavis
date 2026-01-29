import { useCallback, useEffect, useState, type SetStateAction } from 'react';
import { useOpenAiGlobal } from './useOpenAiGlobal';
import type { UnknownObject } from './types';

export function useWidgetState<T extends UnknownObject>(
	defaultState: T | (() => T)
): readonly [T, (state: SetStateAction<T>) => void];
export function useWidgetState<T extends UnknownObject>(
	defaultState?: T | (() => T | null) | null
): readonly [T | null, (state: SetStateAction<T | null>) => void];
export function useWidgetState<T extends UnknownObject>(
	defaultState?: T | (() => T | null) | null
): readonly [T | null, (state: SetStateAction<T | null>) => void] {
	const widgetStateFromWindow = useOpenAiGlobal('widgetState') as T;

	const [widgetState, _setWidgetState] = useState<T | null>(() => {
		if (widgetStateFromWindow != null) {
			return widgetStateFromWindow;
		}

		return typeof defaultState === 'function'
			? defaultState()
			: defaultState ?? null;
	});

	useEffect(() => {
		_setWidgetState(widgetStateFromWindow);
	}, [widgetStateFromWindow]);

	const setWidgetState = useCallback((state: SetStateAction<T | null>) => {
		const setWidgetStateFn = window.openai?.setWidgetState;

		_setWidgetState((prevState) => {
			const newState = typeof state === 'function' ? state(prevState) : state;

			if (newState != null && typeof setWidgetStateFn === 'function') {
				void setWidgetStateFn(newState);
			}

			return newState;
		});
	}, []);

	return [widgetState, setWidgetState] as const;
}
