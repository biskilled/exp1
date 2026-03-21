/**
 * Mobile Component Patches
 *
 * Import this AFTER main.js in mobile/PWA builds.
 * Patches existing view functions to add mobile-specific behaviour:
 * - Bottom sheets instead of modals
 * - Swipe gestures on chat messages
 * - Pull-to-refresh on sessions
 * - Haptic feedback on key interactions
 * - Session sidebar replaced with bottom sheet
 */

import { device, showBottomSheet, onSwipe, haptic, initPullToRefresh, getDefaultWorkflowMode }
  from './utils/layout.js';
import { setState } from './stores/state.js';

// Only apply patches on mobile/touch
if (device.isTouch) {
  patchModals();
  patchWorkflowMode();
  patchChatView();
  patchProjectView();
  patchNavigation();
}

// ── Patch: Replace modal with bottom sheet on mobile ────────────────────────

function patchModals() {
  // Intercept modal-overlay creation and convert to bottom sheets
  const observer = new MutationObserver(mutations => {
    for (const mutation of mutations) {
      for (const node of mutation.addedNodes) {
        if (node.classList?.contains('modal-overlay')) {
          convertModalToSheet(node);
        }
      }
    }
  });
  observer.observe(document.body, { childList: true });
}

function convertModalToSheet(overlay) {
  const modal = overlay.querySelector('.modal');
  if (!modal) return;

  // Move modal content into a bottom sheet
  const title = modal.querySelector('.modal-title')?.textContent || '';
  const content = modal.innerHTML;

  overlay.remove();

  showBottomSheet({ title, content });
}

// ── Patch: Force steps mode on mobile workflow builder ───────────────────────

function patchWorkflowMode() {
  const originalSetState = setState;
  // When workflow view opens on mobile, override mode
  window.addEventListener('viewchange', e => {
    if (e.detail?.view === 'workflow' && device.isMobile) {
      setState({ workflowMode: getDefaultWorkflowMode() });
    }
  });
}

// ── Patch: Chat view mobile enhancements ─────────────────────────────────────

function patchChatView() {
  // Watch for chat view render
  const observer = new MutationObserver(() => {
    const chatMessages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');

    if (chatMessages && !chatMessages.dataset.mobilePatch) {
      chatMessages.dataset.mobilePatch = '1';
      addChatMobileFeatures(chatMessages, chatInput);
    }
  });
  observer.observe(document.getElementById('app') || document.body, {
    childList: true, subtree: true
  });
}

function addChatMobileFeatures(messages, input) {
  // Pull to refresh sessions list
  initPullToRefresh(messages, async () => {
    haptic('light');
    // Reload sessions
    try {
      const r = await fetch(`${state.settings.backend_url}/history/sessions`);
      const sessions = await r.json();
      updateMobileSessionBadge(sessions.length);
    } catch {}
  });

  // Swipe left on message to copy
  messages.addEventListener('touchstart', e => {
    const bubble = e.target.closest('.msg-bubble') || e.target.closest('[class*="bubble"]');
    if (!bubble) return;

    const cleanup = onSwipe(bubble, {
      onLeft: () => {
        const text = bubble.textContent;
        navigator.clipboard?.writeText(text).then(() => haptic('success'));
        showCopyFeedback(bubble);
        cleanup();
      },
      threshold: 80,
    });
  });

  // Sessions bottom sheet button
  addSessionsButton();
}

function addSessionsButton() {
  const inputArea = document.querySelector('#chat-input')?.closest('div[style]');
  if (!inputArea || document.getElementById('mobile-sessions-btn')) return;

  const btn = document.createElement('button');
  btn.id = 'mobile-sessions-btn';
  btn.style.cssText = `
    position:absolute;top:0.75rem;right:0.75rem;
    background:var(--surface2);border:1px solid var(--border);
    color:var(--text2);font-size:0.7rem;
    padding:0.3rem 0.6rem;border-radius:var(--radius);
    cursor:pointer;z-index:10;
  `;
  btn.textContent = '≡ Sessions';
  btn.onclick = () => showSessionsSheet();

  // Append relative to chat area
  const chatArea = document.querySelector('#chat-messages')?.parentElement;
  if (chatArea) {
    chatArea.style.position = 'relative';
    chatArea.appendChild(btn);
  }
}

