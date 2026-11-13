// Runs JavaScript/TypeScript exercises in the browser (web version).
// Mirrors the Node harness in engine/runner.py: tests call a global test(name, fn) and import
// "./solution.ts" / "./solution.js" and node:assert. TypeScript is transpiled with the TypeScript
// compiler, then every module is loaded from a Blob URL with its imports rewritten.
let tsc = null;  // the TypeScript compiler (its own global is named ts, so ours can't be)
const status = (text) => postMessage({ type: "status", text });
const blob = (src) => URL.createObjectURL(new Blob([src], { type: "text/javascript" }));

// node:assert, enough for course tests.
const ASSERT = `
const show = (v) => { try { return typeof v === "string" ? JSON.stringify(v) : JSON.stringify(v, (k, x) => x instanceof Map ? Object.fromEntries(x) : x instanceof Set ? [...x] : x) ?? String(v); } catch { return String(v); } };
export class AssertionError extends Error { constructor(m) { super(m); this.name = "AssertionError"; } }
const fail = (msg, def) => { throw msg instanceof Error ? msg : new AssertionError(msg || def); };
function deep(a, b) {
  if (Object.is(a, b)) return true;
  if (typeof a !== "object" || typeof b !== "object" || !a || !b) return false;
  if (Object.getPrototypeOf(a) !== Object.getPrototypeOf(b)) return false;
  if (a instanceof Date) return a.getTime() === b.getTime();
  if (a instanceof Map) return a.size === b.size && [...a].every(([k, v]) => b.has(k) && deep(v, b.get(k)));
  if (a instanceof Set) return a.size === b.size && [...a].every((v) => b.has(v));
  const ka = Object.keys(a), kb = Object.keys(b);
  return ka.length === kb.length && ka.every((k) => Object.prototype.hasOwnProperty.call(b, k) && deep(a[k], b[k]));
}
const assert = (v, m) => { if (!v) fail(m, "The expression evaluated to a falsy value"); };
assert.ok = assert;
assert.equal = assert.strictEqual = (a, b, m) => { if (!Object.is(a, b)) fail(m, "Expected values to be strictly equal:\\n\\n" + show(a) + " !== " + show(b)); };
assert.notEqual = assert.notStrictEqual = (a, b, m) => { if (Object.is(a, b)) fail(m, "Expected values to be different, both were " + show(a)); };
assert.deepEqual = assert.deepStrictEqual = (a, b, m) => { if (!deep(a, b)) fail(m, "Expected values to be deeply equal:\\n\\n" + show(a) + "\\n\\nshould equal\\n\\n" + show(b)); };
assert.notDeepEqual = assert.notDeepStrictEqual = (a, b, m) => { if (deep(a, b)) fail(m, "Expected values not to be deeply equal"); };
const matches = (e, x) => !x || (typeof x === "function" ? (x.prototype instanceof Error || x === Error ? e instanceof x : x(e)) : x instanceof RegExp ? x.test(String(e?.message ?? e)) : Object.entries(x).every(([k, v]) => v instanceof RegExp ? v.test(e?.[k]) : deep(e?.[k], v)));
// Like Node: a string second argument is the failure message, not something the error must match.
const split = (x, m) => (typeof x === "string" ? [undefined, x] : [x, m]);
assert.throws = (fn, x0, m0) => { const [x, m] = split(x0, m0); try { fn(); } catch (e) { if (!matches(e, x)) fail(m, "The error didn't match: " + (e?.message ?? e)); return; } fail(m, "Missing expected exception."); };
assert.doesNotThrow = (fn, m) => { try { fn(); } catch (e) { fail(m, "Got unwanted exception: " + (e?.message ?? e)); } };
assert.rejects = async (p, x0, m0) => { const [x, m] = split(x0, m0); try { await (typeof p === "function" ? p() : p); } catch (e) { if (!matches(e, x)) fail(m, "The rejection didn't match: " + (e?.message ?? e)); return; } fail(m, "Missing expected rejection."); };
assert.doesNotReject = async (p, m) => { try { await (typeof p === "function" ? p() : p); } catch (e) { fail(m, "Got unwanted rejection: " + (e?.message ?? e)); } };
assert.match = (s, re, m) => { if (!re.test(s)) fail(m, "The input did not match " + re + ": " + show(s)); };
assert.doesNotMatch = (s, re, m) => { if (re.test(s)) fail(m, "The input was expected not to match " + re); };
assert.fail = (m) => fail(m, "Failed");
assert.strict = assert;
export default assert;
export const { ok, equal, strictEqual, notEqual, notStrictEqual, deepEqual, deepStrictEqual, notDeepEqual, notDeepStrictEqual, throws, doesNotThrow, rejects, doesNotReject, match, doesNotMatch } = assert;
export { fail as _fail };
`;

