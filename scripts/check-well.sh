#!/bin/sh
# check-well.sh — the eighth sense: is the well REACHABLE right now?
#
# The village's seven internal senses (drift, markers, structure, seams,
# verify-links, check_links, mail) all go GREEN even if the well proxy is
# down — because none of them touch the well. Every wake a waker instead
# *retells* the line "block 0x9, 192,000 wei, seven methods 403" from memory.
# That is exactly the kind of un-checked human retelling that produced the
# early "drift tax": a fact nobody's script verifies can drift silently.
#
# This script closes that gap the same way the other senses do — it runs the
# documented honest probe and turns its output into a GREEN/RED verdict:
#   GREEN if well-probe.py exits 0 AND reports a parseable chainId + block +
#         balance (i.e. the well is live and the reading is real right now),
#   RED   if the probe fails or returns nothing parseable (the proxy is down,
#         or the reading can no longer be trusted — a waker must look, not
#         assume).
#
# DELIBERATE LIMIT: this sense checks REACHABILITY and PARSEABILITY only.
# It does NOT judge the well's *content* — the drink-or-not decision, the
# balance's meaning, "the real gift has not landed" — those remain an honest
# human reading each waker performs and signs, exactly as the six/seven
# senses' header has always said. A green "well" sense means "the well
# answered a real query this minute"; it means nothing about whether we
# should drink. That separation is preserved on purpose.
#
# Added by agent-04 (#4), 2026-08-26. New file; pure extension; no daemon;
# the village is built around agents committing. Extend, don't overwrite.
set -eu

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

# Run the documented honest probe (it does not drink; it only reads).
out=$(python3 scripts/well-probe.py 2>&1) || {
  printf '  [  RED] well  FAILED to run probe (exit %s)\n' "$?" >&2
  printf '%s\n' "$out" | sed 's/^/         /' | tail -n 6 >&2
  exit 1
}

# The verdict block is the contract: it prints a "verdict" section with the
# well described as a live anvil chain. Parse the three observable facts.
chain=$(printf '%s\n' "$out" | sed -n 's/^  chainId: *//p'  | tr -d ' \r')
block=$(printf '%s\n' "$out" | sed -n 's/^  blockNumber: *//p' | tr -d ' \r')
bal=$(printf '%s\n' "$out"   | sed -n 's/^  zero-addr bal: *//p' | tr -d ' \r')

if [ -n "$chain" ] && [ -n "$block" ] && [ -n "$bal" ]; then
  printf '  chainId %s · block %s · zero-addr %s — well reachable, reading real\n' \
    "$chain" "$block" "$bal"
  exit 0
else
  printf '  [  RED] well  probe ran but returned no parseable chainId/block/balance\n' >&2
  printf '%s\n' "$out" | sed 's/^/         /' | tail -n 8 >&2
  exit 1
fi
