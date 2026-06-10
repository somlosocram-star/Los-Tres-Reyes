/* Los Tres Reyes — Service Worker
   Nomenclatura secuencial: reyes-vXX (subir el número en cada entrega). */
const CACHE = 'reyes-v54';
const ASSETS = [
  './',
  './index.html',
  './manifest.webmanifest',
  './icon-192.png',
  './icon-512.png',
  './apple-touch-icon.png',
  './favicon-32.png',
  './selenia.jpg',
  './ejercito-blanco.png',
  './ejercito-negro.png',
  './ejercito-gris.png',
  './trompeta.mp3',
  './trompeta-mov.mp3',
  './victoria-final.mp3',
  './derrota-final.mp3',
  './vitores.mp3',
  './btn_recruit.png',
  './btn_move.png',
  './btn_upgrade.png',
  './glyph_pueblo.png',
  './glyph_comarca.png',
  './glyph_ciudad.png',
  './troop_infantry.png',
  './troop_archer.png',
  './troop_catapult.png',
  './batalla_inf.png',
  './batalla_arq.png',
  './batalla_cat.png',
  './batalla_victoria.png',
  './batalla_derrota.png',
  './fin_victoria.png',
  './music-intro.mp3',
  './music-game-1.mp3',
  './music-game-2.mp3',
  './music-game-3.mp3'
];

self.addEventListener('install', e=>{
  self.skipWaiting();
  // se cachea cada asset por separado: si alguno falta (404) no rompe el resto
  e.waitUntil(
    caches.open(CACHE).then(c=>Promise.allSettled(ASSETS.map(u=>c.add(u)))).catch(()=>{})
  );
});

self.addEventListener('activate', e=>{
  e.waitUntil(
    caches.keys().then(keys=>Promise.all(
      keys.filter(k=>k!==CACHE && /^reyes-v/.test(k)).map(k=>caches.delete(k))
    )).then(()=>self.clients.claim())
  );
});

// HTML: RED primero (un despliegue nuevo se ve al instante; caché como respaldo offline)
// estáticos: caché primero. Externos (fuentes/firebase): red normal.
self.addEventListener('fetch', e=>{
  const req=e.request, url=new URL(req.url);
  if(url.origin !== location.origin) return;
  const isHTML = req.mode==='navigate' || (req.headers.get('accept')||'').includes('text/html');
  if(isHTML){
    e.respondWith(
      fetch(req).then(resp=>{ const copy=resp.clone();
        caches.open(CACHE).then(c=>c.put('./index.html', copy)).catch(()=>{}); return resp; })
      .catch(()=>caches.match(req).then(r=> r || caches.match('./index.html')))
    );
    return;
  }
  e.respondWith(
    caches.match(req).then(r=> r || fetch(req).then(resp=>{ const copy=resp.clone();
      caches.open(CACHE).then(c=>c.put(req, copy)).catch(()=>{}); return resp; }).catch(()=>undefined))
  );
});
