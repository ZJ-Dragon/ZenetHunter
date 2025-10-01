

// @ts-check
import { defineConfig } from 'eslint/config';
import js from '@eslint/js';
import tseslint from 'typescript-eslint';
import react from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';
import eslintConfigPrettier from 'eslint-config-prettier/flat';
import globals from 'globals';

// ESLint v9 Flat Config for Vite + React + TypeScript
// - Base: ESLint recommended + typescript-eslint v8 recommended
// - React: plugin-react flat configs (recommended + jsx-runtime)
// - Hooks: plugin-react-hooks recommended-latest for ESLint 9
// - Prettier: turn off conflicting stylistic rules (formatting handled by Prettier itself)
// Docs & references in commit message

export default defineConfig([
  // 0) Global ignores (flat config replaces .eslintignore)
  {
    ignores: ['dist/**', 'build/**', 'node_modules/**']
  },

  // 1) JavaScript & TypeScript base
  js.configs.recommended,
  ...tseslint.configs.recommended,

  // 2) React (flat configs) — note: these don’t set files/globals by default
  {
    files: ['**/*.{ts,tsx,js,jsx}'],
    // spread the flat configs to apply their rules
    ...react.configs.flat.recommended,
    ...react.configs.flat['jsx-runtime'],
    settings: {
      react: { version: 'detect' }
    },
    languageOptions: {
      // provide browser globals (window, document, etc.)
      globals: {
        ...globals.browser
      }
    }
  },

  // 3) React Hooks for ESLint 9 (v5 exposes `recommended-latest` for flat config)
  {
    files: ['**/*.{ts,tsx,js,jsx}'],
    plugins: {
      'react-hooks': reactHooks
    },
    rules: {
      ...reactHooks.configs['recommended-latest'].rules
    }
  },

  // 4) Prettier — disable rules that conflict with Prettier (must be last)
  eslintConfigPrettier
]);
