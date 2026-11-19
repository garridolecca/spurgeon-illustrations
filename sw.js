/* Caches the library, vectors and model on first visit so later visits (and offline use) are instant.
   Versioned data files (?v=...) and model files are cache-first; the app shell is network-first with cache fallback. */
const CACHE = "spurgeon-v1";
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (e) => e.waitUntil(
  caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim())));

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET" || req.headers.has("range")) return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return;
  const versioned = /\/data\//.test(url.pathname) && url.searchParams.has("v");
  const model = /\/models\//.test(url.pathname);
  if (versioned || model) {
    e.respondWith((async () => {
      const cache = await caches.open(CACHE);
      const hit = await cache.match(req);
      if (hit) return hit;
      const res = await fetch(req);
      if (res.ok) {
        await cache.put(req, res.clone());
        if (versioned) {   // drop older versions of the same file
          for (const k of await cache.keys()) {
            const ku = new URL(k.url);
            if (ku.pathname === url.pathname && ku.search !== url.search) await cache.delete(k);
          }
        }
      }
      return res;
    })());
    return;
  }
  e.respondWith((async () => {
    const cache = await caches.open(CACHE);
    try {
      const res = await fetch(req);
      if (res.ok) cache.put(req, res.clone());
      return res;
    } catch {
      const hit = await cache.match(req) || (req.mode === "navigate" ? await cache.match(url.pathname) : undefined);
      if (hit) return hit;
      throw new Error("offline");
    }
  })());
});
