# TOB Calculator

Flask web app that calculates Belgian TOB (0.35%, capped at €1,600 per transaction) from
Interactive Brokers and Saxo statements (PDF, and Saxo Excel exports), using ECB reference
rates for FX. Runs in Docker on the Pi at http://192.168.128.200:5000.

## Branches

- `master` is the live code and GitHub's default branch. The Pi checkout at
  `~/tob-calculator` tracks `origin/master`.
- `main` is an older Render-era version (`tob_calculator.py`, `render.yaml`) with **no shared
  history** with `master`. It is not deployed anywhere. Do not work on it.
  `archive/render-main` (local only) holds uncommitted Render edits saved on 2026-11-09.

## Code

- `app.py` — Flask routes, upload handling, results/download endpoints.
- `tob_core.py` — text extraction, broker detection, IBKR and Saxo parsers, ECB rate fetch,
  grouping and TOB calculation (`process_statements` is the entry point).
- `tob_outputs.py` — Excel, CSV, PDF and Markdown report generation (Belgian number format).

## Run locally (Windows)

`venv\` uses Python 3.12 (the Pi container runs 3.11) with package versions pinned to the
container's `pip freeze`. Debug mode is on by default and a browser opens at
http://localhost:5000.

```
venv\Scripts\python app.py
```

`START_TOB_CALCULATOR.bat` does the same.

## Deploy to the Pi

Push first; the Pi pulls from GitHub, never from this machine.

```
git push origin master
ssh fried@192.168.128.200 "cd ~/tob-calculator && ./deploy.sh"
```

`deploy.sh` runs `git pull --ff-only` then `docker compose up -d --build`. Never edit code on
the Pi: a local change there makes the fast-forward pull fail. Reports persist on the Pi in
`~/tob-calculator/outputs` (volume mount, root-owned); uploads are not persisted.
