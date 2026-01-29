import js from '@eslint/js';
import tseslint from 'typescript-eslint';

export default tseslint.config(
	{ ignores: ['dist/**', 'node_modules/**', 'build/**', '*.js', '*.cjs', '*.mjs'] },
	{
		files: ['src/**/*.ts'],
		extends: [js.configs.recommended, ...tseslint.configs.recommendedTypeChecked],
		languageOptions: {
			parserOptions: {
				project: './tsconfig.json',
				tsconfigRootDir: import.meta.dirname,
			},
		},
		rules: {
			// Strict TypeScript rules
			'@typescript-eslint/no-explicit-any': 'error',
			'@typescript-eslint/no-unsafe-assignment': 'error',
			'@typescript-eslint/no-unsafe-member-access': 'error',
			'@typescript-eslint/no-unsafe-call': 'error',
			'@typescript-eslint/no-unsafe-return': 'error',
			'@typescript-eslint/no-unsafe-argument': 'error',
			'@typescript-eslint/explicit-module-boundary-types': 'error',
			'@typescript-eslint/consistent-type-imports': 'error',
			'@typescript-eslint/no-unused-vars': [
				'error',
				{
					argsIgnorePattern: '^_',
					varsIgnorePattern: '^_',
				},
			],
			'@typescript-eslint/no-non-null-assertion': 'error',
			'@typescript-eslint/consistent-type-definitions': ['error', 'interface'],

			// Relaxed rules for certain patterns
			'@typescript-eslint/no-empty-function': 'off',
			'@typescript-eslint/no-empty-interface': 'off',

			// General ESLint rules
			'no-constant-condition': 'off',
		},
	}
);
