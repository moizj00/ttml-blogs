# Publishing Tracker — TTML Blog

> Posts written from the Obsidian writing KB. **Not yet live** — see the honest status below.

## Status legend
⬜ draft · 🟡 ready-to-commit · ✅ committed (Action syncing) · 🌐 live

## Log

| Date | Title | Lens | Category | Law-checked | Status |
|---|---|---|---|---|---|
| 2026-05-30 | Day 22: Landlord Misses the 21-Day Deposit Deadline | Service/Explainer | landlord-tenant | ✅ §1950.5 + AB 414 | 🟡 ready-to-commit |
| 2026-05-30 | The Billable Hour Is a Tax on Your Anxiety | Argument | pricing-and-roi | n/a (opinion) | 🟡 ready-to-commit |
| 2026-05-30 | He Took the Deposit and the Kitchen Was Still Studs | Narrative→Service | contract-disputes | ✅ $1k/10% cap | 🟡 ready-to-commit |

Slugs (live URLs once committed + synced):
- /blog/landlord-deposit-21-day-deadline-demand
- /blog/billable-hour-vs-flat-fee-legal
- /blog/contractor-took-deposit-disappeared-california

## Honest status — why they're not live yet
I could **read** your `moizj00/ttml-app` repo but the GitHub connection here is **read-only** ("403 Resource not accessible by integration"), so I can't commit. The REST publisher path is also out because `BLOG_PUBLISH_API_KEY` isn't in this sandbox. So publishing needs one action from you.

## The publish path that works (no API key needed)
Your repo auto-publishes: any `*.md` committed to `blog/` on `main` triggers `sync-blog.yml`, which runs `scripts/sync-blog.ts` and upserts into Postgres. I reverse-engineered that script and **formatted the three files to match its frontmatter exactly** (`title`, `slug`, `category`, `status: published`, `date`, `excerpt`, `description`, `author`). They're ready to drop in.

Repo-ready files: `08-Drafts/repo-ready/`
- `2026-05-30-landlord-deposit-21-day-deadline-demand.md`
- `2026-05-30-billable-hour-vs-flat-fee-legal.md`
- `2026-05-30-contractor-took-deposit-disappeared-california.md`

### Option A — commit from your machine (git)
```powershell
cd path\to\ttml-app
copy "C:\Users\Tesla Laptops\Obsidian\root\Clippings\08-Drafts\repo-ready\2026-05-30-*.md" blog\
git add blog\2026-05-30-*.md
git commit -m "blog: 3 posts (deposit 21-day, flat-fee, contractor) from writing KB"
git push origin main
```
The Action runs on push; check the Actions tab for the green "Sync Blog Posts → Database" run. Live within a minute or two.

### Option B — let me commit for you
Reconnect GitHub here with **write** scope (or give me a repo with push access), and I'll push the three files directly. Say the word.

### Option C — REST publisher
Use the rebuilt `08-Drafts/publish-batch.FIXED.py` with `BLOG_PUBLISH_API_KEY` set on your machine. (The installed skill copy is truncated/broken; the repo copy is fine.)

## ⚠️ SEO note — possible keyword overlap (your call)
There may already be a deposit post in the repo's `blog/` targeting a similar query. Two pages competing for one keyword can split ranking. The new one is differentiated (the "day 22" narrative + the 2026 AB 414 update). If you want, I can diff against the existing post and either merge or sharpen the angle — tell me.

## Next up (ideas)
- Investigative lens: how a bad-faith deposit penalty gets calculated (case-walkthrough).
- Service: "Your invoice is 60 days late — the letter that gets clients to pay."
- Personal/founder: why TTML exists (best once you add your own voice samples).
