import { defineConfig } from 'tsdown';

export default defineConfig({
  entry: {
    index: 'src/index.ts',
    types: 'src/types.ts',
  },
  format: ['cjs', 'esm'],
  // isolatedDeclarations is enabled in tsconfig, so tsdown generates .d.ts via
  // oxc (purely syntactic) rather than the TypeScript Compiler API — which is
  // what lets the declaration build run under the TS 7 (tsgo) toolchain.
  dts: true,
  sourcemap: true,
  platform: 'neutral', // Browser + Node.js compatibility
  target: 'es2020',
  clean: true,
  // Match the published exports map: CJS -> .cjs, ESM -> .js
  outExtensions: ({ format }) => ({
    js: format === 'cjs' ? '.cjs' : '.js',
  }),
});
