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

`venv\` uses Python 3.12 (the Pi container runs 3.11) and installs the same locked
`requirements.txt` as the container. Debug mode is on by default and a browser opens at
http://localhost:5000.

```
venv\Scripts\python app.py
```

`START_TOB_CALCULATOR.bat` does the same.

## Dependencies

Rebuilds are pinned end to end: the `Dockerfile` base image by digest, and every Python
package (including sub-dependencies) in `requirements.txt`. The build installs with
`--no-deps` and runs `pip check`, so an incomplete lock fails the build instead of silently
pulling the latest version.

- `requirements.in` lists the top-level packages. Edit only this file by hand.
- `requirements.txt` is the generated lock, used by the Dockerfile and by `venv\` locally.
  Regenerate it after editing `requirements.in` (needs `py -m pip install --user uv` once):

```
py -m uv pip compile requirements.in --universal --python-version 3.11 -o requirements.txt
```

To take a newer base image, replace the digest in the `Dockerfile` with the current one for
`python:3.11-slim`. After any dependency or base-image change, re-run a known statement
locally and on the Pi and compare against a stored report before using it for a filing.

## Deploy to the Pi

Push first; the Pi pulls from GitHub, never from this machine.

```
git push origin master
ssh fried@192.168.128.200 "cd ~/tob-calculator && ./deploy.sh"
```

`deploy.sh` runs `git pull --ff-only` then `docker compose up -d --build`. Never edit code on
the Pi: a local change there makes the fast-forward pull fail. Reports persist on the Pi in
`~/tob-calculator/outputs` (volume mount, root-owned); uploads are not persisted.
