#!/usr/bin/env bash
# world_stats.sh — print the world's git facts, used to refresh about.html.
# Run from the repo root. The deploy cache (.wrangler) is excluded from the
# file count because it is the deploy tool's scratch space, not the world.
set -euo pipefail
cd "$(dirname "$0")/.."

commits=$(git rev-list --count HEAD)
files_total=$(git ls-files | wc -l | tr -d ' ')
files_excl_cache=$(git ls-files | grep -vc '^\.wrangler/' || true)
authors=$(git shortlog -sne HEAD | wc -l | tr -d ' ')

echo "commits=$commits"
echo "files_total=$files_total"
echo "files_excl_cache=$files_excl_cache"
echo "authors=$authors"
