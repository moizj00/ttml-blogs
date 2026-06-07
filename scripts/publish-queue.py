#!/usr/bin/env python3
"""
publish-queue.py — buffer-aware blog publisher.

Wraps publish-batch.py so written-but-unpublished posts are never lost. Every run
drains the BUFFER (pending posts) first, oldest first, and only marks a post
published after a 2xx response. Failed or completeness-blocked posts STAY pending
for the next run instead of being discarded or ignored.

The "buffer" = every .md post in the blog dir whose current content hasn't been
recorded as successfully published in the ledger (.claude/publish-ledger.json).
So the moment a post is written but not (successfully) published, it's buffered;
the next publish run picks it up automatically.

Usage:
    python publish-queue.py --status     # show published vs pending (no network)
    python publish-queue.py --seed       # baseline: mark ALL current posts published (no network)
    python publish-queue.py              # drain: publish all pending, oldest first
    python publish-queue.py --force      # drain, skipping the truncation gate
    python publish-queue.py --dir TTML-Blog

Env:
    TTML_PUBLISH_ENDPOINT   inherited by publish-batch (defaults to PRODUCTION)
    BLOG_PUBLISH_API_KEY    inherited by publish-batch
    TTML_PUBLISH_LEDGER     override ledger path (for tests)

Safety:
    Refuses to drain if no ledger exists yet — prevents mass re-publish of the
    existing 200+ posts. Run `--seed` once first to establish the baseline.

Exit code: 0 only if the buffer is fully drained (nothing left pending).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent

# Reuse publish-batch.py's gate + POST logic. Hyphenated filename → importlib.
_spec = importlib.util.spec_from_file_location("publish_batch", HERE / "publish-batch.py")
pb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pb)

LEDGER = Path(os.environ.get("TTML_PUBLISH_LEDGER", str(REPO / ".claude" / "publish-ledger.json")))
DEFAULT_DIR = REPO / "TTML-Blog"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_ledger() -> dict | None:
    if not LEDGER.exists():
        return None
    try:
        return json.loads(LEDGER.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        sys.exit(f"ERROR: ledger is corrupt, refusing to proceed: {LEDGER}")


def save_ledger(led: dict) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps(led, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def posts_in(dir_: Path) -> list[Path]:
    # Sorted by name; posts are date-prefixed (YYYY-MM-DD-…) so this is oldest-first.
    return sorted((p for p in dir_.glob("*.md") if p.is_file()), key=lambda p: p.name)


def pending(dir_: Path, led: dict) -> list[Path]:
    pub = led.get("published", {})
    out = []
    for p in posts_in(dir_):
        rec = pub.get(p.name)
        if rec is None or rec.get("hash") != sha(p):
            out.append(p)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Buffer-aware blog publisher — drains pending posts first.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("--dir", default=str(DEFAULT_DIR), help="blog directory (default: TTML-Blog)")
    ap.add_argument("--status", action="store_true", help="show pending vs published; no network")
    ap.add_argument("--seed", action="store_true",
                    help="mark ALL current posts as published (baseline); no network")
    ap.add_argument("--force", action="store_true", help="skip the truncation/completeness gate")
    ap.add_argument("--timeout", type=int, default=30)
    args = ap.parse_args()

    dir_ = Path(args.dir).resolve()
    if not dir_.is_dir():
        sys.exit(f"ERROR: blog dir not found: {dir_}")

    led = load_ledger()

    # ── seed: establish baseline so existing posts aren't re-published ──
    if args.seed:
        led = led or {"version": 1, "published": {}}
        now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        n = 0
        for p in posts_in(dir_):
            led["published"][p.name] = {"hash": sha(p), "published_at": now, "seeded": True}
            n += 1
        save_ledger(led)
        print(f"[seed] baselined {n} post(s) as published in {LEDGER}. No network calls made.")
        return 0

    # ── status: report buffer, no network ──
    if args.status:
        led_s = led or {"version": 1, "published": {}}
        pend = pending(dir_, led_s)
        print(f"Ledger: {'present' if led else 'MISSING'} | "
              f"published: {len(led_s.get('published', {}))} | buffer (pending): {len(pend)}")
        for p in pend:
            print(f"  pending: {p.name}")
        if led is None:
            print("Note: no ledger yet — run `--seed` to baseline current posts before draining.")
        return 0

    # ── drain: publish the buffer, oldest first ──
    if led is None:
        sys.exit(
            "ERROR: no ledger found. Run `python scripts/publish-queue.py --seed` once to "
            "baseline current posts as published (prevents mass re-publish), then re-run."
        )

    pend = pending(dir_, led)
    if not pend:
        print("Buffer empty — nothing pending to publish.")
        return 0

    key = pb.load_key()
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"Buffer has {len(pend)} pending post(s). Draining oldest-first…\n")
    published = blocked = failed = 0
    for p in pend:
        if not args.force:
            probs = pb.completeness_problems(p)
            if probs:
                blocked += 1
                print(f"  [SKIP] {p.name} — kept in buffer (incomplete): {probs[0]}")
                continue
        status, body = pb.publish_markdown(p, key, args.timeout)
        if 200 <= status < 300:
            led["published"][p.name] = {"hash": sha(p), "published_at": now}
            save_ledger(led)  # persist after each success → crash-safe, no double-publish
            published += 1
            print(f"  [OK] {status} {p.name}")
        else:
            failed += 1
            print(f"  [FAIL] {status} {p.name} — kept in buffer: {body[:120]}")

    remaining = blocked + failed
    print(f"\nDone. published={published} kept_in_buffer={remaining} "
          f"(blocked={blocked} failed={failed}).")
    return 0 if remaining == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
