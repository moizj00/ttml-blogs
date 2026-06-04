"""Minimal inline publisher for today's batch. Stdlib only."""
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ENDPOINT = "https://talk-to-my-lawyer.com/api/blog/publish"

def load_key():
    if k := os.environ.get("BLOG_PUBLISH_API_KEY", "").strip():
        return k
    p = Path.home() / ".ttml-publish-key"
    if p.is_file():
        k = p.read_text(encoding="utf-8").strip()
        if k:
            return k
    sys.exit("ERROR: no API key found")

def publish(path, key):
    body = path.read_bytes()
    req = urllib.request.Request(
        ENDPOINT,
        data=body,
        method="POST",
        headers={
            "Content-Type": "text/markdown",
            "Authorization": f"Bearer {key}",
            "User-Agent": "ttml-publish-batch-inline/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError) as e:
        return 0, f"network error: {e}"

def main():
    key = load_key()
    today = dt.date.today().strftime("%Y-%m-%d")
    blog_dir = Path(__file__).resolve().parent.parent / "TTML-Blog"
    files = sorted(blog_dir.glob(f"{today}-*.md"))
    if not files:
        sys.exit(f"No files for {today}")
    print(f"Publishing {len(files)} files for {today}...")
    print("-" * 60)
    successes = 0
    failures = []
    for f in files:
        status, body = publish(f, key)
        snippet = body[:200].replace("\n", " ")
        ok = 200 <= status < 300
        marker = "OK " if ok else "ERR"
        print(f"[{marker}] {status:3d}  {f.name}")
        if not ok:
            print(f"     -> {snippet}")
            failures.append((f.name, status, snippet))
        else:
            successes += 1
    print("-" * 60)
    print(f"Result: {successes}/{len(files)} published")
    if failures:
        print(f"Failures: {len(failures)}")
        for name, status, body in failures:
            print(f"  {status} {name}: {body[:150]}")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
