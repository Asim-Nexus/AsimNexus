/**
 * frontend/public/service-worker.js
 * AsimNexus — PWA Service Worker
 *
 * Provides:
 *   - Offline support via Cache API
 *   - Static asset caching (immutable)
 *   - API response caching (stale-while-revalidate)
 *   - Background sync for offline actions
 *   - Push notification handling
 */

const CACHE_VERSION = 'v1';
const STATIC_CACHE = `asimnexus-static-${CACHE_VERSION}`;
const API_CACHE = `asimnexus-api-${CACHE_VERSION}`;
const DYNAMIC_CACHE = `asimnexus-dynamic-${CACHE_VERSION}`;

// Assets to pre-cache on install
const PRECACHE_ASSETS = [
    '/',
    '/manifest.json',
    '/static/js/bundle.js',
    '/static/js/main.chunk.js',
    '/static/js/0.chunk.js',
    '/static/css/main.chunk.css',
];

// API routes to cache (stale-while-revalidate)
const API_CACHE_ROUTES = [
    '/api/self/knowledge/summary',
    '/api/self/knowledge/modules',
    '/api/self/knowledge/routes',
    '/api/health/live',
    '/api/health/ready',
    '/api/health/status',
];

// ── Install ──────────────────────────────────────────────────────────────

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(STATIC_CACHE).then((cache) => {
            return cache.addAll(PRECACHE_ASSETS);
        }).then(() => {
            return self.skipWaiting();
        })
    );
});

// ── Activate ─────────────────────────────────────────────────────────────

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    .filter((name) => {
                        return name.startsWith('asimnexus-') &&
                            name !== STATIC_CACHE &&
                            name !== API_CACHE &&
                            name !== DYNAMIC_CACHE;
                    })
                    .map((name) => caches.delete(name))
            );
        }).then(() => {
            return self.clients.claim();
        })
    );
});

// ── Fetch ────────────────────────────────────────────────────────────────

self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }

    // Skip non-http(s) requests
    if (!url.protocol.startsWith('http')) {
        return;
    }

    // API requests: stale-while-revalidate
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(staleWhileRevalidate(request, API_CACHE));
        return;
    }

    // Static assets: cache-first
    if (isStaticAsset(request)) {
        event.respondWith(cacheFirst(request, STATIC_CACHE));
        return;
    }

    // Navigation requests: network-first with fallback
    if (request.mode === 'navigate') {
        event.respondWith(networkFirstWithFallback(request));
        return;
    }

    // Everything else: network-first
    event.respondWith(networkFirst(request, DYNAMIC_CACHE));
});

// ── Caching Strategies ───────────────────────────────────────────────────

async function cacheFirst(request, cacheName) {
    const cached = await caches.match(request);
    if (cached) {
        return cached;
    }
    try {
        const response = await fetch(request);
        if (response.ok) {
            const cache = await caches.open(cacheName);
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        return new Response('Offline', { status: 503 });
    }
}

async function networkFirst(request, cacheName) {
    try {
        const response = await fetch(request);
        if (response.ok) {
            const cache = await caches.open(cacheName);
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        const cached = await caches.match(request);
        if (cached) {
            return cached;
        }
        return new Response('Offline', { status: 503 });
    }
}

async function staleWhileRevalidate(request, cacheName) {
    const cache = await caches.open(cacheName);
    const cached = await cache.match(request);

    const fetchPromise = fetch(request).then((response) => {
        if (response.ok) {
            cache.put(request, response.clone());
        }
        return response;
    }).catch(() => cached);

    return cached || fetchPromise;
}

async function networkFirstWithFallback(request) {
    try {
        const response = await fetch(request);
        if (response.ok) {
            const cache = await caches.open(DYNAMIC_CACHE);
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        const cached = await caches.match(request);
        if (cached) {
            return cached;
        }
        // Fallback to cached index.html for SPA routing
        const indexCached = await caches.match('/');
        if (indexCached) {
            return indexCached;
        }
        return new Response('Offline', {
            status: 503,
            headers: { 'Content-Type': 'text/html' },
        });
    }
}

// ── Helpers ──────────────────────────────────────────────────────────────

function isStaticAsset(request) {
    const url = new URL(request.url);
    const extensions = ['.js', '.css', '.png', '.jpg', '.jpeg', '.gif',
        '.svg', '.ico', '.woff', '.woff2', '.ttf', '.eot'];
    return extensions.some((ext) => url.pathname.endsWith(ext));
}

// ── Push Notifications ───────────────────────────────────────────────────

self.addEventListener('push', (event) => {
    let data = {};
    try {
        data = event.data ? event.data.json() : {};
    } catch {
        data = { title: 'ASIMNEXUS', body: event.data?.text() || 'New notification' };
    }

    const options = {
        title: data.title || 'ASIMNEXUS',
        body: data.body || '',
        icon: '/icons/icon-192x192.png',
        badge: '/icons/icon-192x192.png',
        data: data.data || {},
        actions: data.actions || [],
        tag: data.tag || 'default',
        renotify: data.renotify || false,
        requireInteraction: data.requireInteraction || false,
        vibrate: data.vibrate || [200, 100, 200],
    };

    event.waitUntil(self.registration.showNotification(options.title, options));
});

self.addEventListener('notificationclick', (event) => {
    event.notification.close();

    const data = event.notification.data || {};
    const urlToOpen = data.url || '/';

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then((windowClients) => {
                // Focus existing window if available
                for (const client of windowClients) {
                    if (client.url.includes(self.location.origin) && 'focus' in client) {
                        client.postMessage({ type: 'notification-click', data });
                        return client.focus();
                    }
                }
                // Otherwise open new window
                if (clients.openWindow) {
                    return clients.openWindow(urlToOpen);
                }
            })
    );
});

// ── Background Sync ──────────────────────────────────────────────────────

self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-messages') {
        event.waitUntil(syncMessages());
    } else if (event.tag === 'sync-actions') {
        event.waitUntil(syncActions());
    }
});

async function syncMessages() {
    // Placeholder: sync queued messages when back online
    const cache = await caches.open('asimnexus-queue');
    const requests = await cache.keys();
    for (const request of requests) {
        try {
            await fetch(request);
            await cache.delete(request);
        } catch (error) {
            console.error('Background sync failed:', error);
        }
    }
}

async function syncActions() {
    // Placeholder: sync queued user actions when back online
    console.log('Background sync: syncing actions...');
}
