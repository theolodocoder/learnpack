"use strict";
// The web version's backend. When the app is opened without the local server (e.g. on GitHub
// Pages), this answers the same /api routes from inside the browser:
//  - courses come from packs/*.json (built by `server.py build-web`) or packs the learner adds
//  - progress, notes and code live in IndexedDB on this device
//  - code runs in Web Workers (Python via Pyodide, JavaScript/TypeScript natively)
window.LocalBackend = (() => {
  const STORE = "kv";
  let dbp;
  function db() {
    dbp ||= new Promise((resolve, reject) => {
      const req = indexedDB.open("learnpack", 1);
      req.onupgradeneeded = () => req.result.createObjectStore(STORE);
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
    return dbp;
  }
  async function tx(mode, fn) {
    const d = await db();
    return new Promise((resolve, reject) => {
      const t = d.transaction(STORE, mode), s = t.objectStore(STORE);
      const out = fn(s);
      t.oncomplete = () => resolve(out && "result" in out ? out.result : out);
      t.onerror = () => reject(t.error);
    });
  }
  const get = (k) => tx("readonly", (s) => s.get(k));
  const put = (k, v) => tx("readwrite", (s) => { s.put(v, k); });
  const del = (k) => tx("readwrite", (s) => { s.delete(k); });
  async function entries(prefix) {
    const d = await db();
    return new Promise((resolve, reject) => {
      const out = [], range = IDBKeyRange.bound(prefix, prefix + "￿");
      const req = d.transaction(STORE).objectStore(STORE).openCursor(range);
      req.onsuccess = () => { const c = req.result; if (c) { out.push([c.key, c.value]); c.continue(); } else resolve(out); };
      req.onerror = () => reject(req.error);
    });
  }

  // ---------- courses ----------
  const cache = {};
  let bundled;
  async function bundledIndex() {
    if (!bundled) {
      try { bundled = await (await fetch("packs/index.json", { cache: "no-cache" })).json(); }
      catch (e) { bundled = []; }
    }
    return bundled;
  }
  // Cached as a promise, so a background prefetch and a click share one download.
  function course(cid) {
    cache[cid] ||= (async () => {
      const own = await get(`pack:${cid}`);
      if (own) return own;
      if ((await bundledIndex()).some((c) => c.id === cid)) {
        const r = await fetch(`packs/${encodeURIComponent(cid)}.json`);
        if (r.ok) return r.json();
      }
      throw new Error("404 That course isn't installed in this browser.");
    })();
    cache[cid].catch(() => delete cache[cid]);
    return cache[cid];
  }
  const lessonsOf = (c) => (c.sections || []).flatMap((s) => s.lessons || []);
  const practiceOf = (c) => lessonsOf(c).flatMap((l) => l.practice || []);
  const job = (c, p, mode, code) => ({ lang: p.language || c.language || "python", mode, code, tests: p.tests,
    support: c._support || {}, requirements: c.requirements?.python || [] });
  // Called when an exercise appears on screen: gets Python/TypeScript and its packages ready in the background.
  async function warm(cid, pid) {
    const c = await course(cid), p = practiceOf(c).find((x) => x.id === pid);
    if (p) window.WebRunner.warm(job(c, p, "warm", p.starter || ""));
  }
  const emptyState = () => ({ done: [], checklist: {}, links: {}, last: "" });

  async function listCourses() {
    const out = [];
    const add = async (summaryOrCourse, imported) => {
      const st = (await get(`${summaryOrCourse.id}:state`)) || emptyState();
      let total = summaryOrCourse.total, ids = null;
      if (imported) { const ls = lessonsOf(summaryOrCourse); total = ls.length; ids = new Set(ls.map((l) => l.id)); }
      const done = ids ? st.done.filter((d) => ids.has(d)).length : st.done.length;
      out.push({ id: summaryOrCourse.id, title: summaryOrCourse.title, description: summaryOrCourse.description || "",
                 accent: summaryOrCourse.theme?.accent || summaryOrCourse.accent || null, total, done: Math.min(done, total), imported });
    };
    for (const s of await bundledIndex()) if (!(await get(`pack:${s.id}`))) await add(s, false);
    for (const [, c] of await entries("pack:")) await add(c, true);
    for (const c of out) if (!c.imported) setTimeout(() => course(c.id).catch(() => {}), 0);  // so opening it is instant
    return out;
  }

  // Notes HTML -> plain text, one line per block (same rule as the server's plain_text).
  function plainText(html) {
    const s = html.replace(/<(br|\/div|\/p|\/li|\/h[1-6]|\/pre)\b[^>]*>/gi, "\n");
    const doc = new DOMParser().parseFromString(s, "text/html");
    return (doc.body.textContent || "").replace(/ /g, " ").split("\n").map((l) => l.trim()).filter(Boolean).join("\n");
  }

  // ---------- the /api routes ----------
  async function api(path, { method = "GET", body } = {}) {
    const url = new URL(path, "http://x");
    const parts = url.pathname.split("/").filter(Boolean).map(decodeURIComponent);
    if (parts[0] === "browse") throw new Error("browse-unavailable");
    if (parts[0] !== "courses") throw new Error("404 not found");
    if (parts.length === 1) return listCourses();
    const cid = parts[1], rest = parts.slice(2), c = await course(cid);
    if (!rest.length) return c;
    if (rest[0] === "state") {
      if (method === "PUT") { await put(`${cid}:state`, body); return { ok: true }; }
      return (await get(`${cid}:state`)) || emptyState();
    }
    if (rest[0] === "notes" && rest.length === 1) {
      const rows = await entries(`${cid}:note:`);
      return rows.map(([k, v]) => ({ id: k.slice(`${cid}:note:`.length), modified: v.modified, text: plainText(v.html) }))
        .sort((a, b) => b.modified - a.modified);
    }
    if (rest[0] === "notes") {
      const key = `${cid}:note:${rest[1]}`;
      if (method === "PUT") {
        if (!plainText(body).trim()) await del(key); else await put(key, { html: body, modified: Date.now() });
        return { ok: true };
      }
      if (method === "DELETE") {
        const n = await get(key);
        if (n) { await put(`${cid}:trash:${rest[1]}-${Date.now()}`, n); await del(key); }
        return { ok: true };
      }
      return (await get(key))?.html || "";
    }
    if (rest[0] === "code") {
      const key = `${cid}:code:${rest[1]}`;
      if (method === "PUT") { await put(key, body); return { ok: true }; }
      const saved = await get(key);
      return saved ?? (practiceOf(c).find((p) => p.id === rest[1])?.starter || "");
    }
    if (rest[0] === "solution") {
      const p = practiceOf(c).find((x) => x.id === rest[1]);
      if (!p?.solution) throw new Error("404 no solution");
      return { solution: p.solution };
    }
    if (rest[0] === "run" && method === "POST") {
      const p = practiceOf(c).find((x) => x.id === body.practice);
      if (!p || p.type !== "code") throw new Error("404 no such practice");
      return window.WebRunner.run(job(c, p, body.mode, String(body.code || "")));
    }
    throw new Error("404 not found");
  }

  // ---------- adding packs (a .learnpack.json bundle, or a .zip of a pack folder) ----------
  const TEXT_FIELDS = new Set(["description", "summary", "body", "prompt", "starter", "tests", "solution", "brief", "question", "explanation"]);
  const SUPPORT_EXT = /\.(py|js|mjs|ts|json|txt|csv)$/i;
  let jszipLoading;
  function loadJSZip() {
    jszipLoading ||= new Promise((resolve, reject) => {
      const s = Object.assign(document.createElement("script"), { src: "https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js" });
      s.onload = () => resolve(window.JSZip); s.onerror = () => reject(new Error("Couldn't load the ZIP reader. Check your internet connection."));
      document.head.append(s);
    });
    return jszipLoading;
  }
  async function fromZip(file) {
    const JSZip = await loadJSZip();
    const zip = await JSZip.loadAsync(file);
    const cj = Object.keys(zip.files).filter((n) => /(^|\/)course\.json$/.test(n)).sort((a, b) => a.length - b.length)[0];
    if (!cj) throw new Error("That ZIP doesn't contain a course.json.");
    const root = cj.slice(0, -"course.json".length);
    const read = async (rel) => {
      const parts = [];
      for (const seg of (root + rel).split("/")) { if (seg === "..") parts.pop(); else if (seg && seg !== ".") parts.push(seg); }
      const name = parts.join("/");
      if (!name.startsWith(root.replace(/\/$/, "")) && root) throw new Error(`A file points outside the pack: ${rel}`);
      const f = zip.file(name);
      if (!f) throw new Error(`The pack is missing a file: ${rel}`);
      return f.async("string");
    };
    const resolve = async (node) => {
      if (Array.isArray(node)) return Promise.all(node.map(resolve));
      if (node && typeof node === "object") {
        const keys = Object.keys(node);
        if (keys.length === 1 && keys[0] === "include") return resolve(JSON.parse(await read(node.include)));
        const out = {};
        for (const [k, v] of Object.entries(node)) {
          out[k] = TEXT_FIELDS.has(k) && v && typeof v === "object" && Object.keys(v).length === 1 && "file" in v ? await read(v.file) : await resolve(v);
        }
        return out;
      }
      return node;
    };
    const c = await resolve(JSON.parse(await read("course.json")));
    c._support = {};
    if (c.support) {
      const dir = root + c.support.replace(/\/$/, "") + "/";
      for (const name of Object.keys(zip.files)) {
        const rest = name.slice(dir.length);
        if (name.startsWith(dir) && rest && !rest.includes("/") && SUPPORT_EXT.test(rest)) c._support[rest] = await zip.file(name).async("string");
      }
    }
    if (c.theme?.css) c._themeCss = await read(c.theme.css);
    return c;
  }
  async function addPack(file) {
    let c;
    if (/\.zip$/i.test(file.name)) c = await fromZip(file);
    else {
      try { c = JSON.parse(await file.text()); } catch (e) { throw new Error("That file isn't a valid course pack (it isn't JSON)."); }
      if (c.sections && !c._bundle && JSON.stringify(c).includes('{"file":')) {
        throw new Error("This course.json points to other files. Add the whole pack folder as a ZIP, or a .learnpack.json bundle.");
      }
    }
    if (!c || typeof c.id !== "string" || !/^[a-z0-9][a-z0-9-]{0,63}$/.test(c.id) || !c.title || !Array.isArray(c.sections)) {
      throw new Error("That file isn't a LearnPack course (it needs an id, a title and sections).");
    }
    if ((c.format ?? 1) !== 1) throw new Error(`This pack is for a newer LearnPack (format ${c.format}).`);
    if ((await bundledIndex()).some((b) => b.id === c.id) && !(await get(`pack:${c.id}`))) {
      throw new Error(`A built-in course already uses the id "${c.id}".`);
    }
    await put(`pack:${c.id}`, c);
    delete cache[c.id];
    return c;
  }
  async function removePack(cid) { await del(`pack:${cid}`); delete cache[cid]; }

  // ---------- backup and restore (everything for one course, as a file) ----------
  async function backup(cid) {
    const strip = (p) => (rows) => Object.fromEntries(rows.map(([k, v]) => [k.slice(p.length), v]));
    return {
      format: "learnpack-backup", version: 1, course: cid, exported: new Date().toISOString(),
      state: (await get(`${cid}:state`)) || emptyState(),
      notes: strip(`${cid}:note:`)(await entries(`${cid}:note:`)),
      code: strip(`${cid}:code:`)(await entries(`${cid}:code:`)),
    };
  }
  async function restore(cid, data) {
    if (data?.format !== "learnpack-backup") throw new Error("That file isn't a LearnPack backup.");
    if (data.course !== cid) throw new Error(`That backup is for the course "${data.course}", not this one.`);
    await put(`${cid}:state`, data.state || emptyState());
    for (const [id, n] of Object.entries(data.notes || {})) await put(`${cid}:note:${id}`, n);
    for (const [id, code] of Object.entries(data.code || {})) await put(`${cid}:code:${id}`, code);
  }

  return { api, addPack, removePack, backup, restore, course, warm };
})();
