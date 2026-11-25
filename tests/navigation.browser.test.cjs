// Requires playwright-core and its Chromium browser.
const assert = require("node:assert/strict");
const { spawn } = require("node:child_process");
const { once } = require("node:events");
const fs = require("node:fs/promises");
const os = require("node:os");
const path = require("node:path");
const readline = require("node:readline");
const test = require("node:test");
const { setTimeout: delay } = require("node:timers/promises");
const { chromium } = require("playwright-core");

const ROOT = path.resolve(__dirname, "..");
const CID = "navigation-demo";
const TOKEN = "navigation-test-token";
const SERVER = [
  "from pathlib import Path",
  "import sys",
  "from server import serve",
  "root = Path(sys.argv[1])",
  "httpd, _ = serve(0, root / 'courses', root / 'data', 'navigation-test-token')",
  "print(f'http://127.0.0.1:{httpd.server_address[1]}', flush=True)",
  "httpd.serve_forever()",
].join("\n");
const WEB_SERVER = [
  "from pathlib import Path",
  "from functools import partial",
  "from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler",
  "from engine.webbuild import build_web",
  "import sys",
  "root = Path(sys.argv[1])",
  "build_web(root / 'site', root / 'courses')",
  "httpd = ThreadingHTTPServer(('127.0.0.1', 0), partial(SimpleHTTPRequestHandler, directory=str(root / 'site')))",
  "print(f'http://127.0.0.1:{httpd.server_address[1]}', flush=True)",
  "httpd.serve_forever()",
].join("\n");

async function navigationPage(t, { web = false, keyboard = false } = {}) {
  const temporary = await fs.mkdtemp(path.join(os.tmpdir(), "learnpack-navigation-"));
  let server, browser;
  t.after(async () => {
    await browser?.close();
    if (server && server.exitCode === null && server.signalCode === null) {
      const stopped = once(server, "exit");
      server.kill();
      await stopped;
    }
    await fs.rm(temporary, { recursive: true, force: true });
  });
  const course = {
    format: 1, id: CID, title: "Navigation test",
    features: { notes: keyboard, timer: false, focusMode: false, studyStats: false, review: false },
    sections: [{
      id: "lessons", title: "Lessons", lessons: ["first", "second", "third"].map((id) => ({
        id, title: id[0].toUpperCase() + id.slice(1) + " lesson", body: "A written lesson.",
      })),
    }],
  };
  if (keyboard) course.sections[0].lessons[1].practice = [{
    id: "brackets", type: "code", language: "javascript", title: "Brackets", prompt: "Write an array.",
    starter: "", solution: "[]", tests: "test('example', () => {});",
  }];
  const pack = path.join(temporary, "courses", CID);
  const data = path.join(temporary, "data", CID);
  await fs.mkdir(pack, { recursive: true });
  await fs.mkdir(data, { recursive: true });
  await fs.writeFile(path.join(pack, "course.json"), JSON.stringify(course));
  const initialState = {
    done: [], last: "", checklist: { retained: true }, links: {}, passed: ["prior-exercise"],
  };
  await fs.writeFile(path.join(data, "state.json"), JSON.stringify(initialState));
  server = spawn(process.env.PYTHON || "python3", ["-u", "-c", web ? WEB_SERVER : SERVER, temporary], { cwd: ROOT });
  let stderr = "";
  server.stderr.on("data", (chunk) => { stderr += chunk; });
  const lines = readline.createInterface({ input: server.stdout });
  const base = await new Promise((resolve, reject) => {
    lines.once("line", resolve);
    server.once("error", reject);
    server.once("exit", (code) => reject(new Error("Test server exited: " + code + "\n" + stderr)));
  });
  lines.close();
  browser = await chromium.launch({ executablePath: process.env.BROWSER_EXECUTABLE, headless: true });
  const page = await browser.newPage();
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  if (web) {
    await page.goto(base);
    await page.evaluate(({ cid, body }) => window.LocalBackend.api(`/courses/${cid}/state`, {
      method: "PUT", body,
    }), { cid: CID, body: initialState });
  }
  const lesson = (id) => base + "/#/" + CID + "/l/" + id;
  const state = async () => {
    if (web) return page.evaluate((cid) => window.LocalBackend.api(`/courses/${cid}/state`), CID);
    const response = await page.request.get(base + "/api/courses/" + CID + "/state", {
      headers: { "X-Learn-Token": TOKEN },
    });
    assert.equal(response.status(), 200);
    return response.json();
  };
  const savedAfter = async (action, last) => {
    if (web) {
      await action();
      const deadline = Date.now() + 10_000;
      for (;;) {
        const saved = await state();
        if (saved.last === last) return saved;
        assert.ok(Date.now() < deadline, `Progress was not saved for ${last}.`);
        await delay(25);
      }
    }
    const saved = page.waitForResponse((response) =>
      response.url() === base + "/api/courses/" + CID + "/state"
      && response.request().method() === "PUT"
      && response.request().postDataJSON().last === last);
    await action();
    assert.equal((await saved).status(), 200);
    return state();
  };
  const tick = (id) => page.locator('a.side-link[href="#/' + CID + "/l/" + id + '"] .tick');
  return { page, base, lesson, state, savedAfter, tick, errors };
}

