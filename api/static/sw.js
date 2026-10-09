const CACHE = "forex-copilot-v3";
const ASSETS = ["/", "/static/app.css", "/static/app.js"];

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE)
      .then(cache => cache.addAll(ASSETS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys.filter(key => key.startsWith("forex-copilot-") && key !== CACHE)
          .map(key => caches.delete(key))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", event => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== "GET" || url.origin !== self.location.origin) return;

  // Market data and app assets must not be served from an old service-worker cache.
  if (url.pathname.startsWith("/mt5/") ||
      url.pathname.startsWith("/health") ||
      url.pathname === "/" ||
      url.pathname.endsWith(".js") ||
      url.pathname.endsWith(".css")) {
    event.respondWith(
      fetch(new Request(request, { cache: "no-store" }))
        .then(response => {
          if (response.ok && !url.pathname.startsWith("/mt5/") && !url.pathname.startsWith("/health")) {
            const copy = response.clone();
            caches.open(CACHE).then(cache => cache.put(request, copy));
          }
          return response;
        })
        .catch(async () => {
          const cached = await caches.match(request);
          if (cached) return cached;
          throw new Error("Network unavailable and no cached app asset exists");
        })
    );
    return;
  }

  event.respondWith(caches.match(request).then(cached => cached || fetch(request)));
});