// node:test, only mock.timers (fake setTimeout/setInterval/Date driven by tick()).
const NODE_TEST = `
const real = { setTimeout, clearTimeout, setInterval, clearInterval, Date };
let now = 0, seq = 0, queue = [], on = false;
const add = (fn, ms, args, every) => { const id = ++seq; queue.push({ id, at: now + Math.max(0, ms | 0), fn, args, every }); return id; };
const remove = (id) => { queue = queue.filter((t) => t.id !== id); };
export const mock = { timers: {
  enable(opts = {}) {
    const apis = opts.apis || ["setTimeout", "setInterval", "Date"];
    now = opts.now ?? 0; on = true;
    if (apis.includes("setTimeout")) { globalThis.setTimeout = (fn, ms, ...a) => add(fn, ms, a, 0); globalThis.clearTimeout = remove; }
    if (apis.includes("setInterval")) { globalThis.setInterval = (fn, ms, ...a) => add(fn, ms, a, Math.max(1, ms | 0)); globalThis.clearInterval = remove; }
    if (apis.includes("Date")) { const D = real.Date; globalThis.Date = class extends D { constructor(...a) { a.length ? super(...a) : super(now); } static now() { return now; } }; }
  },
  tick(ms = 1) {
    const end = now + ms;
    for (;;) {
      queue.sort((a, b) => a.at - b.at || a.id - b.id);
      const t = queue[0];
      if (!t || t.at > end) break;
      now = t.at;
      if (t.every) t.at += t.every; else queue.shift();
      t.fn(...t.args);
    }
    now = end;
  },
  runAll() { this.tick(Math.max(0, ...queue.map((t) => t.at)) - now); },
  reset() { Object.assign(globalThis, real); queue = []; now = 0; on = false; },
} };
export const test = globalThis.test;
export default { mock };
`;

function rewrite(js, urls) {
  const map = (spec) => urls[spec] || (spec.startsWith("./") && urls[spec.replace(/\.(ts|js|mjs)$/, ".ts")]) || urls[spec.replace(/\.(ts|mjs)$/, ".js")] || spec;
  return js
    .replace(/(\bfrom\s*|\bimport\s*)(["'])([^"']+)\2/g, (m, kw, q, spec) => kw + q + map(spec) + q)
    .replace(/\bimport\(\s*(["'])([^"']+)\1\s*\)/g, (m, q, spec) => `import(${q}${map(spec)}${q})`);
}

// A few Node globals that course code commonly touches.
self.setImmediate ||= (fn, ...a) => setTimeout(fn, 0, ...a);
self.clearImmediate ||= (id) => clearTimeout(id);
self.process ||= { env: {}, nextTick: (fn, ...a) => queueMicrotask(() => fn(...a)), platform: "browser", versions: {} };

self.onmessage = async ({ data }) => {
  const { lang, mode, code, tests, support } = data;
  let stdout = "", stderr = "";
  const fmt = (args) => args.map((a) => (typeof a === "string" ? a : (() => { try { return JSON.stringify(a); } catch { return String(a); } })())).join(" ") + "\n";
  console.log = console.info = console.debug = (...a) => { stdout += fmt(a); };
  console.error = console.warn = (...a) => { stderr += fmt(a); };
  try {
    if (lang === "typescript" && !tsc) {
      status("Loading the TypeScript compiler (first time only)…");
      importScripts("https://cdnjs.cloudflare.com/ajax/libs/typescript/5.6.3/typescript.min.js");
      tsc = self.ts;
    }
    postMessage({ type: "started" });
    const compile = (src, name) => (lang === "typescript" || name.endsWith(".ts")) && tsc
      ? tsc.transpileModule(src, { fileName: name, compilerOptions: { module: tsc.ModuleKind.ESNext, target: tsc.ScriptTarget.ES2022 } }).outputText
      : src;
    const urls = { "node:assert": blob(ASSERT), "node:assert/strict": blob(ASSERT), "assert": blob(ASSERT), "node:test": blob(NODE_TEST) };
    for (const [name, src] of Object.entries(support || {})) {
      if (/\.(js|mjs|ts)$/.test(name)) urls["./" + name] = blob(rewrite(compile(src, name), urls));
      else if (name.endsWith(".json")) urls["./" + name] = blob("export default " + src);
    }
    const ext = lang === "typescript" ? "ts" : "js";
    const sol = blob(rewrite(compile(code, "solution." + ext), urls));
    urls["./solution.ts"] = urls["./solution.js"] = urls["./solution.mjs"] = sol;
    if (mode === "run") {
      await import(sol);
      postMessage({ type: "done", stdout, stderr, exit_code: 0, timed_out: false });
      return;
    }
    const list = [];
    self.test = globalThis.test = (name, fn) => list.push({ name, fn });
    const results = [];
    try {
      await import(blob(rewrite(compile(tests, "tests." + ext), urls)));
      for (const t of list) {
        try { await t.fn(); results.push({ name: t.name, passed: true, error: "" }); }
        catch (e) { results.push({ name: t.name, passed: false, error: (e?.name === "AssertionError" ? "" : (e?.name || "Error") + ": ") + (e?.message ?? String(e)) }); }
      }
    } catch (e) {
      results.push({ name: "import", passed: false, error: `${e?.name || "Error"}: ${e?.message ?? e}` });
    }
    postMessage({ type: "done", stdout, stderr, exit_code: 0, timed_out: false, results });
  } catch (e) {
    postMessage({ type: "done", stdout, stderr: stderr + `${e?.name || "Error"}: ${e?.message ?? e}`, exit_code: 1, timed_out: false });
  }
};
