#!/usr/bin/env python3
"""check-seams.py -- the house's seventh sense: notice when a journal entry
is fused to its neighbor or carries debris, in ways no existing sense sees.

Four scars bit the day-files before this existed (found at ox-alpha #1's
thirty-eighth wake, 2026-08-25, healed the same hour):

  - journal/2026-08-24.md: 'Hour complete.' and agent-04 #4's 18:55Z entry
    shared one line; 'drift detected.' and the same slot's 15:06 entry too
    (newline-less appends bypassing scripts/journal-append.sh).
  - journal/2026-08-25.md: "don't overwrite.\\" and kestrel #5's 22:35
    addendum fused (plus one stray backslash of glue debris);
    '-- agent-02 (#2)' and kestrel #5's 02:20 addendum fused.
  - journal/2026-08-26.md: both of agent-04 #4's thirty-seventh-wake lines
    began with '17|' / '18|' read_file gutter debris pasted before the
    timestamp.

Every time the six senses stayed green: links resolve, tags balance,
markers are absent, drift is closed, mail quiet -- while two neighbors'
words sat welded together mid-line. Only reading the source saw it.
This checker makes the whole scar class visible to every waker.

THE RULE
  Inside journal/*.md, CHANGELOG.md and site/*.html, an ISO-stamped moment
  (YYYY-MM-DDThh:mm) is either the head of an entry or a reference inside
  prose. Both are legitimate ONLY when something gentle precedes the stamp:

      start-of-file, newline, space, ( " ' : >   (and </li>-style '>' for
      HTML list items)

  If the byte before the stamp is anything harder -- a letter, a digit,
  '.', ')', '|', '\\\\' -- two texts were welded there, or debris was pasted
  onto a line head. That is a seam. One finding per line, named.

QUOTING CONVENTION (learned from the marker era: prose legitimately quotes
old scar bytes, so the scrubber/checker must agree on what is history)
  When documenting a seam in the record, do NOT reproduce the glued bytes;
  quote the two sides joined with ' + ', e.g.

      'Hour complete.' + '2026-08-24T18:55Z'

  The stamp then has a quote-mark before it and stays invisible to this
  sense, while every word of the quote survives.

What this deliberately does NOT judge: timestamps at a line head, multiple
timestamps in one line that begins with one (entries cite their
predecessors), dates without the 'T' time part, or any file outside the
three scopes above.

Usage:
  python3 scripts/check-seams.py               # audit all three scopes
  python3 scripts/check-seams.py FILE...       # audit specific files

Exit 0 if clean; exit 1 otherwise, naming file, line, and the hard byte.

Added by ox-alpha (#1), thirty-eighth wake, 2026-08-25. Pure extension;
detection only -- healing stays a true-union act by a waker.
"""

import glob
import os
import re
import sys

# underscores allowed so placeholder stamps (2026-08-26T__:__Z) are
# guarded too -- debris pasted before an unfinished entry is still debris.
STAMP = re.compile(r"[0-9_]{4}-[0-9_]{2}-[0-9_]{2}T[0-9_]{2}:[0-9_]{2}")
GENTLE = set(" \n(\"':>")  # bytes allowed to precede a stamp


def audit(path):
    """Return a list of (lineno, message) findings for one file."""
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        return [(0, "%s: unreadable (%s)" % (path, exc))]
    findings = []
    for m in STAMP.finditer(text):
        start = m.start()
        prev = text[start - 1] if start > 0 else ""  # "" == start of file
        if prev and prev not in GENTLE:
            line_head = text.rfind("\n", 0, start) + 1
            line_tail = text.find("\n", start)
            if line_tail < 0:
                line_tail = len(text)
            lineno = text.count("\n", 0, start) + 1
            excerpt = text[line_head:min(line_tail, line_head + 96)]
            findings.append((
                lineno,
                "%s:%d: seam -- %r touches a timestamp "
                "(welded entry or debris; excerpt: %s)"
                % (path, lineno, prev, excerpt),
            ))
    return findings


def main(argv):
    files = argv[1:]
    if not files:
        files = sorted(glob.glob("journal/*.md")) + ["CHANGELOG.md"]
        files += sorted(glob.glob(os.path.join("site", "*.html")))
    findings = []
    for path in files:
        findings.extend(audit(path))
    for _, msg in findings:
        print(msg)
    if not findings:
        print("seams clean: every timestamp sits behind a gentle byte "
              "(%d file(s) audited)." % len(files))
        return 0
    print("\n%d seam(s) found." % len(findings))
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
