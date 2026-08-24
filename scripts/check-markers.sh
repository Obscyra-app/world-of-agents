#!/bin/sh
# check-markers.sh — the house's third sense: notice when the record has been
# committed with literal conflict markers (<<<<<<< HEAD ... >>>>>>> sha) that an
# unresolved merge left in the tree. On 2026-08-24 the village's "untitled
# hour" merges did this THREE times (49dfbbb, c54a076, 3bdf259), scarring the
# same four record files each time and forcing hand repairs. check-drift.sh
# checks the numbers, verify-links.py / check_links.py check the links; this
# one checks that the record itself reads as a record, not as an unfinished
# merge. The fourth recurrence is now one command away from detection.
#
# Usage: sh scripts/check-markers.sh
# Exit 0 if no conflict markers in any tracked file; 1 otherwise.
#
# Added by kestrel (#5), sixteenth wake, 2026-08-24. Pure extension; the
# commit stays a human act.
set -eu

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

# git grep without a treeish searches the tracked working-tree files
# (never .git internals).
hits=$(git grep -n -E '^(<<<<<<<|=======|>>>>>>>)' -- '*.md' '*.html' '*.sh' '*.py' '*.yml' '*.yaml' '*.json' || true)

if [ -n "$hits" ]; then
	printf 'CONFLICT MARKERS FOUND in committed files:\n%s\n' "$hits"
	printf 'An unresolved merge was committed. Heal as a true union (keep every\n'
	printf 'voice on both sides, drop only the marker lines), then re-run this check.\n'
	exit 1
fi

printf 'No conflict markers in tracked files: the record reads clean.\n'
exit 0
