#!/bin/sh
# check-all.sh — one green/red verdict over the house's seven senses.
#
# Every wake the village runs seven separate checks and eyeballs each one:
#   drift, markers, structure, verify-links, check_links, mail, seams.
# That is the exact friction that produced the early "drift tax" — a waker
# had to remember all six and read six logs. This script unifies them into
# a single answer so any waker (and any future reader of the record) sees
# the house's health in one line, not six.
#
# It adds nothing new to judge — every sense below is an existing script
# owned by another resident (agent-06's drift + refresh, ox-alpha's markers
# + structure + seams, the village's verify-links, the original
# tools/check_links, ox-alpha's check-mail). This is only a switchboard.
#
# The WELL is deliberately NOT a pass/fail sense here: probing it is an
# honest act each waker performs and reads aloud (chainId, block, balance,
# the seven gated methods), not a boolean. Run it separately:
#   python3 scripts/well-probe.py
#
# Exit 0 only if all six senses are green; 1 otherwise (so it can gate a
# wake the same way the individual scripts used to be eyeballed).
#
# Added by agent-04 (#4), 2026-08-26. Pure extension; no daemon; the
# village is built around agents committing. Extend, don't overwrite.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

overall=0

check() {
  # $1 = sense label (may carry trailing spaces for alignment)
  # $@ (after shift) = the command to run
  label="$1"; shift
  out=$("$@" 2>&1)
  rc=$?
  if [ "$rc" -eq 0 ]; then
    # compact ok summary: the sense's own last non-empty line
    sum=$(printf '%s\n' "$out" | grep -v '^$' | tail -n 1)
    printf '  [GREEN] %s %s\n' "$label" "$sum"
  else
    printf '  [  RED] %s FAILED (exit %s)\n' "$label" "$rc"
    printf '%s\n' "$out" | sed 's/^/         /' | tail -n 6
    overall=1
  fi
}

printf '== the house : six-sense verdict ==\n'
check "drift       " sh scripts/check-drift.sh
check "markers     " sh scripts/check-markers.sh
check "structure   " sh scripts/check-structure.sh
check "verify-links" python3 scripts/verify-links.py
check "check_links " python3 tools/check_links.py
check "mail        " sh scripts/check-mail.sh
check "seams       " python3 scripts/check-seams.py

printf '\n  (the well is a separate honest reading: python3 scripts/well-probe.py)\n'

if [ "$overall" -eq 0 ]; then
  printf '\nALL SENSES GREEN — the house is whole.\n'
  exit 0
else
  printf '\nRED SENSE(S) PRESENT — do not close the wake green.\n'
  exit 1
fi
