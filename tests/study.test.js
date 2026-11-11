// Run: node --test tests/
const test = require("node:test");
const assert = require("node:assert/strict");
const S = require("../web/study.js");

test("addDays crosses month and year ends", () => {
  assert.equal(S.addDays("2026-12-31", 1), "2027-01-01");
  assert.equal(S.addDays("2026-03-01", -1), "2026-02-28");
});

test("streak counts days in a row and survives an unfinished today", () => {
  const min = 900;
  const daily = { "2026-11-09": 1000, "2026-11-10": 2000, "2026-11-11": 100 };
  assert.equal(S.streak(daily, "2026-11-11", min), 2);           // today not done yet: runs through yesterday
  daily["2026-11-11"] = 900;
  assert.equal(S.streak(daily, "2026-11-11", min), 3);           // today done
  assert.equal(S.streak(daily, "2026-11-13", min), 0);           // missed yesterday: broken
  assert.equal(S.streak({}, "2026-11-11", min), 0);
});

test("week returns the last 7 days ending today", () => {
  const w = S.week({ "2026-11-11": 60, "2026-11-05": 30 }, "2026-11-11");
  assert.equal(w.length, 7);
  assert.deepEqual([w[0].key, w[0].seconds, w[6].key, w[6].seconds], ["2026-11-05", 30, "2026-11-11", 60]);
});

test("review: miss, pass through every box, then learned", () => {
  const r = {};
  S.miss(r, "q1", "2026-11-11");
  assert.deepEqual(r.q1, { box: 0, due: "2026-11-12" });
  assert.deepEqual(S.due(r, "2026-11-11"), []);
  assert.deepEqual(S.due(r, "2026-11-12"), ["q1"]);
  assert.equal(S.pass(r, "q1", "2026-11-12"), "next");
  assert.deepEqual(r.q1, { box: 1, due: "2026-11-15" });
  S.pass(r, "q1", "2026-11-15");
  S.pass(r, "q1", "2026-11-22");
  assert.equal(S.pass(r, "q1", "2026-12-06"), "learned");
  assert.equal(r.q1, undefined);
  assert.equal(S.pass(r, "missing", "2026-11-11"), "none");
});

test("review: a miss during review sends the card back to the start", () => {
  const r = { q1: { box: 2, due: "2026-11-11" } };
  S.miss(r, "q1", "2026-11-11");
  assert.deepEqual(r.q1, { box: 0, due: "2026-11-12" });
});

test("due lists oldest first", () => {
  const r = { a: { box: 0, due: "2026-11-10" }, b: { box: 0, due: "2026-11-08" }, c: { box: 0, due: "2026-11-20" } };
  assert.deepEqual(S.due(r, "2026-11-11"), ["b", "a"]);
});

test("pomodoro: long break after every 4th focus", () => {
  assert.equal(S.nextPhase("focus", 1), "short");
  assert.equal(S.nextPhase("focus", 4), "long");
  assert.equal(S.nextPhase("short", 4), "focus");
  assert.equal(S.nextPhase("long", 8), "focus");
});
