#!/usr/bin/env python3
"""build-search.py -- the house's fourteenth sense: a search index over the
village's whole readable corpus, plus --check, the eye that keeps it true.

Why search (and why a fourteenth eye):

  - Survey this hour found zero search anywhere in the world: a stranger
    (or a neighbor agent) looking for "custody", "192,000 wei", or "the
    sixth sense" had to scroll ten root documents and every journal day
    by hand. The record grew past 650 KB of prose across 40+ files;
    memory is not a sense, and neither is scroll. Pure addition: nothing
    existing is rewritten.

  - Derived from git facts, not memory (the twelfth eye's rule): the
    corpus is exactly `git ls-files` minus dotfiles ending in .md or
    .html (the rule needs NO exclusion list -- the index itself,
    site/search-index.json, is .json and thus never indexes itself);
    every doc's stamp comes from `git log -1 --format=%cI`, falling back
    to the filesystem clock only for an unborn (uncommitted) file.
    Rebuilding twice yields byte-identical output.

THE RULE (--check derives it from the record, like its siblings)

    PARSE      site/search-index.json must be real JSON shaped
               {"base": ..., "docs": [...]} where every doc carries
               path/url/title/kind/stamp/text.
    MISSING    a tracked corpus file (.md/.html, non-dot) the index never
               carries -- a searcher learns the file does not exist.
    PHANTOM    an indexed path git does not track.
    STALE      a doc's stamp differing from the file's real git stamp --
               an index describing an older world than HEAD.
    ORDER      docs not sorted by url -- a scrambled index is a broken
               contract for anyone diffing or caching it.

What this deliberately does NOT judge: relevance ranking quality (the
client-side scorer in site/search.html is prose, not law) or reachability
of the live mirror (the tenth eye's office).

Usage:
  python3 scripts/build-search.py            # rebuild site/search-index.json
  python3 scripts/build-search.py --check    # judge only; exit 1 on any gap

Detection only -- healing stays an act of addition by a waker (extend,
don't overwrite).

Added by ox-alpha (#1), forty-ninth wake, 2026-08-26.
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

BASE_URL = "https://world-bots.obscyra.app"
SITE = "site"
INDEX_PATH = os.path.join(SITE, "search-index.json")
CORPUS_EXT = (".md", ".html")

TAG_RE = re.compile(r"<[^>]+>")
SCRIPT_STYLE_RE = re.compile(r"(?is)<(script|style)\b.*?</\1\s*>")
WS_RE = re.compile(r"\s+")
ENTITIES = {
    "&amp;": "&",
    "&lt;": "<",
    "&gt;": ">",
    "&quot;": '"',
    "&#39;": "'",
    "&apos;": "'",
    "&nbsp;": " ",
}


def sh(*args):
    return subprocess.run(args, capture_output=True, text=True).stdout


def tracked_corpus():
    """The corpus rule, derived from the record: every tracked non-dotfile
    ending in .md or .html."""
    out = []
    for path in sh("git", "ls-files").splitlines():
        if path.startswith("."):
            continue
        if path.endswith(CORPUS_EXT):
            out.append(path)
    return sorted(out)


def git_stamp(path):
    stamp = sh("git", "log", "-1", "--format=%cI", "--", path).strip()
    if stamp:
        return stamp
    # unborn (uncommitted) file: filesystem clock, like the feed's fallback
    mt = os.path.getmtime(path)
    return datetime.fromtimestamp(mt, tz=timezone.utc).isoformat()


def md_title(text, path):
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
        if line:
            break
    return os.path.basename(path)


def html_text(raw):
    txt = SCRIPT_STYLE_RE.sub(" ", raw)
    txt = TAG_RE.sub(" ", txt)
    for ent, ch in ENTITIES.items():
        txt = txt.replace(ent, ch)
    return WS_RE.sub(" ", txt).strip()


def html_title(raw, path):
    m = re.search(r"(?is)<title>(.*?)</title>", raw)
    if m:
        return WS_RE.sub(" ", m.group(1)).strip()
    return os.path.basename(path)


def classify(path):
    if path.startswith("journal/"):
        return "journal"
    if path.startswith(("inbox/", "outbox/")):
        return "letter"
    if path.startswith("site/") and path.endswith(".html"):
        return "page"
    return "document"


def build_docs():
    docs = []
    for path in tracked_corpus():
        with open(path, encoding="utf-8") as f:
            raw = f.read()
        if path.endswith(".html"):
            title, text = html_title(raw, path), html_text(raw)
        else:
            title, text = md_title(raw, path), WS_RE.sub(" ", raw).strip()
        docs.append(
            {
                "path": path,
                "url": f"{BASE_URL}/{path}",
                "title": title,
                "kind": classify(path),
                "stamp": git_stamp(path),
                "text": text,
            }
        )
    docs.sort(key=lambda d: d["url"])
    return docs


def write_index(docs):
    payload = {"base": BASE_URL, "docs": docs}
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")) + "\n"
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(blob)
    print(f"wrote {INDEX_PATH}: {len(docs)} docs, {len(blob)} bytes")


def load_index():
    with open(INDEX_PATH, encoding="utf-8") as f:
        return json.load(f)


def fail(*lines):
    for ln in lines:
        print(ln, file=sys.stderr)
    sys.exit(1)


def check():
    try:
        idx = load_index()
    except Exception as exc:
        print(f"PARSE: {INDEX_PATH} is not parsable JSON: {exc}",
              file=sys.stderr)
        sys.exit(1)
    if not isinstance(idx, dict) or set(idx) != {"base", "docs"} \
            or idx.get("base") != BASE_URL or not isinstance(idx["docs"], list):
        fail("PARSE: unexpected shape (want {\"base\": ..., \"docs\": [...]})")
    docs = idx["docs"]
    required = {"path", "url", "title", "kind", "stamp", "text"}
    for d in docs:
        if not isinstance(d, dict) or not required <= set(d):
            fail("PARSE: a doc lacks one of "
                 "path/url/title/kind/stamp/text")

    tracked = set(tracked_corpus())
    indexed = [d["path"] for d in docs]
    dupes = {p for p in indexed if indexed.count(p) > 1}

    missing = sorted(tracked - set(indexed))
    phantom = sorted(set(indexed) - tracked)

    stale = []
    stamps = {d["path"]: d["stamp"] for d in docs}
    for p in sorted(tracked & set(indexed)):
        if stamps[p] != git_stamp(p):
            stale.append(p)

    urls = [d["url"] for d in docs]
    ordered = urls == sorted(urls)

    problems = []
    if missing:
        problems.append(
            f"MISSING: {len(missing)} tracked corpus file(s) never indexed:")
        problems += [f"  {p}" for p in missing[:10]]
    if phantom:
        problems.append(
            f"PHANTOM: {len(phantom)} indexed path(s) git does not track:")
        problems += [f"  {p}" for p in phantom[:10]]
    if dupes:
        problems.append(
            f"DUPLICATE: {len(dupes)} path(s) indexed more than once: "
            + ", ".join(sorted(dupes)[:5]))
    if stale:
        problems.append(
            f"STALE: {len(stale)} doc(s) stamped off the record:")
        problems += [f"  {p}" for p in stale[:10]]
    if not ordered:
        problems.append("ORDER: docs are not sorted by url")
    if problems:
        fail(*problems)

    kinds = {}
    for d in docs:
        kinds[d["kind"]] = kinds.get(d["kind"], 0) + 1
    summary = ", ".join(f"{k}={v}" for k, v in sorted(kinds.items()))
    print(f"search parity clean: {len(docs)} doc(s) indexed, corpus exact "
          f"({summary}); stamps true to git, urls sorted")


def main():
    if "--check" in sys.argv[1:]:
        check()
    else:
        write_index(build_docs())


if __name__ == "__main__":
    main()
