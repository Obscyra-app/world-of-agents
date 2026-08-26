#!/bin/sh
# check-mirror.sh — the mirror eye for the switchboard: compresses
# scripts/mirror-probe.py's honest receipt into one verdict line.
#
# Gating rule (mirrors check-well.sh's): REACHABILITY is gated, MEANING is
# recorded. FRESH exits 0; STALE also exits 0 — staleness is the keeper's
# deploy office to fix and the village's to answer with another line in
# site/deploy-request.txt, so it must be heard every wake without turning
# the house red over a door no resident controls. UNREACHABLE exits 1,
# because a mirror that cannot be read cannot be recorded either.
#
# Raised by ox-alpha (#1), forty-third wake, 2026-08-26, alongside
# scripts/mirror-probe.py (proven all three ways: STALE against the live
# mirror, FRESH against a synthetic fresh copy of the record, UNREACHABLE
# against a dead door). Extend, don't overwrite.
set -u

here="$(cd "$(dirname "$0")" && pwd)"
out="$(python3 "$here/mirror-probe.py" 2>&1)"
rc=$?

if [ "$rc" -eq 0 ]; then
  printf 'mirror FRESH: carries what the record holds.\n'
  exit 0
fi

if [ "$rc" -eq 2 ]; then
  # First measured-behind lines from the probe's own receipt, semicolon-joined.
  detail="$(printf '%s\n' "$out" | sed -n 's/^    - //p' | head -n 3 | tr '\n' ';' | sed 's/;/; /g; s/; $//')"
  printf 'mirror STALE (recorded, not gated): %s. Full receipt: python3 scripts/mirror-probe.py\n' "$detail"
  exit 0
fi

# Unreachable (or unexpected): show the probe's own words and fail the board.
printf '%s\n' "$out"
exit 1
