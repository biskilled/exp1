/**
 * Login / Register view.
 *
 * Shown when REQUIRE_AUTH=true on the backend and no valid token is stored.
 * On success, stores JWT in localStorage and calls onSuccess() to continue.
 *
 * Usage:
 *   import { renderLogin } from './views/login.js';
 *   renderLogin(document.body, backendUrl, () => initApp());
 */

export function renderLogin(container, backendUrl, onSuccess) {
  let mode = 'login'; // 'login' | 'register'

  function render() {
    const isRegister = mode === 'register';
    container.innerHTML = `
      <div class="login-overlay">
        <div class="login-card">
          <div class="login-logo">aicli</div>
          <div class="login-subtitle">AI-powered dev CLI</div>

          <div class="login-tabs">
            <button class="login-tab ${!isRegister ? 'active' : ''}" id="tab-login">Sign in</button>
            <button class="login-tab ${isRegister ? 'active' : ''}" id="tab-register">Create account</button>
          </div>

          <form id="login-form">
            <div class="login-field">
              <label>Email</label>
              <input type="email" id="login-email" placeholder="you@example.com" autocomplete="email" required />
            </div>
            <div class="login-field">
              <label>Password</label>
              <input type="password" id="login-password" placeholder="••••••••" autocomplete="${isRegister ? 'new-password' : 'current-password'}" required />
            </div>
            ${isRegister ? `
            <div class="login-field">
              <label>Confirm password</label>
              <input type="password" id="login-confirm" placeholder="••••••••" autocomplete="new-password" required />
            </div>
            <div class="login-field">
              <label>Coupon code <span style="color:var(--text2,#777);font-weight:400">(optional)</span></label>
              <input type="text" id="login-coupon" placeholder="e.g. AICLI" autocomplete="off" />
            </div>` : ''}
            <div id="login-error" class="login-error" style="display:none"></div>
            <button type="submit" class="login-btn" id="login-submit">
              ${isRegister ? 'Create account' : 'Sign in'}
            </button>
          </form>

          <div class="login-note">
            Your API keys are stored locally in this app and sent directly to AI providers.
            The server only tracks token usage — it never sees your keys.
          </div>
        </div>
      </div>
    `;

    _bindStyles();

    document.getElementById('tab-login').onclick = () => { mode = 'login'; render(); };
    document.getElementById('tab-register').onclick = () => { mode = 'register'; render(); };
    document.getElementById('login-form').onsubmit = (e) => _handleSubmit(e);
  }

  async function _handleSubmit(e) {
    e.preventDefault();
    const email = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value;
    const errEl = document.getElementById('login-error');
    const btn = document.getElementById('login-submit');

    if (mode === 'register') {
      const confirm = document.getElementById('login-confirm').value;
      if (password !== confirm) {
        _showError('Passwords do not match');
        return;
      }
    }

    btn.disabled = true;
    btn.textContent = 'Working…';
    errEl.style.display = 'none';

    const endpoint = mode === 'register' ? '/auth/register' : '/auth/login';

    try {
      const res = await fetch(`${backendUrl}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();

      if (!res.ok) {
        _showError(data.detail || 'Authentication failed');
        return;
      }

      // Store token
      localStorage.setItem('aicli_token', data.token);
      localStorage.setItem('aicli_user', JSON.stringify(data.user));

      // Apply coupon code if provided during registration
      if (mode === 'register') {
        const couponEl = document.getElementById('login-coupon');
        const coupon = couponEl?.value.trim();
        if (coupon) {
          try {
            await fetch(`${backendUrl}/billing/apply-coupon`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${data.token}` },
              body: JSON.stringify({ code: coupon }),
            });
          } catch (_) { /* coupon errors are non-fatal */ }
        }
      }

      // Clear login screen and continue
      container.innerHTML = '';
      onSuccess(data.token, data.user);

    } catch (err) {
      _showError(`Connection error: ${err.message}`);
    } finally {
      btn.disabled = false;
      btn.textContent = mode === 'register' ? 'Create account' : 'Sign in';
    }
  }

  function _showError(msg) {
    const errEl = document.getElementById('login-error');
    if (errEl) {
      errEl.textContent = msg;
      errEl.style.display = 'block';
    }
  }

  render();
}


