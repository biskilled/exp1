/**
 * Admin panel — 4-tab layout: Users / Pricing / Coupons / API Keys
 * Only accessible to users with role === 'admin' or is_admin === true.
 */

import { api } from '../utils/api.js';
import { toast } from '../utils/toast.js';
import { state } from '../stores/state.js';

export async function renderAdmin(container) {
  container.className = 'view active';
  container.style.cssText = 'display:flex;flex-direction:column;overflow:hidden;height:100%';

  container.innerHTML = `
    <div style="flex:1;display:flex;flex-direction:column;overflow:hidden">
      <div style="padding:0.75rem 1.25rem;border-bottom:1px solid var(--border);
                  display:flex;align-items:center;gap:0.75rem;flex-shrink:0">
        <span style="font-size:0.85rem;font-weight:700;color:var(--text)">Admin Panel</span>
        <div style="flex:1"></div>
      </div>

      <!-- Tab bar -->
      <div style="display:flex;border-bottom:1px solid var(--border);flex-shrink:0;padding:0 1.25rem">
        ${['users','pricing','coupons','apikeys','usage'].map((t, i) => `
          <button id="admin-tab-${t}" onclick="window._adminTab('${t}')"
            style="padding:0.55rem 1rem;border:none;border-bottom:2px solid ${i===0?'var(--accent)':'transparent'};
                   background:none;cursor:pointer;font-size:0.75rem;
                   color:${i===0?'var(--text)':'var(--text2)'};
                   font-weight:${i===0?'600':'normal'};transition:all 0.15s">
            ${{ users:'👥 Users', pricing:'💲 Pricing', coupons:'🎟 Coupons', apikeys:'🔑 API Keys', usage:'📊 Usage' }[t]}
          </button>
        `).join('')}
      </div>

      <div id="admin-body" style="flex:1;overflow-y:auto;padding:1rem 1.25rem"></div>
    </div>
  `;

  let _activeTab = 'users';

  window._adminTab = (tab) => {
    _activeTab = tab;
    ['users','pricing','coupons','apikeys','usage'].forEach(t => {
      const btn = document.getElementById(`admin-tab-${t}`);
      if (btn) {
        btn.style.borderBottomColor = t === tab ? 'var(--accent)' : 'transparent';
        btn.style.color = t === tab ? 'var(--text)' : 'var(--text2)';
        btn.style.fontWeight = t === tab ? '600' : 'normal';
      }
    });
    _renderTab(tab);
  };

  async function _renderTab(tab) {
    const body = document.getElementById('admin-body');
    if (!body) return;
    body.innerHTML = '<div style="color:var(--muted);font-size:0.72rem">Loading…</div>';
    try {
      if (tab === 'users')   await _renderUsers(body);
      if (tab === 'pricing') await _renderPricing(body);
      if (tab === 'coupons') await _renderCoupons(body);
      if (tab === 'apikeys') await _renderApiKeys(body);
      if (tab === 'usage')   await _renderUsage(body);
    } catch (e) {
      body.innerHTML = `<div style="color:var(--red);font-size:0.75rem">Error: ${e.message}</div>`;
    }
  }

  await _renderTab('users');

  window._adminRefreshUsers = async () => {
    const btn  = document.getElementById('admin-stats-refresh');
    const body = document.getElementById('admin-body');
    if (btn) btn.style.opacity = '0.3';
    if (body) await _renderUsers(body).catch(() => {});
    if (btn) btn.style.opacity = '1';
    // Also refresh balance chip + sidebar so platform totals stay in sync
    if (window._updateBalance) window._updateBalance().catch(() => {});
  };
}


// ── Users Tab ─────────────────────────────────────────────────────────────────

