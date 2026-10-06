/* Dourak service worker — installability + a friendly offline page only.
   It deliberately caches NOTHING: every request goes to the network, so a
   new deploy is picked up immediately and nothing conflicts with the app's
   own per-build cache busting. Only same-origin page navigations are
   handled; Firebase, Google and all other requests are left untouched. */
const OFFLINE_HTML = `<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>دورك</title>
<style>body{margin:0;min-height:100vh;display:grid;place-items:center;background:#F2F7F5;font-family:system-ui,sans-serif;color:#0b2a26;text-align:center}
.c{padding:28px;max-width:320px}img{width:84px;height:84px;border-radius:22px}h1{font-size:20px;margin:16px 0 6px}p{color:#5b6f6b;margin:0 0 18px}
button{border:0;border-radius:14px;padding:12px 22px;background:#087C68;color:#fff;font-size:15px;font-weight:700}</style></head>
<body><div class="c"><img src="icon-192.png" alt=""><h1>لا يوجد اتصال بالإنترنت</h1><p>دورك يحتاج اتصالًا لعرض الطابور مباشرة.</p><button onclick="location.reload()">إعادة المحاولة</button></div></body></html>`;
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (event) => event.waitUntil(self.clients.claim()));
self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET' || req.mode !== 'navigate' || new URL(req.url).origin !== self.location.origin) return;
  event.respondWith(fetch(req).catch(() => new Response(OFFLINE_HTML, { headers: { 'Content-Type': 'text/html; charset=utf-8' } })));
});
