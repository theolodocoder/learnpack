"use strict";
// Web version: runs exercises in Web Workers and returns the same result shape as engine/runner.py.
// Each language keeps one warm worker. A run that takes longer than 60 seconds is stopped by
// terminating the worker (a fresh one is made next time), so an infinite loop never freezes the page.
//
// Worker protocol: the page posts one job ({ lang, mode: "run" | "check" | "warm", code, tests, support,
// requirements }); the worker replies with any number of { type: "status", text } while it loads,
// { type: "started" } when the learner's code begins, then one { type: "done", stdout, stderr, exit_code, results? }.
window.WebRunner = (() => {
  const MARKER = "__LEARN_RESULTS__";  // the Python harness prints its JSON results after this line, as engine/runner.py does
  const TIMEOUT = 60_000;
  const workers = {};
  const BUILD = "dev";  // replaced with a build id by `server.py build-web`, so browsers never run a stale worker
  const workerUrl = (lang) => `${lang === "python" ? "py-worker.js" : "js-worker.js"}?v=${BUILD}`;
  let currentStatus = "";  // the latest loading message, so a run queued behind a warm-up can show it too
  // app.js listens for this event to show "Loading Python…" and similar on the Run/Check buttons.
  const say = (text) => { currentStatus = text; window.dispatchEvent(new CustomEvent("learnpack-runner", { detail: text })); };

  // One run at a time per language: a worker handles one job, so overlapping clicks queue up.
  const queues = {};
  function run(job) {
    const kind = job.lang === "python" ? "python" : "js";
    const next = (queues[kind] || Promise.resolve()).then(() => runNow(job, kind));
    queues[kind] = next.catch(() => {});  // a failed run must not block the ones queued after it
    return next;
  }

  function runNow(job, kind) {
    const worker = (workers[kind] ||= new Worker(workerUrl(job.lang)));
    return new Promise((resolve) => {
      let timer = null;
      const finish = (result) => { clearTimeout(timer); worker.onmessage = null; resolve(result); };
      worker.onerror = (e) => { delete workers[kind]; worker.terminate(); finish({ stdout: "", stderr: `The runner crashed: ${e.message || "unknown error"}`, exit_code: 1, timed_out: false, results: job.mode === "check" ? [{ name: "tests", passed: false, error: "The runner crashed. Try again." }] : undefined }); };
      worker.onmessage = ({ data }) => {
        if (data.type === "status") say(data.text);
        if (data.type === "started") {
          // The clock starts only now, so downloading Python or packages never counts against the learner's code.
          say("");
          timer = setTimeout(() => {
            delete workers[kind]; worker.terminate();
            finish({ stdout: "", stderr: `Stopped: your code ran longer than ${TIMEOUT / 1000} seconds.`, exit_code: null, timed_out: true,
                     results: job.mode === "check" ? [{ name: "tests", passed: false, error: "Timed out" }] : undefined });
          }, TIMEOUT);
        }
        if (data.type === "done") {
          const result = { stdout: data.stdout, stderr: data.stderr, exit_code: data.exit_code, timed_out: false };
          if (job.mode === "check") {
            // The JS worker sends results directly; Python prints them after MARKER, so cut them out of stdout.
            let results = data.results;
            if (!results) {
              const i = data.stdout.lastIndexOf("\n" + MARKER);
              if (i >= 0) { results = JSON.parse(data.stdout.slice(i + MARKER.length + 1)); result.stdout = data.stdout.slice(0, i); }
            }
            result.results = results?.length ? results : [{ name: "tests", passed: false, error: data.stderr || "Tests did not run" }];
          }
          finish(result);
        }
      };
      worker.postMessage(job);
    });
  }
  // Load the language runtime and this exercise's packages in the background, so the first Check is quick.
  const warmed = new Set();
  function warm(job) {
    // Python warm-ups differ by packages (chosen from the imports in the code and tests); other runtimes warm once.
    const key = job.lang === "python" ? "python:" + job.requirements.join(",") + job.tests : job.lang;
    if (warmed.has(key)) return;
    warmed.add(key);
    run({ ...job, mode: "warm" }).then(() => say(""), () => {});
  }
  return { run, warm, status: () => currentStatus };
})();
