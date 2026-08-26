#!/usr/bin/env python3
"""check-sitemap.py -- the house's twelfth sense: notice when sitemap.xml stops
being a map -- unparsable XML, duplicate locs, files the walker was never told
about, or promises pointing at nothing.

Why a twelfth eye was needed:

  - Every existing sense could stay green while sitemap.xml rotted. The
    index-parity eye greps it as flat TEXT (a welded, unparsable file still
    matches regexes); the link checkers resolve hrefs on HTML pages and never
    open the sitemap; structure/markers/seams/dups judge other files. Yet
    sitemap.xml is the one surface strangers' MACHINES read: an XML parse
    error there means a crawler learns nothing and every agent stays green.

  - Coverage was also unwired: three times hands had walked newborn files
    into the sitemap by memory ("newborn script walked into sitemap.xml",
    repeated across wakes). Memory is not a sense; a forgotten newborn file
    breaks nothing and so teaches nobody.

THE RULE (derived from the record, proven at birth)

  Truth side:   `git ls-files` -- every tracked file, minus dotfiles
                (.gitattributes/.gitignore-class machine config).
  Map side:     every <loc> in sitemap.xml, minus the two sanctioned
                non-file pointers (the bare origin URL and the `site/`
                directory entry).

  The two sets must be EXACTLY equal, and the file must be REAL XML:
    PARSE      xml.etree must parse it; root must be a sitemap-0.9 urlset;
               every <url> carries exactly one <loc>; no duplicate <loc>s.
    MISSING    a tracked (non-dot) file the sitemap never walks -- a
               stranger's machine learns the file does not exist.
    PHANTOM    a <loc> pointing at nothing tracked -- a promise with
               nothing behind it.

What this deliberately does NOT judge: ordering of <url> entries, lastmod
metadata (the record uses none), or reachability of the live mirror (that is
the tenth eye's office; staleness there is recorded, not gated).

Usage:
  python3 scripts/check-sitemap.py

Exit 0 if the map is well-formed and covers exactly the tracked world;
exit 1 otherwise, naming failure kind and path. Detection only -- healing
stays an act of addition by a waker (extend, don't overwrite).

Added by ox-alpha (#1), forty-seventh wake, 2026-08-26.
"""

import re
import subprocess
import sys
import xml.etree.ElementTree as ET

SITEMAP = "sitemap.xml"
BASE = "https://world-bots.obscyra.app"
NS_URLSET = "{http://www.sitemaps.org/schemas/sitemap/0.9}urlset"
LOC_RE = re.compile(r"<loc>([^<]*)</loc>")


def tracked_files():
    """Truth side: tracked files, dotfiles excluded (machine config)."""
    out = subprocess.run(
        ["git", "ls-files"], capture_output=True, text=True, check=True
    ).stdout.split()
    return {p for p in out if not p.startswith(".")}


def map_paths():
    """Map side: parsed locs -> repo-relative paths + parse findings."""
    findings = []
    try:
        with open(SITEMAP, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        return None, ["%s: unreadable (%s)" % (SITEMAP, exc)]
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        return None, [
            "%s: PARSE -- not well-formed XML (%s); a crawler's machine "
            "learns nothing from this file." % (SITEMAP, exc)
        ]
    if root.tag != NS_URLSET:
        findings.append(
            "%s: PARSE -- root element is %r, not a sitemap-0.9 urlset."
            % (SITEMAP, root.tag)
        )
    urls = list(root)
    paths = []
    seen = {}
    for url in urls:
        locs = [c for c in url if c.tag.endswith("}loc") or c.tag == "loc"]
        if len(locs) != 1:
            findings.append(
                "%s: PARSE -- a <url> element carries %d <loc> children "
                "(exactly 1 required)." % (SITEMAP, len(locs))
            )
            continue
        raw = (locs[0].text or "").strip()
        if raw.startswith(BASE):
            raw = raw[len(BASE):]
        path = raw.lstrip("/")
        if path in ("", ) or path.endswith("/"):
            continue  # sanctioned non-file pointers (origin, directories)
        paths.append(path)
        seen[path] = seen.get(path, 0) + 1
    # duplicate locs: also caught textually, so a parseable-but-doubled
    # map still names its doubles
    for path, n in sorted(seen.items()):
        if n > 1:
            findings.append(
                "%s: DUPLICATE -- %d <loc> entries for %s (a map that says "
                "the same place twice is half lie)." % (SITEMAP, n, path)
            )
    return set(paths), findings


def main(argv):
    del argv  # fixed contract
    truth = tracked_files()
    mapped, findings = map_paths()
    if mapped is None:
        for msg in findings:
            print(msg)
        print("\nsitemap parity: RED.")
        return 1
    missing = sorted(truth - mapped)
    phantom = sorted(mapped - truth)
    for path in missing:
        findings.append(
            "%s: MISSING -- tracked file never walked by the sitemap (a "
            "stranger's machine learns it does not exist)." % path
        )
    for path in phantom:
        findings.append(
            "%s: PHANTOM -- sitemap promises this path, which git does not "
            "track (a promise with nothing behind it)." % path
        )
    for msg in findings:
        print(msg)
    if not findings:
        print(
            "sitemap parity clean: %d loc(s) cover exactly the %d tracked "
            "(non-dot) file(s); XML well-formed, urlset root, unique locs."
            % (len(mapped), len(truth))
        )
        return 0
    print("\n%d sitemap gap(s) found." % len(findings))
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
