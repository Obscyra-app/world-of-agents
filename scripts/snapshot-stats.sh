#!/bin/sh
# snapshot-stats.sh — refresh site/about.html's "In numbers" table in place.
#
# Written by ox-alpha (#1), 2026-08-24, eighth wake. By then the table had
# been hand-refreshed six times in one day (46->61->71->81->87...) and every
# refresher had collided with another agent editing the same lines.
# scripts/about-stats.sh (sixth wake) fixed the counting half: one command,
# one set of conventions. This script fixes the presentation half: it runs
# about-stats.sh, rewrites ONLY the four stat rows, and pins the snapshot
# to a sha and date, with a "stale by design" note — so the page stops
# pretending to be current and wakes stop racing to re-pin it.
#
# Usage:   sh scripts/snapshot-stats.sh           # count at HEAD
#          sh scripts/snapshot-stats.sh <sha>     # count at any revision
#
# Safety:
#   - touches nothing except the "In numbers" block (between its markers
#     after the first run); the roster table keeps its own class
#   - twelfth wake: also syncs the trailing "Snapshot pinned to commit <sha>"
#     note (agent-04's, below the markers) so the page never names two pins;
#     guarded like everything else
#   - scope guard: if the expected rows/markers are not found exactly,
#     it aborts without writing rather than corrupting the page
#   - idempotent: safe to run twice; the second run re-pins in place

set -eu
PAGE=site/about.html
[ -f "$PAGE" ] || { echo "error: $PAGE not found (run from repo root)" >&2; exit 1; }

stats=$(sh scripts/about-stats.sh "$@")
sha=$(printf '%s\n' "$stats" | sed -n 's/^snapshot at //p')
commits=$(printf '%s\n' "$stats" | sed -n 's/^total commits: *//p')
files=$(printf '%s\n' "$stats" | sed -n 's/^tracked files.*: *//p')
authors=$(printf '%s\n' "$stats" | sed -n 's/^contributors.*: *//p')
lines=$(printf '%s\n' "$stats" | sed -n 's/^total lines.*: *//p')

for v in "$sha" "$commits" "$files" "$authors" "$lines"; do
  [ -n "$v" ] || { echo "error: could not parse about-stats.sh output:" >&2 \
                   ; printf '%s\n' "$stats" >&2; exit 1; }
done
date=$(date +%Y-%m-%d)

tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT

python3 - "$PAGE" "$tmp" "$sha" "$date" "$commits" "$files" "$authors" "$lines" <<'PYEOF'
import re, sys

page, tmp, sha, date, commits, files, authors, lines = sys.argv[1:9]
html = open(page, encoding="utf-8").read()

vals = {"Total commits": commits, "Tracked files": files,
        "Contributors": authors, "Total lines": lines}

rowpat = re.compile(
    r'(<tr><td class="stat-label">(Total commits|Tracked files|Contributors|Total lines)[^<]*</td>)'
    r'<td class="stat">\d+</td></tr>')

html, nrows = rowpat.subn(lambda m: m.group(1) + '<td class="stat">' + vals[m.group(2)] + "</td></tr>", html)
if nrows != 4:
    sys.exit("scope guard: expected 4 stat rows, found %d -- aborting, page untouched" % nrows)

# Keep agent-04's trailing pin note in agreement with the snapshot sha.
# Guarded: only rewritten when the exact sentence shape is present, and
# exactly once; otherwise abort rather than guess.
pinpat = re.compile(r"Snapshot pinned to commit [0-9a-f]+ \(HEAD at refresh\)")
html, npins = pinpat.subn("Snapshot pinned to commit %s (HEAD at refresh)" % sha, html)
if npins > 1:
    sys.exit("scope guard: expected at most 1 pin-sha note, found %d -- aborting" % npins)

begin = "<!-- stats-table: managed by scripts/snapshot-stats.sh; re-pin via that script, not by hand -->"
end = "<!-- /stats-table -->"

block = (
    "\n"
    '  <p class="muted"><strong>Snapshot %s</strong>, taken %s. Stale by design:\n'
    "  this world grows with every commit, so any count is true only at its pinned\n"
    "  revision &mdash; read drift here as information, not error. Live counts:\n"
    "  <code>sh scripts/about-stats.sh</code> &middot; re-pin this table:\n"
    "  <code>sh scripts/snapshot-stats.sh</code>.</p>\n"
    "  <table>\n"
    '    <tr><td class="stat-label">Total commits (at snapshot)</td><td class="stat">%s</td></tr>\n'
    '    <tr><td class="stat-label">Tracked files (excl. deploy-tool cache)</td><td class="stat">%s</td></tr>\n'
    '    <tr><td class="stat-label">Contributors (git authors)</td><td class="stat">%s</td></tr>\n'
    '    <tr><td class="stat-label">Total lines across those files (exact)</td><td class="stat">%s</td></tr>\n'
    "  </table>\n"
) % (sha, date, commits, files, authors, lines)

if begin in html and end in html:
    pre, rest = html.split(begin, 1)
    _, post = rest.split(end, 1)
    html = pre + begin + block + "  " + end + post
elif begin in html or end in html:
    sys.exit("scope guard: only one stats-table marker found -- aborting")
else:
    anchor = "<h2>In numbers</h2>"
    i = html.find(anchor)
    if i == -1:
        sys.exit('scope guard: no "In numbers" heading and no markers -- aborting')
    j = html.find("</table>", i)
    if j == -1:
        sys.exit("scope guard: no stats table after the heading -- aborting")
    j += len("</table>")
    html = html[:i + len(anchor)] + "\n" + begin + block + "  " + end + html[j:]

open(tmp, "w", encoding="utf-8").write(html)
PYEOF

mv "$tmp" "$PAGE"
echo "about.html updated: snapshot $sha (taken $date) -- $commits commits, $files files, $authors authors, $lines lines"
