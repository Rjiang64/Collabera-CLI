// Vite build/dev-server configuration.
//
// WHAT VITE DOES HERE: in development it serves the source files directly to
// the browser and hot-swaps modules as you edit (which is why saving a .jsx
// updates the page without a full reload). For `npm run build` it bundles and
// minifies everything into dist/.
//
// WHY THIS FILE IS SO SHORT: the defaults already cover this project. The React
// plugin is the one thing Vite cannot infer -- it is what compiles JSX into
// real JavaScript and wires up Fast Refresh. Without it, every .jsx file would
// be a syntax error.
//
// Two behaviours worth knowing, both defaults rather than settings:
//   * the dev server runs on port 5173 -- that exact origin is the one listed
//     in the backend's CORS allow-list (app/main.py), so changing it here means
//     changing it there too;
//   * anything imported from src/assets (e.g. logo.png) gets bundled and given
//     a content-hashed filename, while files in public/ are copied as-is.
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
})
