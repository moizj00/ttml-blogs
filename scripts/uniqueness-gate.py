#!/usr/bin/env python3
"""
uniqueness-gate.py — Block near-duplicate blog posts. Stdlib only.

The whole point of the "quality behemoth" front-of-funnel is that every post is
genuinely unique. This is the back-stop: before a draft is queued or published,
compare it against everything already published (TTML-Blog/) and the rest of the
drip queue. If it overlaps too much in title OR body, fail so a human re-angles
it instead of shipping a near-twin that splits SEO and reads as filler.

Two signals, both 0..1:
  * title similarity  — difflib ratio on normalized titles
  * body similarity   — Jaccard overlap of 5-word shingles

Usage:
  python uniqueness-gate.py DRAFT.md [DRAFT.md ...]
  python uniqueness-gate.py --dir blog-queue            # check every draft in a dir
  python uniqueness-gate.py DRAFT.md --against TTML-Blog # corpus to compare against
  python uniqueness-gate.py DRAFT.md --title 0.72 --body 0.28   # thresholds
  python uniqueness-gate.py --dir blog-queue --json     # machine-readable

Exit code 0 = all drafts unique enough; 1 = at least one too-similar (or error).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CORPUS = REPO_ROOT / "TTML-Blog"

DEFAULT_TITLE_THRESHOLD = 0.72   # difflib ratio
DEFAULT_BODY_THRESHOLD = 0.25    # shingle Jaccard

_STOP = {
    "the", "a", "an", "and", "or", "but", "to", "of", "in", "on", "for", "with",
    "is", "are", "be", "you", "your", "i", "it", "this", "that", "how", "what",
    "can", "do", "does", "if", "as", "at", "by", "from", "california", "ca",
}


def split_frontmatter(text: str) -> tuple[dict, str]:
    fm: dict = {}
    body = text
    if text.lstrip().startswith("---"):
        s = text.find("---")
        e = text.find("\n---", s + 3)
        if e != -1:
            block = text[s + 3:e]
            nl = text.find("\n", e + 1)
            body = text[nl + 1:] if nl != -1 else ""
            for line in block.splitlines():
                m = re.match(r"\s*([A-Za-z_]+):\s*(.+?)\s*$", line)
                if m:
                    fm[m.group(1).lower()] = m.group(2).strip().strip('"').strip("'")
    return fm, body


def post_title(fm: dict, body: str, path: Path) -> str:
    if fm.get("title"):
        return fm["title"]
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def normalize(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9§$]+", text.lower())
    return [w for w in words if w not in _STOP and len(w) > 2]


def shingles(words: list[str], k: int = 5) -> set[str]:
    if len(words) < k:
        return {" ".join(words)} if words else set()
    return {" ".join(words[i:i + k]) for i in range(len(words) - k + 1)}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def title_ratio(a: str, b: str) -> float:
    na = " ".join(normalize(a))
    nb = " ".join(normalize(b))
    return SequenceMatcher(None, na, nb).ratio()


def load_corpus(corpus_dir: Path, exclude: set[Path]) -> list[dict]:
    out = []
    if not corpus_dir.is_dir():
        sys.exit(f"ERROR: corpus dir not found: {corpus_dir}")
    for p in sorted(corpus_dir.glob("*.md")):
        if p.resolve() in exclude:
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        fm, body = split_frontmatter(text)
        out.append({
            "path": p,
            "title": post_title(fm, body, p),
            "shingles": shingles(normalize(body)),
        })
    return out


def check_draft(draft: Path, corpus: list[dict], t_thr: float, b_thr: float) -> dict:
    text = draft.read_text(encoding="utf-8", errors="replace")
    fm, body = split_frontmatter(text)
    d_title = post_title(fm, body, draft)
    d_sh = shingles(normalize(body))
    worst = {"title_sim": 0.0, "body_sim": 0.0, "against": None}
    matches = []
    for c in corpus:
        ts = title_ratio(d_title, c["title"])
        bs = jaccard(d_sh, c["shingles"])
        if ts >= t_thr or bs >= b_thr:
            matches.append({"against": c["path"].name, "title_sim": round(ts, 3), "body_sim": round(bs, 3)})
        if (ts, bs) > (worst["title_sim"], worst["body_sim"]):
            worst = {"title_sim": round(ts, 3), "body_sim": round(bs, 3), "against": c["path"].name}
    matches.sort(key=lambda m: max(m["title_sim"], m["body_sim"]), reverse=True)
    return {"draft": draft.name, "title": d_title, "duplicate": bool(matches),
            "closest": worst, "matches": matches[:5]}


def main() -> int:
    ap = argparse.ArgumentParser(description="Cross-post uniqueness gate for TTML blog drafts.")
    ap.add_argument("files", nargs="*", help="draft markdown files")
    ap.add_argument("--dir", help="check every *.md in this directory")
    ap.add_argument("--against", default=str(DEFAULT_CORPUS),
                    help="corpus directory to compare against (default: TTML-Blog/)")
    ap.add_argument("--title", type=float, default=DEFAULT_TITLE_THRESHOLD)
    ap.add_argument("--body", type=float, default=DEFAULT_BODY_THRESHOLD)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

    drafts: list[Path] = [Path(f).resolve() for f in args.files]
    if args.dir:
        drafts += sorted(Path(args.dir).resolve().rglob("*.md"))
    drafts = list(dict.fromkeys(drafts))
    if not drafts:
        sys.exit("ERROR: pass draft file(s) or --dir.")

    corpus = load_corpus(Path(args.against).resolve(), exclude=set(drafts))
    results = [check_draft(d, corpus, args.title, args.body) for d in drafts]
    dupes = [r for r in results if r["duplicate"]]

    if args.json:
        print(json.dumps({"results": results, "duplicate_count": len(dupes)}, indent=2, ensure_ascii=False))
    else:
        print(f"Checked {len(drafts)} draft(s) against {len(corpus)} published post(s)\n")
        for r in results:
            if r["duplicate"]:
                print(f"  [DUP]  {r['draft']}")
                for m in r["matches"]:
                    print(f"         ~ {m['against']}  (title {m['title_sim']}, body {m['body_sim']})")
            else:
                c = r["closest"]
                print(f"  [OK]   {r['draft']}  (closest: title {c['title_sim']}, body {c['body_sim']})")
        print(f"\nDone. {len(dupes)}/{len(drafts)} flagged as near-duplicate.")
    return 1 if dupes else 0


if __name__ == "__main__":
    sys.exit(main())
