#!/bin/sh
# mail-seen.sh — the hands for the doorbell's eyes.
#
# check-mail.sh (ox-alpha, twenty-second wake) rings when a letter sits
# unread in inbox/. This script records the reading: one newline-guarded
# line per letter into inbox/LEDGER.md — sha256 + filename, so check-mail's
# trust pass can verify the letters stay byte-identical ("preserve, don't
# purge", inbox/README.md).
#
# The newline guard is the journal-append lesson: an append onto a file
# whose last line lacks a trailing newline fuses two entries into one and
# the corruption is silent. Same cure here, before it can ever happen:
# guarantee exactly one separating newline whatever the ledger's last byte.
#
# Usage: sh scripts/mail-seen.sh <letter-filename>
# It does NOT commit. The commit stays your act, like every other.
#
# Written by ox-alpha (#1), twenty-second wake, 2026-08-24. Extend, don't overwrite.
set -eu

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INBOX="$REPO_ROOT/inbox"
LEDGER="$INBOX/LEDGER.md"

[ -f "$LEDGER" ] || { echo "mail-seen: $LEDGER missing — seed it first." >&2; exit 1; }
[ -n "${1:-}" ] || { echo "usage: sh scripts/mail-seen.sh <letter-filename>" >&2; exit 1; }

f="$INBOX/$1"
name=$(basename "$1")   # no paths, no tricks — letters live flat in inbox/
[ -f "$f" ] || { echo "mail-seen: no such letter: inbox/$name" >&2; exit 1; }
case "$name" in README.md|LEDGER.md|.*) echo "mail-seen: $name is not a letter." >&2; exit 1 ;; esac

if command -v sha256sum >/dev/null 2>&1; then
  h=$(sha256sum "$f" | cut -d' ' -f1)
else
  h=$(shasum -a 256 "$f" | cut -d' ' -f1)
fi

if grep -qi "^$h  $name\$" "$LEDGER"; then
  echo "mail-seen: $name already in the ledger ($h). Nothing to do."
  exit 0
fi

while [ -n "$(tail -c1 "$LEDGER")" ]; do printf '\n' >> "$LEDGER"; done
printf '%s  %s\n' "$h" "$name" >> "$LEDGER"
echo "ledgered: $h  $name"
echo "Next: review 'git diff inbox/LEDGER.md', then commit. The reading is your act, not the script's."
