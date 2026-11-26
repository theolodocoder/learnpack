"use strict";
// LearnPack front end: the whole single-page app (no build step, loaded by web/index.html).
// It renders any course pack and works in two modes:
//   - Local: served by server.py, which injects LEARN_TOKEN and answers /api/* requests.
//   - Web version (STATIC): plain files on GitHub Pages; web/local.js (LocalBackend) and the
//     runner workers answer the same API inside the browser, and progress lives in this browser.
//
// Globals used throughout:
//   S  app state (course list, open course, its id, the learner's saved state)
//   $  querySelector shorthand: $(selector, root = document)
//
// Sections, in order:
//   helpers, state, theme, notes drawer, outline menu button, routing, web version offline cache,
//   router and course loading, page chrome (top bar and sidebar), views: home and dashboard,
//   views: lesson, views: practice, views: project, focus mode and shortcuts, Pomodoro timer,
//   study time and Today panel, views: review, pack features and look, course switcher,
//   in-app browser, web version only (add a course, back up and restore).

// ---------- helpers ----------
const $ = (sel, root = document) => root.querySelector(sel);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const store = {
  get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} },
};

// Web version: no local server (the page wasn't served by server.py), so the browser does its job.
const STATIC = window.LEARN_TOKEN === "__" + "TOKEN__";