test("Next completes the lesson and preserves navigation and manual completion", { timeout: 60_000 }, async (t) => {
  const { page, lesson, savedAfter, tick, errors } = await navigationPage(t);
  await page.goto(lesson("first"));
  await page.getByRole("heading", { name: "First lesson", exact: true }).waitFor();
  let saved = await savedAfter(
    () => page.getByRole("link", { name: "Next: Second lesson", exact: true }).click(), "second");
  await page.getByRole("heading", { name: "Second lesson", exact: true }).waitFor();
  assert.deepEqual(saved.done, ["first"], "Next must persist completion of the lesson being left.");
  assert.match(await tick("first").getAttribute("class"), /\bon\b/);
  assert.equal(await page.locator("#topbar-pct").textContent(), "33% done");

  await savedAfter(() => page.reload(), "second");
  await page.getByRole("heading", { name: "Second lesson", exact: true }).waitFor();
  assert.match(await tick("first").getAttribute("class"), /\bon\b/);
  saved = await savedAfter(
    () => page.getByRole("link", { name: "Previous", exact: true }).click(), "first");
  assert.deepEqual(saved.done, ["first"], "Previous must not complete the lesson being left.");
  saved = await savedAfter(
    () => page.getByRole("link", { name: "Next: Second lesson", exact: true }).click(), "second");
  assert.deepEqual(saved.done, ["first"], "Revisiting Next must not duplicate completed lessons.");

  saved = await savedAfter(
    () => page.getByRole("button", { name: "Mark as done", exact: true }).click(), "second");
  assert.deepEqual(saved.done, ["first", "second"]);
  saved = await savedAfter(() => page.locator("#done-btn").click(), "second");
  assert.deepEqual(saved.done, ["first"], "Manual unmark must still work.");
  saved = await savedAfter(
    () => page.locator('a.side-link[href="#/' + CID + '/l/third"]').click(), "third");
  assert.deepEqual(saved.done, ["first"], "Sidebar navigation must not complete skipped lessons.");
  await savedAfter(
    () => page.getByRole("link", { name: "Previous", exact: true }).click(), "second");
  saved = await savedAfter(
    () => page.getByRole("link", { name: "Next: Third lesson", exact: true }).click(), "third");
  assert.deepEqual(saved.done, ["first", "second"]);
  assert.equal(await page.getByRole("link", { name: /^Next:/ }).count(), 0);
  saved = await savedAfter(
    () => page.getByRole("button", { name: "Mark as done", exact: true }).click(), "third");
  assert.deepEqual(saved.done, ["first", "second", "third"]);
  assert.deepEqual(saved.passed, ["prior-exercise"], "Lesson completion must not alter exercise results.");
  assert.deepEqual(saved.checklist, { retained: true });
  assert.equal(await page.locator("#topbar-pct").textContent(), "100% done");
  assert.deepEqual(errors, []);
});

