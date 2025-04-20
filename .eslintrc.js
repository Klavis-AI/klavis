// Base ESLint configuration for all TypeScript packages
module.exports = {
  root: true,
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 2022,
    sourceType: 'module',
  },
  plugins: ['@typescript-eslint'],
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'prettier', // Avoid conflicts with prettier formatting
  ],
  env: {
    node: true,
    es2022: true,
  },
  rules: {
    // Common rules for all projects
    'no-console': ['warn', { allow: ['warn', 'error', 'info'] }],
    '@typescript-eslint/explicit-module-boundary-types': 'off',
    '@typescript-eslint/no-explicit-any': 'warn',
    '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }],
    '@typescript-eslint/no-non-null-assertion': 'warn',
    'no-duplicate-imports': 'error',
  },
  ignorePatterns: ['node_modules', 'dist', 'build'],
};