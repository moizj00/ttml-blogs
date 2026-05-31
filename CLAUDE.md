# Vault operating guide (CLAUDE.md)

This is an Obsidian vault. Operate it through the official `obsidian` CLI so the note
graph stays consistent. The conventions below are what this vault actually uses.

> Two contracts. For *how to write* here (voice, anti-AI rules, craft), defer to
> `Clippings/AGENTS.md`, `Clippings/01-Voice/voice-fingerprint.md`, and
> `Clippings/02-Rules/anti-ai-tells.md`. This file governs only *file mechanics*.

## Detected conventions
- Organizational scheme: numbered pipeline under `Clippings/` (`01-Voice` → `08-Drafts`);
  vault root holds only daily notes. Not PARA/Zettelkasten.
- Internal links: `[[wikilinks]]` (156 in use, zero internal markdown). External URLs: `[text](url)`.
- Frontmatter — no single schema; match the note's type:
  - Hand-authored KB notes (most of `Clippings/`): none. `# H1` + optional `>` summary, then prose.
  - Web-clipped docs: title, source, author, published, created, description, tags: [clippings].
  - TTML posts (`Clippings/08-Drafts/repo-ready/`): title, slug, category, status, date,
    author, excerpt, description — fixed by the publish pipeline; don't rename these keys.
- Tags: frontmatter `tags:` lists, lowercase; only `clippings` is in active use.
- Daily notes: vault root, `YYYY-MM-DD.md`, no template. Append with `obsidian daily:append`.
- Structure: prefer flat; deepest path is 3 levels (`Clippings/07-Foundation/Library/`). Flag anything deeper.

## How to operate this vault
PREFER the official `obsidian` CLI for ANY operation that touches links, frontmatter, or
file location — it routes through Obsidian's API and keeps wikilinks intact:
- Move / rename a note      → obsidian move ...            (NEVER shell `mv` — breaks backlinks)
- Delete a note             → CLI delete, after confirming with me  (NEVER `rm`)
- Create a linked note      → obsidian create ...          (then link it into the graph)
- Append to daily note      → obsidian daily:append content="..."
- Set a frontmatter property → obsidian property:set ...   (NEVER regex-rewrite YAML)
- Search                    → obsidian search query="..." format=json
- Read a note               → obsidian read file="..."
Use direct file edits ONLY for in-place body-text changes that don't move the file or alter links.

## Rules
- The Obsidian app must be RUNNING for the CLI to work (binary: C:\Program Files\Obsidian\Obsidian.com).
- `obsidian move` will NOT create a destination folder (errors ENOENT) — create the folder first.
- NEVER modify anything in `.obsidian/` — app config, not content.
- `Clippings/08-Drafts/` mixes prose with build artifacts (publish-batch.FIXED.py, repo-ready/,
  __pycache__/). Never run note ops on those; keep __pycache__/ gitignored.
- Two writers touch this folder: Obsidian Sync + a 30-min git auto-commit. Make complete edits;
  pause sync for big reorganizations.
- Keep every new note linked into the graph; an orphan is a note I'll never find again.
- Undo button: clean git tree before structural batches (`git reset --hard vaultops-baseline`);
  run `obsidian unresolved` after and fix or revert anything broken before calling it done.
- Match the conventions above rather than imposing new ones.
