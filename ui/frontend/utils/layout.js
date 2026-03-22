/**
 * layout.js — Responsive layout and device detection
 *
 * Exports the `device` object (isMobile, isTablet, isDesktop, isTouch, isPWA,
 * isIOS, isAndroid, orientation) and `BP` breakpoint constants. Provides
 * `initLayout()` to apply CSS classes to `<html>`, `onLayoutChange(fn)` for
 * resize callbacks, and mobile-specific helpers: `initKeyboardDetection`,
 * `initPullToRefresh`, `showBottomSheet`, `haptic`, `onSwipe`, and
 * `responsiveVal` for breakpoint-aware value selection.
 */

// ── Breakpoints ───────────────────────────────────────────────────────────────
export const BP = {
  MOBILE:  767,
  TABLET:  1100,
};

// ── Device detection ──────────────────────────────────────────────────────────
export const device = {
  get isMobile()  { return window.innerWidth <= BP.MOBILE; },
  get isTablet()  { return window.innerWidth > BP.MOBILE && window.innerWidth <= BP.TABLET; },
  get isDesktop() { return window.innerWidth > BP.TABLET; },
  get isTouch()   { return window.matchMedia('(hover: none) and (pointer: coarse)').matches; },
  get isPWA()     { return window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true; },
  get isIOS()     { return /iPad|iPhone|iPod/.test(navigator.userAgent); },
  get isAndroid() { return /Android/.test(navigator.userAgent); },
  get orientation() { return window.innerWidth > window.innerHeight ? 'landscape' : 'portrait'; },
};

// ── Subscribers ───────────────────────────────────────────────────────────────
const resizeCallbacks = new Set();

export function onLayoutChange(fn) {
  resizeCallbacks.add(fn);
  return () => resizeCallbacks.delete(fn);
}

// Debounced resize handler
let resizeTimer;
window.addEventListener('resize', () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => {
    applyLayoutClasses();
    resizeCallbacks.forEach(fn => fn(device));
  }, 100);
});

// ── Apply layout classes to <html> ────────────────────────────────────────────
export function applyLayoutClasses() {
  const html = document.documentElement;
  html.classList.toggle('is-mobile',  device.isMobile);
  html.classList.toggle('is-tablet',  device.isTablet);
  html.classList.toggle('is-desktop', device.isDesktop);
  html.classList.toggle('is-touch',   device.isTouch);
  html.classList.toggle('is-pwa',     device.isPWA);
  html.classList.toggle('is-ios',     device.isIOS);
  html.classList.toggle('is-android', device.isAndroid);
  html.classList.toggle('is-landscape', device.orientation === 'landscape');
  html.classList.toggle('is-portrait',  device.orientation === 'portrait');
}

// ── Workflow mode selection ───────────────────────────────────────────────────
/**
 * Returns the appropriate default workflow mode for current device.
 * Visual canvas is desktop-only; mobile gets steps, tablet gets steps or yaml.
 */
export function getDefaultWorkflowMode() {
  if (device.isMobile) return 'steps';
  if (device.isTablet) return 'steps';
  return 'visual';
}

// ── Virtual keyboard detection (iOS / Android) ────────────────────────────────
let _viewportHeight = window.innerHeight;

