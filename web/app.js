"use strict";
// Learning platform front end. Renders any course pack served by server.py.

const $ = (sel, root = document) => root.querySelector(sel);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const store = {
  get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} },
};

async function api(path, { method = "GET", body, text = false } = {}) {
  const res = await fetch("/api" + path, {
    method,
    headers: { "X-Learn-Token": window.LEARN_TOKEN, ...(body !== undefined && !text ? { "Content-Type": "application/json" } : {}) },
    body: body === undefined ? undefined : text ? body : JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${res.status} ${(await res.text()).slice(0, 200)}`);
  return (res.headers.get("Content-Type") || "").includes("json") ? res.json() : res.text();
}

function md(text) {
  const html = DOMPurify.sanitize(marked.parse(text || ""), { ADD_ATTR: ["target"] });
  const div = document.createElement("div");
  div.innerHTML = html;
  div.querySelectorAll("pre code").forEach((el) => { try { hljs.highlightElement(el); } catch (e) {} });
  div.querySelectorAll("a[href^='http']").forEach((a) => { a.target = "_blank"; a.rel = "noopener"; });
  return div.innerHTML;
}

function debounce(fn, ms) {
  let t;
  const d = (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };
  d.flush = (...a) => { clearTimeout(t); return fn(...a); };
  return d;
}

// ---------- state ----------
const S = { courses: null, course: null, cid: null, state: null, editors: [] };
const allLessons = () => S.course.sections.flatMap((s) => s.lessons.map((l) => ({ ...l, section: s })));
const isDone = (id) => S.state.done.includes(id);

const saveState = debounce(async () => {
  try { await api(`/courses/${S.cid}/state`, { method: "PUT", body: S.state }); }
  catch (e) { toastError("Progress didn't save. Is the server still running?"); }
}, 300);

function toastError(msg) {
  let t = $("#toast");
  if (!t) { t = document.createElement("div"); t.id = "toast"; t.className = "error-box"; t.setAttribute("role", "alert");
    Object.assign(t.style, { position: "fixed", bottom: "16px", left: "50%", transform: "translateX(-50%)", background: "var(--surface)", zIndex: 50 });
    document.body.append(t); }
  t.textContent = msg; t.hidden = false;
  clearTimeout(t._h); t._h = setTimeout(() => (t.hidden = true), 5000);
}

// ---------- theme ----------
const THEMES = ["system", "light", "dark"];
function applyTheme(t) {
  if (t === "system") delete document.documentElement.dataset.theme; else document.documentElement.dataset.theme = t;
  const dark = t === "dark" || (t === "system" && matchMedia("(prefers-color-scheme: dark)").matches);
  $("#hl-light").disabled = dark; $("#hl-dark").disabled = !dark;
  $("#theme-btn").textContent = { system: "◐", light: "☀", dark: "☾" }[t];
  $("#theme-btn").title = `Theme: ${t} (click to change)`;
}
$("#theme-btn").onclick = () => {
  const next = THEMES[(THEMES.indexOf(store.get("theme") || "system") + 1) % 3];
  store.set("theme", next); applyTheme(next);
};
matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => applyTheme(store.get("theme") || "system"));
applyTheme(store.get("theme") || "system");

// ---------- notes drawer (works like Apple Notes) ----------
const ed = $("#nv-editor");
document.execCommand("defaultParagraphSeparator", false, "div");

const DAY = 864e5;
const startOfDay = (d) => new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
const fmtLong = (ms) => new Date(ms).toLocaleString(undefined, { day: "numeric", month: "long", year: "numeric", hour: "2-digit", minute: "2-digit" });
function fmtShort(ms) {
  const d = new Date(ms), age = startOfDay(new Date()) - startOfDay(d);
  if (age <= 0) return d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
  if (age === DAY) return "Yesterday";
  if (age < 7 * DAY) return d.toLocaleDateString(undefined, { weekday: "long" });
  return d.toLocaleDateString();
}
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
      const r = await fetch(`/api/courses/${S.cid}/notes/${key}`, { headers: { "X-Learn-Token": window.LEARN_TOKEN } });
      if (!r.ok) throw new Error(r.status);
      const raw = await r.text();
      const html = r.headers.get("X-Note-Format") === "md" ? marked.parse(raw) : raw;  // older Markdown notes convert on open
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
  const r = document.createRange(); r.selectNodeContents(ed); r.collapse(false);
  const s = getSelection(); s.removeAllRanges(); s.addRange(r);
}
function caretClosest(selector) {
  const n = getSelection().anchorNode;
  const el = n && (n.nodeType === 1 ? n : n.parentElement);
  const hit = el?.closest(selector);
  return hit && ed.contains(hit) ? hit : null;
}
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
      const s = getSelection(), inNode = s.anchorNode === node, off = s.anchorOffset;
      const div = document.createElement("div"); node.replaceWith(div); div.append(node);
      if (inNode) s.collapse(node, off);
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
window.addEventListener("hashchange", route);
route();

async function route() {
  const parts = location.hash.replace(/^#\/?/, "").split("/").filter(Boolean).map(decodeURIComponent);
  $("#sidebar").classList.remove("open");
  Notes.save.flush();
  S.editors = [];
  try {
    if (!S.courses) S.courses = await api("/courses");
    if (!parts.length) {
      if (S.courses.length === 1) return void location.replace(`#/${S.courses[0].id}`);
      return renderHome();
    }
    await loadCourse(parts[0]);
    const [, kind, id] = parts;
    S.studyPage = ["l", "p", "review"].includes(kind);  // time on these pages counts as study
    if (kind === "l") return renderLesson(id);
    if (kind === "p") return renderProject(id);
    if (kind === "review") return feature("review") ? renderReview() : renderDashboard();
    return renderDashboard();
  } catch (e) {
    $("#main").innerHTML = `<div class="page"><div class="error-box">Couldn't load this page: ${esc(e.message)}. Check the terminal running <code>server.py</code>.</div></div>`;
  }
}

