# CI with GitHub Actions: tests and eval gates

## Why this matters

LLM apps break quietly. A one-word prompt edit, a new model version or a changed chunk size can drop answer quality from 92% to 70%, and nothing crashes. Continuous integration (CI) runs your tests and evals on every push and pull request, and blocks the merge when they fail, so quality regressions get caught by a machine instead of by your client. A green CI badge on a portfolio repo also tells reviewers you work like a professional.

## 1. GitHub Actions in five terms

GitHub Actions runs commands on GitHub's machines when something happens in your repo.

- **Workflow:** a YAML file in `.github/workflows/`. A repo can have several.
- **Event (`on:`):** what triggers it: `push`, `pull_request`, a schedule, or a manual button (`workflow_dispatch`).
- **Job:** a set of steps that runs on one fresh virtual machine (a **runner**, e.g. `ubuntu-latest`). Jobs run in parallel unless one `needs` another.
- **Step:** either a shell command (`run:`) or a reusable **action** (`uses:`), such as `actions/checkout`, which clones your repo onto the runner.
- **Exit code:** a step fails if its command exits with a nonzero code, and a failed step fails the job. That's the whole mechanism behind "the build is red".

Every run starts from a clean machine: nothing from your laptop, no `.env`, no installed packages. If your tests pass there, they don't depend on anything you forgot to commit.

## 2. The workflow file

Save this as `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v7

      - name: Install uv
        uses: astral-sh/setup-uv@v9.0.0
        with:
          enable-cache: true

      - name: Install Python
        run: uv python install

      - name: Install dependencies
        run: uv sync --locked --all-extras --dev

      - name: Unit tests
        run: uv run pytest -q

      - name: Offline evals
        run: uv run python evals/run_offline.py --out eval-results.json

      - name: Eval gate (fail below 90%)
        run: uv run python evals/gate.py eval-results.json 0.9

      - name: Upload eval results
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: eval-results
          path: eval-results.json
          if-no-files-found: ignore

  docker:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v7
      - name: Build the image
        run: docker build -t app:ci .
```

What each part does:

- **`on:`** runs on every push to `main` and on every pull request. Pushes to other branches get checked through their pull request.
- **`permissions: contents: read`** gives the workflow's automatic `GITHUB_TOKEN` read-only access. Grant only what a workflow needs.
- **`concurrency`** cancels an older run on the same branch when you push again, so you don't wait for (or pay minutes for) stale runs.
- **`timeout-minutes`**: a hung test fails after 15 minutes instead of the six-hour default.
- **`astral-sh/setup-uv`** installs uv. `enable-cache: true` saves uv's package cache between runs, keyed on your `uv.lock`, so the install step drops from a minute to seconds after the first run.
- **`uv python install`** installs the Python version pinned in `.python-version` / `requires-python`, so CI uses the same Python as you.
- **`uv sync --locked`** fails if `uv.lock` doesn't match `pyproject.toml`: you forgot to commit the lock file after adding a package. `--dev` includes pytest.
- **`uv run pytest -q`**: pytest exits nonzero if any test fails.
- **The eval steps** run your eval suite and then the gate, which exits `1` when the pass rate is below 0.9.
- **`if: always()`** uploads the results file even when the gate failed, which is exactly when you want to read it. Download it from the run's summary page.
- **The `docker` job** proves the Dockerfile still builds. It runs in parallel with `test`.

> **Note:** For extra supply-chain safety, pin third-party actions to a full commit SHA instead of a tag, e.g. `astral-sh/setup-uv@c771a70e6277c0a99b617c7a806ffedaca235ff9 # v9.0.0`. A tag can be moved; a SHA can't. The uv docs show this form.

Push the file and open the **Actions** tab in your repo to watch it run. Add a badge to your README:

```markdown
![CI](https://github.com/<you>/<repo>/actions/workflows/ci.yml/badge.svg)
```

