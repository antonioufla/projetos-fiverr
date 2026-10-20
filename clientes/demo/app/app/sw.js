// Service worker do OrcaFacil: deixa o app funcionando sem internet.
const CACHE = 'orcafacil-{{VERSAO}}';
const BASE = '{{BASE}}';
const ARQUIVOS = [
  BASE + '/', BASE + '/manifest.webmanifest', BASE + '/static/app.css?v={{VERSAO}}', BASE + '/static/app.js?v={{VERSAO}}',
  BASE + '/static/icons/icon-192.png?v={{VERSAO}}', BASE + '/static/icons/icon-512.png?v={{VERSAO}}', BASE + '/static/icons/favicon.png?v={{VERSAO}}',
];
self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ARQUIVOS)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k.startsWith('orcafacil-') && k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET' || new URL(req.url).origin !== location.origin) return;
  if (req.mode === 'navigate') {
    // pagina: tenta a rede (versao nova), sem internet usa a copia salva
    e.respondWith(fetch(req).then((r) => { const c = r.clone(); caches.open(CACHE).then((x) => x.put(BASE + '/', c)); return r; })
      .catch(() => caches.match(BASE + '/')));
    return;
  }
  // arquivos: cache primeiro, atualiza em segundo plano
  e.respondWith(caches.match(req, { ignoreSearch: true }).then((hit) => {
    const rede = fetch(req).then((r) => { if (r.ok) { const c = r.clone(); caches.open(CACHE).then((x) => x.put(req, c)); } return r; }).catch(() => hit);
    return hit || rede;
  }));
});