async function _renderUsers(body) {
  const [data, stats] = await Promise.all([api.adminListUsers(), api.adminGetStats()]);
  const users = data.users || [];

  const _fmt = (n) => `$${(n || 0).toFixed(2)}`;
  const _stat = (label, val, color = 'var(--text)') =>
    `<div style="display:flex;flex-direction:column;gap:0.2rem">
       <div style="font-size:0.6rem;color:var(--muted);text-transform:uppercase;letter-spacing:0.04em">${label}</div>
       <div style="font-size:0.95rem;font-weight:700;color:${color}">${val}</div>
     </div>`;

  const statsBar = `
    <div style="display:flex;gap:1.5rem;flex-wrap:wrap;align-items:flex-start;background:var(--surface2);
                border:1px solid var(--border);border-radius:var(--radius);
                padding:0.85rem 1.2rem;margin-bottom:1.1rem;position:relative">
      ${_stat('Users', `${stats.active_users ?? users.length} / ${stats.user_count ?? users.length}`)}
      ${_stat('Total Balance', _fmt(stats.total_balance_usd), stats.total_balance_usd >= 0 ? 'var(--green)' : 'var(--red)')}
      ${_stat('Total Added', _fmt(stats.total_added_usd))}
      ${_stat('Total Charged', _fmt(stats.total_charged_usd), 'var(--accent)')}
      ${_stat('Real Cost', _fmt(stats.total_real_cost_usd), 'var(--text2)')}
      ${_stat('Margin', _fmt(stats.total_margin_usd), stats.total_margin_usd >= 0 ? 'var(--green)' : 'var(--red)')}
      <button onclick="window._adminRefreshUsers()" title="Refresh"
        style="position:absolute;top:0.5rem;right:0.5rem;background:none;border:none;
               color:var(--muted);cursor:pointer;font-size:0.8rem;padding:2px 5px;
               border-radius:4px;transition:opacity 0.2s" id="admin-stats-refresh">↺</button>
    </div>`;

  if (!users.length) {
    body.innerHTML = statsBar + '<div class="empty-state"><p>No users yet.</p></div>';
    return;
  }

  body.innerHTML = statsBar + `
    <table style="width:100%;border-collapse:collapse;font-size:0.75rem">
      <thead>
        <tr style="border-bottom:1px solid var(--border);color:var(--muted)">
          <th style="text-align:left;padding:0.4rem 0.5rem;font-weight:500">Email</th>
          <th style="text-align:left;padding:0.4rem 0.5rem;font-weight:500">Role</th>
          <th style="text-align:right;padding:0.4rem 0.5rem;font-weight:500">Balance</th>
          <th style="text-align:right;padding:0.4rem 0.5rem;font-weight:500">Used</th>
          <th style="text-align:right;padding:0.4rem 0.5rem;font-weight:500">Calls</th>
          <th style="text-align:center;padding:0.4rem 0.5rem;font-weight:500">Actions</th>
        </tr>
      </thead>
      <tbody id="admin-users-tbody">
        ${users.map(u => _userRow(u)).join('')}
      </tbody>
    </table>
  `;

  // Bind role selects and credit/delete buttons
  users.forEach(u => _bindUserRow(u));
}

function _userRow(u) {
  const balance = u.balance_usd ?? ((u.balance_added_usd || 0) - (u.balance_used_usd || 0));
  const role = u.role || (u.is_admin ? 'admin' : 'free');
  return `
    <tr id="urow-${u.id}" style="border-bottom:1px solid var(--border)">
      <td style="padding:0.5rem;color:var(--text)">${_esc(u.email)}</td>
      <td style="padding:0.5rem">
        <select id="role-${u.id}" style="background:var(--surface2);border:1px solid var(--border);
                border-radius:4px;color:var(--text);font-size:0.72rem;padding:2px 4px">
          ${['admin','paid','free'].map(r => `<option value="${r}" ${role===r?'selected':''}>${r}</option>`).join('')}
        </select>
      </td>
      <td style="padding:0.5rem;text-align:right;color:${balance>=0.1?'var(--green)':balance>=0?'var(--text2)':'var(--red)'}">
        $${balance.toFixed(2)}
      </td>
      <td style="padding:0.5rem;text-align:right;color:var(--muted)">
        $${(u.balance_used_usd||0).toFixed(4)}
      </td>
      <td style="padding:0.5rem;text-align:right;color:var(--muted)">
        ${u.usage?.total_calls || 0}
      </td>
      <td style="padding:0.5rem;text-align:center">
        <div style="display:flex;gap:4px;justify-content:center;align-items:center">
          <input id="credit-${u.id}" type="number" min="0" step="0.01" placeholder="$"
            style="width:55px;background:var(--surface2);border:1px solid var(--border);
                   border-radius:4px;color:var(--text);font-size:0.72rem;padding:2px 5px" />
          <button id="credit-btn-${u.id}" onclick="window._adminCredit('${u.id}')"
            style="padding:2px 8px;background:var(--accent);border:none;border-radius:4px;
                   color:#fff;font-size:0.7rem;cursor:pointer">+$</button>
          <button onclick="window._adminSaveRole('${u.id}')"
            style="padding:2px 8px;background:var(--surface2);border:1px solid var(--border);
                   border-radius:4px;color:var(--text2);font-size:0.7rem;cursor:pointer">✓</button>
          <button onclick="window._adminDelUser('${u.id}', '${_esc(u.email)}')"
            style="padding:2px 8px;background:none;border:1px solid var(--border);
                   border-radius:4px;color:var(--red);font-size:0.7rem;cursor:pointer">✕</button>
        </div>
      </td>
    </tr>
  `;
}

