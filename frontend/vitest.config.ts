import { defineConfig, configDefaults } from 'vitest/config'

// Minimal Vitest config for a browser-like test environment
// Docs: test environment (jsdom) & config reference
//  - https://vitest.dev/guide/environment
//  - https://vitest.dev/config/
export default defineConfig({
  test: {
    environment: 'jsdom',
    globals: true,
    // common patterns for React/TS projects
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    exclude: [...configDefaults.exclude],
    coverage: {
      // reporters chosen for local & CI readability
      reporter: ['text', 'json', 'html'],
    },
  },
})
