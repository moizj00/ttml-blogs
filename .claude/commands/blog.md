---
description: Draft a TTML blog post in my voice and file it as a connected node
argument-hint: <topic>
---
Write a TTML blog post on: $ARGUMENTS

1. Learn from what's working first: `obsidian search` my recent posts and read the 2–3 closest drafts plus `Clippings/01-Voice/Samples`, so this builds on them instead of starting cold.
2. Draft with the ttml-blog-batch skill, in my voice — follow `Clippings/AGENTS.md`, `Clippings/01-Voice/voice-fingerprint.md`, `Clippings/02-Rules/anti-ai-tells.md`, and the matching `Clippings/03-Genres` playbook. Run `Clippings/05-Checklists/preflight-checklist.md` before showing me.
3. Then use the obsidian-vault-ops skill to make the new piece a connected node, not an orphan: link it to its genre playbook (e.g. `[[essays-longform]]`) and add a `[[wikilink]]` entry in `[[_publishing-tracker]]`. Use the `obsidian` CLI for any move or rename — never shell `mv`, and create the destination folder first since `obsidian move` won't.
4. Append a dated line to `Clippings/05-Checklists/learnings.md`: the angle, what landed, what to sharpen next time.
5. Run `obsidian unresolved` to confirm no broken links, then show me the draft.
