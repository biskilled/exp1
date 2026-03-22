/**
 * toast.js — Lightweight toast notification system
 *
 * Exports a single `toast(message, type, duration)` function that appends a
 * self-dismissing notification element to a `.toast-container` div (created on
 * first use). Supports `info`, `success`, and `error` severity types with
 * matching icons, and auto-fades after the configurable `duration` (ms).
 */

export function toast(message, type = 'info', duration = 3000) {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const el = document.createElement('div');
  el.className = `toast ${type}`;

  const icons = { success: '✓', error: '✕', info: 'ℹ' };
  el.innerHTML = `<span>${icons[type] || 'ℹ'}</span><span>${message}</span>`;
  container.appendChild(el);

  setTimeout(() => {
    el.style.opacity = '0';
    el.style.transition = 'opacity 0.3s';
    setTimeout(() => el.remove(), 300);
  }, duration);
}
