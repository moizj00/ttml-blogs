#!/usr/bin/env python3
"""
drip-publish.py — Release queued TTML posts a few at a time. Stdlib only.

The batch generates ~10 exceptional posts in one pass, but dumping 10 live at
once reads as spammy and risks a freshness penalty. Instead posts land in
blog-queue/ as `status: draft` with a `publish_after` date, and this script
drips the best N (default 3) live per run:

    pick best eligible  →  vet (uniqueness + completeness)  →  flip to published
                        →  POST to the live REST API        →  move to _published/

"Best" = under-served barrel first (balances the live mix), then the longest-
waiting post (oldest publish_after / date), then an optional `priority:` key.

Eligibility: status is draft/queued AND publish_after (or date) is today-or-past.

Usage:
  python drip-publish.py                 # release up to 3 today
  python drip-publish.py --count 2
  python drip-publish.py --dry-run       # vet + show picks, no POST, no move
  python drip-publish.py --date 2026-06-08   # treat this as "today"
  python drip-publish.py --queue blog-queue --force   # skip vet gates (not advised)

Reuses publish-batch.py (key load, completeness gate, REST POST) and
uniqueness-gate.py (cross-post dedup) by import — single source of truth.

Exit 0 if every selected post published (or nothing was eligible); 1 on any
failure or blocked post.
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import re
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"
QUEUE_DIR = REPO_ROOT / "blog-queue"
PUBLISHED_DIR = QUEUE_DIR / "_published"
BLOG_DIR = REPO_ROOT / "TTML-Blog"
DEFAULT_COUNT = 3   # locked decision: drip 3/day


def _load(mod_name: str, filename: str):
    """Import a hyphenated sibling script as a module."""
    spec = importlib.util.spec_from_file_location(mod_name, SCRIPTS / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


pb = _load("publish_batch", "publish-batch.py")
ug = _load("uniqueness_gate", "uniqueness-gate.py")


# ── frontmatter ──────────────────────────────────────────────────────────────
def parse_frontmatter(text: str) -> dict:
    fm: dict = {}
    if text.lstrip().startswith("---"):
        s = text.find("---")
        e = text.find("\n---", s + 3)
        if e != -1:
            for line in text[s + 3:e].splitlines():
                m = re.match(r"\s*([A-Za-z_]+):\s*(.*?)\s*$", line)
                if m:
                    fm[m.group(1).lower()] = m.group(2).strip().strip('"').strip("'")
    return fm


def _rebuild(text: str, updates: dict, drop: tuple[str, ...]) -> str:
    """Frontmatter rewrite: update/insert `updates`, drop `drop`, keep the rest
    and the closing --- intact."""
    s = text.find("---")
    e = text.find("\n---", s + 3)
    block = text[s + 3:e]
    body = text[e + 4:]            # after "\n---"
    lines = [ln for ln in block.splitlines()]
    seen = set()
    out = []
    for line in lines:
        m = re.match(r"\s*([A-Za-z_]+):", line)
        key = m.group(1).lower() if m else None
        if key in drop:
            continue
        if key in updates:
            out.append(_fmt(key, updates[key]))
            seen.add(key)
        else:
            out.append(line)
    for key, val in updates.items():
        if key not in seen:
            out.append(_fmt(key, val))
    return "---" + "\n" + "\n".join(out).strip("\n") + "\n---" + body


def _fmt(key: str, val: str) -> str:
    if key in ("title", "description", "excerpt", "author"):
        return f'{key}: "{val}"'
    return f"{key}: {val}"


# ── eligibility / ranking ────────────────────────────────────────────────────
def as_date(val: str | None) -> dt.date | None:
    if not val:
        return None
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", val)
    return dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def published_barrel_counts() -> Counter:
    counts: Counter = Counter()
    if BLOG_DIR.is_dir():
        for p in BLOG_DIR.glob("*.md"):
            fm = parse_frontmatter(p.read_text(encoding="utf-8", errors="replace"))
            if fm.get("category"):
                counts[fm["category"].lower()] += 1
    return counts


def eligible_posts(queue: Path, today: dt.date) -> list[dict]:
    out = []
    for p in sorted(queue.glob("*.md")):
        fm = parse_frontmatter(p.read_text(encoding="utf-8", errors="replace"))
        if not (fm.get("slug") and fm.get("title")):
            continue   # not a real post (e.g. README) — skip
        status = fm.get("status", "draft").lower()
        if status == "published":
            continue
        release = as_date(fm.get("publish_after")) or as_date(fm.get("date"))
        if release and release > today:
            continue   # not yet due
        out.append({
            "path": p, "fm": fm,
            "barrel": (fm.get("category") or "general").lower(),
            "release": release or today,
            "priority": int(fm["priority"]) if fm.get("priority", "").isdigit() else 0,
        })
    return out


def rank(posts: list[dict], counts: Counter) -> list[dict]:
    # under-served barrel first, then explicit priority, then longest-waiting
    return sorted(
        posts,
        key=lambda x: (counts.get(x["barrel"], 0), -x["priority"], x["release"]),
    )


# ── release one post ─────────────────────────────────────────────────────────
def release(post: dict, today: dt.date, key: str, timeout: int,
            force: bool, dry: bool) -> tuple[bool, str]:
    path = post["path"]
    text = path.read_text(encoding="utf-8", errors="replace")

    # Gate 1 — completeness (reused from publish-batch)
    if not force:
        probs = pb.completeness_problems(path)
        if probs:
            return False, "incomplete: " + "; ".join(probs)

    # Gate 2 — uniqueness vs all published + the rest of the queue
    if not force:
        corpus = ug.load_corpus(BLOG_DIR, exclude={path.resolve()})
        # also compare against other queued drafts
        for q in QUEUE_DIR.glob("*.md"):
            if q.resolve() == path.resolve():
                continue
            qt = q.read_text(encoding="utf-8", errors="replace")
            qfm, qbody = ug.split_frontmatter(qt)
            corpus.append({"path": q, "title": ug.post_title(qfm, qbody, q),
                           "shingles": ug.shingles(ug.normalize(qbody))})
        res = ug.check_draft(path, corpus, ug.DEFAULT_TITLE_THRESHOLD, ug.DEFAULT_BODY_THRESHOLD)
        if res["duplicate"]:
            top = res["matches"][0]
            return False, f"near-duplicate of {top['against']} (title {top['title_sim']}, body {top['body_sim']})"

    # Flip to live: status=published, date=release day, drop publish_after
    live_text = _rebuild(text, {"status": "published", "date": today.isoformat()},
                         drop=("publish_after", "priority"))

    if dry:
        return True, "DRY-RUN ok (would publish + move)"

    path.write_text(live_text, encoding="utf-8")
    status, body = pb.publish_markdown(path, key, timeout)
    if not (200 <= status < 300):
        return False, f"API {status}: {body[:120]}"

    PUBLISHED_DIR.mkdir(parents=True, exist_ok=True)
    dest = PUBLISHED_DIR / path.name
    path.replace(dest)
    return True, f"published ({status}) -> _published/{dest.name}"


def main() -> int:
    ap = argparse.ArgumentParser(description="Drip-publish queued TTML posts.")
    ap.add_argument("--count", type=int, default=DEFAULT_COUNT, help="max posts to release")
    ap.add_argument("--queue", default=str(QUEUE_DIR))
    ap.add_argument("--date", help="treat this YYYY-MM-DD as today")
    ap.add_argument("--timeout", type=int, default=30)
    ap.add_argument("--dry-run", action="store_true", help="vet + show picks, no POST/move")
    ap.add_argument("--force", action="store_true", help="skip vet gates (not advised)")
    args = ap.parse_args()

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

    queue = Path(args.queue).resolve()
    if not queue.is_dir():
        sys.exit(f"ERROR: queue dir not found: {queue}")
    today = as_date(args.date) or dt.date.today()

    counts = published_barrel_counts()
    pool = eligible_posts(queue, today)
    if not pool:
        print(f"Nothing eligible to publish in {queue} (as of {today}).")
        return 0

    picks = rank(pool, counts)[: args.count]
    key = "" if args.dry_run else pb.load_key()

    print(f"{'DRY-RUN: ' if args.dry_run else ''}Releasing up to {args.count} of "
          f"{len(pool)} eligible (queue has more)…\n")
    ok = 0
    for post in picks:
        good, msg = release(post, today, key, args.timeout, args.force, args.dry_run)
        tag = "[OK]" if good else "[BLOCK]"
        print(f"  {tag} {post['path'].name}  [{post['barrel']}]  {msg}")
        if good:
            ok += 1

    print(f"\nDone. {ok}/{len(picks)} released. {len(pool) - ok} still queued.")
    return 0 if ok == len(picks) else 1


if __name__ == "__main__":
    sys.exit(main())