function _bindUserRow(u) {
  window._adminSaveRole = async (uid) => {
    const sel = document.getElementById(`role-${uid}`);
    if (!sel) return;
    try {
      await api.adminPatchUser(uid, { role: sel.value });
      toast('Role updated', 'success');
    } catch (e) { toast(`Error: ${e.message}`, 'error'); }
  };

  window._adminCredit = async (uid) => {
    const inp = document.getElementById(`credit-${uid}`);
    if (!inp) return;
    const amt = parseFloat(inp.value);
    if (!amt || amt <= 0) { toast('Enter a positive amount', 'error'); return; }
    try {
      await api.adminPatchUser(uid, { credit_usd: amt });
      toast(`$${amt.toFixed(2)} credited`, 'success');
      inp.value = '';
      // Refresh users tab
      const body = document.getElementById('admin-body');
      if (body) { body.innerHTML = '<div style="color:var(--muted);font-size:0.72rem">Refreshing…</div>'; await _renderUsers(body); }
    } catch (e) { toast(`Error: ${e.message}`, 'error'); }
  };

  window._adminDelUser = async (uid, email) => {
    if (!confirm(`Deactivate user: ${email}?`)) return;
    try {
      await api.adminDeleteUser(uid);
      toast(`User deactivated: ${email}`, 'success');
      const row = document.getElementById(`urow-${uid}`);
      if (row) row.style.opacity = '0.3';
    } catch (e) { toast(`Error: ${e.message}`, 'error'); }
  };
}

function _esc(s) {
  return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}


// ── Pricing Tab ───────────────────────────────────────────────────────────────

