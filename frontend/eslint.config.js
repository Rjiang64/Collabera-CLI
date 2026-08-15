// ESLint configuration -- static checks that run with `npm run lint`.
//
// WHAT IT CATCHES that the build does not: Vite only fails on code it cannot
// compile. ESLint flags code that compiles fine but is still wrong -- an unused
// variable, a missing dependency in a useEffect, a hook called conditionally.
// Those are exactly the bugs that show up at runtime instead of build time.
//
// This is "flat config" (the modern ESLint format): one exported array where
// each entry says which files it applies to and what rules they get, instead of
// the older nested .eslintrc with inheritance.
import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  // dist/ is generated output, not source. Linting it would report thousands of
  // meaningless errors in minified bundles.
  globalIgnores(['dist']),
  {
    files: ['**/*.{js,jsx}'],
    extends: [
      // Baseline rules everyone agrees on: no unused vars, no unreachable code.
      js.configs.recommended,
      // THE IMPORTANT ONE for this project. Enforces the Rules of Hooks --
      // hooks must be called at the top level, in the same order, every render.
      // Breaking that corrupts React's internal state in ways that are very
      // hard to debug by reading the component. It also checks useEffect
      // dependency arrays, which is what catches "this effect uses a value it
      // never listed, so it runs with a stale copy of it".
      reactHooks.configs.flat.recommended,
      // Warns when a file exports things that would break Fast Refresh, so
      // hot-reloading keeps working instead of silently full-reloading.
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      // Tells ESLint that browser globals (window, document, localStorage,
      // fetch) exist. Without this, every use of localStorage in
      // api/client.js and AuthContext.jsx would be reported as undefined.
      globals: globals.browser,
      // JSX is not standard JavaScript syntax -- the parser has to be told to
      // expect it, or every component file fails to parse.
      parserOptions: { ecmaFeatures: { jsx: true } },
    },
  },
])
