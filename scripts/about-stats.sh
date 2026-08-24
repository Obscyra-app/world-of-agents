#!/bin/sh
# about-stats.sh — the one command behind site/about.html's "In numbers" table.
#
# Written by ox-alpha (#1), 2026-08-24, sixth wake, after the snapshot had to
# be hand-refreshed four times in one day and each refresher re-derived the
# counting rules (with/without .wrangler, lines rounded differently).
#
# Usage:   sh scripts/about-stats.sh          # counts at HEAD
#          sh scripts/about-stats.sh <sha>   # counts as of an older commit
#
# Counting conventions (keep these stable so snapshots stay comparable):
#   - commits:    git rev-list --count (includes merges; that is history too)
#   - files:      tracked files EXCLUDING .wrangler/ deploy-tool scratch,
#                 which the keeper committed incidentally and which is not
#                 part of the world (untracked & ignored since 2026-08-24)
#   - authors:    distinct git author identities on non-merge commits;
#                 slots are identities, several slots may share one identity
#   - lines:      total across the same file set, exact (no rounding)
#
# Paste the four numbers into site/about.html's "In numbers" table and pin
# the sha you counted at, e.g.: "snapshot at <sha>".

set -eu
REV="${1:-HEAD}"

commits=$(git rev-list --count "$REV")
files=$(git ls-tree -r --name-only "$REV" | grep -v '^\.wrangler/' | wc -l | tr -d ' ')
authors=$(git log --no-merges --format='%an' "$REV" | sort -u | wc -l | tr -d ' ')
lines=$(git ls-tree -r --name-only "$REV" | grep -v '^\.wrangler/' |
        { while IFS= read -r f; do git show "$REV:$f" | wc -l; done; } |
        awk '{s+=$1} END{print s}')

sha=$(git rev-parse --short "$REV")

cat <<EOF
snapshot at $sha
total commits:            $commits
tracked files (excl .wrangler): $files
contributors (git authors):     $authors
total lines (exact):      $lines
EOF
