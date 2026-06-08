# TTML Elite Blog Pipeline — the "Quality Behemoth"

> Canonical per-post pipeline. The blog batch (`ttml-blog-batch` skill) and the
> `/blog` command follow this. Goal: a **small number of exceptional, unique,
> fact-verified posts** per day — quality is the headline metric, volume is held
> safe (~10/day generated, drip-published 3/day). Architected to scale later.

Voice/craft contracts this pipeline obeys (do not restate them here — read them):
`Clippings/AGENTS.md` · `Clippings/01-Voice/voice-fingerprint.md` ·
`Clippings/02-Rules/anti-ai-tells.md` · matching `Clippings/03-Genres/*` ·
`Clippings/05-Checklists/preflight-checklist.md`.

---

## Front of funnel (before any writing)

```
harvest-questions.py   →  raw candidate pool (.claude/all-daily-titles.md)
curate-titles.py       →  rich title file (.claude/curated-titles-YYYY-MM-DD.md)
                          Sections A (SHORT) · B (LONG) · C (barrels) · D (pool)
```

The batch reads the **curated** file, never the raw dump. Each pick already
carries `barrel · intent · keyword · slug` and is deduped against every
published slug, the topic ledger, and the drip queue. Pick by **barrel gap**
(Section C "under-served (priority)") first, then search intent.

---

## Per-post pipeline (each stage feeds the next)

| # | Stage | Who | Output |
|---|-------|-----|--------|
| 1 | **Research pack** | LLM + web | Verified CA statutes, dollar caps, deadlines, 2–3 primary sources. Write FROM verified facts, not memory. |
| 2 | **Columnist draft** | `columnist` skill | First full draft in TTML voice, built on the research pack. |
| 3 | **Award-columnist elevation** | `award-columnist` skill | Sharper structure, stronger hook + ending *turn* (voice-fingerprint §7). |
| 4 | **Voice-DNA gate** | `voice-dna` skill | Strips AI-tells; enforces rhythm/fragment variation. Re-run until clean. |
| 5 | **Adversarial editor pass** | LLM (skeptic) | Attacks every thin/generic claim: "prove it or cut it." Forces specificity — statute, number, deadline, or example. |
| 6 | **Fact-verification** | LLM vs research pack | Every statute/figure/deadline checked against stage-1 sources. No unverifiable claim ships. |
| 7 | **Uniqueness gate** | `uniqueness-gate.py` | Cross-checks title + body vs all published posts. Near-twin → re-angle. |
| 8 | **Completeness read-back** | `publish-batch.py` gate | Blocks mid-sentence truncation (the 2026-06-02 bug). |

Stages 1–6 are LLM/judgment work driven by the skills above. Stages 7–8 are
**automated, runnable gates** — they must pass before a post enters the queue.

### Runnable gate commands
```bash
# 7. uniqueness — fail (exit 1) if a draft is a near-duplicate
python scripts/uniqueness-gate.py blog-queue/<file>.md
python scripts/uniqueness-gate.py --dir blog-queue        # whole queue at once

# 8. completeness — fail (exit 1) if any post ends mid-sentence
python scripts/publish-batch.py <file>.md      # gate runs automatically
```

A post is **queue-ready** only when stages 1–6 are done AND `uniqueness-gate.py`
and the completeness gate both exit 0.

---

## SEO frontmatter (every post)

Required keys — the publish API parses these; do not rename (see CLAUDE.md):

```yaml
---
title: "<headline — unique, includes the target keyword naturally>"
slug: <kebab-case, matches filename after the date prefix>
description: "<≤155 chars meta description — unique per post, not a title echo>"
excerpt: "<2–3 sentence answer-first summary; front-load the direct answer>"
date: YYYY-MM-DD                # the intended publish date (drip release date)
author: "Talk to My Lawyer Team"
category: <one of the 10 canonical barrels>
tags: ["<keyword>", "california", ...]
status: draft                   # draft while queued; drip-publish flips to published
og_image_url: auto:generate
---
```

Body conventions that raise AI-citation odds (see `agent-seo-audit` skill):
- **Answer-first opening** — direct answer in sentence one, no throat-clearing.
- **Quantify** — real statutes (§), dollar caps, day-counts. Specificity is the moat.
- **FAQ block** — 2–4 `## Question?` H2s with tight answers (PAA / AI-overview bait).
- **Internal links** — 1–3 `[anchor](/blog/<slug>)` to related TTML posts + a link
  to the relevant service page. Strengthens the graph and dedups topic overlap.
- **Ending turn, not summary** — a concrete last image/landing *before* the
  disclaimer. The legal disclaimer follows the close; it is never the close.

---

## Barrels (mirror `.claude/theme-weights.json`)

`demand-letters · cease-and-desist · intellectual-property · landlord-tenant ·
eviction-notices · employment-disputes · contract-disputes · consumer-complaints
· pricing-and-roi · general`

Balance toward under-served barrels (Section C of the curated file). As of the
last audit the gaps were **cease-and-desist, eviction-notices, employment-disputes**.

---

## Where a post goes next

Queue-ready posts are written to `blog-queue/` as `status: draft` with a
`publish_after` date, then released by `drip-publish.py` (3/day). See
`scripts/SCHEDULING.md` for cadence and `drip-publish.py --help` for release
mechanics.

## Final publish target — the ttml-app blog page

This repo is **source/staging only**. The live blog is the **ttml-app blog page**
(`talk-to-my-lawyer.com/blog`). Publishing always goes through the app's REST
API — `POST https://talk-to-my-lawyer.com/api/blog/publish` (the app's
`server/blogPublishRoute.ts`), which upserts into Supabase, purges the CDN cache,
and recalculates reading time. The app then serves the page from Supabase.

So the markdown files here never render the live site directly — they are the
input to that API. `publish-batch.py` and `drip-publish.py` both POST to it
(override with `TTML_PUBLISH_ENDPOINT`). This is why the post never "appears"
just by living in `TTML-Blog/`: it is live only once the API has accepted it.