// Calls the course API: the local server over fetch, or LocalBackend in the web version.
async function api(path, { method = "GET", body, text = false } = {}) {
  if (STATIC) return window.LocalBackend.api(path, { method, body });
  const res = await fetch("api" + path, {
    method,
    headers: { "X-Learn-Token": window.LEARN_TOKEN, ...(body !== undefined && !text ? { "Content-Type": "application/json" } : {}) },
    body: body === undefined ? undefined : text ? body : JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${res.status} ${(await res.text()).slice(0, 200)}`);
  return (res.headers.get("Content-Type") || "").includes("json") ? res.json() : res.text();
}

// Markdown to safe HTML, with code highlighting and external links opening in a new tab.
function md(text) {
  const html = DOMPurify.sanitize(marked.parse(text || ""), { ADD_ATTR: ["target"] });
  const div = document.createElement("div");
  div.innerHTML = html;
  div.querySelectorAll("pre code").forEach((el) => { try { hljs.highlightElement(el); } catch (e) {} });
  div.querySelectorAll("a[href^='http']").forEach((a) => { a.target = "_blank"; a.rel = "noopener"; });
  return div.innerHTML;
}

// Delays fn until ms have passed without a new call; .flush() runs it right away.
function debounce(fn, ms) {
  let timer;
  const debounced = (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), ms); };
  debounced.flush = (...args) => { clearTimeout(timer); return fn(...args); };
  return debounced;
}

// ---------- state ----------
const S = { courses: null, course: null, cid: null, state: null };
// Every lesson of the open course in order, each with a link back to its section.
const allLessons = () => S.course.sections.flatMap((section) => section.lessons.map((lesson) => ({ ...lesson, section })));
const isDone = (id) => S.state.done.includes(id);

const saveState = debounce(async () => {
  try { await api(`/courses/${S.cid}/state`, { method: "PUT", body: S.state }); }
  catch (e) { toastError("Progress didn't save. Is the server still running?"); }
}, 300);

function toastError(msg) {
  let box = $("#toast");
  if (!box) { box = document.createElement("div"); box.id = "toast"; box.className = "error-box"; box.setAttribute("role", "alert");
    Object.assign(box.style, { position: "fixed", bottom: "16px", left: "50%", transform: "translateX(-50%)", background: "var(--surface)", zIndex: 50 });
    document.body.append(box); }
  box.textContent = msg; box.hidden = false;
  clearTimeout(box._h); box._h = setTimeout(() => (box.hidden = true), 5000);
}

// ---------- theme ----------
const THEMES = ["system", "light", "dark"];
// Sets the page theme ("system", "light" or "dark") and the matching code-highlighting stylesheet.
function applyTheme(theme) {
  if (theme === "system") delete document.documentElement.dataset.theme; else document.documentElement.dataset.theme = theme;
  const dark = theme === "dark" || (theme === "system" && matchMedia("(prefers-color-scheme: dark)").matches);
  $("#hl-light").disabled = dark; $("#hl-dark").disabled = !dark;
  $("#theme-btn").textContent = { system: "◐", light: "☀", dark: "☾" }[theme];
  $("#theme-btn").title = `Theme: ${theme} (click to change)`;
  document.querySelectorAll("[data-theme-set]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.themeSet === theme)));
}
// Phones hide the top bar's theme button; the same choice lives at the bottom of the ☰ menu.
const themeChooser = () => `<div class="side-theme" role="group" aria-label="Theme"><span>Theme</span>${THEMES.map((theme) =>
  `<button data-theme-set="${theme}" aria-pressed="${(store.get("theme") || "system") === theme}">${theme[0].toUpperCase() + theme.slice(1)}</button>`).join("")}</div>`;
document.addEventListener("click", (e) => {
  const b = e.target.closest("[data-theme-set]");
  if (b) { store.set("theme", b.dataset.themeSet); applyTheme(b.dataset.themeSet); }
});
$("#theme-btn").onclick = () => {
  const next = THEMES[(THEMES.indexOf(store.get("theme") || "system") + 1) % 3];
  store.set("theme", next); applyTheme(next);
};
matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => applyTheme(store.get("theme") || "system"));
applyTheme(store.get("theme") || "system");

// ---------- notes drawer (works like Apple Notes) ----------
const ed = $("#nv-editor");  // the note editor (contenteditable)
document.execCommand("defaultParagraphSeparator", false, "div");

const DAY = 864e5;
const startOfDay = (d) => new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
const fmtLong = (ms) => new Date(ms).toLocaleString(undefined, { day: "numeric", month: "long", year: "numeric", hour: "2-digit", minute: "2-digit" });
// Note list timestamp: time today, "Yesterday", a weekday this week, else the date.
function fmtShort(ms) {
  const d = new Date(ms), age = startOfDay(new Date()) - startOfDay(d);
  if (age <= 0) return d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
  if (age === DAY) return "Yesterday";
  if (age < 7 * DAY) return d.toLocaleDateString(undefined, { weekday: "long" });
  return d.toLocaleDateString();
}
// The heading a note is listed under, by how recently it changed.
function groupOf(ms) {
  const d = new Date(ms), age = startOfDay(new Date()) - startOfDay(d);
  if (age <= 0) return "Today";
  if (age === DAY) return "Yesterday";
  if (age < 7 * DAY) return "Previous 7 Days";
  if (age < 30 * DAY) return "Previous 30 Days";
  return d.toLocaleDateString(undefined, d.getFullYear() === new Date().getFullYear() ? { month: "long" } : { month: "long", year: "numeric" });
}

const Notes = {
  pageKey: null, // the note that belongs to the page you're on
  key: null,     // the note open in the editor (null while loading: nothing saves then)
  dirty: false,
  list: [],
  get open() { return !$("#notes").hidden; },

  async show(view) {
    $("#notes").hidden = false; store.set("notesOpen", "1");
    if (view === "list" || !this.pageKey) return this.showList();
    if (this.key !== this.pageKey || $("#nv-note").hidden) await this.openNote(this.pageKey);
  },
  hide() { this.save.flush(); $("#notes").hidden = true; store.set("notesOpen", ""); },

  async showList() {
    this.save.flush();
    $("#nv-note").hidden = true; $("#nv-list").hidden = false; this.closeFormat();
    try { this.list = await api(`/courses/${S.cid}/notes`); } catch (e) { this.list = []; }
    this.renderList();
  },
  renderList() {
    const q = $("#nv-search").value.trim().toLowerCase();
    const items = this.list.filter((n) => !q || n.text.toLowerCase().includes(q));
    $("#nv-count").textContent = `${this.list.length} ${this.list.length === 1 ? "Note" : "Notes"}`;
    if (!items.length) {
      $("#nv-items").innerHTML = `<p class="nv-empty">${q ? "No results" : "No notes yet"}</p>`;
      return;
    }
    let html = "", group = null;
    for (const n of items) {
      const g = groupOf(n.modified);
      if (g !== group) { html += `${group ? "</div>" : ""}<h3 class="nv-group">${esc(g)}</h3><div class="nv-card">`; group = g; }
      const [title, ...rest] = n.text.split("\n");
      html += `<button class="nv-item ${n.id === this.key ? "current" : ""}" data-note="${esc(n.id)}">
        <div class="nv-title">${esc(title || "New Note")}</div>
        <div class="nv-sub"><time>${esc(fmtShort(n.modified))}</time>${esc(rest.join(" ") || "No additional text")}</div></button>`;
    }
    $("#nv-items").innerHTML = html + "</div>";
  },

  async openNote(key, { focus = false } = {}) {
    this.save.flush();
    this.key = null; this.dirty = false;
    $("#nv-list").hidden = true; $("#nv-note").hidden = false; this.closeFormat();
    ed.contentEditable = "false"; ed.innerHTML = ""; this.status("");
    try {
      let raw, format = "html";
      if (STATIC) raw = await api(`/courses/${S.cid}/notes/${key}`);
      else {
        const r = await fetch(`api/courses/${S.cid}/notes/${key}`, { headers: { "X-Learn-Token": window.LEARN_TOKEN } });
        if (!r.ok) throw new Error(r.status);
        raw = await r.text(); format = r.headers.get("X-Note-Format");
      }
      const html = format === "md" ? marked.parse(raw) : raw;  // older Markdown notes convert on open
      ed.innerHTML = DOMPurify.sanitize(html) || "<div><br></div>";
      const known = this.list.find((n) => n.id === key);
      $("#nv-date").textContent = fmtLong(known ? known.modified : Date.now());
      this.key = key; ed.contentEditable = "true";
      if (focus || !raw) { ed.focus(); placeCaretAtEnd(); }
    } catch (e) { this.status("Couldn't load this note. Is the server running?"); }
  },

  edited() {
    if (!this.key) return;
    this.dirty = true;
    $("#nv-date").textContent = fmtLong(Date.now());
    this.save();
  },
  save: debounce(async function () {
    if (!Notes.key || !Notes.dirty) return;
    Notes.dirty = false;
    const key = Notes.key, html = ed.innerHTML;
    try { await api(`/courses/${S.cid}/notes/${key}`, { method: "PUT", body: html, text: true }); Notes.status(""); }
    catch (e) { Notes.dirty = true; Notes.status("Not saved. Restart the server, then keep typing."); }
  }, 500),
  status(msg) { $("#nv-status").textContent = msg; },

  compose() { this.openNote(`note-${Date.now().toString(36)}`, { focus: true }); },
  async remove() {
    if (!this.key || !confirm("Delete this note? It moves to the notes/.trash folder in learner-data.")) return;
    const key = this.key; this.key = null; this.dirty = false;
    try { await api(`/courses/${S.cid}/notes/${key}`, { method: "DELETE" }); } catch (e) { toastError("Couldn't delete the note."); }
    this.showList();
  },

  toggleFormat() { const f = $("#nv-format"); f.hidden ? (f.hidden = false, syncFormat()) : this.closeFormat(); $("#nv-aa").setAttribute("aria-expanded", String(!f.hidden)); },
  closeFormat() { $("#nv-format").hidden = true; $("#nv-aa").setAttribute("aria-expanded", "false"); },
};

function placeCaretAtEnd() {
  const range = document.createRange(); range.selectNodeContents(ed); range.collapse(false);
  const sel = getSelection(); sel.removeAllRanges(); sel.addRange(range);
}
// The nearest element matching selector around the caret, if it's inside the editor.
function caretClosest(selector) {
  const node = getSelection().anchorNode;
  const el = node && (node.nodeType === 1 ? node : node.parentElement);
  const hit = el?.closest(selector);
  return hit && ed.contains(hit) ? hit : null;
}
// Runs an editing command on the note, then saves and refreshes the format toolbar.
function exec(cmd, value) { ed.focus(); document.execCommand(cmd, false, value); Notes.edited(); syncFormat(); }
function setBlock(tag) { exec("formatBlock", tag); }
function toggleChecklist() {
  const li = caretClosest("li");
  if (li?.parentElement.classList.contains("checklist")) return exec("insertUnorderedList");  // back to plain text
  if (li?.parentElement.tagName === "UL") { li.parentElement.classList.add("checklist"); return Notes.edited(); }
  exec("insertUnorderedList");
  caretClosest("ul")?.classList.add("checklist");
  Notes.edited();
}
// Highlights the format toolbar buttons that match the text at the caret.
function syncFormat() {
  if ($("#nv-format").hidden) return;
  const block = caretClosest("h1, h2, h3, pre")?.tagName.toLowerCase() || "div";
  document.querySelectorAll("[data-block]").forEach((b) => b.classList.toggle("on", b.dataset.block === block));
  document.querySelectorAll("[data-cmd]").forEach((b) => b.classList.toggle("on", document.queryCommandState(b.dataset.cmd)));
}

// Keep stray text in block elements so the first line always styles as the title.
ed.addEventListener("input", () => {
  for (const node of [...ed.childNodes]) {
    if (node.nodeType === 3 && node.textContent.trim()) {
      const sel = getSelection(), inNode = sel.anchorNode === node, offset = sel.anchorOffset;
      const div = document.createElement("div"); node.replaceWith(div); div.append(node);
      if (inNode) sel.collapse(node, offset);
    }
  }
  Notes.edited();
});
ed.addEventListener("mousedown", (e) => {  // tap the circle to tick a checklist item
  const li = e.target.closest?.("ul.checklist > li");
  if (li && e.clientX < li.getBoundingClientRect().left) {
    e.preventDefault();
    li.dataset.checked = li.dataset.checked === "true" ? "false" : "true";
    Notes.edited();
  }
});
ed.addEventListener("keydown", (e) => {
  const mod = e.metaKey || e.ctrlKey;
  if (mod && e.shiftKey) {
    const map = { t: "h1", h: "h2", j: "h3", b: "div", m: "pre" }, k = e.key.toLowerCase();
    if (map[k]) { e.preventDefault(); setBlock(map[k]); }
    if (k === "l") { e.preventDefault(); toggleChecklist(); }
  }
  if (e.key === "Enter" && caretClosest("ul.checklist > li")) {
    setTimeout(() => { const li = caretClosest("ul.checklist > li"); if (li && !li.textContent.trim()) delete li.dataset.checked; });
  }
});
ed.addEventListener("paste", (e) => { e.preventDefault(); exec("insertText", e.clipboardData.getData("text/plain")); });
document.addEventListener("selectionchange", () => { if (document.activeElement === ed) syncFormat(); });

// Toolbar buttons must not steal the text selection.
document.querySelectorAll(".nv-format button, #nv-check").forEach((b) => b.addEventListener("mousedown", (e) => e.preventDefault()));
document.querySelectorAll("[data-block]").forEach((b) => (b.onclick = () => setBlock(b.dataset.block)));
document.querySelectorAll("[data-cmd]").forEach((b) => (b.onclick = () => exec(b.dataset.cmd)));
$("#nv-check").onclick = toggleChecklist;
$("#nv-aa").onclick = () => Notes.toggleFormat();
$("#nv-delete").onclick = () => Notes.remove();
$("#nv-back").onclick = () => Notes.showList();
document.querySelectorAll("[data-compose]").forEach((b) => (b.onclick = () => Notes.compose()));
document.querySelectorAll("[data-close]").forEach((b) => (b.onclick = () => Notes.hide()));
$("#nv-search").addEventListener("input", () => Notes.renderList());
$("#nv-items").addEventListener("click", (e) => { const b = e.target.closest("[data-note]"); if (b) Notes.openNote(b.dataset.note); });
$("#notes-btn").onclick = () => (Notes.open ? Notes.hide() : Notes.show());
window.addEventListener("beforeunload", (e) => { if (Notes.dirty) { Notes.save.flush(); e.preventDefault(); } });

// ---------- outline menu button ----------
// ☰ folds the whole outline away on wide screens (remembered), and slides it over the page on phones.
const narrow = () => matchMedia("(max-width: 860px)").matches;
function paintMenuBtn() {
  const shown = narrow() ? $("#sidebar").classList.contains("open") : !document.body.classList.contains("side-collapsed");
  $("#menu-btn").setAttribute("aria-expanded", String(shown));
  $("#menu-btn").setAttribute("aria-label", shown ? "Hide course outline" : "Show course outline");
  $("#menu-btn").title = shown ? "Hide course outline" : "Show course outline";
}
$("#menu-btn").onclick = () => {
  if (narrow()) $("#sidebar").classList.toggle("open");
  else {
    const hide = !document.body.classList.contains("side-collapsed");
    document.body.classList.toggle("side-collapsed", hide);
    store.set("sideCollapsed", hide ? "1" : "");
  }
  paintMenuBtn();
};
document.body.classList.toggle("side-collapsed", !!store.get("sideCollapsed"));
paintMenuBtn();

// ---------- routing ----------
let routeSeq = 0;  // declared before the first route() call below
window.addEventListener("hashchange", route);
route();

// ---------- web version: offline cache and preloading ----------
// Runs fn when the browser is idle (or after 200 ms where requestIdleCallback is missing).
function idle(fn) { (window.requestIdleCallback || ((f) => setTimeout(f, 200)))(fn, { timeout: 2000 }); }
if (STATIC) {
  if ("serviceWorker" in navigator) window.addEventListener("load", () => navigator.serviceWorker.register("sw.js").catch(() => {}));
  // Pointing at (or tabbing to) a lesson link gets its exercises and video thumbnail ready before the click.
  const lessonFromLink = (e) => {
    const a = e.target.closest?.("a[href*='/l/']");
    const m = a?.getAttribute("href").match(/^#\/([^/]+)\/l\/([^/]+)$/);
    if (m) window.LocalBackend.warmLesson(decodeURIComponent(m[1]), decodeURIComponent(m[2]));
  };
  document.addEventListener("pointerover", lessonFromLink, { passive: true });
  document.addEventListener("focusin", lessonFromLink);
}

// ---------- router and course loading ----------
// Renders the page for the current hash: #/ (home), #/course, #/course/l/lesson, #/course/p/section, #/course/review.
async function route() {
  const parts = location.hash.replace(/^#\/?/, "").split("/").filter(Boolean).map(decodeURIComponent);
  const seq = ++routeSeq, stale = () => seq !== routeSeq;  // a newer click wins; older loads don't render
  $("#sidebar").classList.remove("open");
  Notes.save.flush();
  try {
    if (!S.courses) S.courses = await api("/courses");
    if (stale()) return;
    if (!parts.length) {
      if (S.courses.length === 1 && !STATIC) return void location.replace(`#/${S.courses[0].id}`);
      return renderHome();
    }
    if (S.cid !== parts[0]) showOpening(parts[0]);
    await loadCourse(parts[0]);
    if (stale()) return;
    const [, kind, id] = parts;
    S.studyPage = ["l", "p", "review"].includes(kind);  // time on these pages counts as study
    if (kind === "l") return renderLesson(id);
    if (kind === "p") return renderProject(id);
    if (kind === "review") return feature("review") ? renderReview() : renderDashboard();
    return renderDashboard();
  } catch (e) {
    if (stale()) return;
    $("#main").innerHTML = `<div class="page"><div class="error-box">Couldn't load this page: ${esc(e.message)}. ${STATIC ? `Check your internet connection and <a href="${esc(location.hash)}" onclick="location.reload()">try again</a>.` : "Check the terminal running <code>server.py</code>."}</div></div>`;
  }
}

// Opening a course can mean downloading it first, so show that straight away: on the card that was
// clicked, or as a loading page when the link was opened directly.
function showOpening(cid) {
  const title = S.courses?.find((course) => course.id === cid)?.title || "the course";
  const card = document.querySelector(`a.course-card[href="#/${CSS.escape(cid)}"]`);
  if (card) {
    document.querySelectorAll(".course-card.is-loading").forEach((c) => c.classList.remove("is-loading"));
    card.classList.add("is-loading"); card.setAttribute("aria-busy", "true");
    const p = card.querySelector("p:last-child");
    if (p) p.innerHTML = `<span class="spinner" aria-hidden="true"></span>Opening ${esc(title)}…`;
  } else {
    $("#main").innerHTML = `<div class="page"><p class="loading-page" role="status"><span class="spinner" aria-hidden="true"></span>Opening ${esc(title)}…</p></div>`;
  }
}

