

const CACHE_NAME = 'studio02-v1';
// Lista mínima para que no dé error al refrescar
const ASSETS = [
  '/',
  '/static/css/styles.css',
  '/static/js/calendario.js',
  'https://cdn.jsdelivr.net/npm/fullcalendar@6.1.10/index.global.min.js',
  'https://cdn.jsdelivr.net/npm/fullcalendar@6.1.10/index.global.min.css'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      // Usamos .addAll pero solo con archivos locales garantizados
      return cache.addAll(ASSETS);
    }).catch(err => console.log('Error en caché:', err))
  );
});

// Estrategia: Network First (prioriza red, si falla, usa caché)
self.addEventListener('fetch', (e) => {
  e.respondWith(
    fetch(e.request).catch(() => caches.match(e.request))
  );
});