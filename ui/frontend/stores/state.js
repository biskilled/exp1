import { BACKEND_URL } from '../utils/config.js';

// Central reactive state
export const state = {
  // Auth
  user: null,           // { id, email, is_admin } from /auth/me
  requireAuth: false,   // from /health

  // Navigation
  activeView: 'home',
  activeSettingsSection: 'apikeys',

  // Projects
  projects: [],          // all projects from /projects/
  currentProject: null,  // { name, description, code_dir, default_provider, ... }
  currentProjectTab: 'chat',  // 'chat' | 'prompts' | 'settings' | 'commands'

  // Workflows
  workflows: [],
  workflowMode: 'yaml',

  // Settings (UI preferences + backend URL; API keys live in localStorage)
  settings: {
    backend_url: BACKEND_URL,
    default_models: {
      claude:   'claude-sonnet-4-6',
      openai:   'gpt-4.1',
      deepseek: 'deepseek-chat',
      gemini:   'gemini-2.0-flash',
      grok:     'grok-3',
    },
    ui: { theme: 'dark', font_size: 13 },
  },

  // Backend
  backendOnline: false,
};

const listeners = new Set();

export function subscribe(fn) {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

export function setState(updates) {
  Object.assign(state, updates);
  listeners.forEach(fn => fn(state));
}
