// Service Worker para Discoteca Guerrero PWA
const CACHE_NAME = 'guerrero-disco-v1';

const PRECACHE_ASSETS = [
  './',
  'index.html',
  'baile.html',
  'manifest.webmanifest',
  'manifest.json',
  'favicon.ico',
  'icons/icon-192.png',
  'icons/icon-512.png',
  'icons/icon-maskable-192.png',
  'icons/icon-maskable-512.png',
  'icons/apple-touch-icon.png',
  'icons/favicon-32x32.png',
  'icons/favicon-16x16.png',
  'beat_baile.wav'
];

// Instalación: pre-cacheo de shell
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(PRECACHE_ASSETS).catch((err) => {
        console.warn('[SW] Pre-cache parcial:', err);
      });
    }).then(() => self.skipWaiting())
  );
});

// Activación: limpieza de cachés antiguas y toma de control inmediata
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            console.log('[SW] Eliminando caché obsoleta:', key);
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Intercepción de peticiones con estrategia híbrida
self.addEventListener('fetch', (event) => {
  const req = event.request;

  // Solo peticiones GET y protocolos http/https
  if (req.method !== 'GET' || !req.url.startsWith('http')) {
    return;
  }

  // 1. Navegación (HTML): Red primero, fallback a caché
  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req)
        .then((networkRes) => {
          if (networkRes && networkRes.status === 200) {
            const resClone = networkRes.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(req, resClone));
          }
          return networkRes;
        })
        .catch(() => {
          return caches.match(req).then((cached) => {
            return cached || caches.match('index.html') || caches.match('./');
          });
        })
    );
    return;
  }

  // 2. Modelos 3D (.glb, .gltf), fuentes, scripts CDN y audio
  const url = new URL(req.url);
  const is3DAsset = url.pathname.endsWith('.glb') || url.pathname.endsWith('.gltf');
  const isCDN = url.hostname.includes('cdnjs') || url.hostname.includes('jsdelivr') || url.hostname.includes('unpkg') || url.hostname.includes('googleapis') || url.hostname.includes('gstatic');

  if (is3DAsset || isCDN) {
    // Cache-First con actualización en segundo plano
    event.respondWith(
      caches.match(req).then((cachedRes) => {
        if (cachedRes) {
          // Si ya está en caché, devolverlo inmediatamente y refrescar en segundo plano si hay red
          fetch(req).then((netRes) => {
            if (netRes && netRes.status === 200) {
              caches.open(CACHE_NAME).then((cache) => cache.put(req, netRes));
            }
          }).catch(() => {/* modo offline */});
          return cachedRes;
        }

        // Si no está en caché, descargarlo y guardarlo
        return fetch(req).then((netRes) => {
          if (netRes && netRes.status === 200) {
            const clone = netRes.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(req, clone));
          }
          return netRes;
        });
      })
    );
    return;
  }

  // 3. Resto de recursos (imágenes, CSS, audio local): Stale-While-Revalidate
  event.respondWith(
    caches.match(req).then((cachedRes) => {
      const fetchPromise = fetch(req)
        .then((netRes) => {
          if (netRes && (netRes.status === 200 || netRes.status === 0)) {
            const clone = netRes.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(req, clone));
          }
          return netRes;
        })
        .catch(() => cachedRes);

      return cachedRes || fetchPromise;
    })
  );
});