async function loadCourse(cid) {
  if (S.cid === cid) return;
  [S.course, S.state] = await Promise.all([api(`/courses/${cid}`), api(`/courses/${cid}/state`)]);
  S.cid = cid;
  S.state.passed ||= [];
  S.state.study ||= {};      // day -> seconds studied
  S.state.pomodoros ||= {};  // day -> focus sessions finished
  S.state.review ||= {};     // quiz id -> {box, due}
  S.state.goal ||= 60;       // daily goal, minutes
  S.quizIndex = {};
  for (const l of allLessons()) for (const p of l.practice || []) if (p.type === "quiz") S.quizIndex[p.id] = { item: p, lesson: l };
  applyLook();
  $("#brand").textContent = S.course.title;
  $("#brand").href = `#/${cid}`;
  $("#brand").classList.toggle("switchable", S.courses?.length > 1);
  $("#brand").setAttribute("aria-haspopup", S.courses?.length > 1 ? "menu" : "false");
  document.title = S.course.title;
}

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
  const total = lessons.length, done = lessons.filter((l) => isDone(l.id)).length;
  return { total, done, pct: total ? Math.round((done / total) * 100) : 0 };
}

function renderProgress() {
  const p = progress(allLessons());
  $("#topbar-fill").style.width = p.pct + "%";
  $("#topbar-pct").textContent = `${p.pct}% done`;
}

