#!/usr/bin/env python3
"""
blog-crud.py — Full CRUD for TTML blog posts. Stdlib only (urllib), no pip install.

Design (matches how the stack actually works):
  * READS  (list, get)        -> Supabase PostgREST directly. There is no public
                                 read API, so this is the part direct-DB access wins.
  * WRITES (post, set-status) -> the REST publish API (POST /api/blog/publish).
                                 The API upserts AND purges the Cloudflare cache +
                                 recalculates reading time. Writing straight to
                                 Postgres would leave the live page serving stale
                                 cache, so writes deliberately go through the API.
  * DELETE (delete)           -> Supabase (no delete endpoint exists). Because that
                                 skips cache purge, --safe first flips the post to
                                 draft via the API (which purges + hides it) and
                                 then deletes the row.

Usage:
  python blog-crud.py list [--status published|draft|all] [--category C] [--limit N]
  python blog-crud.py get <slug> [--full]
  python blog-crud.py post <file.md> [<file.md> ...]      # create or update (upsert)
  python blog-crud.py set-status <slug> <published|draft>  # cache-safe via API
  python blog-crud.py delete <slug> --yes [--safe]

Config (no secrets in this file):
  SUPABASE_URL   env, else default below (non-secret project URL)
  Supabase key   env SUPABASE_KEY / SUPABASE_SERVICE_KEY,
                 else ~/.ttml-supabase-key, else .supabase-key next to this script.
                 Reads of published rows work with the anon/publishable key;
                 reading drafts and delete need the service_role key.
  Publish key    env BLOG_PUBLISH_API_KEY, else TTML_PUBLISH_KEY_FILE path,
                 else ~/.ttml-publish-key, else .publish-key next to this script.

Exit code 0 on success, non-zero on any failure.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://uqkqathpcthzuqhwraco.supabase.co").rstrip("/")
PUBLISH_ENDPOINT = os.environ.get("TTML_PUBLISH_ENDPOINT", "https://talk-to-my-lawyer.com/api/blog/publish")
TABLE = "blog_posts"

VALID_CATEGORIES = {
    "demand-letters", "cease-and-desist", "contract-disputes", "eviction-notices",
    "employment-disputes", "consumer-complaints", "pre-litigation-settlement",
    "debt-collection", "landlord-tenant", "intellectual-property",
    "pricing-and-roi", "general",
}


# --------------------------------------------------------------------------- keys
def _first_key(env_names: list[str], files: list[Path]) -> str | None:
    for name in env_names:
        if v := os.environ.get(name, "").strip():
            return v
    for p in files:
        if p.is_file():
            v = p.read_text(encoding="utf-8").strip()
            if v:
                return v
    return None


def _jwt_role(key: str) -> str | None:
    """Best-effort decode of a Supabase JWT's `role` claim (anon vs service_role)."""
    try:
        import base64
        payload = key.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload)).get("role")
    except Exception:
        return None


def supabase_key(required: bool = True) -> str | None:
    here = Path(__file__).resolve().parent
    k = _first_key(
        ["SUPABASE_KEY", "SUPABASE_SERVICE_KEY", "SUPABASE_SERVICE_ROLE_KEY"],
        [Path.home() / ".ttml-supabase-key", here / ".supabase-key"],
    )
    if not k and required:
        sys.exit(
            "ERROR: no Supabase key. Set SUPABASE_KEY (or SUPABASE_SERVICE_KEY) env var, "
            "or write the key to ~/.ttml-supabase-key. "
            "blog_posts has RLS enabled, so reads and delete need the service_role key "
            "(Supabase dashboard -> Project Settings -> API -> service_role secret). "
            "The anon/publishable key will connect but RLS hides every row."
        )
    if k and _jwt_role(k) == "anon":
        print(
            "WARNING: this looks like the ANON key. blog_posts has RLS on, so reads "
            "will come back empty and delete will silently no-op. Use the service_role key.",
            file=sys.stderr,
        )
    return k


