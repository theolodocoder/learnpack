// Web version only: makes repeat visits load from cache and lets the app work offline.
//  - On install: caches the app and every library index.html references, plus the bundled packs.
//  - Our own files: answered from cache at once, refreshed in the background (the next visit gets updates).
//  - Versioned CDN files, Python and its packages: cached the first time, then served from cache.
// Progress, notes and code live in IndexedDB and are never touched here.
const BUILD = "dev";  // replaced with a build id by `server.py build-web`
const SHELL = `learnpack-shell-${BUILD}`;
const RUNTIME = "learnpack-runtime-v1";

// Files that never change at a given URL (versioned), so cache-first is safe.
const IMMUTABLE = /^https:\/\/(cdnjs\.cloudflare\.com|cdn\.jsdelivr\.net|fonts\.gstatic\.com|files\.pythonhosted\.org)\//;
// Changes now and then: serve the cached copy, refresh it in the background.
const REFRESH = /^https:\/\/(fonts\.googleapis\.com|pypi\.org)\//;

self.addEventListener("install", (e) => {
  e.waitUntil((async () => {
    const cache = await caches.open(SHELL);
    const html = await (await fetch("./", { cache: "no-cache" })).text();
    const refs = [...html.matchAll(/(?:src|href)="([^"#]+)"/g)].map((m) => m[1]).filter((u) => !u.startsWith("data:"));
    const own = ["./", "py-worker.js", "js-worker.js", "packs/index.json"].map((u) => (u.endsWith(".js") ? `${u}?v=${BUILD}` : u));
    const index = await (await fetch("packs/index.json", { cache: "no-cache" })).json().catch(() => []);
    const packs = index.map((c) => `packs/${encodeURIComponent(c.id)}.json`);
    // One failed file shouldn't stop the rest from being cached.
    await Promise.all([...own, ...refs, ...packs].map((u) => cache.add(new Request(u, { mode: u.startsWith("http") ? "cors" : "same-origin" })).catch(() => {})));
    self.skipWaiting();
  })());
});

self.addEventListener("activate", (e) => {
  e.waitUntil((async () => {
    for (const k of await caches.keys()) if (k.startsWith("learnpack-shell-") && k !== SHELL) await caches.delete(k);
    await self.clients.claim();
  })());
});

async function cacheFirst(req) {
  const hit = await caches.match(req);
  if (hit) return hit;
  const res = await fetch(req);
  if (res.ok || res.type === "opaque") (await caches.open(RUNTIME)).put(req, res.clone());
  return res;
}

async function staleWhileRevalidate(req, cacheName) {
  const cache = await caches.open(cacheName);
  const hit = await cache.match(req, { ignoreVary: true });
  const fresh = fetch(req).then((res) => { if (res.ok) cache.put(req, res.clone()); return res; });
  if (hit) { fresh.catch(() => {}); return hit; }
  return fresh;
}

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = req.url;
  if (IMMUTABLE.test(url)) return e.respondWith(cacheFirst(req));
  if (REFRESH.test(url)) return e.respondWith(staleWhileRevalidate(req, RUNTIME));
  if (new URL(url).origin !== location.origin) return;  // YouTube and everything else: straight to the network
  // Pages are all the same index.html (routes live in the #hash).
  const key = req.mode === "navigate" ? new Request("./") : req;
  e.respondWith(staleWhileRevalidate(key, SHELL));
});
