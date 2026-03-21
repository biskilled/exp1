"""
PWA router — serves the frontend as a Progressive Web App.
Mount this in main.py to turn the FastAPI backend into a full PWA host.
"""
import os
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

router = APIRouter()

# ── Static file serving ───────────────────────────────────────────────────────
# In production, mount the built Vite output here.
# The frontend/dist folder is created by `npm run build`

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
DIST_DIR     = os.path.join(FRONTEND_DIR, "dist")
STATIC_DIR   = os.path.join(os.path.dirname(__file__), "..", "static")


@router.get("/manifest.json")
async def manifest():
    """PWA web manifest."""
    manifest_path = os.path.join(STATIC_DIR, "manifest.json")
    if os.path.exists(manifest_path):
        return FileResponse(manifest_path, media_type="application/manifest+json")

    # Fallback inline manifest
    return JSONResponse({
        "name": "AgentDesk",
        "short_name": "AgentDesk",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#090910",
        "theme_color": "#0f0f18",
        "icons": [
            {"src": "/static/icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/static/icons/icon-512.png",  "sizes": "512x512",  "type": "image/png"},
        ],
    }, headers={"Content-Type": "application/manifest+json"})


@router.get("/sw.js")
async def service_worker():
    """Service worker — must be served from root scope."""
    sw_path = os.path.join(STATIC_DIR, "sw.js")
    if os.path.exists(sw_path):
        return FileResponse(sw_path, media_type="application/javascript",
                            headers={"Service-Worker-Allowed": "/"})
    return HTMLResponse("// SW not found", media_type="application/javascript")


@router.get("/", response_class=HTMLResponse)
@router.get("/app", response_class=HTMLResponse)
async def index():
    """Serve the SPA shell with PWA meta tags injected."""

    # Check for built dist first
    dist_index = os.path.join(DIST_DIR, "index.html")
    if os.path.exists(dist_index):
        with open(dist_index) as f:
            return HTMLResponse(f.read())

    # Dev fallback — inline SPA shell
    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
  <meta name="theme-color" content="#0f0f18" />
  <meta name="apple-mobile-web-app-capable" content="yes" />
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
  <meta name="apple-mobile-web-app-title" content="AgentDesk" />
  <meta name="mobile-web-app-capable" content="yes" />

  <!-- PWA manifest -->
  <link rel="manifest" href="/manifest.json" />

  <!-- Apple touch icons -->
  <link rel="apple-touch-icon" href="/static/icons/icon-192.png" />

  <!-- Fonts -->
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Syne:wght@400;700;800&display=swap" rel="stylesheet">

  <!-- Styles -->
  <link rel="stylesheet" href="/static/css/main.css" />
  <link rel="stylesheet" href="/static/css/responsive.css" />

  <title>AgentDesk</title>
</head>
<body>
  <div id="app"></div>

  <!-- Scripts -->
  <script type="module" src="/static/js/layout.js"></script>
  <script type="module" src="/static/js/commands.js"></script>
  <script type="module" src="/static/js/app.js"></script>

  <!-- Register service worker -->
  <script>
    if ('serviceWorker' in navigator) {{
      window.addEventListener('load', () => {{
        navigator.serviceWorker.register('/sw.js', {{ scope: '/' }})
          .then(reg => console.log('[SW] Registered, scope:', reg.scope))
          .catch(err => console.warn('[SW] Registration failed:', err));
      }});
    }}

    // Handle PWA launch shortcuts (?view=chat etc)
    const urlParams = new URLSearchParams(window.location.search);
    const view = urlParams.get('view');
    if (view) {{
      window.__INITIAL_VIEW__ = view;
    }}
  </script>
</body>
</html>""")


@router.post("/chat/share")
async def share_target(message: str = ""):
    """Web Share Target — receives shared text and opens as chat message."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/?view=chat&prefill={message}", status_code=303)
