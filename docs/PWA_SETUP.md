# PWA Setup

> **Applies to:** AsimNexus React Frontend

---

## Overview

The AsimNexus frontend is configured as a Progressive Web Application (PWA), allowing it to be installed as a standalone app on desktop and mobile devices.

---

## Manifest

**Location:** [`frontend/react/public/manifest.json`](../frontend/react/public/manifest.json)

The manifest controls how the app appears when installed:

```json
{
  "name": "AsimNexus",
  "short_name": "AsimNexus",
  "description": "World Operating System",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#0a0a1a",
  "theme_color": "#0a0a1a",
  "icons": [
    { "src": "/icon-192x192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icon-512x512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

### Requirements

- `start_url` must be `/` or the app's root path
- `display` must be `standalone` or `fullscreen` for installability
- At least one 192x192 and one 512x512 icon must be defined
- `theme_color` and `background_color` should match the app's design system

---

## Service Worker

**Location:** [`frontend/react/public/service-worker.js`](../frontend/react/public/service-worker.js)

The service worker enables offline caching and faster load times.

### Registration

The service worker is registered in the main app entry point (typically `src/index.js` or `src/App.js`):

```javascript
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/service-worker.js')
      .then(registration => {
        console.log('SW registered:', registration);
      })
      .catch(error => {
        console.log('SW registration failed:', error);
      });
  });
}
```

---

## Building for Production

```bash
cd frontend/react
npm run build
```

The build output will be in `frontend/react/build/`. This directory can be served by any static file server or the AsimNexus backend.

### Verify PWA Compliance

Check that the build output includes:

- `build/manifest.json` — valid JSON with required fields
- `build/service-worker.js` — valid service worker
- `build/icon-192x192.png` — app icon (192x192)
- `build/icon-512x512.png` — app icon (512x512)

---

## Lighthouse Audit

Run a Lighthouse audit to verify PWA compliance:

1. Open the deployed app in Chrome
2. Open DevTools → Lighthouse tab
3. Check **Progressive Web App** category
4. Run audit

### Required PWA Checks

| Check | Requirement |
|-------|-------------|
| `start_url` responds with 200 | App loads at `/` |
| Service worker registered | SW file exists and registers |
| HTTPS or localhost | Required for service worker |
| Manifest has `display: standalone` | Installable |
| Manifest has icons | At least 192x192 and 512x512 |
| Redirects HTTP → HTTPS | If deployed publicly |

---

## Troubleshooting

### Service Worker Not Registering

1. Check that the service worker file exists at the public path
2. Ensure the app is served over HTTPS (or localhost)
3. Check browser console for registration errors

### Manifest Not Loading

1. Verify `manifest.json` is valid JSON
2. Check that `start_url` path is correct
3. Ensure all referenced icon files exist

### App Not Installable

1. Run Lighthouse audit to identify missing requirements
2. Common issues: missing icons, wrong `display` value, no service worker
