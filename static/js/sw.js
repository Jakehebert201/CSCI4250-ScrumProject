// Minimal service worker to satisfy registration during development.
// You can expand this with caching strategies later.
self.addEventListener('install', event => {
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', event => {
  // For now, let network handle everything (no caching)
});