async function _renderPricing(body) {
  const p = await api.adminGetPricing();

  const providers = ['claude','openai','deepseek','gemini','grok'];
  const allModels = [
    'claude-sonnet-4-6','claude-haiku-4-5-20251001','gpt-4.1','deepseek-chat',
    'gemini-2.0-flash','grok-3',
  ];

  body.innerHTML = `
    <div style="max-width:600px">
      <div style="font-weight:700;font-size:0.8rem;margin-bottom:1rem">Pricing Configuration</div>

      <div style="margin-bottom:1.25rem">
        <div style="font-size:0.72rem;color:var(--text2);margin-bottom:0.4rem">Free Tier Limit (USD)</div>
        <input id="price-free-limit" type="number" min="0" step="0.5"
          value="${p.free_tier_limit_usd ?? 5}"
          style="width:120px;background:var(--surface2);border:1px solid var(--border);
                 border-radius:6px;color:var(--text);font-size:0.82rem;padding:0.4rem 0.6rem" />
        <span style="font-size:0.65rem;color:var(--muted);margin-left:0.5rem">Maximum spend for free-tier users</span>
      </div>

      <div style="margin-bottom:1.25rem">
        <div style="font-size:0.72rem;color:var(--text2);margin-bottom:0.5rem">Free Tier Models</div>
        <div style="display:flex;flex-wrap:wrap;gap:0.4rem">
          ${allModels.map(m => `
            <label style="display:flex;align-items:center;gap:0.35rem;font-size:0.72rem;cursor:pointer;
                           background:var(--surface2);border:1px solid var(--border);border-radius:4px;padding:0.25rem 0.5rem">
              <input type="checkbox" id="ftm-${m.replace(/[^a-z0-9]/gi,'-')}"
                ${(p.free_tier_models||[]).includes(m)?'checked':''}
                style="accent-color:var(--accent)" />
              ${m}
            </label>
          `).join('')}
        </div>
      </div>

      <div style="margin-bottom:1.5rem">
        <div style="font-size:0.72rem;color:var(--text2);margin-bottom:0.5rem">Markup % per Provider</div>
        <div style="display:flex;flex-direction:column;gap:0.5rem">
          ${providers.map(prov => `
            <div style="display:flex;align-items:center;gap:0.75rem">
              <div style="width:80px;font-size:0.75rem">${prov}</div>
              <input id="markup-${prov}" type="number" min="0" max="500" step="5"
                value="${p.providers?.[prov]?.markup_percent ?? 0}"
                style="width:80px;background:var(--surface2);border:1px solid var(--border);
                       border-radius:6px;color:var(--text);font-size:0.8rem;padding:0.3rem 0.5rem" />
              <span style="font-size:0.68rem;color:var(--muted)">%</span>
            </div>
          `).join('')}
        </div>
      </div>

      <button onclick="window._savePricing()"
        style="padding:0.5rem 1.25rem;background:var(--accent);border:none;border-radius:6px;
               color:#fff;font-size:0.82rem;font-weight:600;cursor:pointer">
        Save Pricing
      </button>
      <span id="pricing-status" style="font-size:0.68rem;color:var(--muted);margin-left:0.75rem"></span>
    </div>
  `;

  window._savePricing = async () => {
    const freeLimit = parseFloat(document.getElementById('price-free-limit').value) || 5;
    const freeModels = allModels.filter(m => {
      const el = document.getElementById(`ftm-${m.replace(/[^a-z0-9]/gi,'-')}`);
      return el?.checked;
    });
    const provCfg = {};
    providers.forEach(prov => {
      const el = document.getElementById(`markup-${prov}`);
      provCfg[prov] = { markup_percent: parseFloat(el?.value || '0') };
    });
    const statusEl = document.getElementById('pricing-status');
    try {
      await api.adminSavePricing({
        free_tier_limit_usd: freeLimit,
        free_tier_models: freeModels,
        providers: provCfg,
      });
      if (statusEl) { statusEl.textContent = '✓ Saved'; statusEl.style.color = 'var(--green)'; }
      toast('Pricing saved', 'success');
    } catch (e) {
      if (statusEl) { statusEl.textContent = `✕ ${e.message}`; statusEl.style.color = 'var(--red)'; }
      toast(`Save failed: ${e.message}`, 'error');
    }
  };
}


// ── Coupons Tab ───────────────────────────────────────────────────────────────