// Loads a course and the learner's state for it (once), filling in defaults for older saved state.
async function loadCourse(cid) {
  if (S.cid === cid) return;
  [S.course, S.state] = await Promise.all([api(`/courses/${cid}`), api(`/courses/${cid}/state`)]);
  S.cid = cid;
  S.state.passed ||= [];
  S.state.watched ||= {};    // "lesson:video:clip" -> 1 once played
  S.state.study ||= {};      // day -> seconds studied
  S.state.pomodoros ||= {};  // day -> focus sessions finished
  S.state.review ||= {};     // quiz id -> {box, due}
  S.state.goal ||= 60;       // daily goal, minutes
  S.quizIndex = {};
  for (const lesson of allLessons()) for (const practice of lesson.practice || []) if (practice.type === "quiz") S.quizIndex[practice.id] = { item: practice, lesson };
  applyLook();
  $("#brand").textContent = S.course.title;
  $("#brand").href = `#/${cid}`;
  const switchable = STATIC || S.courses?.length > 1;  // the web version always offers "All courses" (to add more)
  $("#brand").classList.toggle("switchable", switchable);
  $("#brand").setAttribute("aria-haspopup", switchable ? "menu" : "false");
  document.title = S.course.title;
  if (STATIC) idle(() => window.LocalBackend.warmCourse(cid));
}

// ---------- page chrome: top bar, progress and sidebar outline ----------
// Shows or hides the parts around the page (sidebar, notes, timer, focus) for the view being rendered.
function setChrome({ sidebar = true, notesKey = null } = {}) {
  $("#sidebar").hidden = !sidebar;
  $("#menu-btn").hidden = !sidebar;
  $("#topbar-progress").hidden = !S.course;
  $("#notes-btn").hidden = !feature("notes");
  $("#timer").hidden = !feature("timer");
  $("#focus-btn").hidden = !feature("focusMode");
  if (!feature("focusMode")) Focus.set(false);
  Notes.pageKey = notesKey;
  if (!feature("notes")) $("#notes").hidden = true;
  else if (Notes.open || (store.get("notesOpen") && innerWidth > 1100)) Notes.show();  // follow the page
  if (S.course) { renderProgress(); if (sidebar) renderSidebar(); }
  $("#main").scrollTo?.(0, 0); window.scrollTo(0, 0);
}

function progress(lessons) {
  const total = lessons.length, done = lessons.filter((lesson) => isDone(lesson.id)).length;
  return { total, done, pct: total ? Math.round((done / total) * 100) : 0 };
}

function renderProgress() {
  const { pct } = progress(allLessons());
  $("#topbar-fill").style.width = pct + "%";
  $("#topbar-pct").textContent = `${pct}% done`;
}

function renderSidebar() {
  const cur = location.hash;
  const dueCount = Study.due(S.state.review, Study.dayKey()).length;
  const reviewHref = `#/${S.cid}/review`;
  $("#sidebar").innerHTML = (feature("review") ? `<a class="side-link review-link ${cur === reviewHref ? "active" : ""}" href="${reviewHref}">
      <span class="review-icon" aria-hidden="true">↻</span>Review${dueCount ? `<span class="due-badge">${dueCount}</span>` : ""}</a>` : "") +
    S.course.sections.map((section) => {
    const counts = progress(section.lessons), soon = section.status === "coming-soon";
    const links = section.lessons.map((lesson) => {
      const href = `#/${S.cid}/l/${lesson.id}`;
      return `<a class="side-link ${cur === href ? "active" : ""}" href="${href}"><span class="tick ${isDone(lesson.id) ? "on" : ""}">✓</span>${esc(lesson.title)}</a>`;
    }).join("");
    const proj = section.project ? (() => {
      const href = `#/${S.cid}/p/${section.id}`, items = section.project.checklist || [];
      const ticked = items.length && items.every((_, i) => S.state.checklist[`${section.project.id}:${i}`]);
      return `<a class="side-link project ${cur === href ? "active" : ""}" href="${href}"><span class="tick ${ticked ? "on" : ""}">✓</span>Project: ${esc(section.project.title)}</a>`;
    })() : "";
    const count = `<span class="count">${soon ? "Coming soon" : `${counts.done}/${counts.total}`}</span>`;
    if (soon) return `<div class="side-section soon"><div class="side-section-head"><span class="chev-space"></span><span class="side-title">${esc(section.title)}</span>${count}</div></div>`;
    // The section you're in always shows, even if you folded it earlier.
    const open = !collapsedSections().has(section.id) || (links + proj).includes('side-link active') || (links + proj).includes('side-link project active');
    return `<div class="side-section ${open ? "" : "folded"}">
      <button class="side-section-head" data-sec="${esc(section.id)}" aria-expanded="${open}"><span class="chev" aria-hidden="true"></span><span class="side-title">${esc(section.title)}</span>${count}</button>
      <div class="side-links"><div>${links}${proj}</div></div></div>`;
  }).join("") + themeChooser();
}

// Sections the learner folded in the outline, remembered per course.
const collapsedKey = () => `collapsed:${S.cid}`;
function collapsedSections() {
  try { return new Set(JSON.parse(store.get(collapsedKey()) || "[]")); } catch (e) { return new Set(); }
}
$("#sidebar").addEventListener("click", (e) => {
  const head = e.target.closest("[data-sec]");
  if (!head) return;
  const set = collapsedSections(), id = head.dataset.sec, section = head.parentElement;
  const fold = !section.classList.contains("folded");
  section.classList.toggle("folded", fold);
  head.setAttribute("aria-expanded", String(!fold));
  fold ? set.add(id) : set.delete(id);
  store.set(collapsedKey(), JSON.stringify([...set]));
});

// ---------- views: home and dashboard ----------
function renderHome() {
  S.course = null; S.cid = null;
  applyLook();
  $("#brand").textContent = "LearnPack"; $("#brand").href = "#/"; document.title = "LearnPack";
  $("#brand").classList.remove("switchable");
  setChrome({ sidebar: false });
  $("#main").innerHTML = `<div class="page wide"><div class="hero"><h1 class="page-title">Your courses</h1>
    ${STATIC ? `<p>Pick a course to start. Your progress and notes are saved in this browser, on this device. Use <strong>Back up</strong> on a course page to keep a copy.</p>`
             : `<p>Each course is a folder in <code>courses/</code>. Copy <code>courses/_template</code> to make a new one.</p>`}</div>
    ${S.courses.length ? `<div class="course-grid">${S.courses.map((course) => {
      const pct = course.total ? Math.round((course.done / course.total) * 100) : 0;
      return `<a class="card course-card" href="#/${esc(course.id)}">${courseCover(course.cover)}<h2>${esc(course.title)}</h2><p>${esc(course.description)}</p>
        <div class="lava-track"><div class="lava-fill" style="width:${pct}%"></div></div>
        <p style="margin:8px 0 0">${course.done} of ${course.total} lessons done</p></a>`;
    }).join("")}${STATIC ? addCourseCard() : ""}</div>` : (STATIC ? `<div class="course-grid">${addCourseCard()}</div>` : `<p class="empty">No courses yet. Add a folder with a <code>course.json</code> to <code>courses/</code>.</p>`)}</div>`;
  if (STATIC) wireAddCourse();
}

// A pack's card art (theme.cover): one image for both themes, or a light and a dark one that follow the theme.
function courseCover(cover) {
  if (!cover) return "";
  const light = cover.light || cover.dark, dark = cover.dark || cover.light;
  const img = (src, cls) => `<img class="${cls}" src="${esc(src)}" alt="" decoding="async">`;
  return `<span class="course-cover">${light === dark ? img(light, "") : img(light, "cover-light") + img(dark, "cover-dark")}</span>`;
}

// The first unfinished lesson in a section that's out already.
function nextLesson() {
  return allLessons().find((lesson) => lesson.section.status !== "coming-soon" && !isDone(lesson.id));
}

function renderDashboard() {
  setChrome();
  const overall = progress(allLessons()), next = nextLesson();
  const last = S.state.last && allLessons().find((lesson) => lesson.id === S.state.last);
  const target = (last && !isDone(last.id)) ? last : next;
  $("#main").innerHTML = `<div class="page wide">
    <div class="hero"><h1 class="page-title">${esc(S.course.title)}</h1><p>${esc(S.course.description)}</p>
      <div class="big-progress"><strong>${overall.pct}%</strong><div class="lava-track"><div class="lava-fill" style="width:0"></div></div></div>
      ${target ? `<a class="btn" href="#/${S.cid}/l/${target.id}">${S.state.done.length || target === last ? "Continue" : "Start"}: ${esc(target.title)}</a>`
               : `<p><strong>You've finished every lesson available so far.</strong></p>`}
    </div>
    ${feature("studyStats") ? todayPanel() : ""}
    <div class="section-list">${S.course.sections.map((section) => {
      const counts = progress(section.lessons), soon = section.status === "coming-soon";
      const first = section.lessons[0];
      return `<div class="card section-row ${soon ? "soon" : ""}">
        <div><h3>${first ? `<a href="#/${S.cid}/l/${first.id}">${esc(section.title)}</a>` : esc(section.title)}</h3><p>${esc(section.summary || "")}</p></div>
        <div><div class="stat">${soon ? "Coming soon" : `${counts.done} of ${counts.total} lessons`}</div>
          <div class="lava-track"><div class="lava-fill" style="width:${counts.pct}%"></div></div></div></div>`;
    }).join("")}</div>${STATIC ? backupRow() : ""}</div>`;
  if (STATIC) wireBackup();
  requestAnimationFrame(() => { const f = $(".big-progress .lava-fill"); if (f) f.style.width = overall.pct + "%"; });
}

// ---------- views: lesson (video playlist and Watch, Read, Practice steps) ----------
// The YouTube player is about 1 MB of script, so lessons show its thumbnail and load it on click.
function playerHtml(video, fallbackTitle, play = false, clip = null) {
  const title = esc(clip?.title || video.title || fallbackTitle);
  if (play) return `<iframe src="${ytSrc(video, true, clip)}" title="${title}" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture; fullscreen" allowfullscreen></iframe>`;
  const thumb = video.youtube ? `<img src="https://i.ytimg.com/vi/${encodeURIComponent(video.youtube)}/hqdefault.jpg" alt="" decoding="async">` : "";
  return `<button class="yt-poster" aria-label="Play video: ${title}">${thumb}<span class="yt-play" aria-hidden="true"></span></button>`;
}