## 3. Tests that can run in CI

The runner has no `ANTHROPIC_API_KEY`, no Postgres and no Voyage key, and it shouldn't need them. That's why every earlier section injected the client, the embedder and the store as dependencies. In tests you swap in fakes:

```python
# tests/test_api.py
from fastapi.testclient import TestClient

from app.main import app, get_client, get_store
from tests.fakes import AsyncFake, FakeAnthropic, MemoryStore, reply, text


def test_ask_returns_answer_with_sources():
    fake = FakeAnthropic([reply(text("Refunds take 5 days [1]."))])
    app.dependency_overrides[get_client] = lambda: AsyncFake(fake)
    app.dependency_overrides[get_store] = lambda: MemoryStore.with_samples()
    try:
        r = TestClient(app).post("/ask", json={"question": "How long do refunds take?"},
                                 headers={"X-API-Key": "test-key"})
    finally:
        app.dependency_overrides.clear()
    assert r.status_code == 200
    assert r.json()["sources"], "a cited answer should include sources"
```

Rules that keep CI reliable:

- **No network.** A test that calls a real API fails when the API is slow, costs money on every push, and can't run on a pull request from a fork (no secrets there).
- **No sleeping, no real clocks.** Inject clocks, as in the rate limiter and cache exercises.
- **Settings in tests come from a dict or an override,** not from a `.env` that doesn't exist on the runner.

If your app's lifespan loads settings from the environment, give the test job dummy values: they let the app start, and the fakes mean they're never used.

```yaml
      - name: Unit tests
        run: uv run pytest -q
        env:
          ANTHROPIC_API_KEY: test-not-real
          DATABASE_URL: postgresql://unused/unused
          APP_API_KEY: test-key
```

## 4. Offline evals and the gate

Unit tests check that code does what you wrote. **Evals** check that the system gives good answers. You built eval suites in the agents section. In CI, you split them in two:

**Offline evals** (every push, free, deterministic). These measure everything that doesn't need a live model:

- **Retrieval quality:** recall@k and MRR on your golden questions, using embeddings you computed once and committed, or a deterministic fake embedder. A chunking change that hurts retrieval fails here.
- **Recorded model outputs:** save real Claude responses for your golden set once (a JSON file of input → output), then re-run your parsing, citation checking, tool routing and grading code against them. A refactor that breaks citation extraction fails here, with no API call.
- **Guardrails:** inputs that must be refused, prompt-injection strings that must not change tool calls, oversized inputs that must be rejected.

**Live evals** (on demand or on a schedule, cost money). These run the golden set against the real model, to catch prompt and model regressions. They use a secret and a cheaper model where possible.

The gate is the same either way: compute a pass rate and exit nonzero below the threshold.

```python
# evals/gate.py
import json
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    path, threshold = argv[0], float(argv[1])
    results = json.loads(Path(path).read_text())
    passed = sum(r["passed"] for r in results)
    rate = passed / len(results) if results else 0.0
    ok = bool(results) and rate >= threshold
    print(f"pass rate {passed}/{len(results)} = {rate:.1%} (threshold {threshold:.1%}) {'PASS' if ok else 'FAIL'}")
    for r in results:
        if not r["passed"]:
            print(f"  failed: {r['id']}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

`sys.exit(1)` is what turns a low score into a red build. No results at all counts as a failure: an eval that silently ran zero cases must not pass.

**Choosing the threshold.** Run the suite a few times, look at the pass rate, and set the threshold a little below it, say 0.9 if you're at 0.94. Raise it as you improve. A threshold of 1.0 on an LLM eval tends to fail on noise and teaches everyone to ignore the red build; a threshold of 0.5 never fails. For retrieval metrics, gate on the number directly (`recall@5 >= 0.85`).

> **Try it:** The *An eval gate for CI* exercise builds `run_suite`, `pass_rate`, `eval_gate` and `main`. Run its `__main__` block and change the threshold to see the exit code flip.

### A live eval workflow

Put live evals in a separate workflow so they never run on untrusted pull requests:

```yaml
# .github/workflows/live-evals.yml
name: Live evals

