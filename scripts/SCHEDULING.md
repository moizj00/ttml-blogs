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

## Why the repo is canonical now

All pipeline tooling and the queue live in the git repo
(`C:\Users\moizjmj\ttml-blog`): `curate-titles.py`, `uniqueness-gate.py`,
`drip-publish.py`, `blog-queue/`. The generation routine writes plain markdown
straight into `blog-queue/` (no Obsidian-CLI dependency — the queue is a build
staging area, not part of the note graph).

> NOTE — vault/repo divergence to reconcile: the legacy live vault
> `C:\home\moizjmj\Obsidian\root` (144 posts) and this repo's `TTML-Blog/`
> (217 posts) have drifted apart and are not linked. The repo is the fuller,
> canonical copy. Decide whether the vault should be re-synced from the repo or
> retired; until then, treat the repo as source of truth.

## Staggering publish_after

The generator assigns `publish_after` dates so the queue drips naturally — e.g.
3 posts/day across the next ~3 days for a 10-post batch. drip-publish releases
only posts whose `publish_after` (or `date`) is today-or-past, best 3 first
(under-served barrel → priority → longest-waiting).