async function _renderCoupons(body) {
  const data = await api.adminGetCoupons();
  const coupons = data.coupons || [];

  body.innerHTML = `
    <div style="max-width:700px">
      <div style="font-weight:700;font-size:0.8rem;margin-bottom:1rem">Coupon Codes</div>

      <!-- Create form -->
      <div style="background:var(--surface2);border:1px solid var(--border);border-radius:var(--radius);
                  padding:0.75rem 1rem;margin-bottom:1.25rem">
        <div style="font-size:0.72rem;font-weight:600;margin-bottom:0.6rem">Create New Coupon</div>
        <div style="display:flex;gap:0.5rem;flex-wrap:wrap;align-items:flex-end">
          <div>
            <div style="font-size:0.62rem;color:var(--muted);margin-bottom:0.2rem">Code</div>
            <input id="new-coupon-code" placeholder="MYCODE" style="width:110px;${_inp()}"/>
          </div>
          <div>
            <div style="font-size:0.62rem;color:var(--muted);margin-bottom:0.2rem">Amount ($)</div>
            <input id="new-coupon-amount" type="number" min="0" step="0.5" value="10" style="width:80px;${_inp()}"/>
          </div>
          <div>
            <div style="font-size:0.62rem;color:var(--muted);margin-bottom:0.2rem">Max Uses</div>
            <input id="new-coupon-uses" type="number" min="1" value="999" style="width:80px;${_inp()}"/>
          </div>
          <div>
            <div style="font-size:0.62rem;color:var(--muted);margin-bottom:0.2rem">Description</div>
            <input id="new-coupon-desc" placeholder="Optional" style="width:160px;${_inp()}"/>
          </div>
          <button onclick="window._createCoupon()"
            style="padding:0.4rem 1rem;background:var(--accent);border:none;border-radius:6px;
                   color:#fff;font-size:0.78rem;cursor:pointer;white-space:nowrap">
            + Create
          </button>
        </div>
        <div id="coupon-create-status" style="font-size:0.65rem;color:var(--muted);margin-top:0.4rem"></div>
      </div>

      <!-- Coupon table -->
      <table style="width:100%;border-collapse:collapse;font-size:0.75rem">
        <thead>
          <tr style="border-bottom:1px solid var(--border);color:var(--muted)">
            <th style="text-align:left;padding:0.4rem 0.5rem;font-weight:500">Code</th>
            <th style="text-align:right;padding:0.4rem 0.5rem;font-weight:500">Amount</th>
            <th style="text-align:right;padding:0.4rem 0.5rem;font-weight:500">Uses</th>
            <th style="text-align:left;padding:0.4rem 0.5rem;font-weight:500">Description</th>
            <th style="text-align:center;padding:0.4rem 0.5rem;font-weight:500">Actions</th>
          </tr>
        </thead>
        <tbody>
          ${coupons.map(c => `
            <tr style="border-bottom:1px solid var(--border)">
              <td style="padding:0.5rem;font-family:monospace;color:var(--accent)">${_esc(c.code)}</td>
              <td style="padding:0.5rem;text-align:right">$${(c.amount_usd||0).toFixed(2)}</td>
              <td style="padding:0.5rem;text-align:right;color:var(--muted)">${c.used_count||0} / ${c.max_uses||'∞'}</td>
              <td style="padding:0.5rem;color:var(--text2)">${_esc(c.description||'')}</td>
              <td style="padding:0.5rem;text-align:center">
                <button onclick="window._deleteCoupon('${_esc(c.code)}')"
                  style="padding:2px 8px;background:none;border:1px solid var(--border);
                         border-radius:4px;color:var(--red);font-size:0.7rem;cursor:pointer">✕</button>
              </td>
            </tr>
          `).join('')}
          ${!coupons.length ? '<tr><td colspan="5" style="padding:1rem;text-align:center;color:var(--muted)">No coupons yet</td></tr>' : ''}
        </tbody>
      </table>
    </div>
  `;

  window._createCoupon = async () => {
    const code   = document.getElementById('new-coupon-code')?.value.trim().toUpperCase();
    const amount = parseFloat(document.getElementById('new-coupon-amount')?.value || '0');
    const uses   = parseInt(document.getElementById('new-coupon-uses')?.value || '1', 10);
    const desc   = document.getElementById('new-coupon-desc')?.value.trim();
    const st     = document.getElementById('coupon-create-status');
    if (!code) { if (st) { st.textContent = 'Enter a code'; st.style.color = 'var(--red)'; } return; }
    if (!amount || amount <= 0) { if (st) { st.textContent = 'Enter a positive amount'; st.style.color = 'var(--red)'; } return; }
    try {
      await api.adminCreateCoupon({ code, amount_usd: amount, max_uses: uses, description: desc });
      if (st) { st.textContent = `✓ Coupon ${code} created`; st.style.color = 'var(--green)'; }
      toast(`Coupon ${code} created`, 'success');
      // Refresh
      const body = document.getElementById('admin-body');
      if (body) await _renderCoupons(body);
    } catch (e) {
      if (st) { st.textContent = `✕ ${e.message}`; st.style.color = 'var(--red)'; }
      toast(`Error: ${e.message}`, 'error');
    }
  };

  window._deleteCoupon = async (code) => {
    if (!confirm(`Delete coupon ${code}?`)) return;
    try {
      await api.adminDeleteCoupon(code);
      toast(`Coupon ${code} deleted`, 'success');
      const body = document.getElementById('admin-body');
      if (body) await _renderCoupons(body);
    } catch (e) { toast(`Error: ${e.message}`, 'error'); }
  };
}

function _inp() {
  return 'background:var(--bg);border:1px solid var(--border);border-radius:4px;color:var(--text);font-size:0.78rem;padding:0.3rem 0.5rem;';
}


// ── API Keys Tab ──────────────────────────────────────────────────────────────

