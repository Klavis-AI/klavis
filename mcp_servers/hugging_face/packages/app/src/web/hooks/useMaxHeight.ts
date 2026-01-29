import { useOpenAiGlobal } from './useOpenAiGlobal';

export const useMaxHeight = (): number | null => {
	return useOpenAiGlobal('maxHeight');
};
