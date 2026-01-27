import pluginJs from '@eslint/js';
import globals from 'globals';
import tseslint from 'typescript-eslint';

// Merge browser + node globals and normalize keys
const combinedGlobals = { ...globals.browser, ...globals.node };
const trimmedGlobals = Object.fromEntries(
  Object.entries(combinedGlobals).map(([key, value]) => [key.trim(), value]),
);

export default [
  // Ignore common build/test artifacts
  {
    ignores: ['coverage/', 'tests/', 'dist/', 'build/', 'node_modules/'],
  },

  // JavaScript files: apply JS recommended rules and globals
  {
    files: ['**/*.{js,cjs,mjs}'],
    ...pluginJs.configs.recommended,
    languageOptions: {
      ...(pluginJs.configs.recommended.languageOptions ?? {}),
      globals: trimmedGlobals,
    },
  },

  // Source files: enable full type-aware linting
  {
    files: ['src/**/*.{ts,tsx}'],
    languageOptions: {
      parser: tseslint.parser,
      parserOptions: {
        projectService: true,
        tsconfigRootDir: new URL('.', import.meta.url).pathname,
        sourceType: 'module',
      },
      globals: trimmedGlobals,
    },
  },
  // Apply TypeScript recommended type-checked configs ONLY to source files
  ...tseslint.configs.recommendedTypeChecked.map((cfg) => ({
    files: ['src/**/*.{ts,tsx}'],
    ...cfg,
  })),

  // Script files: apply basic TS parsing without project service
  // Manually compose a lighter config for scripts to avoid project service issues
  {
    files: ['scripts/**/*.ts'],
    languageOptions: {
      parser: tseslint.parser,
      parserOptions: {
        sourceType: 'module',
      },
      globals: trimmedGlobals,
    },
    plugins: {
      '@typescript-eslint': tseslint.plugin,
    },
    rules: {
      // Start with base rules and add recommended rules
      ...tseslint.configs.base.rules,
      ...tseslint.configs.eslintRecommended.rules,
      ...tseslint.configs.recommended.rules,
    },
  },

  // Repo-specific TypeScript rule tweaks (applied to all TS files)
  {
    files: ['src/**/*.{ts,tsx}', 'scripts/**/*.ts'],
    rules: {
      '@typescript-eslint/no-unused-vars': [
        'error',
        {
          argsIgnorePattern: '^_',
          varsIgnorePattern: '^_',
          caughtErrorsIgnorePattern: '^_',
        },
      ],
    },
  },

  // Restrict console usage in src/ - use structured logger instead
  // Allow warn/error for early boot failures and log for user-facing banners
  // Scripts (CLI tools) are exempt as console output is their primary interface
  {
    files: ['src/**/*.{ts,tsx}'],
    rules: {
      'no-console': [
        'error',
        {
          allow: ['log', 'warn', 'error'],
        },
      ],
    },
  },
];
