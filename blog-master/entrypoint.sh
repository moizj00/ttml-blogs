#!/usr/bin/env bash
# One blog-review run: sync repo → Claude reviews → commit + push memory.md.
set -euo pipefail

: "${ANTHROPIC_API_KEY:?set ANTHROPIC_API_KEY (Anthropic API key)}"
: "${GH_TOKEN:?set GH_TOKEN (GitHub token with push access to the blog repo)}"

REPO="${BLOG_REPO:-moizj00/ttml-blogs}"
BRANCH="${BLOG_BRANCH:-master}"
WORKDIR="${WORKDIR:-/work/repo}"
AUTH_URL="https://x-access-token:${GH_TOKEN}@github.com/${REPO}.git"

echo "[blog-master] $(date -u +%FT%TZ) review run for ${REPO}@${BRANCH}"

# Clone once, then keep the checkout in the mounted volume across runs.
if [ ! -d "$WORKDIR/.git" ]; then
  git clone --depth 50 "$AUTH_URL" "$WORKDIR"
fi
cd "$WORKDIR"
git remote set-url origin "$AUTH_URL"
git config user.name  "${GIT_AUTHOR_NAME:-blog-master-bot}"
git config user.email "${GIT_AUTHOR_EMAIL:-blog-master@users.noreply.github.com}"
git fetch --depth 50 origin "$BRANCH"
git checkout -B "$BRANCH" "origin/${BRANCH}"
git reset --hard "origin/${BRANCH}"

echo "[blog-master] running Claude review pass…"
set +e
claude -p "$(cat /opt/blog-master/review-prompt.md)" \
  --permission-mode acceptEdits \
  --allowedTools "WebFetch,WebSearch,Read,Edit,Grep,Glob" \
  ${CLAUDE_MODEL:+--model "$CLAUDE_MODEL"} \
  --max-turns "${MAX_TURNS:-50}"
rc=$?
set -e
[ "$rc" -ne 0 ] && echo "[blog-master] WARN: claude exited $rc"

if git diff --quiet -- .claude/memory.md; then
  echo "[blog-master] no changes to .claude/memory.md — nothing to push."
  exit 0
fi

git add .claude/memory.md
git commit -m "Blog Master: daily review $(date -u +%F)"
for i in 1 2 3 4; do
  if git push origin "$BRANCH"; then
    echo "[blog-master] pushed review for $(date -u +%F)."
    exit 0
  fi
  echo "[blog-master] push failed; retry $i"; sleep $((2**i))
done
echo "[blog-master] ERROR: push failed after retries."; exit 1
