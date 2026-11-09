#!/usr/bin/env bash
# Deploy on the Pi: pull latest, rebuild image, restart container.
set -euo pipefail
cd "$(dirname "$0")"
git pull --ff-only
docker compose up -d --build
docker compose ps