function renderSidebar() {
  const cur = location.hash;
  const dueCount = Study.due(S.state.review, Study.dayKey()).length;
  const reviewHref = `#/${S.cid}/review`;
  $("#sidebar").innerHTML = (feature("review") ? `<a class="side-link review-link ${cur === reviewHref ? "active" : ""}" href="${reviewHref}">
      <span class="review-icon" aria-hidden="true">↻</span>Review${dueCount ? `<span class="due-badge">${dueCount}</span>` : ""}</a>` : "") +
    S.course.sections.map((s) => {
    const p = progress(s.lessons), soon = s.status === "coming-soon";
    const links = s.lessons.map((l) => {
      const href = `#/${S.cid}/l/${l.id}`;
      return `<a class="side-link ${cur === href ? "active" : ""}" href="${href}"><span class="tick ${isDone(l.id) ? "on" : ""}">✓</span>${esc(l.title)}</a>`;
    }).join("");
    const proj = s.project ? (() => {
      const href = `#/${S.cid}/p/${s.id}`, items = s.project.checklist || [];
      const ticked = items.length && items.every((_, i) => S.state.checklist[`${s.project.id}:${i}`]);
      return `<a class="side-link project ${cur === href ? "active" : ""}" href="${href}"><span class="tick ${ticked ? "on" : ""}">✓</span>Project: ${esc(s.project.title)}</a>`;
    })() : "";
    const count = `<span class="count">${soon ? "Coming soon" : `${p.done}/${p.total}`}</span>`;
    if (soon) return `<div class="side-section soon"><div class="side-section-head"><span class="chev-space"></span><span class="side-title">${esc(s.title)}</span>${count}</div></div>`;
    // The section you're in always shows, even if you folded it earlier.
    const open = !collapsedSections().has(s.id) || (links + proj).includes('side-link active') || (links + proj).includes('side-link project active');
    return `<div class="side-section ${open ? "" : "folded"}">
      <button class="side-section-head" data-sec="${esc(s.id)}" aria-expanded="${open}"><span class="chev" aria-hidden="true"></span><span class="side-title">${esc(s.title)}</span>${count}</button>
      <div class="side-links"><div>${links}${proj}</div></div></div>`;
  }).join("");
}

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

// ---------- views ----------
function renderHome() {
  S.course = null; S.cid = null;
  applyLook();
  $("#brand").textContent = "Learn"; $("#brand").href = "#/"; document.title = "Learn";
  $("#brand").classList.remove("switchable");
  setChrome({ sidebar: false });
  $("#main").innerHTML = `<div class="page wide"><div class="hero"><h1 class="page-title">Your courses</h1>
    <p>Each course is a folder in <code>courses/</code>. Copy <code>courses/_template</code> to make a new one.</p></div>
    ${S.courses.length ? `<div class="course-grid">${S.courses.map((c) => {
      const pct = c.total ? Math.round((c.done / c.total) * 100) : 0;
      return `<a class="card course-card" href="#/${esc(c.id)}"><h2>${esc(c.title)}</h2><p>${esc(c.description)}</p>
        <div class="lava-track"><div class="lava-fill" style="width:${pct}%"></div></div>
        <p style="margin:8px 0 0">${c.done} of ${c.total} lessons done</p></a>`;
    }).join("")}</div>` : `<p class="empty">No courses yet. Add a folder with a <code>course.json</code> to <code>courses/</code>.</p>`}</div>`;
}

function nextLesson() {
  return allLessons().find((l) => l.section.status !== "coming-soon" && !isDone(l.id));
}

