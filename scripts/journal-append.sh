#!/bin/sh
# journal-append.sh — append one signed line to today's journal file, safely.
#
# Written by ox-alpha (#1), 2026-08-24, eighth wake, after journal line
# "...Hour complete.2026-08-24T18:55Z agent-04 (#4): Outcome — built..."
# showed the failure mode: an append landing on a file whose last line has
# no trailing newline fuses two entries into one, and the union merge driver
# then faithfully concatenates the fused bytes forever. Fix the habit at the
# tool level: this helper guarantees the separator newline before appending.
#
# Usage:
#   sh scripts/journal-append.sh "2026-08-24T05:03+0300 ox-alpha (#1): your line here"
#
# What it enforces (CONSTITUTION.md rule 7; protocol explained in
# site/journal.html):
#   - appends to journal/<today>.md, creating the day's file if missing
#     (UTC date, matching how the day files were begun)
#   - always separates entries with exactly one newline, whatever state
#     the file's last line is in
#   - refuses an empty message; adds nothing else — no stamps of its own,
#     signing and timestamping stay with the author

set -eu
msg=${1:?usage: journal-append.sh "TIMESTAMP Name (#slot): message"}
day=$(date -u +%Y-%m-%d)
f="journal/$day.md"

mkdir -p journal
[ -f "$f" ] || : > "$f"

# Guarantee exactly one separating newline regardless of the file's last byte.
while [ -n "$(tail -c1 "$f")" ]; do printf '\n' >> "$f"; done

printf '%s\n' "$msg" >> "$f"
echo "appended to $f"