for (const web of [false, true]) {
  test(`Lesson keyboard navigation (${web ? "web" : "local"})`, { timeout: 60_000 }, async (t) => {
    const { page, base, lesson, state, savedAfter, errors } = await navigationPage(t, { web, keyboard: true });
    const heading = (name) => page.getByRole("heading", { name: name + " lesson", exact: true }).waitFor();
    const press = async (key) => { await page.locator("#main").focus(); await page.keyboard.press(key); };
    await page.goto(lesson("first"));
    await heading("First");
    await press("[");
    assert.equal(page.url(), lesson("first"), "There is no previous lesson at the start.");
    let saved = await savedAfter(() => press("]"), "second");
    await heading("Second");
    assert.deepEqual(saved.done, ["first"], "The shortcut must complete the lesson just like Next.");
    assert.match(await page.locator("#prev-lesson").getAttribute("title"), /\[/);
    assert.match(await page.locator("#next-lesson").getAttribute("title"), /\]/);

    // Real CodeMirror and notes editors must receive bracket input, without navigating.
    await page.locator(".CodeMirror").waitFor();
    await page.locator(".CodeMirror").evaluate((el) => el.CodeMirror.focus());
    await page.keyboard.type("[]");
    assert.equal(await page.locator(".CodeMirror").evaluate((el) => el.CodeMirror.getValue()), "[]");
    assert.equal(page.url(), lesson("second"));
    await page.locator("#notes-btn").click();
    await page.locator('#nv-editor[contenteditable="true"]').waitFor();
    await page.locator("#nv-editor").fill("Notes: ");
    await page.keyboard.type("[]");
    assert.match(await page.locator("#nv-editor").textContent(), /\[\]/);
    assert.equal(page.url(), lesson("second"));
    await page.locator("#notes-btn").click();
    for (const tag of ["input", "textarea", "select"]) {
      await page.evaluate((tag) => {
        const el = document.createElement(tag);
        el.id = "typing-test";
        document.querySelector("#main").append(el);
        el.focus();
      }, tag);
      await page.keyboard.type("[]");
      assert.equal(page.url(), lesson("second"), `${tag} input must not navigate.`);
      if (tag !== "select") assert.equal(await page.locator("#typing-test").inputValue(), "[]");
      await page.locator("#typing-test").evaluate((el) => el.remove());
    }
    // Browser shortcuts, IME composition and held keys must not advance through lessons.
    await page.locator("#main").focus();
    for (const options of [{ ctrlKey: true }, { metaKey: true }, { altKey: true }, { repeat: true }, { isComposing: true }, { prevented: true }]) {
      for (const key of ["[", "]"]) {
        const untouched = await page.evaluate(({ key, options }) => {
          const event = new KeyboardEvent("keydown", { key, bubbles: true, cancelable: true, ...options });
          if (options.prevented) event.preventDefault();
          document.activeElement.dispatchEvent(event);
          return options.prevented || !event.defaultPrevented;
        }, { key, options });
        assert.equal(untouched, true);
        assert.equal(page.url(), lesson("second"));
      }
    }
    saved = await savedAfter(() => press("["), "first");
    await heading("First");
    assert.deepEqual(saved.done, ["first"], "Previous must not complete the lesson being left.");
    saved = await savedAfter(() => press("]"), "second");
    await heading("Second");
    assert.deepEqual(saved.done, ["first"], "Repeated visits must not duplicate completion.");
    saved = await savedAfter(() => press("]"), "third");
    await heading("Third");
    assert.deepEqual(saved.done, ["first", "second"]);
    await press("]");
    assert.equal(page.url(), lesson("third"), "There is no next lesson at the end.");
    await page.reload();
    await heading("Third");
    assert.deepEqual((await state()).done, ["first", "second"], "Completion survives a reload.");
    await page.goto(base + "/#/" + CID);
    await page.getByRole("heading", { name: "Navigation test", exact: true }).waitFor();
    await press("[");
    await press("]");
    assert.equal(page.url(), base + "/#/" + CID, "Shortcuts only apply to lesson pages.");
    assert.deepEqual(errors, []);
  });
}
