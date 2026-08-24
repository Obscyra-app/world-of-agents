#!/usr/bin/env python3
"""
verify-links.py — check that every internal href/src in site/*.html resolves.

Usage: python scripts/verify-links.py
Exit 0 if all links resolve, 1 otherwise. Plain stdlib only.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

HREF_RE = re.compile(r'''href\s*=\s*["']([^"']+)["']''', re.I)
SRC_RE = re.compile(r'''src\s*=\s*["']([^"']+)["']''', re.I)

def collect_links(html_path):
    text = html_path.read_text(encoding="utf-8", errors="ignore")
    links = HREF_RE.findall(text) + SRC_RE.findall(text)
    # filter to relative internal links (ignore http, mailto, #, data:)
    out = []
    for l in links:
        if l.startswith("http://") or l.startswith("https://"):
            continue
        if l.startswith("mailto:") or l.startswith("data:") or l.startswith("#"):
            continue
        if l.startswith("//"):
            continue
        # strip query/fragment
        clean = l.split("#")[0].split("?")[0]
        if not clean:
            continue
        out.append((l, clean))
    return out

def resolve_link(source_file, raw, clean):
    # absolute from repo root: /site/... or /README.md etc not used, but handle
    if clean.startswith("/"):
        target = ROOT / clean.lstrip("/")
    else:
        target = (source_file.parent / clean).resolve()
        # keep inside repo check via relative_to
    try:
        target.relative_to(ROOT)
    except ValueError:
        return None, "escapes repo"
    # if target is directory, check index.html
    if target.is_dir():
        target = target / "index.html"
    return target, None

def main():
    html_files = sorted(SITE.glob("*.html"))
    if not html_files:
        print("No site/*.html found")
        return 1
    total = 0
    broken = []
    for hf in html_files:
        for raw, clean in collect_links(hf):
            total += 1
            target, err = resolve_link(hf, raw, clean)
            if err or target is None:
                broken.append((hf.name, raw, err or "unresolvable"))
                continue
            if not target.exists():
                broken.append((hf.name, raw, f"missing: {target.relative_to(ROOT)}"))
    print(f"Checked {total} internal links across {len(html_files)} files.")
    if broken:
        print(f"Broken: {len(broken)}")
        for src, raw, msg in broken:
            print(f"  {src}: href=\"{raw}\" -> {msg}")
        return 1
    else:
        print("All links resolve.")
        return 0

if __name__ == "__main__":
    sys.exit(main())
