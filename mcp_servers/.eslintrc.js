// Base ESLint configuration for all MCP servers
module.exports = {
    root: true, // This is now the root config
    parser: '@typescript-eslint/parser',
    parserOptions: {
        ecmaVersion: 2022,
        sourceType: 'module',
        tsconfigRootDir: '.',
        project: './tsconfig.json', // Points to the mcp_servers tsconfig
    },
    plugins: ['@typescript-eslint', 'prettier'],
    extends: [
        'eslint:recommended',
        'plugin:@typescript-eslint/recommended',
        'prettier', // Avoid conflicts with prettier formatting
        'plugin:prettier/recommended',
    ],
    env: {
        node: true,
        es2022: true,
    },
    rules: {
        // MCP server-specific rules
        'no-console': ['error', { allow: ['warn', 'error'] }],
        '@typescript-eslint/explicit-module-boundary-types': 'off',
        '@typescript-eslint/no-explicit-any': 'error',
        '@typescript-eslint/no-unused-vars': [
            'error',
            { argsIgnorePattern: '^_', varsIgnorePattern: '^_' },
        ],
        '@typescript-eslint/no-non-null-assertion': 'warn',
        'no-duplicate-imports': 'error',
        'prettier/prettier': 'error',
    },
    overrides: [
        {
            files: ['**/*.test.ts', '**/*.spec.ts'],
            rules: {
                'no-console': 'off',
                '@typescript-eslint/no-explicit-any': 'warn',
            },
        },
    ],
    ignorePatterns: ['node_modules', 'dist', 'build'],
};