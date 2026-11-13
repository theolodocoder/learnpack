"use strict";
// Web version: runs exercises in Web Workers and returns the same result shape as engine/runner.py.
// Each language keeps one warm worker. A run that takes longer than 60 seconds is stopped by
// terminating the worker (a fresh one is made next time), so an infinite loop never freezes the page.
window.WebRunner = (() => {
  const MARKER = "__LEARN_RESULTS__";
  const TIMEOUT = 60_000;
  const workers = {};
  const BUILD = "dev";  // replaced with a build id by `server.py build-web`, so browsers never run a stale worker
  const file = (lang) => `${lang === "python" ? "py-worker.js" : "js-worker.js"}?v=${BUILD}`;
  const say = (text) => window.dispatchEvent(new CustomEvent("learnpack-runner", { detail: text }));

  // One run at a time per language: a worker handles one job, so overlapping clicks queue up.
  const queues = {};
  function run(job) {
    const kind = job.lang === "python" ? "python" : "js";
    const next = (queues[kind] || Promise.resolve()).then(() => runNow(job, kind));
    queues[kind] = next.catch(() => {});
    return next;
  }

  function runNow(job, kind) {
    const w = (workers[kind] ||= new Worker(file(job.lang)));
    return new Promise((resolve) => {
      let timer = null;
      const finish = (r) => { clearTimeout(timer); w.onmessage = null; resolve(r); };
      w.onerror = (e) => { delete workers[kind]; w.terminate(); finish({ stdout: "", stderr: `The runner crashed: ${e.message || "unknown error"}`, exit_code: 1, timed_out: false, results: job.mode === "check" ? [{ name: "tests", passed: false, error: "The runner crashed. Try again." }] : undefined }); };
      w.onmessage = ({ data }) => {
        if (data.type === "status") say(data.text);
        if (data.type === "started") {
          say("");
          timer = setTimeout(() => {
            delete workers[kind]; w.terminate();
            finish({ stdout: "", stderr: `Stopped: your code ran longer than ${TIMEOUT / 1000} seconds.`, exit_code: null, timed_out: true,
                     results: job.mode === "check" ? [{ name: "tests", passed: false, error: "Timed out" }] : undefined });
          }, TIMEOUT);
        }
        if (data.type === "done") {
          const r = { stdout: data.stdout, stderr: data.stderr, exit_code: data.exit_code, timed_out: false };
          if (job.mode === "check") {
            let results = data.results;
            if (!results) {
              const i = data.stdout.lastIndexOf("\n" + MARKER);
              if (i >= 0) { results = JSON.parse(data.stdout.slice(i + MARKER.length + 1)); r.stdout = data.stdout.slice(0, i); }
            }
            r.results = results?.length ? results : [{ name: "tests", passed: false, error: data.stderr || "Tests did not run" }];
          }
          finish(r);
        }
      };
      w.postMessage(job);
    });
  }
  return { run };
})();