function renderDashboard() {
  setChrome();
  const p = progress(allLessons()), next = nextLesson();
  const last = S.state.last && allLessons().find((l) => l.id === S.state.last);
  const target = (last && !isDone(last.id)) ? last : next;
  $("#main").innerHTML = `<div class="page wide">
    <div class="hero"><h1 class="page-title">${esc(S.course.title)}</h1><p>${esc(S.course.description)}</p>
      <div class="big-progress"><strong>${p.pct}%</strong><div class="lava-track"><div class="lava-fill" style="width:0"></div></div></div>
      ${target ? `<a class="btn" href="#/${S.cid}/l/${target.id}">${S.state.done.length || target === last ? "Continue" : "Start"}: ${esc(target.title)}</a>`
               : `<p><strong>You've finished every lesson available so far.</strong></p>`}
    </div>
    ${feature("studyStats") ? todayPanel() : ""}
    <div class="section-list">${S.course.sections.map((s) => {
      const sp = progress(s.lessons), soon = s.status === "coming-soon";
      const first = s.lessons[0];
      return `<div class="card section-row ${soon ? "soon" : ""}">
        <div><h3>${first ? `<a href="#/${S.cid}/l/${first.id}">${esc(s.title)}</a>` : esc(s.title)}</h3><p>${esc(s.summary || "")}</p></div>
        <div><div class="stat">${soon ? "Coming soon" : `${sp.done} of ${sp.total} lessons`}</div>
          <div class="lava-track"><div class="lava-fill" style="width:${sp.pct}%"></div></div></div></div>`;
    }).join("")}</div></div>`;
  requestAnimationFrame(() => { const f = $(".big-progress .lava-fill"); if (f) f.style.width = p.pct + "%"; });
}

function ytSrc(v) {
  const base = "https://www.youtube-nocookie.com/embed/";
  const q = new URLSearchParams({ rel: "0", modestbranding: "1" });
  if (v.start) q.set("start", v.start);
  if (v.playlist) { q.set("list", v.playlist); return `${base}videoseries?${q}`; }
  return `${base}${encodeURIComponent(v.youtube)}?${q}`;
}

function renderLesson(id) {
  const list = allLessons(), i = list.findIndex((l) => l.id === id);
  if (i < 0) { setChrome(); $("#main").innerHTML = `<div class="page"><p class="empty">That lesson doesn't exist. <a href="#/${S.cid}">Back to the course</a></p></div>`; return; }
  const l = list[i], prev = list[i - 1], next = list[i + 1];
  S.state.last = l.id; saveState();
  setChrome({ notesKey: l.id });
  const videos = l.videos || [];
  $("#main").innerHTML = `<article class="page">
    <div class="crumbs">${esc(l.section.title)}</div>
    <h1 class="page-title">${esc(l.title)}</h1>
    <p class="meta">${[l.duration, videos.length ? `${videos.length} video${videos.length > 1 ? "s" : ""}` : "", (l.practice || []).length ? `${l.practice.length} practice` : ""].filter(Boolean).join(", ")}</p>
    ${videos.length ? `<section class="block" aria-label="Video">
      ${videos.length > 1 ? `<div class="video-tabs tabs">${videos.map((v, k) => `<button class="tab ${k ? "" : "active"}" data-video="${k}">${esc(v.title || `Video ${k + 1}`)}</button>`).join("")}</div>` : ""}
      <div class="player"><iframe src="${ytSrc(videos[0])}" title="${esc(videos[0].title || l.title)}" allow="accelerometer; encrypted-media; gyroscope; picture-in-picture; fullscreen" allowfullscreen loading="lazy"></iframe></div>
      ${videos.length === 1 && videos[0].title ? `<p class="meta" style="margin-top:8px">${esc(videos[0].title)}</p>` : ""}
    </section>` : ""}
    <section class="block prose">${md(l.body.replace(/^\s*# [^\n]*\n/, ""))}</section>
    ${(l.resources || []).length ? `<section class="block"><h2>Go deeper</h2><ul class="resources">${l.resources.map((r) => {
      let host = ""; try { host = new URL(r.url).hostname.replace(/^www\./, ""); } catch (e) {}
      return `<li><a href="${esc(r.url)}" target="_blank" rel="noopener"><span>${esc(r.title)}</span><span class="host">${esc(host)} ↗</span></a></li>`;
    }).join("")}</ul></section>` : ""}
    ${(l.practice || []).length ? `<section class="block"><h2>Practice</h2><div id="practice"></div></section>` : ""}
    <div class="lesson-foot">
      <button class="btn ghost done-btn ${isDone(l.id) ? "is-done" : ""}" id="done-btn"></button>
      <div class="nav">
        ${prev ? `<a class="btn ghost small" href="#/${S.cid}/l/${prev.id}">Previous</a>` : ""}
        ${next ? `<a class="btn small" href="#/${S.cid}/l/${next.id}">Next: ${esc(next.title)}</a>` : ""}
        ${l.section.project ? `<a class="btn ghost small" href="#/${S.cid}/p/${l.section.id}">Section project</a>` : ""}
      </div>
    </div></article>`;

  document.querySelectorAll("[data-video]").forEach((b) => (b.onclick = () => {
    document.querySelectorAll("[data-video]").forEach((x) => x.classList.toggle("active", x === b));
    const v = videos[+b.dataset.video];
    $(".player iframe").src = ytSrc(v); $(".player iframe").title = v.title || l.title;
  }));

  const doneBtn = $("#done-btn");
  const paint = () => { doneBtn.innerHTML = isDone(l.id) ? `<span class="done-check">✓</span> Done` : "Mark as done"; doneBtn.classList.toggle("is-done", isDone(l.id)); };
  paint();
  doneBtn.onclick = () => {
    S.state.done = isDone(l.id) ? S.state.done.filter((x) => x !== l.id) : [...S.state.done, l.id];
    saveState(); paint(); renderSidebar(); renderProgress();
  };

  const host = $("#practice");
  (l.practice || []).forEach((p) => host.append(p.type === "quiz" ? quizCard(p) : codeCard(p)));
}

