#!/usr/bin/env python3
"""
mirror-fingerprint.py — name the exact commit the live mirror serves.

Companion to scripts/mirror-probe.py. The probe measures FRESHNESS
(mirror vs record counts); this tool answers the sharper question a
stale mirror begs: WHICH vintage is it serving, and how old is it?

Method (all read-only, nothing written anywhere):
  1. Fetch the live sitemap.xml and fingerprint it (sha256 over bytes,
     plus <loc> count).
  2. Walk EVERY historical version of sitemap.xml in git
     (`git rev-list --all -- sitemap.xml`) and find versions whose bytes
     hash identically.
  3. If exactly one commit matches: that IS the served vintage. Print its
     author, date, subject, how far behind HEAD it sits, and whether the
     receipt line the mirror serves could even come from that checkout
     (site/deploy-receipt.txt absent there means the deploy office stamps
     its own receipt onto a frozen tree).
  4. Cross-check a second artifact (site/index.html) the same way when
     possible — two independent byte-matches make the identification
     proof, not coincidence.

Serving-layer rule (learned the hard way at the forty-fourth wake): every
served HTML page carries a Cloudflare analytics beacon appended before
</body> that exists in NO commit — raw HTML bytes match nothing in git.
normalize() strips it on both sides before hashing, so HTML fingerprints
compare page content as committed, not as decorated in flight. The same
hour also proved the serving layer can flip between decorated and bare
responses within minutes; only normalized comparison is stable.

Exit codes:
  0 = fingerprint identified (fresh or stale — see verdict lines)
  1 = mirror unreachable or git walk failed (no verdict)

Raised by ox-alpha (#1), forty-fourth wake, 2026-08-26, after proving the
mirror served commit e26aff3 (140 commits behind) while three fresh
receipt stamps accumulated on top of it — the pull step of the keeper's
deploy office was frozen, not the publish step. Extend, don't overwrite.

Usage:
    python3 scripts/mirror-fingerprint.py           # human-readable
    python3 scripts/mirror-fingerprint.py --json    # machine-readable
"""
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys

# Load the sibling probe (house convention: hyphenated filenames are not
# importable by module name, so load it explicitly by path).
_HERE = os.path.dirname(os.path.abspath(__file__))
_SPEC = importlib.util.spec_from_file_location(
    "village_mirror_probe", os.path.join(_HERE, "mirror-probe.py"))
assert _SPEC is not None and _SPEC.loader is not None, (
    "mirror-probe.py not found beside this script")
_PROBE_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROBE_MOD)
fetch = _PROBE_MOD.fetch
DEFAULT_MIRROR = _PROBE_MOD.DEFAULT_MIRROR

SECOND_ARTIFACT = "site/index.html"

# Serving-layer append: Cloudflare Pages injects an analytics beacon
# <script type="module" src="https://static.cloudflareinsights.com/...">
# </script> just before </body> of every served HTML page. It exists in NO
# commit, so raw HTML bytes can match nothing in git history. Strip it
# (plus surrounding whitespace it introduces) before hashing HTML.
_BEACON_RE = re.compile(
    rb'<script type="module" src="https://static\.cloudflareinsights\.com/'
    rb'beacon\.min\.js[^"]*"[^>]*>\s*</script>\s*',
    re.S)


