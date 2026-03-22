/**
 * config.js — Central frontend configuration
 *
 * Resolves and exports `BACKEND_URL` using a three-tier fallback: Vite build-time
 * env var (`VITE_BACKEND_URL`), then a runtime value injected by the Electron main
 * process (`window.__BACKEND_URL__`), then the local development default
 * (`http://localhost:8000`). Set `BACKEND_URL` in your environment before
 * `npm run dev` or `npm run build` to target a remote server.
 */

export const BACKEND_URL =
  (typeof import.meta !== 'undefined' && import.meta.env?.VITE_BACKEND_URL) ||
  (typeof window !== 'undefined' && window.__BACKEND_URL__) ||
  'http://localhost:8000';
