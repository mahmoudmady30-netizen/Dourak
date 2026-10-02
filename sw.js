const CACHE = 'dourak-v112-shell-v1';
const SHELL = ['./', './index.html', './manifest.json', './icon-192.png', './icon-512.png', './dourak-logo.svg', './dourak-icon.svg'];
const OFFLINE_HTML = '<!doctype html><html lang="ar" dir="rtl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>دورك</title><style>body{margin:0;min-height:100vh;display:grid;place-items:center;background:#F2F7F5;font-family:system-ui,sans-serif;color:#0b2a26;text-align:center}.c{padding:28px;max-width:320px}button{border:0;border-radius:14px;padding:12px 22px;background:#087C68;color:#fff;font-size:15px;font-weight:700}</style><body><div class="c"><h1>دورك</h1><p>لا يوجد اتصال بالإنترنت. عند عودة الاتصال ستستأنف البيانات المباشرة تلقائيًا.</p><button onclick="location.reload()">إعادة المحاولة</button></div>';

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE)
      .then((cache) => cache.addAll(SHELL).catch(() => {}))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  const url = new URL(req.url);
  if (req.method !== 'GET' || url.origin !== self.location.origin) return;

  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req)
        .then((response) => {
          const copy = response.clone();
          caches.open(CACHE).then((cache) => cache.put('./index.html', copy)).catch(() => {});
          return response;
        })
        .catch(() => caches.match('./index.html').then((cached) => cached || new Response(OFFLINE_HTML, {
          headers: {'Content-Type': 'text/html;charset=utf-8'}
        })))
    );
    return;
  }

  event.respondWith(caches.match(req).then((cached) => cached || fetch(req)));
});
