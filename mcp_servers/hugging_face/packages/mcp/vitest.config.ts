import { defineConfig } from 'vitest/config';

export default defineConfig({
	plugins: [],
	test: {
		globals: true,
		setupFiles: [],
		include: ['**/*.{test,spec}.{js,ts,jsx,tsx}'],
	},
});
