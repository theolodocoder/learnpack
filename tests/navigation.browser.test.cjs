// Requires playwright-core and its Chromium browser.
const assert = require("node:assert/strict");
const { spawn } = require("node:child_process");
const { once } = require("node:events");
const fs = require("node:fs/promises");
const os = require("node:os");
const path = require("node:path");
const readline = require("node:readline");
const test = require("node:test");
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

test("Next completes the lesson and preserves navigation and manual completion", { timeout: 60_000 }, async (t) => {
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
    features: { notes: false, timer: false, focusMode: false, studyStats: false, review: false },
    sections: [{
      id: "lessons", title: "Lessons", lessons: ["first", "second", "third"].map((id) => ({
        id, title: id[0].toUpperCase() + id.slice(1) + " lesson", body: "A written lesson.",
      })),
    }],
  };
  const pack = path.join(temporary, "courses", CID);
  const data = path.join(temporary, "data", CID);
  await fs.mkdir(pack, { recursive: true });
  await fs.mkdir(data, { recursive: true });
  await fs.writeFile(path.join(pack, "course.json"), JSON.stringify(course));
  await fs.writeFile(path.join(data, "state.json"), JSON.stringify({
    done: [], last: "", checklist: { retained: true }, links: {}, passed: ["prior-exercise"],
  }));
  server = spawn(process.env.PYTHON || "python3", ["-u", "-c", SERVER, temporary], { cwd: ROOT });
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
  const lesson = (id) => base + "/#/" + CID + "/l/" + id;
  const state = async () => {
    const response = await page.request.get(base + "/api/courses/" + CID + "/state", {
      headers: { "X-Learn-Token": TOKEN },
    });
    assert.equal(response.status(), 200);
    return response.json();
  };
  const savedAfter = async (action, last) => {
    const saved = page.waitForResponse((response) =>
      response.url() === base + "/api/courses/" + CID + "/state"
      && response.request().method() === "PUT"
      && response.request().postDataJSON().last === last);
    await action();
    assert.equal((await saved).status(), 200);
    return state();
  };
  const tick = (id) => page.locator('a.side-link[href="#/' + CID + "/l/" + id + '"] .tick');

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
