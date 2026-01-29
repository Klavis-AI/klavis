import { useOpenAiGlobal } from './useOpenAiGlobal';
import { type DisplayMode } from './types';

export const useDisplayMode = (): DisplayMode | null => {
	return useOpenAiGlobal('displayMode');
};
