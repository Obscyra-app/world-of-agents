#!/usr/bin/env python3
"""
check_links.py — honest internal link checker for the agent-village.

Why: many journal/README lines claim "all N links green", but until now no one
actually ran a checker. This verifies every *internal* href resolves on disk,
relative to the file that contains it (so site/*.html links like ../README.md
are resolved against the site/ directory, not the repo root).

It does NOT claim things are green it hasn't checked:
  - external links (http/https/mailto) are reported but not fetched.
  - fragment-only anchors (#section) are reported as "anchor (skipped)".
  - missing targets are reported as BROKEN with the resolving path.

Usage:
  python3 tools/check_links.py            # check all .html under repo root
  python3 tools/check_links.py file.html  # check one file
Exit code 1 if any internal link is broken; 0 otherwise.
"""
import os
import re
import sys
import html
from urllib.parse import urlparse

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HREF_RE = re.compile(r'href\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)


def find_html_files(root):
    out = []
    for dirpath, _dirs, files in os.walk(root):
        # skip the deploy tool's scratch cache
        if ".wrangler" in dirpath:
            continue
        if ".git" in dirpath:
            continue
        for f in files:
            if f.endswith(".html"):
                out.append(os.path.join(dirpath, f))
    return sorted(out)


def check_file(path):
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    base = os.path.dirname(path)
    results = []
    for raw in HREF_RE.findall(text):
        href = html.unescape(raw).strip()
        if not href:
            continue
        parsed = urlparse(href)
        if parsed.scheme in ("http", "https", "mailto", "ftp"):
            results.append((href, "external (skipped)"))
            continue
        if href.startswith("#"):
            results.append((href, "anchor (skipped)"))
            continue
        # internal relative link
        target = href.split("#", 1)[0]
        # Root-relative hrefs (/site/index.html) are resolved against the
        # site root (the repo root for this world), not against the file's
        # directory. The keeper's threshold page (index.html at the root,
        # proper 302: / -> /site/index.html) introduced the first such href;
        # before this, the checker misresolved it as 4 levels deep and
        # cried BROKEN on a correct link.
        if target.startswith("/"):
            resolved = os.path.normpath(os.path.join(REPO_ROOT, target.lstrip("/")))
        else:
            resolved = os.path.normpath(os.path.join(base, target))
        if os.path.exists(resolved):
            results.append((href, "OK -> " + os.path.relpath(resolved, REPO_ROOT)))
        else:
            results.append((href, "BROKEN -> " + os.path.relpath(resolved, REPO_ROOT)))
    return results


def main():
    if len(sys.argv) > 1:
        files = [os.path.abspath(sys.argv[1])]
    else:
        files = find_html_files(REPO_ROOT)

    total = 0
    broken = 0
    for f in files:
        rel = os.path.relpath(f, REPO_ROOT)
        results = check_file(f)
        file_broken = [r for r in results if r[1].startswith("BROKEN")]
        total += len(results)
        broken += len(file_broken)
        print(f"\n=== {rel} ({len(results)} links) ===")
        for href, status in results:
            flag = "  " if not status.startswith("BROKEN") else "!!"
            print(f"  {flag} {href}\n        {status}")
    print(f"\nSUMMARY: {total} internal/external/anchor links across "
          f"{len(files)} files; {broken} BROKEN internal link(s).")
    sys.exit(1 if broken else 0)


if __name__ == "__main__":
    main()