def publish_key() -> str:
    here = Path(__file__).resolve().parent
    files = [Path.home() / ".ttml-publish-key", here / ".publish-key"]
    if env_file := os.environ.get("TTML_PUBLISH_KEY_FILE", "").strip():
        files.insert(0, Path(env_file))
    k = _first_key(["BLOG_PUBLISH_API_KEY"], files)
    if not k:
        sys.exit(
            "ERROR: no publish API key. Set BLOG_PUBLISH_API_KEY env var "
            "or write it to ~/.ttml-publish-key."
        )
    return k


# ----------------------------------------------------------------------- http io
def _request(url: str, method: str, headers: dict, data: bytes | None = None,
             timeout: int = 30) -> tuple[int, str]:
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError) as e:
        return 0, f"network error: {e}"


def _pg_headers(key: str, extra: dict | None = None) -> dict:
    h = {"apikey": key, "Authorization": f"Bearer {key}", "Accept": "application/json"}
    if extra:
        h.update(extra)
    return h


def pg_get(query: str, key: str) -> list[dict]:
    url = f"{SUPABASE_URL}/rest/v1/{TABLE}?{query}"
    code, body = _request(url, "GET", _pg_headers(key))
    if not (200 <= code < 300):
        sys.exit(f"ERROR: Supabase read failed [{code}]: {body[:300]}")
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        sys.exit(f"ERROR: bad JSON from Supabase: {body[:300]}")


# ------------------------------------------------------------------- subcommands
def cmd_list(args: argparse.Namespace) -> int:
    key = supabase_key()
    cols = "id,slug,title,status,category,published_at,updated_at"
    parts = [f"select={cols}", "order=updated_at.desc", f"limit={args.limit}"]
    if args.status != "all":
        parts.append(f"status=eq.{args.status}")
    if args.category:
        parts.append(f"category=eq.{urllib.parse.quote(args.category)}")
    rows = pg_get("&".join(parts), key)
    if not rows:
        print("(no posts match)")
        return 0
    print(f"{'ID':>4}  {'STATUS':<9}  {'CATEGORY':<22}  SLUG")
    print("-" * 80)
    for r in rows:
        print(f"{r['id']:>4}  {r['status']:<9}  {(r.get('category') or ''):<22}  {r['slug']}")
    print(f"\n{len(rows)} post(s).")
    return 0


def cmd_get(args: argparse.Namespace) -> int:
    key = supabase_key()
    sel = "*" if args.full else "id,slug,title,status,category,excerpt,published_at,updated_at,reading_time_minutes"
    rows = pg_get(f"slug=eq.{urllib.parse.quote(args.slug)}&select={sel}", key)
    if not rows:
        print(f"(no post with slug '{args.slug}')")
        return 1
    row = rows[0]
    if not args.full:
        row.pop("content", None)
    print(json.dumps(row, indent=2, ensure_ascii=False))
    return 0


def _publish_markdown(path: Path, key: str) -> tuple[int, str]:
    headers = {
        "Content-Type": "text/markdown",
        "Authorization": f"Bearer {key}",
        "User-Agent": "ttml-blog-crud/1.0",
    }
    return _request(PUBLISH_ENDPOINT, "POST", headers, data=path.read_bytes())


def _publish_json(payload: dict, key: str) -> tuple[int, str]:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
        "User-Agent": "ttml-blog-crud/1.0",
    }
    return _request(PUBLISH_ENDPOINT, "POST", headers, data=json.dumps(payload).encode("utf-8"))


def cmd_post(args: argparse.Namespace) -> int:
    key = publish_key()
    failures = 0
    for f in args.files:
        p = Path(f).resolve()
        if not p.is_file():
            print(f"  SKIP (not a file): {p}")
            failures += 1
            continue
        code, body = _publish_markdown(p, key)
        ok = 200 <= code < 300
        print(f"  {'OK' if ok else 'FAIL'} [{code}] {p.name}  {body.strip()[:140]}")
        if not ok:
            failures += 1
    return 1 if failures else 0