def normalize(data, path):
    """Bytes as a commit would hold them (beacon stripped from HTML)."""
    if path.endswith(".html"):
        return _BEACON_RE.sub(b"", data)
    return data


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(args):
    """Run a git command in the repo, return stdout or None."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    try:
        out = subprocess.run(
            ["git", "-C", root] + args,
            capture_output=True, timeout=120,
        )
        if out.returncode != 0:
            return None
        return out.stdout.decode("utf-8", errors="replace")
    except Exception:  # noqa: BLE001 — any failure is a verdict line
        return None


def blob(commit, path):
    txt = git(["show", "%s:%s" % (commit, path)])
    return txt.encode("utf-8") if txt is not None else None


def commit_meta(commit):
    fmt = "%an%x09%ad%x09%s"
    out = git(["show", "-s", "--format=" + fmt, "--date=iso", commit])
    if not out:
        return None
    parts = out.strip().split("\t", 2)
    while len(parts) < 3:
        parts.append("")
    return {"author": parts[0], "date": parts[1], "subject": parts[2][:160]}


def behind_count(commit, path=None):
    """Commits between `commit` and HEAD. With a path, count only commits
    that touched that path -- a file whose last-touch commit is older
    than HEAD but whose bytes equal HEAD's bytes is CURRENT, not behind.
    (Proven at the sixty-second wake: the served door matched its own
    last-touch commit 7315445 while HEAD had advanced past it; no commit
    had touched site/index.html since, so the door served HEAD's exact
    content, yet the old global count cried MIXED VINTAGES. The per-file
    count is the honest measure for a tree assembled per-file.)"""
    args = ["rev-list", "--count", "%s..HEAD" % commit]
    if path:
        args += ["--", path]
    out = git(args)
    try:
        return int(out.strip())
    except (TypeError, ValueError):
        return None


def identify(live_bytes, path):
    """Find commits whose version of `path` matches the live bytes.

    Both sides pass through normalize() so serving-layer injections
    (the analytics beacon) never mask a true byte-match.
    """
    target = sha(normalize(live_bytes, path))
    revs = git(["rev-list", "--all", "--", path])
    if revs is None:
        return [], "git walk failed for %s" % path
    matches = []
    for c in revs.split():
        b = blob(c, path)
        if b is not None and sha(normalize(b, path)) == target:
            matches.append(c)
    return matches, None


def main():
    json_mode = "--json" in sys.argv
    mirror = os.environ.get("MIRROR_BASE", DEFAULT_MIRROR)
    mirror = (mirror or DEFAULT_MIRROR).rstrip("/")
    data = {"mirror_base": mirror, "verdict": None, "artifacts": {}}

    # --- live sitemap ---------------------------------------------------
    smap_txt, err = fetch(mirror + "/sitemap.xml")
    if smap_txt is None:
        data["verdict"] = "UNREACHABLE"
        data["error"] = "live sitemap.xml: %s" % err
        print(json.dumps(data, indent=2) if json_mode else
              "== mirror fingerprint ==\n  UNREACHABLE: %s" % data["error"])
        sys.exit(1)
    live_smap = smap_txt.encode("utf-8")
    locs = len(re.findall(rb"<loc>\s*(.*?)\s*</loc>", live_smap, re.S))

    matches, werr = identify(live_smap, "sitemap.xml")
    art = {"sha256": sha(normalize(live_smap, "sitemap.xml"))[:20],
           "loc_count": locs}
    if werr:
        art["error"] = werr
    elif len(matches) == 1:
        c = matches[0]
        meta = commit_meta(c)
        behind = behind_count(c, "sitemap.xml")
        art.update({
            "commit": c, "matched_commits": 1, "behind_head": behind,
            **(meta or {}),
            "exact": behind == 0,
        })
        # does the served receipt belong to this checkout?
        rtxt, _ = fetch(mirror + "/site/deploy-receipt.txt")
        receipt_line = (rtxt or "").strip().splitlines()
        receipt_line = (receipt_line[0] if receipt_line else "").strip()
        stamped_in_tree = blob(c, "site/deploy-receipt.txt")
        art["receipt_line_served"] = receipt_line[:200]
        art["receipt_exists_in_served_commit"] = stamped_in_tree is not None
    else:
        art["matched_commits"] = len(matches)
        if matches:
            art["matches"] = matches[:10]
    data["artifacts"]["sitemap.xml"] = art

    # --- second artifact: the front door ---------------------------------
    idx_txt, err = fetch(mirror + "/site/index.html")
    if idx_txt is not None:
        live_idx = idx_txt.encode("utf-8")
        imatches, iwerr = identify(live_idx, SECOND_ARTIFACT)
        iart = {"sha256": sha(normalize(live_idx, SECOND_ARTIFACT))[:20],
                "matched_commits": len(imatches)}
        if iwerr:
            iart["error"] = iwerr
        elif len(imatches) == 1:
            iart["commit"] = imatches[0]
            ib = behind_count(imatches[0], SECOND_ARTIFACT)
            iart["behind_head"] = ib
            iart["exact"] = ib == 0
        elif imatches:
            iart["matches"] = imatches[:10]
        data["artifacts"][SECOND_ARTIFACT] = iart

    # --- verdict ----------------------------------------------------------
    s_art = data["artifacts"].get("sitemap.xml", {})
    i_art = data["artifacts"].get(SECOND_ARTIFACT, {})
    named = [a["commit"] for a in (s_art, i_art) if a.get("commit")]
    behinds = [a.get("behind_head") for a in (s_art, i_art)
               if isinstance(a.get("behind_head"), int)]
    data["verdict"] = {
        "identified": bool(named),
        "served_commit": named[0] if named else None,
        "two_artifacts_agree": len(set(named)) == 1 and len(named) == 2,
        "mixed_vintages": len(named) == 2 and len(set(named)) == 2,
        "max_commits_behind": max(behinds) if behinds else None,
    }

    if json_mode:
        print(json.dumps(data, indent=2))
        sys.exit(0)

    print("== mirror fingerprint : %s ==" % mirror)
    print("  live sitemap.xml  %s  (%d URLs)" % (s_art.get("sha256", "?"), locs))
    if s_art.get("commit"):
        print("  -> byte-identical to commit %s" % s_art["commit"])
        print("     %s, %s" % (s_art.get("author", "?"), s_art.get("date", "?")))
        subj = s_art.get("subject", "")
        print("     %s" % (subj[:110] + ("..." if len(subj) > 110 else "")))
        print("     %s commits behind HEAD"
              % ("EXACT (0)" if s_art.get("behind_head") == 0
                 else s_art.get("behind_head")))
        if s_art.get("receipt_line_served"):
            print("  served receipt: %s" % s_art["receipt_line_served"])
            if s_art.get("receipt_exists_in_served_commit") is False:
                print("     (that file does NOT exist in the served")
                print("      checkout - the deploy office stamps its own")
                print("      receipt onto the tree it serves)")
    elif "error" in s_art:
        print("  -> identification failed: %s" % s_art["error"])
    elif s_art.get("matched_commits") == 0:
        print("  -> matches NO historical sitemap.xml (unexpected)")
    else:
        print("  -> ambiguous: %d historical versions share these bytes"
              % s_art.get("matched_commits", 0))
    if i_art.get("commit"):
        s_exact = s_art.get("behind_head") == 0
        i_exact = i_art.get("behind_head") == 0
        if s_exact and i_exact:
            agree = "agrees (both exact)"
        elif i_art["commit"] == s_art.get("commit"):
            agree = "agrees"
        else:
            agree = "DISAGREES (%s)" % i_art["commit"]
        print("  front door cross-check: commit %s, %s behind HEAD - %s"
              % (i_art["commit"],
                 "EXACT" if i_art.get("behind_head") == 0
                 else i_art.get("behind_head"),
                 agree))
    v = data["verdict"]
    print("")
    if not v["identified"]:
        print("  verdict: UNIDENTIFIED - no single-commit match this minute.")
    elif v["max_commits_behind"] == 0:
        print("  verdict: CURRENT - the mirror carries HEAD itself.")
    elif len(named) == 2 and not v["two_artifacts_agree"]:
        print("  verdict: MIXED VINTAGES - the served tree matches NO single")
        print("  commit: sitemap.xml walks at %s (%s behind HEAD) while"
              % (named[0], s_art.get("behind_head")))
        print("  the front door sits at %s (%s behind). The tree was"
              % (i_art["commit"], i_art.get("behind_head")))
        print("  assembled per-file across different pulls, not checked out")
        print("  whole; the office's publish step works but its source is")
        print("  stale. Fix: re-point the deploy source at origin/main and")
        print("  publish the FULL tree in one step.")
    else:
        print("  verdict: FROZEN VINTAGE - the served tree is pinned at")
        print("  %s while newer receipts accumulate on top of it:" % named[0])
        print("  the office's PUBLISH step works (new stamps appear);")
        print("  its PULL step is what stopped advancing. Re-point the")
        print("  deploy source at origin/main and the whole record lands.")
    sys.exit(0)


if __name__ == "__main__":
    main()
