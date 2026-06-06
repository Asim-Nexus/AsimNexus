/*
 * ASIMNEXUS Service Worker v2.0
 * Offline-First PWA with Advanced Sync
 */
const CACHE_VERSION = 'v2';
const STATIC_CACHE = `asimnexus-static-${CACHE_VERSION}`;
const API_CACHE = `asimnexus-api-${CACHE_VERSION}`;
const IMAGE_CACHE = `asimnexus-images-${CACHE_VERSION}`;

const PRECACHE_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/sw.js',
  '/asim-logo.png',
  '/asim-nexus-background.png',
  '/offline.html'
];

// Install — precache static assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => cache.addAll(PRECACHE_ASSETS))
      .then(() => self.skipWaiting())
  );
});

// Activate — clean old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames =>
      Promise.all(
        cacheNames
          .filter(name => !name.includes(CACHE_VERSION))
          .map(name => caches.delete(name))
      )
    ).then(() => self.clients.claim())
  );
});

// Fetch — smart caching strategy
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests for now
  if (request.method !== 'GET') return;

  // API calls — network first, stale-while-revalidate
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirstStrategy(request));
    return;
  }

  // Images — cache first with background update
  if (request.destination === 'image') {
    event.respondWith(cacheFirstStrategy(request, IMAGE_CACHE));
    return;
  }

  // Static assets — cache first
  event.respondWith(cacheFirstStrategy(request, STATIC_CACHE));
});

// Network First Strategy for API
async function networkFirstStrategy(request) {
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(API_CACHE);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    // Return offline response for API
    return new Response(JSON.stringify({
      offline: true,
      message: 'You are offline. Data will sync when connection is restored.',
      timestamp: new Date().toISOString()
    }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

// Cache First Strategy for static assets
async function cacheFirstStrategy(request, cacheName) {
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    // Background update
    fetch(request).then(response => {
      if (response.ok) {
        caches.open(cacheName).then(cache => cache.put(request, response));
      }
    }).catch(() => {});
    return cachedResponse;
  }

  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    return new Response('Offline', { status: 503 });
  }
}

// Background Sync
self.addEventListener('sync', event => {
  if (event.tag === 'sync-messages') {
    event.waitUntil(syncMessages());
  } else if (event.tag === 'sync-offline-data') {
    event.waitUntil(syncOfflineData());
  }
});

async function syncMessages() {
  const db = await openDB('asimnexus-offline', 1);
  const messages = await db.getAll('messages');
  
  for (const msg of messages) {
    try {
      await fetch('/api/chat/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(msg)
      });
      await db.delete('messages', msg.id);
    } catch (e) {
      console.error('Failed to sync message:', e);
    }
  }
}

async function syncOfflineData() {
  const db = await openDB('asimnexus-offline', 1);
  const requests = await db.getAll('requests');
  
  for (const req of requests) {
    try {
      await fetch(req.url, {
        method: req.method,
        headers: req.headers,
        body: req.body
      });
      await db.delete('requests', req.id);
    } catch (e) {
      console.error('Failed to sync request:', e);
    }
  }
}

// Push Notifications
self.addEventListener('push', event => {
  const data = event.data.json();
  
  const options = {
    body: data.body,
    icon: '/asim-logo.png',
    badge: '/asim-logo.png',
    tag: data.tag || 'asimnexus',
    requireInteraction: true,
    actions: data.actions || []
  };

  event.waitUntil(
    self.registration.showNotification(data.title || 'AsimNexus', options)
  );
});

// Notification click
self.addEventListener('notificationclick', event => {
  event.notification.close();
  
  event.waitUntil(
    clients.openWindow(event.notification.data?.url || '/')
  );
});

// IndexedDB helper
function openDB(name, version) {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(name, version);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    request.onupgradeneeded = event => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('messages')) {
        db.createObjectStore('messages', { keyPath: 'id' });
      }
      if (!db.objectStoreNames.contains('requests')) {
        db.createObjectStore('requests', { keyPath: 'id' });
      }
    };
  });
}