def cmd_set_status(args: argparse.Namespace) -> int:
    if args.value not in ("published", "draft"):
        sys.exit("ERROR: status must be 'published' or 'draft'.")
    skey = supabase_key()
    rows = pg_get(f"slug=eq.{urllib.parse.quote(args.slug)}&select=*", skey)
    if not rows:
        print(f"(no post with slug '{args.slug}')")
        return 1
    r = rows[0]
    # Re-publish the full row through the API with the new status -> upsert + cache purge.
    payload = {
        "slug": r["slug"],
        "title": r["title"],
        "content": r["content"],
        "excerpt": r.get("excerpt") or "",
        "category": r.get("category") or "general",
        "status": args.value,
        "metaDescription": r.get("meta_description") or "",
        "ogImageUrl": r.get("og_image_url") or "",
        "authorName": r.get("author_name") or "Talk to My Lawyer",
    }
    code, body = _publish_json(payload, publish_key())
    ok = 200 <= code < 300
    print(f"  {'OK' if ok else 'FAIL'} [{code}] {r['slug']} -> {args.value}  {body.strip()[:140]}")
    return 0 if ok else 1


def cmd_delete(args: argparse.Namespace) -> int:
    if not args.yes:
        sys.exit("Refusing to delete without --yes. (Add --safe to unpublish+purge cache first.)")
    skey = supabase_key()
    rows = pg_get(f"slug=eq.{urllib.parse.quote(args.slug)}&select=id,slug,status", skey)
    if not rows:
        print(f"(no post with slug '{args.slug}')")
        return 1

    if args.safe:
        # Flip to draft via the API first: this purges the Cloudflare cache and
        # hides the post publicly BEFORE we remove the row.
        print("  --safe: unpublishing via API to purge cache first...")
        ns = argparse.Namespace(slug=args.slug, value="draft")
        if cmd_set_status(ns) != 0:
            sys.exit("ERROR: failed to unpublish first; aborting delete so cache can't go stale.")

    url = f"{SUPABASE_URL}/rest/v1/{TABLE}?slug=eq.{urllib.parse.quote(args.slug)}"
    code, body = _request(url, "DELETE", _pg_headers(skey, {"Prefer": "return=representation"}))
    ok = 200 <= code < 300
    print(f"  {'OK' if ok else 'FAIL'} [{code}] deleted {args.slug}  {body.strip()[:140]}")
    if ok and not args.safe:
        print("  NOTE: row deleted directly in Postgres. If it was published, the "
              "Cloudflare cache for /blog/<slug> may still serve it briefly. "
              "Use --safe next time to purge first.")
    return 0 if ok else 1


# ------------------------------------------------------------------------- entry
def main() -> int:
    ap = argparse.ArgumentParser(description="CRUD for TTML blog posts.",
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("list", help="list posts (Supabase read)")
    p.add_argument("--status", choices=["published", "draft", "all"], default="all")
    p.add_argument("--category")
    p.add_argument("--limit", type=int, default=100)
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("get", help="show one post by slug (Supabase read)")
    p.add_argument("slug")
    p.add_argument("--full", action="store_true", help="include full content")
    p.set_defaults(func=cmd_get)

    p = sub.add_parser("post", help="create/update from markdown file(s) via publish API")
    p.add_argument("files", nargs="+")
    p.set_defaults(func=cmd_post)

    p = sub.add_parser("set-status", help="publish/unpublish a slug (cache-safe via API)")
    p.add_argument("slug")
    p.add_argument("value", choices=["published", "draft"])
    p.set_defaults(func=cmd_set_status)

    p = sub.add_parser("delete", help="delete a slug (Supabase)")
    p.add_argument("slug")
    p.add_argument("--yes", action="store_true", help="confirm deletion")
    p.add_argument("--safe", action="store_true", help="unpublish via API (purge cache) before deleting")
    p.set_defaults(func=cmd_delete)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
