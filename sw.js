/* Los Tres Reyes — Service Worker
   Nomenclatura secuencial: reyes-vXX (subir el número en cada entrega). */
const CACHE = 'reyes-v7';
const ASSETS = [
  './',
  './index.html',
  './manifest.webmanifest',
  './icon-192.png',
  './icon-512.png',
  './apple-touch-icon.png',
  './favicon-32.png',
  './selenia.jpg'
];

self.addEventListener('install', e=>{
  self.skipWaiting();
  e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)).catch(()=>{}));
});

self.addEventListener('activate', e=>{
  e.waitUntil(
    caches.keys().then(keys=>Promise.all(
      keys.filter(k=>k!==CACHE && /^reyes-v/.test(k)).map(k=>caches.delete(k))
    )).then(()=>self.clients.claim())
  );
});

// cache-first para los assets propios; red para todo lo demás (p.ej. fuentes/firebase)
self.addEventListener('fetch', e=>{
  const url = new URL(e.request.url);
  if(url.origin === location.origin){
    e.respondWith(
      caches.match(e.request).then(r=> r || fetch(e.request).then(resp=>{
        const copy=resp.clone();
        caches.open(CACHE).then(c=>c.put(e.request, copy)).catch(()=>{});
        return resp;
      }).catch(()=>caches.match('./index.html')))
    );
  }
});
