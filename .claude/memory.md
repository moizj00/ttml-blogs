# TTML Blogs — Memory

Operational memory for the **ttml-blogs** Obsidian vault (this repo). Scope is
blog work only — vault mechanics, the publishing pipeline, and the Python
tooling. Anything about the `ttml-app` LangGraph/letter pipeline lives in that
separate repo and is intentionally **not** recorded here.

_Last updated: 2026-06-06_

## What this repo is
- An Obsidian vault. Authored content lives under `Clippings/` (numbered pipeline
  `01-Voice` → `08-Drafts`); the vault root holds only daily notes (`YYYY-MM-DD.md`).
- Published/working blog posts live under `TTML-Blog/` (~207 files as of this note).
- Voice/craft contracts: `Clippings/AGENTS.md`, `Clippings/01-Voice/voice-fingerprint.md`,
  `Clippings/02-Rules/anti-ai-tells.md`. File mechanics: root `CLAUDE.md`.

## Blog Python tooling (all of `*.py` here are for blogs)
All stdlib-only unless noted. All currently exist and are up to date.

| File | Purpose | Notes |
|------|---------|-------|
| `scripts/publish-batch.py` | **Canonical** publisher. Pushes blog markdown to the live REST endpoint (`/api/blog/publish`). Modes: explicit files, `--today`, `--date YYYY-MM-DD`, `--json`. | Has a **truncation/completeness gate** — refuses to publish posts that end mid-sentence (the bug that shipped 3 cut-off posts on 2026-06-02); override with `--force`. Flexible blog-dir + API-key lookup (env vars → key files). |
| `scripts/publish-batch-inline.py` | Minimal publisher for *today's* batch only. Globs `TTML-Blog/YYYY-MM-DD-*.md` and POSTs each. | Stripped-down sibling of the canonical script; key only from `BLOG_PUBLISH_API_KEY` or `~/.ttml-publish-key`. |
| `scripts/harvest-questions.py` | **Playwright** scraper → 15–20 blog title candidates per run. Sources: Reddit (old.reddit), FindQuestions, AlsoAsked, Google News. | Requires Playwright (not stdlib-only). Writes `.claude/daily-titles-YYYY-MM-DD.md`, then auto-syncs via `sync-titles-to-master.py`. |
| `scripts/sync-titles-to-master.py` | Merges every `.claude/daily-titles-YYYY-MM-DD.md` into `.claude/all-daily-titles.md` (grouped by date, newest first), then deletes the per-day files. | Idempotent. `--keep-per-day` to retain dailies; `--claude-dir` / `--out` overrides. Single-source-of-truth pattern. |
| `Clippings/08-Drafts/publish-batch.FIXED.py` | **Stale build artifact** — an earlier copy of the publisher. Differs from (is older than) `scripts/publish-batch.py`. | Do not run note ops on it (per CLAUDE.md). `scripts/publish-batch.py` is the one to use; consider this one a historical artifact. |

PowerShell helpers also live in `scripts/` (`boot-readiness.ps1`,
`ttml-keep-awake.ps1`, `register-wake-task.ps1`, `wol-check.ps1`,
`check-keepawake.ps1`) — Windows automation/keep-awake for the publishing box.

## `.claude/` state files (blog memory/state)
- `all-daily-titles.md` — rolling master of harvested title candidates (maintained by `sync-titles-to-master.py`).
- `published-topics.md` — log of topics already published (dedupe source).
- `citation-scores.md` — citation/quality scoring data.
- `theme-weights.json` — theme rotation weights for batch planning.
- `memory.md` — this file.

## Publishing workflow (typical day)
1. (optional) `python scripts/harvest-questions.py` → fresh title candidates into `.claude/`.
2. Draft posts in voice → save into `TTML-Blog/` as `YYYY-MM-DD-<slug>.md`.
3. `python scripts/publish-batch.py --dir TTML-Blog --today` (or `--date …`).
   - The completeness gate blocks truncated posts; fix the ending or `--force`.
4. Commit. (A 30-min git auto-commit also runs — make complete edits.)

## Conventions to remember
- Internal links are `[[wikilinks]]`; external are `[text](url)`.
- Use the `obsidian` CLI for anything touching links/frontmatter/file location
  (the app must be running). Direct file edits only for in-place body text and
  non-note files like everything in `.claude/`.
- Keep `__pycache__/` gitignored; never run note ops on `Clippings/08-Drafts/`
  build artifacts.

## Blog Creation Master — self-learning review loop
**Charter.** A recurring reviewer that reads live posts on
`talk-to-my-lawyer.com/blog`, critiques them against this vault's craft
standards (`Clippings/02-Rules/anti-ai-tells.md`,
`Clippings/01-Voice/voice-fingerprint.md`), and records remarks here so future
drafting improves. Steady-state job each tick = review a *rotating* subset of
posts and append a dated entry below. Heavier tools (`/deep-research`, the
`blog` skill) are invoked **selectively** — only when a review surfaces a gap
worth deeper work — to control cost. Each entry is committed + pushed so
learnings persist.

**How it runs (durable).** Two delivery paths, both running the same
`blog-master/review-prompt.md`:
- **GitHub Action** — `.github/workflows/blog-master.yml`, daily cron, zero infra.
  Needs repo secret `ANTHROPIC_API_KEY`; pushes via the built-in token. (Fires
  only once on the default branch.)
- **Docker** — `blog-master/` container for an always-on host (`restart: always`).
See `blog-master/README.md`. Cadence: **daily, deeper** — each cycle reviews a
rotating subset of 3 posts and does a citation-check deep-dive on the weakest.
(An in-session Monitor heartbeat was the earlier stopgap; superseded by the
container because an in-session loop dies on container reclaim.)

### Review log (newest first)

#### 2026-06-06 — Cycle 1 · dog-bite, friend-loan, ex-employer non-compete
**Verdict: craft discipline is strong; one systemic weakness to fix.**
- ✅ **Hooks** — all three open with a concrete, direct answer, zero
  throat-clearing: _"California dog owners are strictly liable under Civil Code
  § 3342."_ · _"Yes — an attorney demand letter can recover a personal loan in
  California."_ · _"Almost certainly not — and the letter itself may be unlawful."_
- ✅ **Sentence rhythm** — strong fragment ↔ long-compound variation throughout.
- ✅ **AI-tell vocabulary** — effectively absent. The anti-ai-tells gate is holding.
- ✅ **Specificity** — real statutes, dollar caps, deadlines (_"$12,500"_,
  _"CCP § 337"_, _"10–14 days"_).
- ❌ **Endings collapse into boilerplate** — every post ends on the legal
  disclaimer or a bare cross-reference, not a landing. Directly violates
  voice-fingerprint §7 ("Endings turn, not summarize"). **#1 fix.**
- ❌ **Rhetorical repetition** — dog-bite hammers "insurer's first offer" ~3×
  without deepening the point.
- ❌ **Citation density** — the non-compete piece stacks §16600 / 16600.5 /
  16601 with no plain-language bridge between cites.

**Learnings to feed back into drafting:**
1. Require a real **ending turn** before the disclaimer — a concrete last image
   or quiet landing. The disclaimer is boilerplate that *follows* the close, never *is* it.
2. Cap a single tactical theme at ~2 mentions; a third should deepen with a new
   example, not restate.
3. When citing 3+ statutes in a row, bridge each with one plain-language clause.

_Next cycle: rotate to the NDA, HOA/Davis-Stirling, and AB 1482 posts._