// onResult(right) is called after each check. By default (in a lesson) a wrong answer
// goes into the review queue; the review page passes its own handler.
function quizCard(p, { onResult = lessonQuizResult(p), heading = "Quick check" } = {}) {
  const el = document.createElement("div");
  el.className = "card practice";
  const name = `q-${p.id}`;
  el.innerHTML = `<div class="practice-head"><h3>${esc(heading)}</h3><span class="badge">Quiz</span></div>
    <div class="prose">${md(p.question)}</div>
    <div class="options">${p.options.map((o, i) => `<label class="option"><input type="radio" name="${name}" value="${i}"><span>${esc(o)}</span></label>`).join("")}</div>
    <div class="actions"><button class="btn small">Check answer</button></div><div class="explain" hidden></div>`;
  $("button", el).onclick = () => {
    const picked = $(`input[name="${name}"]:checked`, el);
    const ex = $(".explain", el);
    if (!picked) { ex.hidden = false; ex.textContent = "Pick an answer first."; return; }
    el.querySelectorAll(".option").forEach((o, i) => { o.classList.remove("correct", "wrong"); if (i === p.answer) o.classList.add("correct"); });
    const right = +picked.value === p.answer;
    if (!right) picked.closest(".option").classList.add("wrong");
    ex.hidden = false;
    ex.innerHTML = `<strong>${right ? "Correct." : "Not quite."}</strong> ${md(p.explanation || "")}`;
    onResult(right, el);
  };
  return el;
}

function lessonQuizResult(p) {
  return (right, el) => {
    if (right || !feature("review")) return;
    Study.miss(S.state.review, p.id, Study.dayKey());
    saveState(); renderSidebar();
    const ex = $(".explain", el);
    ex.insertAdjacentHTML("beforeend", `<p class="review-note">Added to your review queue. It comes back tomorrow.</p>`);
  };
}