/**
 * Check if a stored token is still valid.
 * Returns {valid: bool, token: str|null, user: dict|null}
 */
export async function checkStoredAuth(backendUrl) {
  const token = localStorage.getItem('aicli_token');
  if (!token) return { valid: false, token: null, user: null };

  try {
    const res = await fetch(`${backendUrl}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) {
      const user = await res.json();
      return { valid: true, token, user };
    }
  } catch (_) {
    // server unreachable — let app continue in offline mode
  }
  return { valid: false, token: null, user: null };
}


export function logout() {
  localStorage.removeItem('aicli_token');
  localStorage.removeItem('aicli_user');
}


// ── Styles ────────────────────────────────────────────────────────────────────

function _bindStyles() {
  if (document.getElementById('login-styles')) return;
  const style = document.createElement('style');
  style.id = 'login-styles';
  style.textContent = `
    .login-overlay {
      position: fixed; inset: 0;
      background: var(--bg, #0d0d0d);
      display: flex; align-items: center; justify-content: center;
      z-index: 9999;
    }
    .login-card {
      background: var(--surface, #1a1a1a);
      border: 1px solid var(--border, #333);
      border-radius: 12px;
      padding: 2rem 2.5rem;
      width: 100%; max-width: 400px;
      box-shadow: 0 24px 64px rgba(0,0,0,.6);
    }
    .login-logo {
      font-family: var(--font-ui, monospace);
      font-size: 1.8rem; font-weight: 900;
      letter-spacing: -2px; color: var(--accent, #7c5cbf);
      margin-bottom: 0.2rem;
    }
    .login-subtitle {
      font-size: 0.72rem; color: var(--text2, #777);
      margin-bottom: 1.5rem;
    }
    .login-tabs {
      display: flex; gap: 0.5rem; margin-bottom: 1.5rem;
    }
    .login-tab {
      flex: 1; padding: 0.45rem;
      background: transparent;
      border: 1px solid var(--border, #333);
      border-radius: 6px;
      color: var(--text2, #888);
      cursor: pointer; font-size: 0.8rem;
      transition: all 0.15s;
    }
    .login-tab.active {
      background: var(--accent, #7c5cbf);
      border-color: var(--accent, #7c5cbf);
      color: #fff;
    }
    .login-field { margin-bottom: 1rem; }
    .login-field label {
      display: block; font-size: 0.72rem;
      color: var(--text2, #777); margin-bottom: 0.35rem;
    }
    .login-field input {
      width: 100%; box-sizing: border-box;
      padding: 0.55rem 0.75rem;
      background: var(--bg, #111);
      border: 1px solid var(--border, #333);
      border-radius: 6px;
      color: var(--text, #eee);
      font-size: 0.88rem;
      outline: none;
    }
    .login-field input:focus { border-color: var(--accent, #7c5cbf); }
    .login-error {
      background: #3d1515; border: 1px solid #7a2a2a;
      border-radius: 6px; padding: 0.5rem 0.75rem;
      color: #ff8080; font-size: 0.78rem;
      margin-bottom: 0.75rem;
    }
    .login-btn {
      width: 100%; padding: 0.65rem;
      background: var(--accent, #7c5cbf);
      border: none; border-radius: 6px;
      color: #fff; font-size: 0.9rem; font-weight: 600;
      cursor: pointer; transition: opacity 0.15s;
    }
    .login-btn:hover { opacity: 0.88; }
    .login-btn:disabled { opacity: 0.5; cursor: not-allowed; }
    .login-note {
      margin-top: 1.25rem;
      font-size: 0.67rem; color: var(--text2, #555);
      text-align: center; line-height: 1.5;
    }
  `;
  document.head.appendChild(style);
}
