"use strict";
// Study logic with no DOM: dates, streaks, the review schedule, timer phases.
// Loaded by the browser as window.Study, and by tests/study.test.js through require().
(function () {
  const pad = (n) => String(n).padStart(2, "0");

  // Local calendar day, so "today" matches the learner's clock, not UTC.
  function dayKey(d = new Date()) {
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  }

  function addDays(key, n) {
    const [y, m, d] = key.split("-").map(Number);
    return dayKey(new Date(y, m - 1, d + n));
  }

  // Days in a row with at least `minSeconds` of study. Today still counts as "not broken"
  // until it's over, so the streak runs through yesterday when today hasn't hit the bar yet.
  function streak(daily, today, minSeconds) {
    let day = (daily[today] || 0) >= minSeconds ? today : addDays(today, -1);
    let n = 0;
    while ((daily[day] || 0) >= minSeconds) { n++; day = addDays(day, -1); }
    return n;
  }

  function week(daily, today) {
    return Array.from({ length: 7 }, (_, i) => {
      const key = addDays(today, i - 6);
      return { key, seconds: daily[key] || 0 };
    });
  }

  // Leitner-style review: a miss restarts the card tomorrow; each correct review waits longer.
  // After the last interval is passed, the card is learned and leaves the queue.
  const INTERVALS = [1, 3, 7, 14];

  function miss(review, id, today) {
    review[id] = { box: 0, due: addDays(today, INTERVALS[0]) };
  }

  function pass(review, id, today) {
    const card = review[id];
    if (!card) return "none";
    const box = card.box + 1;
    if (box >= INTERVALS.length) { delete review[id]; return "learned"; }
    review[id] = { box, due: addDays(today, INTERVALS[box]) };
    return "next";
  }

  function due(review, today) {
    return Object.entries(review)
      .filter(([, c]) => c.due <= today)
      .sort((a, b) => a[1].due.localeCompare(b[1].due))
      .map(([id]) => id);
  }

  // Pomodoro phases: a long break after every `every` focus sessions.
  function nextPhase(phase, focusDone, every = 4) {
    if (phase !== "focus") return "focus";
    return focusDone > 0 && focusDone % every === 0 ? "long" : "short";
  }

  const Study = { dayKey, addDays, streak, week, INTERVALS, miss, pass, due, nextPhase };
  if (typeof module !== "undefined") module.exports = Study;
  else window.Study = Study;
})();
