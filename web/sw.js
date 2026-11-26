// Web version only: makes repeat visits load from cache and lets the app work offline.
//  - On install: caches the app and every library index.html references, plus the bundled packs.
//  - Our own files: answered from cache at once, refreshed in the background (the next visit gets updates).
//  - Versioned CDN files, Python and its packages: cached the first time, then served from cache.
// Progress, notes and code live in IndexedDB and are never touched here.
const BUILD = "dev";  // replaced with a build id by `server.py build-web`
// Two caches: SHELL holds this build's own files and is replaced on every deploy (old ones are deleted on
// activate); RUNTIME holds libraries, Python packages and course packs, and outlives deploys.
const SHELL = `learnpack-shell-${BUILD}`;
const RUNTIME = "learnpack-runtime-v1";

// Files that never change at a given URL (versioned), so cache-first is safe.
const IMMUTABLE = /^https:\/\/(cdnjs\.cloudflare\.com|cdn\.jsdelivr\.net|fonts\.gstatic\.com|files\.pythonhosted\.org)\//;
// Changes now and then: serve the cached copy, refresh it in the background.
const REFRESH = /^https:\/\/(fonts\.googleapis\.com|pypi\.org)\//;

self.addEventListener("install", (event) => {
  event.waitUntil((async () => {
    const shell = await caches.open(SHELL), runtime = await caches.open(RUNTIME);
    // Precache whatever index.html links to, so the list never drifts from the page.
    const html = await (await fetch("./", { cache: "no-cache" })).text();
    const refs = [...html.matchAll(/(?:src|href)="([^"#]+)"/g)].map((m) => m[1]).filter((u) => !u.startsWith("data:"));
    const index = await (await fetch("packs/index.json", { cache: "no-cache" })).json().catch(() => []);
    // This build's own files (small, versioned) go in this build's cache. Libraries and course packs live in
    // the long-lived cache and are only downloaded if missing, so a new release doesn't re-download megabytes
    // while the learner's page is loading.
    const own = ["./", "packs/index.json", `py-worker.js?v=${BUILD}`, `js-worker.js?v=${BUILD}`, ...refs.filter((u) => !u.startsWith("http"))];
    const shared = [...refs.filter((u) => u.startsWith("http")), ...index.map((c) => `packs/${encodeURIComponent(c.id)}.json`)];
    // CDN files are fetched with CORS so the cache holds readable responses, not opaque ones.
    const req = (u) => new Request(u, { mode: u.startsWith("http") ? "cors" : "same-origin" });
    // One failed file shouldn't stop the rest from being cached.
    await Promise.all([
      ...own.map((u) => shell.add(req(u)).catch(() => {})),
      ...shared.map(async (u) => { if (!(await runtime.match(u))) await runtime.add(req(u)).catch(() => {}); }),
    ]);
    self.skipWaiting();  // take over without waiting for every open tab to close
  })());
});

self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    for (const k of await caches.keys()) if (k.startsWith("learnpack-shell-") && k !== SHELL) await caches.delete(k);
    await self.clients.claim();
  })());
});

async function cacheFirst(req) {
  const hit = await caches.match(req);
  if (hit) return hit;
  const res = await fetch(req);
  // An opaque response (a no-cors request, e.g. a <script> without crossorigin) hides its status, so keep it too.
  if (res.ok || res.type === "opaque") (await caches.open(RUNTIME)).put(req, res.clone());
  return res;
}

// Answer from cache at once and refresh it in the background; with nothing cached, wait for the network.
async function staleWhileRevalidate(req, cacheName) {
  const cache = await caches.open(cacheName);
  const hit = await cache.match(req, { ignoreVary: true });  // ignore Vary, so a copy cached under other request headers still matches
  const fresh = fetch(req).then((res) => { if (res.ok) cache.put(req, res.clone()); return res; });
  if (hit) { fresh.catch(() => {}); return hit; }  // offline: the cached copy already answered
  return fresh;
}

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = req.url;
  if (IMMUTABLE.test(url)) return event.respondWith(cacheFirst(req));
  if (REFRESH.test(url)) return event.respondWith(staleWhileRevalidate(req, RUNTIME));
  if (new URL(url).origin !== location.origin) return;  // YouTube and everything else: straight to the network
  // Pages are all the same index.html (routes live in the #hash).
  const key = req.mode === "navigate" ? new Request("./") : req;
  // Course packs (but not their index) are large and long-lived, so they live in RUNTIME with the libraries.
  event.respondWith(staleWhileRevalidate(key, new URL(url).pathname.includes("/packs/") && !url.endsWith("index.json") ? RUNTIME : SHELL));
});
