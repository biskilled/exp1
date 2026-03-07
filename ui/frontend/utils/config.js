/**
 * Central frontend configuration.
 *
 * BACKEND_URL resolution order:
 *   1. import.meta.env.VITE_BACKEND_URL  — set at Vite build time via env var
 *   2. window.__BACKEND_URL__            — injected at runtime by server/Electron
 *   3. 'http://localhost:8000'           — local development fallback
 *
 * To target a different backend, set BACKEND_URL in your environment before
 * running `npm run dev` or `npm run build`:
 *   BACKEND_URL=https://my-server.railway.app npm run dev
 */

export const BACKEND_URL =
  (typeof import.meta !== 'undefined' && import.meta.env?.VITE_BACKEND_URL) ||
  (typeof window !== 'undefined' && window.__BACKEND_URL__) ||
  'http://localhost:8000';
