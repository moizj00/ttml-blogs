#!/usr/bin/env bash
# Smoke test / driver for the TTML blog publishing toolchain.
#
# Exercises the real CLIs (scripts/publish-batch.py, scripts/sync-titles-to-master.py)
# against a LOCAL mock HTTP endpoint and temp fixtures — it NEVER touches the
# production blog (talk-to-my-lawyer.com). Exits non-zero if any check fails.
#
# Usage:  bash .claude/skills/run-ttml-blogs/smoke.sh
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SCRIPTS="$REPO_ROOT/scripts"
PY="${PYTHON:-python3}"
WORK="$(mktemp -d)"
MOCK_PID=""
trap '[ -n "$MOCK_PID" ] && kill "$MOCK_PID" 2>/dev/null; rm -rf "$WORK"' EXIT

pass=0; fail=0
check() { # want got label
  if [ "$1" = "$2" ]; then echo "  PASS $3"; pass=$((pass+1));
  else echo "  FAIL $3 (got '$2' want '$1')"; fail=$((fail+1)); fi
}

echo "== 1. publish-batch.py --help =="
$PY "$SCRIPTS/publish-batch.py" --help >/dev/null 2>&1
check 0 "$?" "publish-batch.py --help exits 0"

echo "== 2. start local mock publish endpoint =="
cat > "$WORK/mock.py" <<'PYEOF'
from http.server import BaseHTTPRequestHandler, HTTPServer
import sys
class H(BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get('content-length', 0)); self.rfile.read(n)
        self.send_response(200); self.send_header('Content-Type','application/json'); self.end_headers()
        self.wfile.write(b'{"ok":true,"mock":true}')
    def log_message(self, *a): pass
HTTPServer(('127.0.0.1', int(sys.argv[1])), H).serve_forever()
PYEOF
PORT=8799
$PY "$WORK/mock.py" "$PORT" & MOCK_PID=$!
sleep 1
export TTML_PUBLISH_ENDPOINT="http://127.0.0.1:$PORT/publish"
export BLOG_PUBLISH_API_KEY="dummy-key-for-smoke"   # gate runs before any network call

echo "== 3. publish a COMPLETE post (expect OK via mock) =="
mkdir -p "$WORK/blog"
cat > "$WORK/blog/2026-01-01-sample-complete.md" <<'MDEOF'
---
title: "Sample Complete Post"
slug: sample-complete-post
date: 2026-01-01
---
# Sample Complete Post
This is a short but complete body. It ends on a real sentence.
MDEOF
out=$($PY "$SCRIPTS/publish-batch.py" "$WORK/blog/2026-01-01-sample-complete.md" 2>&1); rc=$?
echo "$out" | sed 's/^/    /'
check 0 "$rc" "complete post publishes (exit 0 via mock)"

echo "== 4. truncated post is BLOCKED by completeness gate (expect exit 1, no network) =="
cat > "$WORK/blog/2026-01-01-truncated.md" <<'MDEOF'
---
title: "Truncated Post"
slug: truncated-post
date: 2026-01-01
---
# Truncated Post
This sentence just stops in the middle of
MDEOF
out=$($PY "$SCRIPTS/publish-batch.py" "$WORK/blog/2026-01-01-truncated.md" 2>&1); rc=$?
echo "$out" | sed 's/^/    /'
check 1 "$rc" "truncated post blocked (exit 1)"

echo "== 5. sync-titles-to-master.py merges + collapses daily files =="
CDIR="$WORK/claude"; mkdir -p "$CDIR"
cat > "$CDIR/daily-titles-2026-01-01.md" <<'MDEOF'
harvested_at: 2026-01-01
total_harvested: 2
1. First sample title
2. Second sample title
MDEOF
$PY "$SCRIPTS/sync-titles-to-master.py" --claude-dir "$CDIR" >/dev/null 2>&1
check 0 "$?" "sync-titles exits 0"
grep -q "First sample title" "$CDIR/all-daily-titles.md" 2>/dev/null
check 0 "$?" "master file built with merged titles"
[ ! -f "$CDIR/daily-titles-2026-01-01.md" ]
check 0 "$?" "per-day file deleted after merge"

echo "== 6. publish-queue.py buffer (seed → pending → drain; blocked stays buffered) =="
export TTML_PUBLISH_LEDGER="$WORK/ledger.json"
QDIR="$WORK/qblog"; mkdir -p "$QDIR"
cat > "$QDIR/2026-06-01-old.md" <<'MDEOF'
---
title: "Old"
---
# Old
A complete older post.
MDEOF
python3 "$SCRIPTS/publish-queue.py" --dir "$QDIR" >/dev/null 2>&1
check 1 "$?" "queue refuses to drain without a ledger (no mass re-publish)"
python3 "$SCRIPTS/publish-queue.py" --dir "$QDIR" --seed >/dev/null 2>&1
check 0 "$?" "queue --seed baselines existing posts"
cat > "$QDIR/2026-06-05-good.md" <<'MDEOF'
---
title: "Good"
---
# Good
A complete new post.
MDEOF
printf -- '---\ntitle: "T"\n---\n# T\nstops mid sentence at' > "$QDIR/2026-06-04-trunc.md"
out=$(python3 "$SCRIPTS/publish-queue.py" --dir "$QDIR" 2>&1); rc=$?
echo "$out" | sed 's/^/    /'
check 1 "$rc" "drain exits 1 while a post stays buffered"
echo "$out" | grep -q "\[OK\] 200 2026-06-05-good.md"; check 0 "$?" "good post published via mock"
python3 "$SCRIPTS/publish-queue.py" --dir "$QDIR" --status 2>&1 | grep -q "pending: 2026-06-04-trunc.md"
check 0 "$?" "truncated post still buffered after drain (not discarded)"

echo
echo "RESULT: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
