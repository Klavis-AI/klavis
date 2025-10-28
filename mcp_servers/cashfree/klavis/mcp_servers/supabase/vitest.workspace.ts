import { readFile } from 'fs/promises';
import { Plugin } from 'vite';
import { defineWorkspace } from 'vitest/config';

function sqlLoaderPlugin(): Plugin {
  return {
    name: 'sql-loader',
    async transform(code, id) {
      if (id.endsWith('.sql')) {
        const textContent = await readFile(id, 'utf8');
        return `export default ${JSON.stringify(textContent)};`;
      }
      return code;
    },
  };
}

export default defineWorkspace([
  {
    plugins: [sqlLoaderPlugin()],
    test: {
      name: 'unit',
      include: ['src/**/*.{test,spec}.ts'],
      setupFiles: ['./vitest.setup.ts'],
      testTimeout: 30_000, // PGlite can take a while to initialize
    },
  },
  {
    plugins: [sqlLoaderPlugin()],
    test: {
      name: 'e2e',
      include: ['test/**/*.e2e.ts'],
      setupFiles: ['./vitest.setup.ts'],
      testTimeout: 30_000,
    },
  },
]);
