---
title: "TTML Blog — Obsidian Authoring + REST Publishing Workflow"
note: "Internal process note. Not a published article (status: draft)."
status: draft
---

# TTML Blog — Obsidian Authoring + REST Publishing

Articles are **authored in this Obsidian vault**, then published **directly to the live site via the REST API**. No git push, no GitHub Actions in the publish path.

```
Author in Obsidian (TTML-Blog/<YYYY-MM-DD-slug>.md)
        |
        v
publish-batch.py  ->  POST https://talk-to-my-lawyer.com/api/blog/publish   (Authorization: Bearer <key>)
        |
        v
blog_posts table (live DB)   [upsert by slug]
        |
        v
tRPC blogRouter.list / getBySlug  ->  BlogIndex.tsx / BlogPost.tsx (live site)
```

## Where things live

- **Authoring (here):** `C:\Users\Tesla Laptops\Obsidian\root\TTML-Blog\`
- **Publisher script:** `C:\Users\moizjmj\ttml-app-work\scripts\publish-batch.py` (stdlib Python, no pip)
- **API endpoint:** `POST https://talk-to-my-lawyer.com/api/blog/publish` (override via `TTML_PUBLISH_ENDPOINT`)
- **API key:** auto-detected from `BLOG_PUBLISH_API_KEY` env var, or `~/.ttml-publish-key` (already saved on this machine)

## Per-run procedure

1. **Pre-flight topics:** read `.claude/published-topics.md` in the repo, pick the weekday theme, avoid duplicates.
2. **Author each article into the vault** at `TTML-Blog/<YYYY-MM-DD-slug>.md` (filesystem write; slugs/filenames space-free kebab-case), then `obsidian reload` to index.
3. **Manage/verify via the `obsidian` CLI:** `obsidian files folder=TTML-Blog total`, `obsidian property:set ...`, `obsidian read path=...`, `obsidian unresolved total`.
4. **Publish via REST** (run from the no-space `scripts\` dir; pass the vault folder via env var because the vault path has spaces):
   ```bat
   cd /d C:\Users\moizjmj\ttml-app-work\scripts
   set "TTML_BLOG_DIR=C:\Users\Tesla Laptops\Obsidian\root\TTML-Blog"
   python publish-batch.py --date YYYY-MM-DD
   ```
   The endpoint upserts by slug, so re-running is safe.
5. **Record** the titles in `.claude/published-topics.md` and **commit the vault** (git).

## Hard rules (Windows)

- The `obsidian` CLI splits args on spaces and ignores quotes — never pass a space-containing argument. Keep paths space-free; write body text via the filesystem.
- For git/shell on the vault, use the 8.3 short path `C:\Users\TESLAL~1\Obsidian\root` (no spaces) — the `cmd` wrapper mishandles quoted space paths.
- Never `obsidian delete` by an ambiguous name — it can resolve to the wrong file.
- The **obsidian-git** plugin is disabled; it was auto-discarding untracked files. Commit new posts promptly; re-enable obsidian-git only if you understand its auto-backup settings.
- TTML posts use `/blog/<slug>` Markdown links (not wikilinks). Never paste the API key into chat.
