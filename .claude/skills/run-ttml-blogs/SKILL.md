---
name: run-ttml-blogs
description: Run, test, and drive the TTML blog publishing toolchain — publish blog markdown to the live site, sync harvested title files, run the completeness/truncation gate, and smoke-test the pipeline safely against a local mock. Use when asked to run ttml-blogs, publish a blog post, test the publish pipeline, or sync daily titles.
---

# Run TTML Blogs

This repo is an Obsidian vault whose "app" is a set of **stdlib-only Python CLIs**
in `scripts/` that publish blog posts to `talk-to-my-lawyer.com` and manage
harvested title state. There is no server and no GUI. You drive it by running the
CLIs; the safe way to exercise the publisher without hitting production is the
**`smoke.sh` driver**, which redirects it to a local mock endpoint.

All paths below are relative to the repo root.

> ⚠️ **`publish-batch.py` posts to PRODUCTION by default.** Its endpoint defaults
> to `https://talk-to-my-lawyer.com/api/blog/publish`. For any test/dry run, set
> `TTML_PUBLISH_ENDPOINT` to a local URL (the driver does this for you). Only run
> against the real endpoint when you actually intend to publish.

## Prerequisites
- `python3` (3.11 verified). The publisher and title-sync are **stdlib only** —
  no `pip install` needed.
- Title harvesting only (optional, heavier): `pip install playwright && playwright
  install chromium`, plus outbound network to Reddit/Google. **Not verified in
  this container** (Playwright absent; scraper is network-gated).

## Run (agent path) — the driver
The driver runs the real `publish-batch.py` and `sync-titles-to-master.py`
against a local mock endpoint and temp fixtures. It never touches production.

```bash
bash .claude/skills/run-ttml-blogs/smoke.sh
```

Expected tail (verified this container):
```
== 5. sync-titles-to-master.py merges + collapses daily files ==
  PASS sync-titles exits 0
  PASS master file built with merged titles
  PASS per-day file deleted after merge

RESULT: 6 passed, 0 failed
```
It checks: `--help` works; a **complete** post publishes (200 via mock); a
**truncated** post is blocked by the completeness gate (exit 1, no network); and
`sync-titles` merges daily title files into `all-daily-titles.md` then deletes
the per-day files.

## Publish with the buffer (recommended) — `publish-queue.py`
Use this instead of `publish-batch.py` for routine publishing. It guarantees that
**written-but-unpublished posts are never lost**: it tracks publish state in a
ledger (`.claude/publish-ledger.json`) and on every run **drains the buffer
(pending posts) oldest-first**, marking a post published only after a 2xx. A post
that fails or is blocked by the truncation gate **stays in the buffer** for the
next run instead of being discarded.

First-time setup (once) — baseline existing posts so they aren't re-published:
```bash
python3 scripts/publish-queue.py --seed          # no network; marks current posts published
```
Then, routine publishing (drains pending first, then new posts — they're all just
"pending"):
```bash
python3 scripts/publish-queue.py --status        # show buffer (no network)
python3 scripts/publish-queue.py                 # drain: publish all pending, oldest-first
```
- Exit 0 only when the buffer is fully drained; exit 1 if anything is still pending
  (failed/blocked) so automation knows to retry.
- Refuses to drain with no ledger (prevents mass re-publish of the 200+ posts).
- Honors the same `TTML_PUBLISH_ENDPOINT` / `BLOG_PUBLISH_API_KEY` as
  `publish-batch.py`, and the same completeness gate (`--force` to skip).
- `TTML_PUBLISH_LEDGER` overrides the ledger path (used by the smoke test).

> Make `publish-queue.py` the single publishing entry point. If you publish via
> `publish-batch.py` directly, the ledger won't record it and the queue may later
> treat that post as pending again.

## Direct invocation — individual tools
Run a single CLI directly (set a dummy key + local endpoint to stay off prod):

```bash
# Publish flow against a mock (safe). Needs BOTH env vars set:
export BLOG_PUBLISH_API_KEY=dummy
export TTML_PUBLISH_ENDPOINT=http://127.0.0.1:8799/publish   # have a server listening
python3 scripts/publish-batch.py path/to/2026-01-01-some-post.md

# Completeness gate only (no publish): a truncated file exits 1 before any POST.
python3 scripts/publish-batch.py --help

# Merge harvested daily titles into the master log (operates on .claude/):
python3 scripts/sync-titles-to-master.py --claude-dir /tmp/sometitles --keep-per-day
```

## Run (human / real publish path)
To actually publish to the live site, provide a **real** key and leave the
endpoint at its production default. Prefer the buffer-aware queue so any
previously-unpublished posts go out first:

```bash
export BLOG_PUBLISH_API_KEY=<real key>          # or ~/.ttml-publish-key
python3 scripts/publish-queue.py --seed         # first time only (baseline)
python3 scripts/publish-queue.py                # drain buffer → publish pending
```
Legacy one-shot (no buffer tracking): `python3 scripts/publish-batch.py --dir
TTML-Blog --today`. Both honor `--force` to skip the truncation gate. (Not run
here — they write to production.)

## Gotchas (learned by running it)
- **Key is loaded before anything else.** `publish-batch.py` calls `load_key()`
  first; with no `BLOG_PUBLISH_API_KEY` (or key file) it exits `ERROR: no API key`
  before the completeness gate or any file work. Set a dummy key for dry runs.
- **Default endpoint is production.** Always export `TTML_PUBLISH_ENDPOINT` for
  tests. The driver points it at a local `http.server` mock.
- **Completeness gate blocks "truncated" posts.** A post whose last non-empty
  line doesn't end in terminal punctuation (`.!?…"’”')]*_\``) is refused with
  exit 1 — this is the guard added after 3 cut-off posts shipped on 2026-06-02.
  Override with `--force`.
- **`sync-titles-to-master.py` is destructive by default.** After merging it
  **deletes** the `daily-titles-YYYY-MM-DD.md` files it consumed. Pass
  `--keep-per-day` to retain them. It writes/reads inside `.claude/`.
- **`harvest-questions.py` imports Playwright at module top**, so even `--help`
  fails with `ModuleNotFoundError: No module named 'playwright'` until you install
  it. It also scrapes Reddit/Google — needs external network.

## Troubleshooting
| Symptom | Fix |
|---|---|
| `ERROR: no API key` | Export `BLOG_PUBLISH_API_KEY` (a dummy value is fine for dry runs against the mock). |
| Post unexpectedly hit production | You didn't set `TTML_PUBLISH_ENDPOINT`; it defaults to the live site. |
| `BLOCKED: ...look incomplete/truncated` | The body ends mid-sentence. Restore the ending, or pass `--force` if intentional. |
| `ModuleNotFoundError: No module named 'playwright'` | `pip install playwright && playwright install chromium` (only needed for `harvest-questions.py`). |
