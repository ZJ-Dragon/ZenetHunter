

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';

// Vite config with sensible defaults for React + TS
// Docs: https://vite.dev/config/  |  React plugin: https://github.com/vitejs/vite-plugin-react
// Server & preview options: https://vite.dev/config/server-options  |  Build options: https://vite.dev/config/build-options

export default defineConfig(({ mode }) => {
  const isProd = mode === 'production';

  return {
    plugins: [react()],

    // Use `@` to refer to the `src/` directory
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src'), // e.g. import Button from '@/components/Button'
      },
    },

    // Dev server configuration (NAS/LAN friendly)
    server: {
      host: true, // listen on all addresses (0.0.0.0)
      port: 5173,
      strictPort: true, // fail fast if port is taken
      open: false,
    },

    // Preview built assets locally (mirrors server settings)
    preview: {
      host: true,
      port: 5173,
      strictPort: true,
    },

    // Build configuration
    build: {
      outDir: 'dist',
      target: 'es2020',
      sourcemap: !isProd, // helpful in staging/dev; off in production
      assetsInlineLimit: 4 * 1024, // inline small assets as base64 URIs
      rollupOptions: {
        output: {
          manualChunks: {
            react: ['react', 'react-dom'],
          },
        },
      },
    },

    // Define global replacements (available as constants in code)
    // See: https://vite.dev/config/shared-options#define
    define: {
      __APP_VERSION__: JSON.stringify(process.env.npm_package_version || '0.0.0'),
    },

    // Generate CSS sourcemaps in dev for easier debugging
    css: {
      devSourcemap: !isProd,
    },
  };
});