// The lesson's videos, as one numbered playlist under the player (like a classroom): each long video
// with clips is a group of short parts; other videos are single items. Parts you've played get a tick.
// "Watch the full video" swaps clips for the original (beta, remembered per browser).
function videoBlock(host, lesson, videos) {
  const anyClips = videos.some((v) => v.clips?.length);
  // What's playing: k = video index, c = clip index (-1 = the whole video), mode = "clips" or "full".
  const st = { k: 0, c: 0, mode: store.get("videoMode") === "full" ? "full" : "clips" };
  const clipsOf = (v) => (st.mode === "clips" && v.clips?.length ? v.clips : null);
  if (!clipsOf(videos[0])) st.c = -1;
  const mins = (s) => `${Math.max(1, Math.round(s / 60))} min`;
  const watched = (k, c) => !!S.state.watched?.[`${lesson.id}:${k}:${c}`];
  const markWatched = (k, c) => { S.state.watched ||= {}; if (!watched(k, c)) { S.state.watched[`${lesson.id}:${k}:${c}`] = 1; saveState(); } };
  const practiceTitle = (id) => {
    const practice = (lesson.practice || []).find((x) => x.id === id);
    if (!practice) return "";
    if (practice.title) return practice.title;
    const q = String(practice.question || "").replace(/[`*_#>]/g, "").replace(/\s+/g, " ").trim();  // a quiz: show its question
    return `Quick check: ${q.length > 48 ? q.slice(0, 46).trimEnd() + "…" : q}`;
  };
  const credit = (v) => (v.title || "").split(":")[0];           // "freeCodeCamp: SQL Tutorial…" -> "freeCodeCamp"
  const named = (v) => (v.title || "").replace(/^[^:]+:\s*/, "");  // … -> "SQL Tutorial…"
  const clipCount = () => videos.reduce((n, v) => n + (clipsOf(v)?.length || 0), 0);
  const minutes = () => videos.reduce((t, v) => t + (clipsOf(v) || []).reduce((a, c) => a + c.end - c.start, 0), 0);

  const item = (k, c, num, title, len, then) => {
    const on = st.k === k && st.c === c, done = watched(k, c);
    return `<li class="pl-item ${on ? "on" : ""} ${done ? "done" : ""}">
      <button class="pl-play" data-k="${k}" data-c="${c}" aria-current="${on}">
        <span class="pl-num" aria-hidden="true">${done ? "✓" : num}</span>
        <span class="pl-title">${esc(title)}</span>${len ? `<span class="pl-len">${len}</span>` : ""}
      </button><span class="pl-try-slot">${then ? `<a href="#" class="pl-try" data-then="${esc(then)}">Now try →</a>` : ""}</span></li>`;
  };
  const playlist = () => {
    let n = 0;
    return `<ol class="playlist">${videos.map((v, k) => {
      const clips = clipsOf(v);
      if (!clips) return item(k, -1, ++n, v.title || `Video ${k + 1}`, v.clips?.length && st.mode === "full" ? "Full video" : "", null);
      return `<li class="pl-group"><div class="pl-group-head"><span>${esc(named(v) || "Video")}</span><span class="pl-credit">${esc(credit(v))}</span></div>
        <ol>${clips.map((c, i) => item(k, i, ++n, c.title, mins(c.end - c.start), c.then)).join("")}</ol></li>`;
    }).join("")}</ol>`;
  };
  const draw = (play = false) => {
    const v = videos[st.k], clips = clipsOf(v), clip = clips && st.c >= 0 ? clips[st.c] : null;
    const then = clip?.then && practiceTitle(clip.then);
    const single = videos.length === 1 && !clips;
    host.innerHTML = `
      <div class="step-label">Step 1 · Watch</div>
      ${single ? "" : `<div class="watch-head"><span>${clipCount() ? `${clipCount()} short clips · about ${Math.round(minutes() / 60)} min` : `${videos.length} videos`}</span>
        ${anyClips ? `<button class="link-btn" data-mode="${st.mode === "clips" ? "full" : "clips"}">${st.mode === "clips" ? "Watch full videos instead" : "Use short clips <span class=\"beta\">beta</span>"}</button>` : ""}</div>`}
      <div class="player">${playerHtml(v, lesson.title, play, clip)}</div>
      <div class="now-playing">
        <span>${clip ? `<b>Part ${st.c + 1} of ${clips.length}</b> · ${esc(clip.title)}` : esc(v.title || "")}</span>
        ${then ? `<a href="#" class="now-try" data-then="${esc(clip.then)}">Now try: ${esc(then)} →</a>` : ""}
      </div>
      ${single ? "" : playlist()}`;
  };
  host.addEventListener("click", (e) => {
    const t = e.target.closest("[data-k],[data-mode],[data-then],.yt-poster");
    if (!t) return;
    if (t.dataset.then) {
      e.preventDefault();
      const card = document.querySelector(`[data-practice-id="${CSS.escape(t.dataset.then)}"]`);
      if (card) { card.scrollIntoView({ behavior: "smooth", block: "start" }); card.classList.remove("flash"); void card.offsetWidth; card.classList.add("flash"); }
    } else if (t.dataset.mode) {
      st.mode = t.dataset.mode; store.set("videoMode", st.mode);
      st.c = clipsOf(videos[st.k]) ? 0 : -1; draw();
    } else if (t.dataset.k) {
      st.k = +t.dataset.k; st.c = +t.dataset.c; markWatched(st.k, st.c); draw(true);
      host.querySelector(".player").scrollIntoView({ behavior: "smooth", block: "nearest" });
    } else { markWatched(st.k, st.c); draw(true); }  // the play button on the thumbnail
  });
  draw();
}

// The privacy-enhanced YouTube embed URL for a video, a clip of it, or a playlist.
function ytSrc(video, autoplay = false, clip = null) {
  const base = "https://www.youtube-nocookie.com/embed/";
  const q = new URLSearchParams({ rel: "0", modestbranding: "1" });
  if (autoplay) q.set("autoplay", "1");
  if (clip) { q.set("start", clip.start); q.set("end", clip.end); }
  else if (video.start) q.set("start", video.start);
  if (video.playlist) { q.set("list", video.playlist); return `${base}videoseries?${q}`; }
  return `${base}${encodeURIComponent(video.youtube)}?${q}`;
}

// "1 Watch → 2 Read → 3 Practice" under the title: shows the lesson as a flow, jumps to each step,
// and lights up the step you're reading.
function lessonSteps(lesson) {
  const steps = [lesson.videos?.length && ["step-watch", "Watch"], ["step-read", "Read"], lesson.practice?.length && ["step-practice", "Practice"]].filter(Boolean);
  if (steps.length < 2) return "";
  return `<nav class="lesson-steps" aria-label="Lesson steps">${steps.map(([id, name], i) =>
    `<button data-step="${id}"><span class="ls-num">${i + 1}</span>${name}</button>${i < steps.length - 1 ? '<span class="ls-line" aria-hidden="true"></span>' : ""}`).join("")}</nav>`;
}
// Makes the step buttons scroll to their section and highlights the step in view.
function wireLessonSteps() {
  const nav = $(".lesson-steps");
  if (!nav) return;
  const buttons = [...nav.querySelectorAll("[data-step]")];
  const light = (id) => buttons.forEach((b) => b.classList.toggle("on", b.dataset.step === id));
  nav.addEventListener("click", (e) => { const b = e.target.closest("[data-step]"); if (b) { light(b.dataset.step); document.getElementById(b.dataset.step)?.scrollIntoView({ behavior: "smooth", block: "start" }); } });
  light(buttons[0].dataset.step);
  const io = new IntersectionObserver((entries) => {
    const seen = entries.filter((x) => x.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
    if (seen) light(seen.target.id);
  }, { rootMargin: "-20% 0px -60% 0px" });
  buttons.forEach((b) => { const el = document.getElementById(b.dataset.step); if (el) io.observe(el); });
}

function renderLesson(id) {
  const list = allLessons(), i = list.findIndex((x) => x.id === id);
  if (i < 0) { setChrome(); $("#main").innerHTML = `<div class="page"><p class="empty">That lesson doesn't exist. <a href="#/${S.cid}">Back to the course</a></p></div>`; return; }
  const lesson = list[i], prev = list[i - 1], next = list[i + 1];
  S.state.last = lesson.id; saveState();
  setChrome({ notesKey: lesson.id });
  const videos = lesson.videos || [];
  $("#main").innerHTML = `<article class="page">
    <div class="crumbs">${esc(lesson.section.title)}</div>
    <h1 class="page-title">${esc(lesson.title)}</h1>
    <p class="meta">${[lesson.duration, videos.length ? `${videos.length} video${videos.length > 1 ? "s" : ""}` : "", (lesson.practice || []).length ? `${lesson.practice.length} practice` : ""].filter(Boolean).join(", ")}</p>
    ${lessonSteps(lesson)}
    ${videos.length ? `<section class="block video-block" id="step-watch" aria-label="Watch"></section>` : ""}
    <section class="block" id="step-read"><div class="step-label">Step ${videos.length ? 2 : 1} · Read</div><div class="prose">${md(lesson.body.replace(/^\s*# [^\n]*\n/, ""))}</div></section>
    ${(lesson.practice || []).length ? `<section class="block" id="step-practice"><div class="step-label">Step ${videos.length ? 3 : 2} · Practice</div><h2>Practice</h2><div id="practice"></div></section>` : ""}
    ${(lesson.resources || []).length ? `<section class="block" id="step-deeper"><h2>Go deeper</h2><ul class="resources">${lesson.resources.map((res) => {
      let host = ""; try { host = new URL(res.url).hostname.replace(/^www\./, ""); } catch (e) {}
      return `<li><a href="${esc(res.url)}" target="_blank" rel="noopener"><span>${esc(res.title)}</span><span class="host">${esc(host)} ↗</span></a></li>`;
    }).join("")}</ul></section>` : ""}
    <div class="lesson-foot">
      <button class="btn ghost done-btn ${isDone(lesson.id) ? "is-done" : ""}" id="done-btn"></button>
      <div class="nav">
        ${prev ? `<a class="btn ghost small" id="prev-lesson" title="Previous lesson ([)" href="#/${S.cid}/l/${prev.id}">Previous</a>` : ""}
        ${next ? `<a class="btn small" id="next-lesson" title="Next lesson (])" href="#/${S.cid}/l/${next.id}">Next: ${esc(next.title)}</a>` : ""}
        ${lesson.section.project ? `<a class="btn ghost small" href="#/${S.cid}/p/${lesson.section.id}">Section project</a>` : ""}
      </div>
    </div></article>`;

  if (videos.length) videoBlock($(".video-block"), lesson, videos);
  wireLessonSteps();

  const doneBtn = $("#done-btn");
  const paint = () => { doneBtn.innerHTML = isDone(lesson.id) ? `<span class="done-check">✓</span> Done` : "Mark as done"; doneBtn.classList.toggle("is-done", isDone(lesson.id)); };
  paint();
  const setDone = (done) => {
    if (isDone(lesson.id) === done) return;
    S.state.done = done ? [...S.state.done, lesson.id] : S.state.done.filter((x) => x !== lesson.id);
    saveState(); paint(); renderSidebar(); renderProgress();
  };
  doneBtn.onclick = () => setDone(!isDone(lesson.id));
  $("#next-lesson")?.addEventListener("click", () => setDone(true));

  const host = $("#practice");
  (lesson.practice || []).forEach((practice) => host.append(practice.type === "quiz" ? quizCard(practice) : codeCard(practice)));
  if (STATIC && next) idle(() => window.LocalBackend.warmLesson(S.cid, next.id));  // the likely next click
}

// ---------- views: practice (quiz and code exercise cards) ----------
// onResult(right) is called after each check. By default (in a lesson) a wrong answer
// goes into the review queue; the review page passes its own handler.
function quizCard(quiz, { onResult = lessonQuizResult(quiz), heading = "Quick check" } = {}) {
  const el = document.createElement("div");
  el.className = "card practice";
  el.dataset.practiceId = quiz.id;
  const name = `q-${quiz.id}`;
  el.innerHTML = `<div class="practice-head"><h3>${esc(heading)}</h3><span class="badge">Quiz</span></div>
    <div class="prose">${md(quiz.question)}</div>
    <div class="options">${quiz.options.map((o, i) => `<label class="option"><input type="radio" name="${name}" value="${i}"><span>${esc(o)}</span></label>`).join("")}</div>
    <div class="actions"><button class="btn small">Check answer</button></div><div class="explain" hidden></div>`;
  $("button", el).onclick = () => {
    const picked = $(`input[name="${name}"]:checked`, el);
    const ex = $(".explain", el);
    if (!picked) { ex.hidden = false; ex.textContent = "Pick an answer first."; return; }
    el.querySelectorAll(".option").forEach((o, i) => { o.classList.remove("correct", "wrong"); if (i === quiz.answer) o.classList.add("correct"); });
    const right = +picked.value === quiz.answer;
    if (!right) picked.closest(".option").classList.add("wrong");
    ex.hidden = false;
    ex.innerHTML = `<strong>${right ? "Correct." : "Not quite."}</strong> ${md(quiz.explanation || "")}`;
    onResult(right, el);
  };
  return el;
}

// The default quiz handler in a lesson: a wrong answer joins the review queue.
function lessonQuizResult(quiz) {
  return (right, el) => {
    if (right || !feature("review")) return;
    Study.miss(S.state.review, quiz.id, Study.dayKey());
    saveState(); renderSidebar();
    const ex = $(".explain", el);
    ex.insertAdjacentHTML("beforeend", `<p class="review-note">Added to your review queue. It comes back tomorrow.</p>`);
  };
}

// A code exercise: editor, Check (runs the tests), Run, solution and reset. Saves as you type.
function codeCard(exercise) {
  const lang = exercise.language || S.course.language || "python";
  const el = document.createElement("div");
  el.className = "card practice";
  el.dataset.practiceId = exercise.id;
  const passed = () => S.state.passed.includes(exercise.id);
  el.innerHTML = `<div class="practice-head"><h3>${esc(exercise.title)}</h3>
      <span><span class="badge">${{ python: "Python", javascript: "JavaScript", typescript: "TypeScript" }[lang]}</span> ${exercise.needs_api_key ? `<span class="badge key" title="Run uses your real API key from .env; Check is free and offline">Uses API key on Run</span> ` : ""}<span class="badge status"></span></span></div>
    <div class="prose">${md(exercise.prompt.replace(/^\s*# [^\n]*\n/, ""))}</div>
    <div class="editor"><textarea></textarea></div>
    <div class="actions">
      <button class="btn small" data-act="check">Check</button>
      <button class="btn ghost small" data-act="run">Run</button>
      <span class="spacer"></span>
      <span class="save-status code-status"></span>
      <button class="btn ghost small" data-act="solution">Show solution</button>
      <button class="btn ghost small" data-act="reset">Reset</button>
    </div>
    <div class="output" hidden></div>`;
  const status = $(".status", el);
  const paintStatus = () => { status.textContent = passed() ? "Passed" : "Not passed yet"; status.classList.toggle("ok", passed()); };
  paintStatus();

  const cm = CodeMirror.fromTextArea($("textarea", el), {
    mode: { python: "python", javascript: "text/javascript", typescript: "text/typescript" }[lang],
    lineNumbers: true, indentUnit: lang === "python" ? 4 : 2, matchBrackets: true, viewportMargin: Infinity,
    extraKeys: { Tab: (editor) => editor.replaceSelection(lang === "python" ? "    " : "  "), "Cmd-Enter": () => go("run"), "Ctrl-Enter": () => go("run"), "Shift-Enter": () => go("check") },
  });
  let loaded = false;  // never save over the learner's file before it has loaded
  api(`/courses/${S.cid}/code/${exercise.id}`).then((code) => { cm.setValue(code); cm.clearHistory(); loaded = true; cm.on("change", () => save()); setTimeout(() => cm.refresh(), 0); })
    .catch(() => { codeStatus.className = "save-status code-status bad"; codeStatus.textContent = "Couldn't load your saved code"; });

  const codeStatus = $(".code-status", el);
  const save = debounce(async () => {
    if (!loaded) return;
    try { await api(`/courses/${S.cid}/code/${exercise.id}`, { method: "PUT", body: cm.getValue(), text: true }); codeStatus.className = "save-status code-status"; codeStatus.textContent = "Saved"; }
    catch (e) { codeStatus.className = "save-status code-status bad"; codeStatus.textContent = "Save failed"; }
  }, 800);

  const out = $(".output", el);
  if (STATIC) {  // web version: get the runtime ready once the exercise is on screen
    const io = new IntersectionObserver((es) => { if (es.some((x) => x.isIntersecting)) { io.disconnect(); window.LocalBackend.warm(S.cid, exercise.id); } });
    io.observe(el);
  }
  // Runs the learner's code (mode "run") or its tests (mode "check") and shows the output.
  async function go(mode) {
    const btns = el.querySelectorAll("[data-act]"), btn = el.querySelector(`[data-act="${mode}"]`);
    btns.forEach((b) => (b.disabled = true));
    btn.classList.add("is-busy"); out.setAttribute("aria-busy", "true");
    // A spinner the whole time; loading messages ("Installing numpy…") replace the text, and when one
    // clears it goes back to "Running tests…" instead of leaving a stale message up.
    const busy = (text) => { out.innerHTML = `<pre role="status"><span class="spinner" aria-hidden="true"></span>${esc(text)}</pre>`; };
    const running = mode === "check" ? "Running tests…" : "Running…";
    out.hidden = false; busy(running);
    save.flush();
    const onStatus = (e) => busy(e.detail || running);
    window.addEventListener("learnpack-runner", onStatus);
    if (STATIC && window.WebRunner.status()) busy(window.WebRunner.status());  // still loading from the warm-up
    try {
      const result = await api(`/courses/${S.cid}/run`, { method: "POST", body: { practice: exercise.id, code: cm.getValue(), mode } });
      let html = "";
      if (mode === "check") {
        const ok = result.results.every((t) => t.passed), passedCount = result.results.filter((t) => t.passed).length;
        html += `<p class="${ok ? "summary-ok" : "summary-bad"}">${ok ? "All tests passed." : `${passedCount} of ${result.results.length} tests passed.`}</p>`;
        html += `<ul class="results">${result.results.map((t) => `<li class="${t.passed ? "pass" : "fail"}"><span class="mark">${t.passed ? "✓" : "✗"}</span><span>${esc(t.name.replace(/^test_/, "").replaceAll("_", " "))}${t.passed ? "" : `<span class="err">${esc(t.error.trim())}</span>`}</span></li>`).join("")}</ul>`;
        if (ok && !passed()) { S.state.passed.push(exercise.id); saveState(); }
        paintStatus();
      }
      const stdout = esc(result.stdout || "");
      if (stdout || result.stderr) html += `<pre>${stdout}${result.stderr ? `<span class="stderr">${esc(result.stderr)}</span>` : ""}</pre>`;
      else if (mode === "run") html += `<pre>(no output, exit code ${result.exit_code})</pre>`;
      out.innerHTML = html;
    } catch (e) {
      out.innerHTML = `<pre class="stderr">Couldn't run your code: ${esc(e.message)}. Is the server still running?</pre>`;
    } finally {
      window.removeEventListener("learnpack-runner", onStatus);
      btns.forEach((b) => (b.disabled = false)); btn.classList.remove("is-busy"); out.removeAttribute("aria-busy");
    }
  }

  el.addEventListener("click", async (e) => {
    const act = e.target.closest("[data-act]")?.dataset.act;
    if (act === "run" || act === "check") go(act);
    if (act === "reset" && confirm("Replace your code with the starter code? Your current code will be lost.")) { cm.setValue(exercise.starter); }
    if (act === "solution") {
      if (!confirm("Show the reference solution? Try to get it passing yourself first.")) return;
      const { solution } = await api(`/courses/${S.cid}/solution/${exercise.id}`);
      out.hidden = false; out.innerHTML = `<p><strong>Reference solution</strong></p><pre>${esc(solution)}</pre>`;
    }
  });
  return el;
}

// ---------- views: project ----------
function renderProject(sid) {
  const section = S.course.sections.find((x) => x.id === sid);
  if (!section?.project) { setChrome(); $("#main").innerHTML = `<div class="page"><p class="empty">No project here. <a href="#/${S.cid}">Back to the course</a></p></div>`; return; }
  const project = section.project;
  setChrome({ notesKey: project.id });
  const links = S.state.links[project.id] || {};
  $("#main").innerHTML = `<article class="page">
    <div class="crumbs">${esc(section.title)}, section project</div>
    <h1 class="page-title">${esc(project.title)}</h1>
    <section class="block prose">${md(project.brief)}</section>
    ${(project.checklist || []).length ? `<section class="block"><h2>Checklist</h2><ul class="checklist">${project.checklist.map((item, i) => {
      const k = `${project.id}:${i}`;
      return `<li><label><input type="checkbox" data-k="${esc(k)}" ${S.state.checklist[k] ? "checked" : ""}><span>${md(item).replace(/^<p>|<\/p>\s*$/g, "")}</span></label></li>`;
    }).join("")}</ul></section>` : ""}
    ${project.links ? `<section class="block"><h2>Where it lives</h2>
      <label class="field">GitHub repo<input type="url" data-link="repo" placeholder="https://github.com/you/project" value="${esc(links.repo || "")}"></label>
      <label class="field">Live URL<input type="url" data-link="live" placeholder="https://your-app.example.com" value="${esc(links.live || "")}"></label>
      <div class="actions">${["repo", "live"].map((k) => /^https?:\/\//.test(links[k] || "") ? `<a class="btn ghost small" href="${esc(links[k])}" target="_blank" rel="noopener">Open ${k === "repo" ? "repo" : "live app"} ↗</a>` : "").join("")}</div>
    </section>` : ""}
  </article>`;
  $("#main").querySelectorAll("[data-k]").forEach((cb) => (cb.onchange = () => {
    if (cb.checked) S.state.checklist[cb.dataset.k] = true; else delete S.state.checklist[cb.dataset.k];
    saveState(); renderSidebar();
  }));
  $("#main").querySelectorAll("[data-link]").forEach((inp) => (inp.oninput = () => {
    S.state.links[project.id] = { ...(S.state.links[project.id] || {}), [inp.dataset.link]: inp.value.trim() };
    saveState();
  }));
}

// ---------- focus mode and keyboard shortcuts ----------
// Focus mode: only the lesson stays on screen. F toggles, Esc leaves.
// Focus mode puts the browser in full screen and leaves the interface as it is. Browsers only allow
// full screen from a click or key press, so it starts from the button or F, never on page load.
const Focus = {
  on: false,
  set(on) {
    this.on = on;
    document.body.classList.toggle("focus-mode", on);
    $("#focus-btn").setAttribute("aria-pressed", String(on));
    $("#focus-btn").title = on ? "Leave focus mode (F or Esc)" : "Focus mode (F)";
    const full = !!document.fullscreenElement;
    if (on && !full) document.documentElement.requestFullscreen?.().catch(() => {});  // still focus mode if refused
    if (!on && full) document.exitFullscreen?.().catch(() => {});
  },
};
// Leaving full screen with the browser's own Esc also leaves focus mode, so the two stay in sync.
document.addEventListener("fullscreenchange", () => { if (!document.fullscreenElement && Focus.on) Focus.set(false); });
$("#focus-btn").onclick = () => Focus.set(!Focus.on);
// True when a key press is going into a text field or code editor, so shortcuts stay out of the way.
const typing = (t) => t.closest?.("input, textarea, select, [contenteditable='true'], .CodeMirror");
document.addEventListener("keydown", (e) => {
  if (e.metaKey || e.ctrlKey || e.altKey || typing(e.target) || !feature("focusMode")) return;
  if (e.key === "f" || e.key === "F") { e.preventDefault(); Focus.set(!Focus.on); }
  if (e.key === "Escape" && Focus.on) Focus.set(false);
});
// Use the lesson links so Next also records completion, just like a click.
document.addEventListener("keydown", (e) => {
  if (e.defaultPrevented || e.isComposing || e.repeat || e.metaKey || e.ctrlKey || e.altKey || typing(e.target)) return;
  const link = e.key === "[" ? $("#prev-lesson") : e.key === "]" ? $("#next-lesson") : null;
  if (link) { e.preventDefault(); link.click(); }
});

// ---------- Pomodoro timer ----------
// Focus timer (Pomodoro). Runs off a wall-clock end time, so it survives page changes and reloads.
const Timer = {
  phases: { focus: "Focus", short: "Short break", long: "Long break" },
  lens() {  // phase lengths in minutes, with the learner's changes
    const defaults = { focus: 25, short: 5, long: 15 };
    try { return { ...defaults, ...JSON.parse(store.get("timerLens") || "{}") }; } catch (e) { return defaults; }
  },
  load() {
    try { return JSON.parse(store.get("timer") || "null"); } catch (e) { return null; }
  },
  state: null,
  init() {
    this.state = this.load() || { phase: "focus", running: false, left: this.lens().focus * 60e3, endsAt: 0, done: 0 };
    this.paint();
    setInterval(() => this.tick(), 1000);
  },
  persist() { store.set("timer", JSON.stringify(this.state)); },
  remaining() { const s = this.state; return s.running ? Math.max(0, s.endsAt - Date.now()) : s.left; },
  start() { const s = this.state; s.running = true; s.endsAt = Date.now() + s.left; this.persist(); this.paint(); },
  pause() { const s = this.state; s.left = this.remaining(); s.running = false; this.persist(); this.paint(); },
  setPhase(phase) {
    this.state = { ...this.state, phase, running: false, left: this.lens()[phase] * 60e3 };
    this.persist(); this.paint();
  },
  finish() {
    const s = this.state;
    if (s.phase === "focus" && S.cid) {
      const day = Study.dayKey();
      S.state.pomodoros[day] = (S.state.pomodoros[day] || 0) + 1;
      saveState();
      if (location.hash === `#/${S.cid}`) renderDashboard();  // refresh the Today numbers
    }
    if (s.phase === "focus") s.done = (s.done || 0) + 1;
    const next = Study.nextPhase(s.phase, s.done);
    chime();
    toast(s.phase === "focus" ? `Focus session done. Time for a ${next === "long" ? "long" : "short"} break.` : "Break's over. Ready to focus?");
    this.setPhase(next);
  },
  tick() {
    if (this.state.running && this.remaining() <= 0) this.finish();
    this.paint();
  },
  paint() {
    const s = this.state, ms = this.remaining();
    const t = `${String(Math.floor(ms / 60e3)).padStart(2, "0")}:${String(Math.floor(ms / 1e3) % 60).padStart(2, "0")}`;
    $("#timer-time").textContent = t;
    $("#timer-big").textContent = t;
    $("#timer").dataset.phase = s.phase;
    $("#timer").classList.toggle("running", s.running);
    $("#timer-start").textContent = s.running ? "Pause" : ms < this.lens()[s.phase] * 60e3 ? "Resume" : "Start";
    document.querySelectorAll("[data-phase]").forEach((b) => b.classList.toggle("active", b.dataset.phase === s.phase));
    const today = S.cid ? S.state.pomodoros[Study.dayKey()] || 0 : 0;
    $("#timer-meta").textContent = `${today} focus session${today === 1 ? "" : "s"} today`;
    const base = S.course ? S.course.title : "LearnPack";
    document.title = s.running ? `${t} ${this.phases[s.phase]} · ${base}` : base;
  },
};
// A soft two-note chime (Web Audio) when a timer phase ends.
function chime() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    [660, 880].forEach((freq, i) => {
      const osc = ctx.createOscillator(), gain = ctx.createGain(), t0 = ctx.currentTime + i * 0.22;
      osc.frequency.value = freq; osc.connect(gain); gain.connect(ctx.destination);
      gain.gain.setValueAtTime(0.0001, t0); gain.gain.exponentialRampToValueAtTime(0.2, t0 + 0.02); gain.gain.exponentialRampToValueAtTime(0.0001, t0 + 0.5);
      osc.start(t0); osc.stop(t0 + 0.55);
    });
  } catch (e) {}
}
function toast(msg) {
  let box = $("#study-toast");
  if (!box) { box = document.createElement("div"); box.id = "study-toast"; box.className = "study-toast"; box.setAttribute("role", "status"); document.body.append(box); }
  box.textContent = msg; box.hidden = false;
  clearTimeout(box._h); box._h = setTimeout(() => (box.hidden = true), 6000);
}
$("#timer-btn").onclick = () => {
  const pop = $("#timer-pop"); pop.hidden = !pop.hidden;
  $("#timer-btn").setAttribute("aria-expanded", String(!pop.hidden));
  if (!pop.hidden) document.querySelectorAll("[data-len]").forEach((i) => (i.value = Timer.lens()[i.dataset.len]));
};
document.addEventListener("click", (e) => {
  if (!$("#timer-pop").hidden && !e.target.closest("#timer")) { $("#timer-pop").hidden = true; $("#timer-btn").setAttribute("aria-expanded", "false"); }
});
$("#timer-start").onclick = () => (Timer.state.running ? Timer.pause() : Timer.start());
$("#timer-reset").onclick = () => Timer.setPhase(Timer.state.phase);
$("#timer-skip").onclick = () => Timer.setPhase(Study.nextPhase(Timer.state.phase, (Timer.state.done || 0) + (Timer.state.phase === "focus" ? 1 : 0)));
document.querySelectorAll("[data-phase]").forEach((b) => (b.onclick = () => Timer.setPhase(b.dataset.phase)));
document.querySelectorAll("[data-len]").forEach((i) => (i.onchange = () => {
  const v = Math.min(+i.max, Math.max(1, Math.round(+i.value) || 1));
  i.value = v;
  store.set("timerLens", JSON.stringify({ ...Timer.lens(), [i.dataset.len]: v }));
  if (!Timer.state.running && i.dataset.len === Timer.state.phase) Timer.setPhase(Timer.state.phase);
}));
Timer.init();

// ---------- study time and Today panel ----------
// Study time: counted in 15 s steps while a lesson, project or review page is open and you're
// active (input in the last 3 minutes), or a focus session is running (covers watching videos).
let lastActive = Date.now();
["mousemove", "keydown", "scroll", "click", "touchstart"].forEach((ev) => addEventListener(ev, () => (lastActive = Date.now()), { passive: true }));
setInterval(() => {
  if (!S.cid || !S.studyPage || document.visibilityState !== "visible") return;
  const focusing = Timer.state.running && Timer.state.phase === "focus";
  if (!focusing && Date.now() - lastActive > 3 * 60e3) return;
  const day = Study.dayKey();
  S.state.study[day] = (S.state.study[day] || 0) + 15;
  saveState();
}, 15e3);

const STREAK_MIN = 15 * 60;  // a day counts toward the streak after 15 minutes of study
const mins = (s) => Math.floor(s / 60);

// The dashboard's Today card: goal ring, streak, focus sessions, reviews due and the last 7 days.
function todayPanel() {
  const today = Study.dayKey(), studied = S.state.study[today] || 0, goal = S.state.goal;
  const pct = Math.min(100, Math.round((studied / (goal * 60)) * 100));
  const streak = Study.streak(S.state.study, today, STREAK_MIN);
  const week = Study.week(S.state.study, today), top = Math.max(goal * 60, ...week.map((d) => d.seconds));
  const due = Study.due(S.state.review, today).length, pomos = S.state.pomodoros[today] || 0;
  const circumference = 2 * Math.PI * 42;  // of the goal ring (r = 42)
  return `<section class="card today" aria-label="Today">
    <div class="today-goal">
      <svg class="ring" viewBox="0 0 100 100" aria-hidden="true"><circle cx="50" cy="50" r="42" class="ring-bg"/>
        <circle cx="50" cy="50" r="42" class="ring-fill" stroke-dasharray="${circumference}" stroke-dashoffset="${circumference * (1 - pct / 100)}"/></svg>
      <div class="ring-label"><strong>${mins(studied)}</strong><span>of ${goal} min</span></div>
    </div>
    <div class="today-stats">
      <h2>Today</h2>
      <p>${pct >= 100 ? "Daily goal reached. Nice work." : `${goal - mins(studied)} min to your daily goal.`}</p>
      <ul class="stat-row">
        <li><strong>${streak}</strong><span>day streak</span></li>
        <li><strong>${pomos}</strong><span>focus session${pomos === 1 ? "" : "s"}</span></li>
        <li><strong>${due}</strong><span>to review</span></li>
      </ul>
      <div class="today-actions">
        ${due ? `<a class="btn small" href="#/${S.cid}/review">Review ${due} question${due === 1 ? "" : "s"}</a>` : ""}
        <label class="goal-input">Daily goal <input type="number" id="goal-input" min="5" max="600" step="5" value="${goal}"> min</label>
      </div>
    </div>
    <div class="week" aria-label="Minutes studied, last 7 days">
      ${week.map((d) => {
        const [year, month, date] = d.key.split("-").map(Number);
        const label = new Date(year, month - 1, date).toLocaleDateString(undefined, { weekday: "narrow" });
        const met = d.seconds >= goal * 60;
        return `<div class="week-day ${d.key === today ? "is-today" : ""}" title="${mins(d.seconds)} min on ${d.key}">
          <div class="week-bar"><div class="week-fill ${met ? "met" : ""}" style="height:${Math.round((d.seconds / top) * 100)}%"></div></div><span>${label}</span></div>`;
      }).join("")}
    </div>
  </section>`;
}
document.addEventListener("change", (e) => {
  if (e.target.id !== "goal-input") return;
  S.state.goal = Math.min(600, Math.max(5, Math.round(+e.target.value) || 60));
  saveState(); renderDashboard();
});

// ---------- views: review ----------
// Today's due quiz questions, one at a time (spaced repetition in study.js).
function renderReview() {
  setChrome({ notesKey: null });
  const today = Study.dayKey();
  const queue = Study.due(S.state.review, today).filter((id) => S.quizIndex[id]);
  const later = Object.values(S.state.review).filter((entry) => entry.due > today).sort((a, b) => a.due.localeCompare(b.due));
  const page = $("#main");
  if (!queue.length) {
    page.innerHTML = `<div class="page"><h1 class="page-title">Review</h1>
      <p class="meta">Questions you miss in lessons come back here on later days: tomorrow, then 3, 7 and 14 days later, until you've got them right four times in a row.</p>
      <div class="card review-empty"><h2>Nothing to review today</h2>
      <p>${later.length ? `${later.length} question${later.length === 1 ? "" : "s"} scheduled. The next one is due ${later[0].due === Study.addDays(today, 1) ? "tomorrow" : later[0].due}.` : "Answer the quizzes in each lesson. Any you get wrong will show up here."}</p>
      <a class="btn ghost small" href="#/${S.cid}">Back to the course</a></div></div>`;
    return;
  }
  let i = 0, right = 0;
  const show = () => {
    if (i >= queue.length) {
      page.innerHTML = `<div class="page"><h1 class="page-title">Review done</h1>
        <div class="card review-empty"><h2>${right} of ${queue.length} right</h2>
        <p>Right answers come back later each time; missed ones come back tomorrow.</p>
        <a class="btn" href="#/${S.cid}">Back to the course</a></div></div>`;
      renderSidebar();
      return;
    }
    const { item, lesson } = S.quizIndex[queue[i]];
    page.innerHTML = `<div class="page"><div class="crumbs">Review, ${i + 1} of ${queue.length}</div>
      <h1 class="page-title">Review</h1>
      <div class="lava-track review-progress"><div class="lava-fill" style="width:${(i / queue.length) * 100}%"></div></div>
      <div id="review-card"></div>
      <p class="meta">From <a href="#/${S.cid}/l/${lesson.id}">${esc(lesson.title)}</a></p></div>`;
    const card = quizCard(item, {
      heading: lesson.section.title,
      onResult(ok, el) {
        if (el.dataset.answered) return;  // only the first answer counts
        el.dataset.answered = "1";
        if (ok) { right++; Study.pass(S.state.review, item.id, today); } else Study.miss(S.state.review, item.id, today);
        saveState();
        $(".actions", el).insertAdjacentHTML("beforeend", `<button class="btn small" id="review-next">${i + 1 < queue.length ? "Next question" : "Finish"}</button>`);
        $("#review-next").onclick = () => { i++; show(); };
        $("#review-next").focus();
      },
    });
    $("#review-card").append(card);
  };
  show();
}

// ---------- pack features and look (configured only in the pack's course.json) ----------

// Features default to on; a pack turns one off with "features": {"timer": false}.
const feature = (name) => !!S.course && S.course.features?.[name] !== false;

// Applies the open course's accent color and add-on stylesheet (or clears them on the home page).
function applyLook() {
  const root = document.documentElement.style;
  const accent = S.course?.theme?.accent;
  accent ? root.setProperty("--accent", accent) : root.removeProperty("--accent");
  // A pack's add-on stylesheet loads after the platform's, so it can restyle anything.
  $("#pack-css")?.remove();
  if (STATIC && S.course?._themeCss) {
    document.head.append(Object.assign(document.createElement("style"), { id: "pack-css", textContent: S.course._themeCss }));
  } else if (S.course?.theme?.css) {
    const link = Object.assign(document.createElement("link"), { id: "pack-css", rel: "stylesheet", href: `packs/${S.cid}/theme.css` });
    document.head.append(link);
  }
}

// ---------- course switcher (header title) ----------
// With more than one course installed, the title in the header opens a menu of all courses.
const CourseMenu = {
  async toggle(show = $("#course-menu").hidden) {
    const menu = $("#course-menu");
    if (!show) { menu.hidden = true; $("#brand").setAttribute("aria-expanded", "false"); return; }
    try { S.courses = await api("/courses"); } catch (e) {}
    menu.innerHTML = S.courses.map((course) => {
      const pct = course.total ? Math.round((course.done / course.total) * 100) : 0;
      return `<a class="course-item ${course.id === S.cid ? "current" : ""}" role="menuitem" href="#/${esc(course.id)}" style="--dot:${esc(course.accent || "var(--accent)")}">
        <span class="course-dot" aria-hidden="true"></span>
        <span class="course-name">${esc(course.title)}</span><span class="course-pct">${pct}%</span></a>`;
    }).join("") + `<a class="course-item all" role="menuitem" href="#/">All courses</a>`;
    menu.hidden = false;
    $("#brand").setAttribute("aria-expanded", "true");
  },
};
$("#brand").addEventListener("click", (e) => {
  if (!S.course || !S.courses || (S.courses.length < 2 && !STATIC)) return;  // one course: the title just goes to its dashboard
  e.preventDefault();
  CourseMenu.toggle();
});
document.addEventListener("click", (e) => { if (!e.target.closest(".brand-wrap")) CourseMenu.toggle(false); });
document.addEventListener("keydown", (e) => { if (e.key === "Escape") CourseMenu.toggle(false); });
window.addEventListener("hashchange", () => CourseMenu.toggle(false));

// ---------- in-app browser: links open in a panel, not in new tabs ----------
// Sites that allow framing load live. Sites that refuse are fetched by the server and shown as a
// reading copy in a sandbox with no scripts; links inside it keep opening in the panel.
const Browser = {
  stack: [], at: -1, loadId: 0,  // history of URLs, the one shown, and a counter so stale loads are ignored
  get open() { return !$("#browser").hidden; },
  show(url) {
    this.stack = this.stack.slice(0, this.at + 1);
    this.stack.push(url); this.at = this.stack.length - 1;
    this.load();
  },
  go(step) { const i = this.at + step; if (i >= 0 && i < this.stack.length) { this.at = i; this.load(); } },
  close() {
    $("#browser").hidden = true;
    const frame = $("#br-frame"); frame.removeAttribute("srcdoc"); frame.src = "about:blank";
  },
  state(msg, { error = false } = {}) {  // the loading or error message over the panel ("" hides it)
    const box = $("#br-state");
    box.hidden = !msg; box.classList.toggle("error", error);
    box.innerHTML = msg;
    $("#br-ext").hidden = !error;  // leaving the course is only offered when a page can't be shown here
  },
  async load() {
    const url = this.stack[this.at], id = ++this.loadId, frame = $("#br-frame");
    $("#browser").hidden = false;
    $("#br-back").disabled = this.at <= 0;
    $("#br-fwd").disabled = this.at >= this.stack.length - 1;
    let host = url; try { host = new URL(url).hostname.replace(/^www\./, ""); } catch (e) {}
    $("#br-title").textContent = host; $("#br-url").textContent = url;
    $("#br-ext").href = url; $("#br-mode").hidden = true;
    this.state('<span class="spinner" aria-hidden="true"></span> Loading…');
    try {
      const page = await api(`/browse?url=${encodeURIComponent(url)}`);
      if (id !== this.loadId) return;  // a newer click won
      if (page.title) $("#br-title").textContent = page.title;
      frame.onload = () => { if (id === this.loadId) { this.state(""); if (!page.embeddable) this.hook(); } };
      frame.removeAttribute("srcdoc");
      if (page.embeddable) {
        frame.setAttribute("sandbox", "allow-scripts allow-same-origin allow-forms allow-popups allow-presentation");
        frame.src = page.url;
      } else {
        $("#br-mode").hidden = false;
        frame.setAttribute("sandbox", "allow-same-origin");  // no scripts run in a reading copy
        frame.src = "about:blank";
        frame.srcdoc = page.html;
      }
    } catch (e) {
      if (id !== this.loadId) return;
      if (e.message === "browse-unavailable") return this.liveOnly(url, id);  // web version: no server to fetch with
      const msg = (e.message.match(/"error":\s*"([^"]+)"/) || [])[1] || "This page couldn't be shown here.";
      this.state(`<strong>Can't show this page here.</strong><br>${esc(msg)}`, { error: true });
    }
  },
  // Web version: there's no server to make reading copies, so sites known to block embedding get a
  // clear "open it in a new tab" card, and everything else loads live.
  BLOCKS: /(^|\.)(github\.com|x\.com|twitter\.com|linkedin\.com|google\.com|facebook\.com|instagram\.com|medium\.com|stackoverflow\.com|reddit\.com|notion\.so|figma\.com)$/i,
  liveOnly(url, id) {
    let host = ""; try { host = new URL(url).hostname; } catch (e) {}
    if (this.BLOCKS.test(host)) {
      return this.state(`<strong>${esc(host.replace(/^www\./, ""))} doesn't allow being shown inside other pages.</strong><br>Use the ↗ button above to open it in a new tab, then come back here.`, { error: true });
    }
    const frame = $("#br-frame");
    frame.onload = () => { if (id === this.loadId) this.state(""); };
    frame.removeAttribute("srcdoc");
    frame.setAttribute("sandbox", "allow-scripts allow-same-origin allow-forms allow-popups allow-presentation");
    frame.src = url;
    $("#br-ext").hidden = false;  // in case the site refuses to load in the panel
  },
  hook() {  // keep link clicks inside a reading copy in the panel
    let doc; try { doc = $("#br-frame").contentDocument; } catch (e) { return; }
    doc?.addEventListener("click", (e) => {
      const a = e.target.closest?.("a[href]");
      if (!a) return;
      const href = a.href;
      if (/^https?:/i.test(href) && !(a.getAttribute("href") || "").startsWith("#")) { e.preventDefault(); this.show(href); }
    });
  },
};
// Every external link inside the course opens in the panel (videos are embedded already).
$("#main").addEventListener("click", (e) => {
  const a = e.target.closest("a[href]");
  if (!a || !feature("browser") || !/^https?:\/\//i.test(a.getAttribute("href") || "")) return;
  if (e.metaKey || e.ctrlKey || e.shiftKey) return;  // a deliberate new-tab click is respected
  e.preventDefault();
  Browser.show(a.href);
});
$("#br-back").onclick = () => Browser.go(-1);
$("#br-fwd").onclick = () => Browser.go(1);
$("#br-reload").onclick = () => Browser.load();
$("#br-close").onclick = () => Browser.close();
document.addEventListener("keydown", (e) => { if (e.key === "Escape" && Browser.open && !document.fullscreenElement) Browser.close(); });
window.addEventListener("hashchange", () => Browser.close());

// Drag the panel's left edge to resize it (arrow keys work too). The width is remembered.
(() => {
  const panel = $("#browser"), handle = $("#br-resize");
  const clamp = (w) => Math.round(Math.min(innerWidth - 160, Math.max(360, w)));
  const apply = (w) => { panel.style.width = clamp(w) + "px"; };
  const saved = +store.get("browserWidth");
  if (saved) apply(saved);
  handle.addEventListener("pointerdown", (e) => {
    e.preventDefault();
    handle.setPointerCapture(e.pointerId);
    document.body.classList.add("resizing");  // stops the page inside the panel from eating the drag
    const move = (ev) => apply(innerWidth - ev.clientX);
    const up = () => {
      document.body.classList.remove("resizing");
      handle.removeEventListener("pointermove", move);
      store.set("browserWidth", parseInt(panel.style.width, 10));
    };
    handle.addEventListener("pointermove", move);
    handle.addEventListener("pointerup", up, { once: true });
  });
  handle.addEventListener("keydown", (e) => {
    const step = e.shiftKey ? 80 : 24;
    if (e.key === "ArrowLeft" || e.key === "ArrowRight") {
      e.preventDefault();
      apply(panel.getBoundingClientRect().width + (e.key === "ArrowLeft" ? step : -step));
      store.set("browserWidth", parseInt(panel.style.width, 10));
    }
  });
  window.addEventListener("resize", () => { if (panel.style.width) apply(parseInt(panel.style.width, 10)); });
})();

// ---------- web version only: add a course, back up and restore ----------
function addCourseCard() {
  return `<label class="card course-card add-course" id="add-course" tabindex="0">
    <h2>Add a course</h2>
    <p>Drop a course pack here (a <code>.learnpack.json</code> file or a <code>.zip</code> of a pack folder), or click to choose one.</p>
    <span class="btn ghost small">Choose a file</span>
    <input type="file" id="add-course-file" accept=".json,.zip,application/json,application/zip" hidden>
    <p class="add-status" id="add-status" role="status"></p></label>`;
}
function wireAddCourse() {
  const card = $("#add-course"), input = $("#add-course-file"), status = $("#add-status");
  const add = async (file) => {
    if (!file) return;
    status.className = "add-status"; status.textContent = `Adding ${file.name}…`;
    try {
      const course = await window.LocalBackend.addPack(file);
      S.courses = await api("/courses");
      location.hash = `#/${course.id}`;
    } catch (e) { status.className = "add-status bad"; status.textContent = e.message.replace(/^\d+ /, ""); }
  };
  input.onchange = () => add(input.files[0]);
  card.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); input.click(); } });
  ["dragenter", "dragover"].forEach((ev) => card.addEventListener(ev, (e) => { e.preventDefault(); card.classList.add("dragging"); }));
  ["dragleave", "drop"].forEach((ev) => card.addEventListener(ev, () => card.classList.remove("dragging")));
  card.addEventListener("drop", (e) => { e.preventDefault(); add(e.dataTransfer.files[0]); });
}
function backupRow() {
  const imported = S.courses?.find((c) => c.id === S.cid)?.imported;
  return `<div class="backup-row">
    <span>Your progress, notes and code are saved in this browser.</span>
    <button class="btn ghost small" id="backup-btn">Back up</button>
    <label class="btn ghost small">Restore<input type="file" id="restore-file" accept=".json,application/json" hidden></label>
    ${imported ? `<button class="btn ghost small" id="remove-course">Remove course</button>` : ""}
    <span class="add-status" id="backup-status" role="status"></span></div>`;
}
function wireBackup() {
  const say = (msg, bad) => { const box = $("#backup-status"); box.className = "add-status" + (bad ? " bad" : ""); box.textContent = msg; };
  $("#backup-btn").onclick = async () => {
    const data = await window.LocalBackend.backup(S.cid);
    const link = Object.assign(document.createElement("a"), {
      href: URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" })),
      download: `${S.cid}-backup-${new Date().toISOString().slice(0, 10)}.json`,
    });
    document.body.append(link); link.click(); link.remove();
    say("Backup downloaded. Keep it somewhere safe.");
  };
  $("#restore-file").onchange = async (e) => {
    const file = e.target.files[0]; if (!file) return;
    try {
      await window.LocalBackend.restore(S.cid, JSON.parse(await file.text()));
      S.state = await api(`/courses/${S.cid}/state`);
      S.state.passed ||= []; S.state.study ||= {}; S.state.pomodoros ||= {}; S.state.review ||= {}; S.state.goal ||= 60; S.state.watched ||= {};
      renderDashboard(); say("Restored.");
    } catch (err) { say(err.message, true); }
  };
  const rm = $("#remove-course");
  if (rm) rm.onclick = async () => {
    if (!confirm("Remove this course from this browser? Your progress stays saved in case you add it again.")) return;
    await window.LocalBackend.removePack(S.cid);
    S.courses = await api("/courses"); S.cid = null; location.hash = "#/";
  };
}
