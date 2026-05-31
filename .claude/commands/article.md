---
description: Draft a standalone article or essay in my voice and file it as a connected node
argument-hint: <topic>
---
Write a standalone article or essay on: $ARGUMENTS

1. Learn from what's working first: `obsidian search` my recent pieces and read the 2–3 closest ones plus `Clippings/01-Voice/Samples`, so this builds on them instead of starting cold.
2. Draft with the columnist skill in my voice — or the award-columnist skill if I've called this a flagship piece. Follow `Clippings/AGENTS.md`, `Clippings/01-Voice/voice-fingerprint.md`, `Clippings/02-Rules/anti-ai-tells.md`, and the matching `Clippings/03-Genres` playbook (essays-longform, business-professional, creative-narrative, or social-shortform). Run `Clippings/05-Checklists/preflight-checklist.md` before showing me.
3. Then use the obsidian-vault-ops skill to make it a connected node, not an orphan: link it to its genre playbook and add a `[[wikilink]]` entry in `[[_publishing-tracker]]`. Use the `obsidian` CLI for any move or rename — never shell `mv`, and create the destination folder first since `obsidian move` won't.
4. Append a dated line to `Clippings/05-Checklists/learnings.md`: the angle, what landed, what to sharpen next time.
5. Run `obsidian unresolved` to confirm no broken links, then show me the draft.