function codeCard(p) {
  const lang = p.language || S.course.language || "python";
  const el = document.createElement("div");
  el.className = "card practice";
  const passed = () => S.state.passed.includes(p.id);
  el.innerHTML = `<div class="practice-head"><h3>${esc(p.title)}</h3>
      <span><span class="badge">${{ python: "Python", javascript: "JavaScript", typescript: "TypeScript" }[lang]}</span> ${p.needs_api_key ? `<span class="badge key" title="Run uses your real API key from .env; Check is free and offline">Uses API key on Run</span> ` : ""}<span class="badge status"></span></span></div>
    <div class="prose">${md(p.prompt.replace(/^\s*# [^\n]*\n/, ""))}</div>
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
    extraKeys: { Tab: (c) => c.replaceSelection(lang === "python" ? "    " : "  "), "Cmd-Enter": () => go("run"), "Ctrl-Enter": () => go("run"), "Shift-Enter": () => go("check") },
  });
  S.editors.push(cm);
  let loaded = false;  // never save over the learner's file before it has loaded
  api(`/courses/${S.cid}/code/${p.id}`).then((code) => { cm.setValue(code); cm.clearHistory(); loaded = true; cm.on("change", () => save()); setTimeout(() => cm.refresh(), 0); })
    .catch(() => { codeStatus.className = "save-status code-status bad"; codeStatus.textContent = "Couldn't load your saved code"; });

  const codeStatus = $(".code-status", el);
  const save = debounce(async () => {
    if (!loaded) return;
    try { await api(`/courses/${S.cid}/code/${p.id}`, { method: "PUT", body: cm.getValue(), text: true }); codeStatus.className = "save-status code-status"; codeStatus.textContent = "Saved"; }
    catch (e) { codeStatus.className = "save-status code-status bad"; codeStatus.textContent = "Save failed"; }
  }, 800);

  const out = $(".output", el);
  async function go(mode) {
    const btns = el.querySelectorAll("[data-act]");
    btns.forEach((b) => (b.disabled = true));
    out.hidden = false; out.innerHTML = `<pre>${mode === "check" ? "Running tests…" : "Running…"}</pre>`;
    save.flush();
    try {
      const r = await api(`/courses/${S.cid}/run`, { method: "POST", body: { practice: p.id, code: cm.getValue(), mode } });
      let html = "";
      if (mode === "check") {
        const ok = r.results.every((t) => t.passed), n = r.results.filter((t) => t.passed).length;
        html += `<p class="${ok ? "summary-ok" : "summary-bad"}">${ok ? "All tests passed." : `${n} of ${r.results.length} tests passed.`}</p>`;
        html += `<ul class="results">${r.results.map((t) => `<li class="${t.passed ? "pass" : "fail"}"><span class="mark">${t.passed ? "✓" : "✗"}</span><span>${esc(t.name.replace(/^test_/, "").replaceAll("_", " "))}${t.passed ? "" : `<span class="err">${esc(t.error.trim())}</span>`}</span></li>`).join("")}</ul>`;
        if (ok && !passed()) { S.state.passed.push(p.id); saveState(); }
        paintStatus();
      }
      const stdout = esc(r.stdout || "");
      if (stdout || r.stderr) html += `<pre>${stdout}${r.stderr ? `<span class="stderr">${esc(r.stderr)}</span>` : ""}</pre>`;
      else if (mode === "run") html += `<pre>(no output, exit code ${r.exit_code})</pre>`;
      out.innerHTML = html;
    } catch (e) {
      out.innerHTML = `<pre class="stderr">Couldn't run your code: ${esc(e.message)}. Is the server still running?</pre>`;
    } finally { btns.forEach((b) => (b.disabled = false)); }
  }

  el.addEventListener("click", async (e) => {
    const act = e.target.closest("[data-act]")?.dataset.act;
    if (act === "run" || act === "check") go(act);
    if (act === "reset" && confirm("Replace your code with the starter code? Your current code will be lost.")) { cm.setValue(p.starter); }
    if (act === "solution") {
      if (!confirm("Show the reference solution? Try to get it passing yourself first.")) return;
      const { solution } = await api(`/courses/${S.cid}/solution/${p.id}`);
      out.hidden = false; out.innerHTML = `<p><strong>Reference solution</strong></p><pre>${esc(solution)}</pre>`;
    }
  });
  return el;
}

function renderProject(sid) {
  const s = S.course.sections.find((x) => x.id === sid);
  if (!s?.project) { setChrome(); $("#main").innerHTML = `<div class="page"><p class="empty">No project here. <a href="#/${S.cid}">Back to the course</a></p></div>`; return; }
  const pr = s.project;
  setChrome({ notesKey: pr.id });
  const links = S.state.links[pr.id] || {};
  $("#main").innerHTML = `<article class="page">
    <div class="crumbs">${esc(s.title)}, section project</div>
    <h1 class="page-title">${esc(pr.title)}</h1>
    <section class="block prose">${md(pr.brief)}</section>
    ${(pr.checklist || []).length ? `<section class="block"><h2>Checklist</h2><ul class="checklist">${pr.checklist.map((c, i) => {
      const k = `${pr.id}:${i}`;
      return `<li><label><input type="checkbox" data-k="${esc(k)}" ${S.state.checklist[k] ? "checked" : ""}><span>${md(c).replace(/^<p>|<\/p>\s*$/g, "")}</span></label></li>`;
    }).join("")}</ul></section>` : ""}
    ${pr.links ? `<section class="block"><h2>Where it lives</h2>
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
    S.state.links[pr.id] = { ...(S.state.links[pr.id] || {}), [inp.dataset.link]: inp.value.trim() };
    saveState();
  }));
}

