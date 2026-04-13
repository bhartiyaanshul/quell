import { defineConfig } from 'tsup';

export default defineConfig([
  {
    entry: ['src/cli.ts'],
    format: ['esm'],
    target: 'node20',
    clean: true,
    dts: false,
    sourcemap: true,
    splitting: false,
    banner: {
      js: '#!/usr/bin/env node',
    },
  },
  {
    entry: ['src/index.ts'],
    format: ['esm'],
    target: 'node20',
    clean: false,
    dts: true,
    sourcemap: true,
    splitting: false,
  },
]);
