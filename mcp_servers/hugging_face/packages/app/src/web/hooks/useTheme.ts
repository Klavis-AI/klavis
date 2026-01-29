import { useOpenAiGlobal } from './useOpenAiGlobal';
import { type Theme } from './types';

export const useTheme = (): Theme | null => {
	return useOpenAiGlobal('theme');
};