export function initKeyboardDetection() {
  if (!device.isTouch) return;

  window.visualViewport?.addEventListener('resize', () => {
    const current = window.visualViewport.height;
    const diff = _viewportHeight - current;

    if (diff > 100) {
      // Keyboard opened — push content up
      document.body.style.paddingBottom = diff + 'px';
      document.getElementById('app')?.style.setProperty('height', current + 'px');
      // Scroll active input into view
      setTimeout(() => {
        const active = document.activeElement;
        if (active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA')) {
          active.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }, 50);
    } else {
      document.body.style.paddingBottom = '';
      document.getElementById('app')?.style.removeProperty('height');
    }
  });
}

// ── Pull-to-refresh for chat messages ────────────────────────────────────────
export function initPullToRefresh(container, onRefresh) {
  if (!device.isTouch) return;

  let startY = 0;
  let pulling = false;

  container.addEventListener('touchstart', e => {
    if (container.scrollTop === 0) {
      startY = e.touches[0].clientY;
      pulling = true;
    }
  }, { passive: true });

  container.addEventListener('touchmove', e => {
    if (!pulling) return;
    const dy = e.touches[0].clientY - startY;
    if (dy > 0 && dy < 80) {
      container.style.transform = `translateY(${dy * 0.4}px)`;
    }
  }, { passive: true });

  container.addEventListener('touchend', async () => {
    if (!pulling) return;
    pulling = false;
    const current = parseFloat(container.style.transform.replace('translateY(', '') || '0');
    container.style.transform = '';
    if (current > 25) {
      await onRefresh();
    }
  });
}

// ── Bottom sheet (mobile modal replacement) ───────────────────────────────────
export function showBottomSheet({ title, content, actions = [] }) {
  const existing = document.getElementById('bottom-sheet-overlay');
  if (existing) existing.remove();

  const overlay = document.createElement('div');
  overlay.id = 'bottom-sheet-overlay';
  overlay.style.cssText = `
    position:fixed;inset:0;background:rgba(0,0,0,0.6);z-index:500;
    display:flex;align-items:flex-end;
    backdrop-filter:blur(4px);
    animation:fadeIn 0.15s ease-out;
  `;

  const sheet = document.createElement('div');
  sheet.style.cssText = `
    width:100%;
    background:var(--surface);
    border-radius:16px 16px 0 0;
    border-top:1px solid var(--border2);
    padding:0.75rem 1.25rem calc(1.25rem + var(--safe-bottom));
    max-height:85vh;
    overflow-y:auto;
    animation:slideUp 0.25s cubic-bezier(0.32,0.72,0,1);
    -webkit-overflow-scrolling:touch;
  `;

  // Drag handle
  sheet.innerHTML = `
    <div style="width:40px;height:4px;background:var(--border2);border-radius:2px;margin:0 auto 1rem"></div>
    <div style="font-family:var(--font-ui);font-weight:700;font-size:1rem;margin-bottom:0.5rem">${title}</div>
    <div id="bottom-sheet-content">${content}</div>
    ${actions.length ? `
      <div style="display:flex;flex-direction:column;gap:0.5rem;margin-top:1rem">
        ${actions.map(a => `
          <button class="btn ${a.style || 'btn-ghost'}" onclick="${a.onclick}" style="width:100%;min-height:48px;font-size:0.85rem">
            ${a.label}
          </button>
        `).join('')}
        <button class="btn btn-ghost" onclick="document.getElementById('bottom-sheet-overlay').remove()"
          style="width:100%;min-height:48px;color:var(--muted)">Cancel</button>
      </div>
    ` : ''}
  `;

  overlay.appendChild(sheet);
  document.body.appendChild(overlay);

  // Swipe to dismiss
  let startY = 0;
  sheet.addEventListener('touchstart', e => { startY = e.touches[0].clientY; }, { passive: true });
  sheet.addEventListener('touchmove', e => {
    const dy = e.touches[0].clientY - startY;
    if (dy > 0) { sheet.style.transform = `translateY(${Math.min(dy, 200)}px)`; }
  }, { passive: true });
  sheet.addEventListener('touchend', e => {
    const dy = e.changedTouches[0].clientY - startY;
    sheet.style.transform = '';
    if (dy > 80) overlay.remove();
  });

  // Tap backdrop to close
  overlay.addEventListener('click', e => { if (e.target === overlay) overlay.remove(); });

  // Inject keyframe animations
  if (!document.getElementById('sheet-anim')) {
    const style = document.createElement('style');
    style.id = 'sheet-anim';
    style.textContent = `
      @keyframes fadeIn  { from{opacity:0} to{opacity:1} }
      @keyframes slideUp { from{transform:translateY(100%)} to{transform:translateY(0)} }
    `;
    document.head.appendChild(style);
  }

  return overlay;
}

// ── Haptic feedback (mobile) ──────────────────────────────────────────────────
export function haptic(type = 'light') {
  if (!device.isTouch) return;
  try {
    const patterns = { light: [10], medium: [30], heavy: [50], success: [10, 50, 10] };
    navigator.vibrate?.(patterns[type] || [10]);
  } catch {}
}

// ── Swipe gesture detection ───────────────────────────────────────────────────
export function onSwipe(element, { onLeft, onRight, threshold = 60 } = {}) {
  if (!device.isTouch) return () => {};

  let startX = 0;

  const handleStart = e => { startX = e.touches[0].clientX; };
  const handleEnd   = e => {
    const dx = e.changedTouches[0].clientX - startX;
    if (Math.abs(dx) < threshold) return;
    if (dx < 0 && onLeft)  { haptic('light'); onLeft(); }
    if (dx > 0 && onRight) { haptic('light'); onRight(); }
  };

  element.addEventListener('touchstart', handleStart, { passive: true });
  element.addEventListener('touchend',   handleEnd,   { passive: true });

  return () => {
    element.removeEventListener('touchstart', handleStart);
    element.removeEventListener('touchend',   handleEnd);
  };
}

// ── Responsive value helper ───────────────────────────────────────────────────
/**
 * Returns different values based on breakpoint.
 * Usage: responsiveVal({ mobile: 'sm', tablet: 'md', desktop: 'lg' })
 */
export function responsiveVal({ mobile, tablet, desktop }) {
  if (device.isMobile  && mobile  !== undefined) return mobile;
  if (device.isTablet  && tablet  !== undefined) return tablet;
  if (desktop !== undefined) return desktop;
  return mobile ?? tablet ?? desktop;
}

// ── Init ──────────────────────────────────────────────────────────────────────
export function initLayout() {
  applyLayoutClasses();
  initKeyboardDetection();

  // Re-apply on orientation change
  window.addEventListener('orientationchange', () => {
    setTimeout(applyLayoutClasses, 200);
  });

  console.log(`[Layout] ${device.isDesktop?'Desktop':device.isTablet?'Tablet':'Mobile'} · Touch:${device.isTouch} · PWA:${device.isPWA}`);
}