on:
  workflow_dispatch:
  schedule:
    - cron: "0 6 * * 1"   # Mondays 06:00 UTC

permissions:
  contents: read

jobs:
  live:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v7
      - uses: astral-sh/setup-uv@v9.0.0
        with:
          enable-cache: true
      - run: uv python install
      - run: uv sync --locked --dev
      - name: Run golden set against the real model
        run: uv run python evals/run_live.py --out live-results.json
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          MODEL: claude-haiku-5-5
      - name: Gate
        run: uv run python evals/gate.py live-results.json 0.85
```

`workflow_dispatch` adds a **Run workflow** button in the Actions tab. Use a CI-only Anthropic key with a low spend limit.

## 5. Secrets in Actions

Add a secret in the repo's **Settings → Secrets and variables → Actions → New repository secret**. Reference it as `${{ secrets.NAME }}`, ideally only in the `env:` of the step that needs it, not at the top of the workflow.

What GitHub does for you, and what it can't:

- **Values are masked in logs.** If the exact secret string appears in output, it's shown as `***`.
- Masking only matches the exact string. A secret that's been transformed (base64-encoded, split, part of a URL with other text, printed character by character) **can leak**. Never `echo` a secret, never print settings, never run with debug flags that dump the environment.
- **Pull requests from forks don't get your secrets.** That's on purpose: otherwise anyone could open a PR that prints them. Keep the default `pull_request` trigger for tests; avoid `pull_request_target` combined with checking out the PR's code, a well-known way to leak secrets.
- If you generate a sensitive value during a run, mask it yourself: `echo "::add-mask::$VALUE"`.
- If a secret did appear in a log, treat it as leaked: revoke it and create a new one.

## 6. Required checks: make red mean "can't merge"

A failing check you can merge anyway is a suggestion. Make it a rule:

1. Repo **Settings → Rules → Rulesets → New branch ruleset** (or the older **Settings → Branches → Add branch protection rule**).
2. Target the `main` branch.
3. Enable **Require a pull request before merging** and **Require status checks to pass**, and add the `test` and `docker` jobs (they appear once they've run at least once).
4. Optionally **Block force pushes**.

Now changes reach `main` only through a pull request whose tests and eval gate passed. Even working alone, this habit catches the "quick fix" you were sure didn't need testing, and it's how teams you'll join work.

## Common mistakes

- **Tests that need a key or a database.** They fail in CI, or worse, someone adds the real key as a secret and every push spends money. Fakes and dependency overrides.
- **Forgetting to commit `uv.lock`.** `uv sync --locked` fails; that's the point.
- **An eval script that prints a score but always exits 0.** CI only sees the exit code. Use the gate.
- **A threshold of 1.0 on noisy evals,** so the build is red half the time and everyone learns to ignore it.
- **Printing secrets** or settings in CI logs, or exposing secrets to fork pull requests via `pull_request_target`.
- **Live evals on every push.** Slow and costly; run them on demand, on a schedule, or before a release.
- **Not making the check required,** so a red build can still be merged.

## Recap

- A workflow in `.github/workflows/` runs jobs on fresh runners; a nonzero exit code fails the step and the build.
- The CI workflow: checkout, `setup-uv` with caching, `uv python install`, `uv sync --locked`, `pytest`, offline evals, the gate, and a Docker build job.
- Offline evals (retrieval metrics, recorded outputs, guardrails) run on every push for free; live evals run on demand with a CI-only key.
- The eval gate turns a pass rate below the threshold into exit code 1; no results is a failure.
- Secrets live in repo settings, are masked in logs only as exact strings, and aren't given to fork pull requests.
- Required status checks on `main` turn a red build into a blocked merge.
