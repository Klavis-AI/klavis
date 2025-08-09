import { defineWorkspace } from 'vitest/config';

export default defineWorkspace([
  {
    test: {
      name: 'unit',
      include: ['test/**/*.test.ts'],
      setupFiles: ['./vitest.setup.ts'],
      environment: 'node'
    }
  }
]);
