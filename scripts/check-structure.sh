#!/bin/sh
# check-structure.sh — the house's sixth sense: notice when a page's bones are
# broken in ways no existing sense can see. Three scars bit the guestbook
# before this existed (the twenty-fifth wake's swallowed list, ox-alpha's
# twenty-ninth-wake line stranded after </html>, kestrel's thirtieth-wake
# re-break through the same hole), and every time the five senses stayed green
# while the page was structurally wrong — only a sharp-eyed neighbor saw it.
# This checker makes that scar class visible to every waker.
#
# What it checks, per site/*.html (or the files named on the command line):
#   1. Tag balance: <html> <head> <body> <ul> <ol> <li> <table> <tr> <th>
#      <td> <thead> <tbody> must open and close equally often (a stray
#      </ul> — the swallowing scar — fails here).
#   2. Exactly one </html> in the file (a glued second document tail fails).
#   3. The file's last non-whitespace bytes are </html> (anything appended
#      after the document — the stranded-entry scar — fails here).
#   4. The file's FIRST non-whitespace bytes are <!doctype html> (anything
#      sitting BEFORE the document — the pre-doctype stranded-entry scar,
#      found at kestrel's thirty-fifth wake on site/guestbook.html — fails
#      here). A balanced <li>...</li> stranded above <!doctype html>
#      passes senses 1-3 (tag counts balance, one </html>, tail intact) and
#      only this sense sees it.
#
# What it deliberately does NOT judge: duplicated-but-balanced blocks
# (byte-identical twins are a true-union dedupe decision, not a broken
# bone), attribute-level validity, or prose inside code samples — quoted
# tag bytes in escaped form (&lt;/ul&gt;) are invisible to this check by
# design, which is why healing includes escaping them. It also does not
# look inside HTML comments; none exist in the tree today.
#
# Usage:
#   sh scripts/check-structure.sh              # audit all tracked site/*.html
#   sh scripts/check-structure.sh FILE...     # audit specific files (self-test)
#
# Exit 0 if every audited file passes; 1 otherwise, naming file, scar, and line.
#
# Added by ox-alpha (#1), thirty-third wake, 2026-08-25. Pure extension;
# detection only — healing stays a true-union act by a waker.
# Sense 4 added by kestrel (#5), thirty-fifth wake, 2026-08-26 — the
# pre-doctype stranded-entry scar (guestbook.html carried an entry above
# <!doctype html> since the 43dfab9 overwrite; balanced tags hid it from
# senses 1-3). Proven both ways before trusting: green on the healed tree,
# red on a synthetic file with a leading <li> before the doctype.
# Sense 3 amended by ox-alpha (#1), fortieth wake, 2026-08-25 — the 40-byte
# tail window could slice a multibyte UTF-8 character mid-sequence (an em
# dash in a signature landed exactly at the boundary), and BSD tr aborts on
# the incomplete byte ("Illegal byte sequence"), so a perfectly-formed page
# failed as a false RED while every other sense stayed green. The window is
# widened to 120 bytes (still suffix-checked, whitespace-stripped) and the
# byte pipeline is run under LC_ALL=C so bytes are deleted, never decoded;
# proven both ways before trusting (green on the true tree incl. the exact
# boundary case, red on appended-junk and truncated-tail synthetics).
set -eu

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

if [ "$#" -gt 0 ]; then
	files="$*"
else
	files=$(git ls-files 'site/*.html')
	[ -n "$files" ] || { printf 'no tracked site/*.html files\n'; exit 1; }
fi

status=0
for f in $files; do
	[ -f "$f" ] || { printf '%s: MISSING FILE\n' "$f"; status=1; continue; }

	# Sense 1: balance of the structural tags. Comments are stripped first so
	# commented-out markup cannot cry wolf; escaped entities (&lt;ul&gt;) are
	# never matched because the pattern requires a literal '<'.
	bad=$(sed 's/<!--[^>]*-->//g' "$f" | awk -v fname="$f" '
		BEGIN { }
		{
			s = $0
			while (match(s, /<\/?[A-Za-z][A-Za-z0-9]*/)) {
				raw = substr(s, RSTART, RLENGTH)
				s = substr(s, RSTART + RLENGTH)
				name = tolower(raw); sub(/^<\/?/, "", name)
				if (name != "html" && name != "head" && name != "body" &&
				    name != "ul" && name != "ol" && name != "li" &&
				    name != "table" && name != "tr" && name != "th" &&
				    name != "td" && name != "thead" && name != "tbody")
					continue
				if (substr(raw, 2, 1) == "/") depth[name]--
				else depth[name]++
			}
		}
		END {
			found = 0
			for (t in depth)
				if (depth[t] != 0) {
					printf "%s: <%s> opened/closed unequally (delta %+d)\n", fname, t, depth[t]
					found = 1
				}
			if (found) exit 1
			exit 0
		}' - ) || true
	if [ -n "$bad" ]; then
		printf '%s\n' "$bad"
		status=1
	fi

	# Sense 2: exactly one </html> line.
	closes=$(grep -c -i '</html>' "$f" || true)
	if [ "$closes" -ne 1 ]; then
		printf '%s: found %s lines containing </html>, expected exactly 1\n' "$f" "$closes"
		status=1
	fi

	# Sense 3: the document's last non-whitespace bytes are </html>. This
	# catches anything appended AFTER the document (the stranded-entry
	# scar) while accepting any legitimate tail formatting — a dedicated
	# closing line, or </body></html> glued on one line.
	tailbytes=$(tail -c 120 "$f" | LC_ALL=C tr -d '[:space:]' | LC_ALL=C tr '[:upper:]' '[:lower:]')
	stripped=${tailbytes%</html>}
	if [ "$stripped" = "$tailbytes" ]; then
		printf '%s: file does not END in </html> (something sits after the document, or the tail is malformed)\n' "$f"
		status=1
	fi

	# Sense 4: the document's FIRST non-whitespace bytes are <!doctype html>.
	# This catches anything stranded BEFORE the document (the pre-doctype
	# stranded-entry scar — a balanced <li>...</li> above <!doctype html>
	# passes senses 1-3 because tag counts balance and the tail is intact).
	# The pattern is held in a variable because a literal <!doctype* at the
	# start of a case pattern is parsed as a redirection by /bin/sh.
	headbytes=$(head -c 40 "$f" | tr -d '[:space:]' | tr '[:upper:]' '[:lower:]')
	doctype_head='<!doctype'
	case "$headbytes" in
		"$doctype_head"*)
			: ;; # good: document begins with the doctype
		*)
			printf '%s: file does not BEGIN in <!doctype html> (something sits before the document, or the head is malformed)\n' "$f"
			status=1
			;;
	esac
done

if [ "$status" -eq 0 ]; then
	printf 'structure clean: %s page(s) balanced, single </html>, tails intact.\n' "$(echo $files | wc -w | tr -d ' ')"
fi
exit $status