async function showSessionsSheet() {
  haptic('light');
  try {
    const r = await fetch(`${state.settings.backend_url}/history/sessions`);
    const sessions = await r.json();

    const content = sessions.length === 0
      ? '<p style="color:var(--muted);font-size:0.78rem">No sessions yet</p>'
      : sessions.slice(0, 15).map(s => `
          <div onclick="window._loadChatSession('${s.id}');document.getElementById('bottom-sheet-overlay')?.remove()"
            style="padding:0.75rem;border-bottom:1px solid var(--border);cursor:pointer;font-size:0.78rem">
            ${s.title || s.id.slice(0, 12)}
            <span style="float:right;font-size:0.6rem;color:var(--muted)">${new Date(s.updated_at).toLocaleDateString()}</span>
          </div>
        `).join('');

    showBottomSheet({
      title: 'Chat Sessions',
      content,
      actions: [{ label: '+ New Chat', style: 'btn-primary', onclick: "window._newChatSession();document.getElementById('bottom-sheet-overlay')?.remove()" }]
    });
  } catch {
    showBottomSheet({ title: 'Sessions', content: '<p style="color:var(--red)">Backend offline</p>' });
  }
}

function showCopyFeedback(el) {
  const feedback = document.createElement('div');
  feedback.textContent = 'Copied!';
  feedback.style.cssText = `
    position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);
    background:var(--surface2);border:1px solid var(--border);
    border-radius:var(--radius);padding:0.5rem 1rem;
    font-size:0.75rem;color:var(--green);z-index:999;
    animation:fadeIn 0.15s ease-out;
  `;
  document.body.appendChild(feedback);
  setTimeout(() => feedback.remove(), 1200);
}

function updateMobileSessionBadge(count) {
  const badge = document.querySelector('#nav-chat .nav-badge');
  if (badge) badge.textContent = count;
}

// ── Patch: Project view mobile — collapsible LLM list ────────────────────────

function patchProjectView() {
  const observer = new MutationObserver(() => {
    const llmList = document.querySelector('.llm-list');
    if (llmList && !llmList.dataset.mobilePatch && device.isMobile) {
      llmList.dataset.mobilePatch = '1';

      // Add horizontal scroll snap
      llmList.style.scrollSnapType = 'x mandatory';
      llmList.querySelectorAll('.llm-item').forEach(item => {
        item.style.scrollSnapAlign = 'start';
      });
    }
  });
  observer.observe(document.getElementById('app') || document.body, {
    childList: true, subtree: true
  });
}

// ── Patch: Navigation — add swipe left/right between main views ───────────────

function patchNavigation() {
  const VIEW_ORDER = ['home', 'projects', 'workflow', 'chat', 'settings'];

  onSwipe(document.getElementById('app') || document.body, {
    onLeft: () => {
      const current = window.__CURRENT_VIEW__ || 'home';
      const idx = VIEW_ORDER.indexOf(current);
      if (idx < VIEW_ORDER.length - 1) {
        haptic('light');
        window._nav(VIEW_ORDER[idx + 1]);
      }
    },
    onRight: () => {
      const current = window.__CURRENT_VIEW__ || 'home';
      const idx = VIEW_ORDER.indexOf(current);
      if (idx > 0) {
        haptic('light');
        window._nav(VIEW_ORDER[idx - 1]);
      }
    },
    threshold: 100, // higher threshold to avoid accidental swipes
  });

  // Track current view
  const origNav = window._nav;
  window._nav = (view, opts) => {
    window.__CURRENT_VIEW__ = view;
    origNav(view, opts);
  };
}
