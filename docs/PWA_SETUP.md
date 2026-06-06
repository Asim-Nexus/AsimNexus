# PWA Setup Guide

> **Version:** 1.0.0+build42 (RC-1)  
> **Last updated:** 2026-05-31  
> **Applies to:** Frontend at [`frontend/react/`](frontend/react/)

---

## Overview

AsimNexus is designed as a Progressive Web Application (PWA), allowing it to be installed on desktop and mobile devices directly from the browser — no app store required.

---

## PWA Files

| File | Path | Purpose |
|------|------|---------|
| Manifest | `frontend/react/public/manifest.json` | App metadata, icons, display mode |
| Service Worker | `frontend/react/public/service-worker.js` | Offline caching, background sync |
| App Shell | `frontend/react/src/App.js` | Main app component (already PWA-compatible) |

---

## Manifest Configuration

The manifest should include:

```json
{
  "name": "AsimNexus",
  "short_name": "AsimNexus",
  "description": "World Operating System — One Kernel. Infinite Worlds.",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#0a0a1a",
  "theme_color": "#00d4ff",
  "icons": [
    {
      "src": "/icons/icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

**Key properties:**
- `display: "standalone"` — Opens without browser chrome
- `start_url: "/"` — Entry point
- `theme_color` — Matches the UI theme

---

## Service Worker

The service worker should handle:

1. **Pre-caching** — Cache the app shell on install
2. **Runtime caching** — Cache API responses for offline access
3. **Offline fallback** — Show cached content when offline
4. **Background sync** — Queue actions for when connectivity returns

### Basic Service Worker Template

```javascript
// frontend/react/public/service-worker.js

const CACHE_NAME = 'asimnexus-v1';
const URLS_TO_CACHE = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json'
];

// Install: pre-cache app shell
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(URLS_TO_CACHE);
    })
  );
});

// Fetch: serve from cache, fallback to network
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request).then(response => {
      return response || fetch(event.request);
    })
  );
});

// Activate: clean old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => {
      return Promise.all(
        keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))
      );
    })
  );
});
```

---

## Registration

In the React entry point (`src/index.js` or similar):

```javascript
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/service-worker.js')
      .then(reg => console.log('SW registered:', reg.scope))
      .catch(err => console.error('SW registration failed:', err));
  });
}
```

---

## Offline-First Architecture

AsimNexus is designed for offline-first operation through:

| Mechanism | Implementation | Status |
|-----------|---------------|--------|
| **Offline Sync Queue** | [`core/identity/personal_os.py`](core/identity/personal_os.py) (OfflineCache class) | **REAL** — Queue, retry, flush, stale cleanup |
| **Local LLM** | GGUF models via llama.cpp | **REAL** — Operates without internet |
| **PWA Cache** | Service worker caching | **CONCEPT** — Needs implementation |
| **Mesh P2P** | Direct peer-to-peer | **PARTIAL** — Framework exists |

---

## Build for Production

```bash
cd frontend/react
npm run build
```

The `build/` directory will contain:
- `build/index.html` — Entry point
- `build/static/` — Bundled JS/CSS
- `build/manifest.json` — PWA manifest
- `build/service-worker.js` — Service worker

Serve the `build/` directory with any static file server:

```bash
npx serve build -s -l 3000
```

---

## Lighthouse Audit

Run a Lighthouse audit to verify PWA readiness:

```bash
npx lighthouse http://localhost:3000 --view
```

### Pass Criteria

| Audit | Requirement | Status |
|-------|-------------|--------|
| `installable-manifest` | Manifest valid with required fields | Needs verification |
| `service-worker` | SW registered and responds | Needs implementation |
| `works-offline` | App returns content when offline | Needs verification |
| `offline-start-url` | Start URL returns 200 when offline | Needs verification |

---

## Mobile-Specific Considerations

### iOS (Safari)
- Full PWA support since iOS 11.3
- Must include `<meta name="apple-mobile-web-app-capable" content="yes">`
- Must include apple-touch-icon links

### Android (Chrome)
- Automatic install prompt when PWA criteria are met
- Add `beforeinstallprompt` event listener for custom install UI

### Windows (Edge)
- Full PWA support
- Can be installed from Edge toolbar

---

## Desktop-Specific Considerations

### Electron Wrapper (Future)
For a native desktop experience, wrap the PWA in Electron:

```bash
npm install -g electron
npx electron-packager . AsimNexus --platform=win32,darwin,linux
```

### Current Desktop Support
The PWA can be installed via browser "Install" button on:
- Chrome/Edge: Install as app
- Safari: Add to Dock
- Firefox: Not supported (use Chrome/Edge)

---

## Verification Checklist

- [ ] `manifest.json` exists with valid JSON
- [ ] `start_url` is set to `/`
- [ ] `display` is `standalone`
- [ ] Icons array has at least 192x192 and 512x512 icons
- [ ] Service worker registers without errors
- [ ] App loads offline (after initial cache)
- [ ] Install prompt fires on supported browsers
- [ ] Lighthouse PWA audit passes

---

## Related

- [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) — System architecture
- [`docs/INSTALL.md`](INSTALL.md) — Installation guide
- [`frontend/react/public/manifest.json`](frontend/react/public/manifest.json) — PWA manifest