async function _renderApiKeys(body) {
  const [keysInfo, stats, liveBalances] = await Promise.all([
    api.adminGetApiKeys(),
    api.adminGetStats(),
    api.adminGetApiBalances().catch(() => ({})),
  ]);
  const byProvider = stats.by_provider || {};
  const providers = [
    { id: 'claude',   label: 'Claude (Anthropic)' },
    { id: 'openai',   label: 'OpenAI' },
    { id: 'deepseek', label: 'DeepSeek' },
    { id: 'gemini',   label: 'Gemini' },
    { id: 'grok',     label: 'Grok (xAI)' },
  ];

  const _sourceBadge = (src) => {
    const cfg = {
      saved:  { label: 'saved',     color: 'var(--green)',  bg: 'rgba(34,197,94,0.1)' },
      env:    { label: 'from .env', color: 'var(--accent)', bg: 'rgba(255,107,53,0.1)' },
      unset:  { label: 'not set',   color: 'var(--muted)',  bg: 'var(--surface2)' },
    }[src] || { label: src, color: 'var(--muted)', bg: 'var(--surface2)' };
    return `<span style="font-size:0.6rem;padding:1px 6px;border-radius:10px;
                         background:${cfg.bg};color:${cfg.color};font-weight:500">${cfg.label}</span>`;
  };

  const _liveBalBadge = (bal) => {
    if (!bal || !bal.available) {
      const reason = bal?.reason === 'no_key' ? 'no key' : bal?.reason === 'unsupported' ? 'N/A' : 'N/A';
      return `<span style="font-size:0.6rem;color:var(--muted)">API balance: ${reason}</span>`;
    }
    const color = bal.balance_usd >= 5 ? 'var(--green)' : bal.balance_usd >= 1 ? 'var(--accent)' : 'var(--red)';
    return `<span style="font-size:0.65rem;font-weight:600;color:${color}">
              API balance: $${bal.balance_usd.toFixed(2)}
            </span>`;
  };

  body.innerHTML = `
    <div style="max-width:640px">
      <div style="font-weight:700;font-size:0.8rem;margin-bottom:0.25rem">Server API Keys</div>
      <div style="font-size:0.65rem;color:var(--muted);margin-bottom:1.25rem">
        Keys are stored in <code>api_keys.json</code> — your <code>.env</code> file is never modified.
        Leave a field blank to keep the current key. Live balance shown where provider API supports it.
      </div>

      <div style="display:flex;flex-direction:column;gap:1.1rem">
        ${providers.map(p => {
          const info    = keysInfo[p.id]     || { masked: '', source: 'unset' };
          const usage   = byProvider[p.id]   || null;
          const liveBal = liveBalances[p.id] || null;
          const usageLine = usage
            ? `<span style="color:var(--accent)">$${usage.charged_usd.toFixed(4)} charged</span>
               <span style="color:var(--muted)">·</span>
               <span style="color:var(--text2)">$${usage.real_cost_usd.toFixed(4)} real</span>
               <span style="color:var(--muted)">·</span>
               <span>${usage.calls} call${usage.calls !== 1 ? 's' : ''}</span>`
            : `<span style="color:var(--muted)">No usage recorded yet</span>`;
          return `
          <div style="background:var(--surface2);border:1px solid var(--border);
                      border-radius:var(--radius);padding:0.65rem 0.85rem">
            <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.3rem;flex-wrap:wrap">
              <div style="font-size:0.75rem;font-weight:600;color:var(--text)">${p.label}</div>
              ${_sourceBadge(info.source)}
              ${_liveBalBadge(liveBal)}
            </div>
            <div style="font-size:0.6rem;color:var(--muted);margin-bottom:0.4rem;
                        display:flex;gap:0.4rem;align-items:center;flex-wrap:wrap">
              <span style="color:var(--text2);font-weight:500">Your tracked spend:</span>
              ${usageLine}
            </div>
            <div style="display:flex;gap:0.5rem;align-items:center">
              <input id="apikey-${p.id}" type="password"
                placeholder="${info.masked ? info.masked : 'Not configured'}"
                style="flex:1;${_inp()}" />
              <button onclick="window._toggleKeyVis('${p.id}')"
                style="background:none;border:1px solid var(--border);border-radius:4px;
                       color:var(--text2);font-size:0.72rem;padding:4px 8px;cursor:pointer">👁</button>
            </div>
          </div>`;
        }).join('')}
      </div>

      <div style="margin-top:1.25rem;display:flex;gap:0.75rem;align-items:center">
        <button onclick="window._saveApiKeys()"
          style="padding:0.5rem 1.25rem;background:var(--accent);border:none;border-radius:6px;
                 color:#fff;font-size:0.82rem;font-weight:600;cursor:pointer">
          Save API Keys
        </button>
        <span id="apikeys-status" style="font-size:0.68rem;color:var(--muted)"></span>
      </div>
      <div style="margin-top:0.75rem;font-size:0.65rem;color:var(--muted)">
        Only filled fields are updated. Leave blank to keep the current key.
        <em>API balance</em> is queried live from each provider (DeepSeek only; others don't expose a balance endpoint).
        <em>Tracked spend</em> is what this server charged users through these keys.
      </div>
    </div>
  `;

  window._toggleKeyVis = (id) => {
    const inp = document.getElementById(`apikey-${id}`);
    if (inp) inp.type = inp.type === 'password' ? 'text' : 'password';
  };

  window._saveApiKeys = async () => {
    const keys = {};
    providers.forEach(p => {
      const val = document.getElementById(`apikey-${p.id}`)?.value.trim();
      if (val) keys[p.id] = val;
    });
    const statusEl = document.getElementById('apikeys-status');
    try {
      await api.adminSaveApiKeys(keys);
      if (statusEl) { statusEl.textContent = '✓ Keys saved'; statusEl.style.color = 'var(--green)'; }
      toast('API keys saved', 'success');
      // Refresh to show updated masked values
      const body = document.getElementById('admin-body');
      if (body) await _renderApiKeys(body);
    } catch (e) {
      if (statusEl) { statusEl.textContent = `✕ ${e.message}`; statusEl.style.color = 'var(--red)'; }
      toast(`Error: ${e.message}`, 'error');
    }
  };
}


