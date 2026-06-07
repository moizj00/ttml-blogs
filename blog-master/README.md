# TTML Blog Master 🧠

A self-learning blog **reviewer** that runs in Docker. Once a day it reads the
live posts on `talk-to-my-lawyer.com/blog`, critiques them against this vault's
own craft standards (`Clippings/02-Rules/anti-ai-tells.md`,
`Clippings/01-Voice/voice-fingerprint.md`), does a deeper citation-check on the
weakest post, and appends dated remarks to `.claude/memory.md` — then commits and
pushes. Over time the review log becomes feedback that sharpens future drafting.

It does **not** edit published posts or generate blog content. Review + record only.

## What Docker buys you (and what it doesn't)
Docker *packages* the master so it runs the same anywhere. It does **not** by
itself make it "always-on" — that comes from running this container on a host
that stays up (a VPS, a NAS, a home server, or a cloud VM) with `restart: always`.
On an ephemeral/laptop host it only runs while that host is awake.

> No always-on host? Use the **GitHub Action** alternative (below) — zero infra.

## Run it (always-on host)
```bash
cd blog-master
cp .env.example .env          # then edit .env — see "Secrets" below
docker compose up -d --build  # builds the image and starts the daily loop
docker compose logs -f        # watch it
```
It sleeps until `DAILY_UTC_HOUR` (default 13:00 UTC), runs one review, pushes, and
repeats. Set `RUN_ON_START=true` in `.env` to fire one review immediately.

## Run it once (no scheduler — host cron / manual)
```bash
docker build -t ttml-blog-master .
docker run --rm --env-file .env -v ttml-blog-work:/work \
  ttml-blog-master /opt/blog-master/entrypoint.sh
```
Then schedule that `docker run` from the host's own cron/systemd timer if you
prefer the host to own the schedule.

## Secrets (two required)
Put these in `.env` (gitignored — never commit, never paste in chat):

| Var | What | How to get it |
|-----|------|---------------|
| `ANTHROPIC_API_KEY` | Powers the Claude review pass | console.anthropic.com → API keys |
| `GH_TOKEN` | Push access to `moizj00/ttml-blogs` | GitHub → fine-grained PAT → Contents: Read and write |

Optional knobs (`CLAUDE_MODEL`, `DAILY_UTC_HOUR`, `RUN_ON_START`, `BLOG_BRANCH`,
`MAX_TURNS`) are documented in `.env.example`.

## How it works
- `loop.sh` — sleeps until the daily hour, then calls `entrypoint.sh` (no cron, so
  no env-stripping surprises).
- `entrypoint.sh` — syncs the repo via `GH_TOKEN`, runs `claude -p` with
  `review-prompt.md`, then commits + pushes `.claude/memory.md` if it changed.
- `review-prompt.md` — the reviewer's instructions: load standards → rotate to the
  next 3 posts → critique → deep-dive the weakest (citation check) → append a dated
  entry to the review log.

The checkout lives in the `/work` volume so it persists between daily runs.

## Files
```
blog-master/
├── Dockerfile          # node22 + git + claude CLI
├── docker-compose.yml  # always-on service (restart: always)
├── entrypoint.sh       # one review run: sync → review → commit+push
├── loop.sh             # daily scheduler
├── review-prompt.md    # the reviewer's instructions
├── .env.example        # secrets template (copy to .env)
└── README.md
```

## Alternative: GitHub Action (no host needed) ✅ included
A server-free durable schedule lives at `.github/workflows/blog-master.yml`. It
runs the same `review-prompt.md` on a daily cron, committing remarks with the
built-in `GITHUB_TOKEN` — no Docker host required.

Setup (one secret):
1. Repo **Settings → Secrets and variables → Actions → New repository secret**:
   `ANTHROPIC_API_KEY` = your Anthropic key.
2. (Optional) Add a repo **variable** `CLAUDE_MODEL` (e.g. `claude-sonnet-4-6`).
3. Merge this branch so the workflow is on the **default branch** — GitHub only
   fires `schedule:` triggers from the default branch.
4. Run it on demand any time via **Actions → Blog Master — daily review → Run
   workflow**.

Docker vs Action: both run the identical review. Use the **Action** if you want
zero infrastructure; use **Docker** if you'd rather run it on your own host (e.g.
to keep the Anthropic key off GitHub, or run more often than scheduled cron allows).
