#!/bin/bash
# LearnPack launcher for macOS and Linux. Double-click (or run ./"Start Learning.command").
# Starts the app and opens your browser. Keep this window open while you study.
cd "$(dirname "$0")" || exit 1

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3.10 or newer is needed. Install it from https://www.python.org/downloads/ and run this again."
  read -r -p "Press Enter to close." _; exit 1
fi

# First run: create .venv with the packages the course exercises use.
if [ ! -d .venv ]; then
  echo "First run: setting up exercise packages (one minute)..."
  if command -v uv >/dev/null 2>&1; then
    uv venv -q && uv pip install -q -r requirements.txt
  else
    python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt
  fi || echo "Package setup failed. The app still runs; exercises that need those packages won't."
fi

python3 server.py
