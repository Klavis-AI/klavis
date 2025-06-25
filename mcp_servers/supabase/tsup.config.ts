import { defineConfig } from 'tsup';

export default defineConfig([
  {
    entry: ['src/mcp.ts'],
    format: ['cjs', 'esm'],
    outDir: 'dist',
    sourcemap: true,
    dts: true,
    minify: true,
    splitting: true,
    loader: {
      '.sql': 'text',
    },
  },
]);