// ---------- study & focus ----------

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
const typing = (t) => t.closest?.("input, textarea, select, [contenteditable='true'], .CodeMirror");
document.addEventListener("keydown", (e) => {
  if (e.metaKey || e.ctrlKey || e.altKey || typing(e.target) || !feature("focusMode")) return;
  if (e.key === "f" || e.key === "F") { e.preventDefault(); Focus.set(!Focus.on); }
  if (e.key === "Escape" && Focus.on) Focus.set(false);
});

// Focus timer (Pomodoro). Runs off a wall-clock end time, so it survives page changes and reloads.
const Timer = {
  phases: { focus: "Focus", short: "Short break", long: "Long break" },
  lens() {
    const d = { focus: 25, short: 5, long: 15 };
    try { return { ...d, ...JSON.parse(store.get("timerLens") || "{}") }; } catch (e) { return d; }
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
      const d = Study.dayKey();
      S.state.pomodoros[d] = (S.state.pomodoros[d] || 0) + 1;
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
    const base = S.course ? S.course.title : "Learn";
    document.title = s.running ? `${t} ${this.phases[s.phase]} · ${base}` : base;
  },
};
function chime() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    [660, 880].forEach((f, i) => {
      const o = ctx.createOscillator(), g = ctx.createGain(), t0 = ctx.currentTime + i * 0.22;
      o.frequency.value = f; o.connect(g); g.connect(ctx.destination);
      g.gain.setValueAtTime(0.0001, t0); g.gain.exponentialRampToValueAtTime(0.2, t0 + 0.02); g.gain.exponentialRampToValueAtTime(0.0001, t0 + 0.5);
      o.start(t0); o.stop(t0 + 0.55);
    });
  } catch (e) {}
}
function toast(msg) {
  let t = $("#study-toast");
  if (!t) { t = document.createElement("div"); t.id = "study-toast"; t.className = "study-toast"; t.setAttribute("role", "status"); document.body.append(t); }
  t.textContent = msg; t.hidden = false;
  clearTimeout(t._h); t._h = setTimeout(() => (t.hidden = true), 6000);
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

// Study time: counted in 15 s steps while a lesson, project or review page is open and you're
// active (input in the last 3 minutes), or a focus session is running (covers watching videos).
let lastActive = Date.now();
["mousemove", "keydown", "scroll", "click", "touchstart"].forEach((ev) => addEventListener(ev, () => (lastActive = Date.now()), { passive: true }));
setInterval(() => {
  if (!S.cid || !S.studyPage || document.visibilityState !== "visible") return;
  const focusing = Timer.state.running && Timer.state.phase === "focus";
  if (!focusing && Date.now() - lastActive > 3 * 60e3) return;
  const d = Study.dayKey();
  S.state.study[d] = (S.state.study[d] || 0) + 15;
  saveState();
}, 15e3);

const STREAK_MIN = 15 * 60;  // a day counts toward the streak after 15 minutes of study
const mins = (s) => Math.floor(s / 60);

function todayPanel() {
  const today = Study.dayKey(), studied = S.state.study[today] || 0, goal = S.state.goal;
  const pct = Math.min(100, Math.round((studied / (goal * 60)) * 100));
  const streak = Study.streak(S.state.study, today, STREAK_MIN);
  const wk = Study.week(S.state.study, today), top = Math.max(goal * 60, ...wk.map((d) => d.seconds));
  const due = Study.due(S.state.review, today).length, pomos = S.state.pomodoros[today] || 0;
  const C = 2 * Math.PI * 42;
  return `<section class="card today" aria-label="Today">
    <div class="today-goal">
      <svg class="ring" viewBox="0 0 100 100" aria-hidden="true"><circle cx="50" cy="50" r="42" class="ring-bg"/>
        <circle cx="50" cy="50" r="42" class="ring-fill" stroke-dasharray="${C}" stroke-dashoffset="${C * (1 - pct / 100)}"/></svg>
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
      ${wk.map((d) => {
        const [y, m, dd] = d.key.split("-").map(Number);
        const label = new Date(y, m - 1, dd).toLocaleDateString(undefined, { weekday: "narrow" });
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

function renderReview() {
  setChrome({ notesKey: null });
  const today = Study.dayKey();
  const queue = Study.due(S.state.review, today).filter((id) => S.quizIndex[id]);
  const later = Object.values(S.state.review).filter((c) => c.due > today).sort((a, b) => a.due.localeCompare(b.due));
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

function applyLook() {
  const root = document.documentElement.style;
  const accent = S.course?.theme?.accent;
  accent ? root.setProperty("--accent", accent) : root.removeProperty("--accent");
  // A pack's add-on stylesheet loads after the platform's, so it can restyle anything.
  $("#pack-css")?.remove();
  if (S.course?.theme?.css) {
    const link = Object.assign(document.createElement("link"), { id: "pack-css", rel: "stylesheet", href: `/packs/${S.cid}/theme.css` });
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
    menu.innerHTML = S.courses.map((c) => {
      const pct = c.total ? Math.round((c.done / c.total) * 100) : 0;
      return `<a class="course-item ${c.id === S.cid ? "current" : ""}" role="menuitem" href="#/${esc(c.id)}" style="--dot:${esc(c.accent || "var(--accent)")}">
        <span class="course-dot" aria-hidden="true"></span>
        <span class="course-name">${esc(c.title)}</span><span class="course-pct">${pct}%</span></a>`;
    }).join("") + `<a class="course-item all" role="menuitem" href="#/">All courses</a>`;
    menu.hidden = false;
    $("#brand").setAttribute("aria-expanded", "true");
  },
};
$("#brand").addEventListener("click", (e) => {
  if (!S.course || !S.courses || S.courses.length < 2) return;  // one course: the title just goes to its dashboard
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
  stack: [], at: -1, loadId: 0,
  get open() { return !$("#browser").hidden; },
  show(url) {
    this.stack = this.stack.slice(0, this.at + 1);
    this.stack.push(url); this.at = this.stack.length - 1;
    this.load();
  },
  go(step) { const i = this.at + step; if (i >= 0 && i < this.stack.length) { this.at = i; this.load(); } },
  close() {
    $("#browser").hidden = true;
    const f = $("#br-frame"); f.removeAttribute("srcdoc"); f.src = "about:blank";
  },
  state(msg, { error = false } = {}) {
    const s = $("#br-state");
    s.hidden = !msg; s.classList.toggle("error", error);
    s.innerHTML = msg;
    $("#br-ext").hidden = !error;  // leaving the course is only offered when a page can't be shown here
  },
  async load() {
    const url = this.stack[this.at], id = ++this.loadId, f = $("#br-frame");
    $("#browser").hidden = false;
    $("#br-back").disabled = this.at <= 0;
    $("#br-fwd").disabled = this.at >= this.stack.length - 1;
    let host = url; try { host = new URL(url).hostname.replace(/^www\./, ""); } catch (e) {}
    $("#br-title").textContent = host; $("#br-url").textContent = url;
    $("#br-ext").href = url; $("#br-mode").hidden = true;
    this.state('<span class="spinner" aria-hidden="true"></span> Loading…');
    try {
      const r = await api(`/browse?url=${encodeURIComponent(url)}`);
      if (id !== this.loadId) return;  // a newer click won
      if (r.title) $("#br-title").textContent = r.title;
      f.onload = () => { if (id === this.loadId) { this.state(""); if (!r.embeddable) this.hook(); } };
      f.removeAttribute("srcdoc");
      if (r.embeddable) {
        f.setAttribute("sandbox", "allow-scripts allow-same-origin allow-forms allow-popups allow-presentation");
        f.src = r.url;
      } else {
        $("#br-mode").hidden = false;
        f.setAttribute("sandbox", "allow-same-origin");  // no scripts run in a reading copy
        f.src = "about:blank";
        f.srcdoc = r.html;
      }
    } catch (e) {
      if (id !== this.loadId) return;
      const msg = (e.message.match(/"error":\s*"([^"]+)"/) || [])[1] || "This page couldn't be shown here.";
      this.state(`<strong>Can't show this page here.</strong><br>${esc(msg)}`, { error: true });
    }
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