// ── Usage Tab ─────────────────────────────────────────────────────────────────

async function _renderUsage(body) {
  const data = await api.adminGetUsageTable();
  const rows  = data.rows        || [];
  const sys   = data.system_rows || [];

  const _fmt  = (n, d = 4) => n != null ? `$${Number(n).toFixed(d)}` : '—';
  const _fmtN = (n) => n != null ? Number(n).toLocaleString() : '—';
  const _mclr = (m) => m > 0 ? 'var(--green)' : m < 0 ? 'var(--red)' : 'var(--text2)';

  // System totals header
  const _sysRow = (s) => {
    const bal = s.api_balance || {};
    let balTxt = '—';
    let balColor = 'var(--muted)';
    if (bal.available) {
      balTxt  = `$${bal.balance_usd.toFixed(2)}`;
      balColor = bal.balance_usd >= 5 ? 'var(--green)' : bal.balance_usd >= 1 ? 'var(--accent)' : 'var(--red)';
    } else if (bal.reason === 'unsupported') {
      balTxt = 'N/A';
    } else if (bal.reason === 'no_key') {
      balTxt = 'no key';
    }
    return `
      <tr style="background:var(--surface2)">
        <td style="padding:0.45rem 0.5rem;font-size:0.7rem;color:var(--muted);font-style:italic">system</td>
        <td style="padding:0.45rem 0.5rem;font-size:0.72rem;color:var(--text2)">${_esc(s.provider)}</td>
        <td style="padding:0.45rem 0.5rem;font-family:monospace;font-size:0.65rem;color:var(--muted)">${_esc(s.api_key_masked || '—')}</td>
        <td colspan="3" style="padding:0.45rem 0.5rem;font-size:0.7rem;color:var(--muted);text-align:center">
          live API balance only
        </td>
        <td style="padding:0.45rem 0.5rem;font-size:0.72rem;font-weight:700;text-align:right;color:${balColor}">${balTxt}</td>
        <td colspan="4" style="padding:0.45rem 0.5rem"></td>
      </tr>`;
  };

  // Group rows by date for visual separation
  let lastDate = '';
  const _dataRows = rows.map(r => {
    const dateHdr = r.date !== lastDate
      ? `<tr><td colspan="11" style="padding:0.3rem 0.5rem;font-size:0.65rem;font-weight:600;
              color:var(--muted);background:var(--surface);border-top:1px solid var(--border);
              border-bottom:1px solid var(--border)">${r.date}</td></tr>`
      : '';
    lastDate = r.date;
    return dateHdr + `
      <tr style="border-bottom:1px solid var(--border)">
        <td style="padding:0.4rem 0.5rem;font-size:0.7rem;color:var(--muted)">${r.date}</td>
        <td style="padding:0.4rem 0.5rem;font-size:0.72rem;overflow:hidden;max-width:120px;
                   text-overflow:ellipsis;white-space:nowrap" title="${_esc(r.email)}">${_esc(r.email)}</td>
        <td style="padding:0.4rem 0.5rem;font-size:0.72rem;color:var(--text2)">${_esc(r.llm)}</td>
        <td style="padding:0.4rem 0.5rem;font-family:monospace;font-size:0.62rem;color:var(--muted)">${_esc(r.api_key_masked || '—')}</td>
        <td style="padding:0.4rem 0.5rem;text-align:right;font-size:0.72rem">${_fmtN(r.tokens)}</td>
        <td style="padding:0.4rem 0.5rem;text-align:right;font-size:0.72rem;color:var(--text2)">${_fmt(r.cost)}</td>
        <td style="padding:0.4rem 0.5rem;text-align:right;font-size:0.72rem;color:var(--accent)">${_fmt(r.revenue)}</td>
        <td style="padding:0.4rem 0.5rem;text-align:right;font-size:0.72rem;color:${_mclr(r.margin)}">${_fmt(r.margin)}</td>
        <td style="padding:0.4rem 0.5rem;text-align:right;font-size:0.72rem">${_fmt(r.balance, 2)}</td>
        <td style="padding:0.4rem 0.5rem;text-align:right;font-size:0.72rem;color:var(--green)">
          ${r.topup_cash > 0 ? `${_fmt(r.topup_cash, 2)} (${r.topup_cash_cnt}×)` : '—'}
        </td>
        <td style="padding:0.4rem 0.5rem;text-align:right;font-size:0.72rem;color:var(--accent)">
          ${r.topup_coupon > 0 ? `${_fmt(r.topup_coupon, 2)} (${r.topup_coupon_cnt}×)` : '—'}
        </td>
      </tr>`;
  }).join('');

  const _th = (label, align = 'right') =>
    `<th style="text-align:${align};padding:0.4rem 0.5rem;font-weight:500;font-size:0.65rem;
               color:var(--muted);white-space:nowrap">${label}</th>`;

  body.innerHTML = `
    <div style="font-weight:700;font-size:0.8rem;margin-bottom:0.25rem">Usage & Revenue</div>
    <div style="font-size:0.65rem;color:var(--muted);margin-bottom:1rem">
      Daily aggregated by user × LLM. System rows show live API balance from provider.
    </div>

    <div style="overflow-x:auto">
      <table style="width:100%;border-collapse:collapse;font-size:0.75rem;min-width:820px">
        <thead>
          <tr style="border-bottom:2px solid var(--border)">
            ${_th('Date', 'left')}
            ${_th('User', 'left')}
            ${_th('LLM', 'left')}
            ${_th('API Key', 'left')}
            ${_th('Tokens')}
            ${_th('Cost')}
            ${_th('Revenue')}
            ${_th('Margin')}
            ${_th('Balance')}
            ${_th('Cash Topup')}
            ${_th('Coupon Topup')}
          </tr>
        </thead>
        <tbody>
          <!-- System rows (live API balances) -->
          <tr><td colspan="11" style="padding:0.3rem 0.5rem;font-size:0.65rem;font-weight:600;
                color:var(--muted);background:var(--surface2);border-bottom:1px solid var(--border)">
            System — Live API Balances
          </td></tr>
          ${sys.map(_sysRow).join('')}
          <!-- Data rows -->
          ${_dataRows || `<tr><td colspan="11" style="padding:1.5rem;text-align:center;color:var(--muted);font-size:0.75rem">
            No usage data yet. Usage will appear here after the first chat message.
          </td></tr>`}
        </tbody>
      </table>
    </div>
  `;
}
