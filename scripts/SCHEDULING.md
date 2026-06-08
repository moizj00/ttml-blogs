# TTML Blog Scheduling — cadence & wiring

> How the daily blog automation runs after the "Quality Behemoth" rewire.
> Managed via the scheduled-tasks system (`list_scheduled_tasks`).

## The problem this fixes

Before: two routines both fired at **09:09 / 09:10**:
- `obsidian-blog-writer` — wrote 10 posts into the live Obsidian vault.
- `vet-review--publish-blogs` — vetted + auto-published them.

Two defects:
1. **Race condition** — the publisher started ~1 minute after the writer, so it
   could begin publishing before all 10 posts were finished writing.
2. **No gate** — publishing was fully automatic; nothing held a post back.

## The new cadence

| Time | Routine | Does | Enabled |
|------|---------|------|---------|
| **06:00** | `obsidian-blog-writer` (generation) | curate titles → enhanced pipeline → write 10 drafts into `blog-queue/` as `status: draft` with staggered `publish_after` dates. Runs the gates. | **on** (generation auto-enabled) |
| **12:00** | `vet-review--publish-blogs` (drip-publish) | `python scripts/drip-publish.py --count 3` → vet + publish the best 3 due posts → move to `_published/`. | **off** (publishing GATED) |

Generation and publishing are now **6 hours apart** — the writer has a long
runway to finish and gate all 10 before any publish window opens. The race is
gone because the two jobs no longer overlap.

## Publishing is gated (by design)

Per the locked decision *"build + auto-enable generation, publishing stays
gated,"* the drip-publish routine is **disabled**. Generation keeps filling the
queue daily; nothing goes live automatically. The queue simply grows a backlog
of vetted drafts.

**To go live**, flip one switch — enable the drip routine:
> `update_scheduled_task(taskId="vet-review--publish-blogs", enabled=true)`

Or release manually any time:
> `python scripts/drip-publish.py --count 3`        (live)
> `python scripts/drip-publish.py --dry-run`        (vet + preview, no POST)

## Where things live vs. where they publish

- **Source / staging**: this git repo (`C:\Users\moizjmj\ttml-blog`) — all
  tooling (`curate-titles.py`, `uniqueness-gate.py`, `drip-publish.py`) and the
  `blog-queue/`. The generation routine writes plain markdown straight into
  `blog-queue/` (no Obsidian-CLI dependency — the queue is a build staging area).
- **Final publish target**: the **ttml-app blog page** at
  `talk-to-my-lawyer.com/blog`. `drip-publish.py` POSTs each released post to the
  app's REST API (`POST /api/blog/publish` → Supabase → CDN purge); the ttml-app
  then serves the live page. The markdown here is the *input* to that API, never
  the live render. See `scripts/PIPELINE.md` → "Final publish target".

> NOTE — the legacy live Obsidian vault `C:\home\moizjmj\Obsidian\root`
> (144 posts) and this repo's `TTML-Blog/` (217 posts) have drifted apart and are
> not linked. This is a **staging** concern only — it does NOT affect the live
> site, which is served by the ttml-app from Supabase regardless of either
> markdown copy. The repo is the fuller, canonical source; decide whether to
> re-sync the vault from it or retire the vault.

## Staggering publish_after

The generator assigns `publish_after` dates so the queue drips naturally — e.g.
3 posts/day across the next ~3 days for a 10-post batch. drip-publish releases
only posts whose `publish_after` (or `date`) is today-or-past, best 3 first
(under-served barrel → priority → longest-waiting).
