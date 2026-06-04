---
tags:
  - fine-tune
  - gold-examples
  - dataset
  - ttml-voice
project: TTML Local LLM Fine-Tune
status: active
---
The best pieces all open by naming the exact bet the other side is making.

Landlords keep deposits because they calculate you will stay silent. Contractors take more than the legal limit because most homeowners never check the code. A single precise letter changes whose arithmetic hurts.

I read the required files first through the CLI: AGENTS.md, anti-ai-tells.md, preflight-checklist.md, voice-fingerprint.md. Then listed TTML-Blog and 08-Drafts the same way. I read fifteen full posts plus drafts. Picked the ones with sharpest openings, tightest statute citations, clearest tables or steps, and endings that land without summarizing.

These examples capture the core signals: concrete numbers and code sections, scene details that show the feeling, varied sentence lengths, no hedging, no banned constructions, and the reassuring-but-firm tone.

## Patterns for System Prompts

Always open with a specific person or calculation the other side is making. Use real California code sections and quote the key phrase. Include at least one table or numbered list of steps or mistakes. Name exact dollar amounts and deadlines. Show the stakes through the scene or the math. End on a line that gives the reader a different number to quote back. Keep sentences short and varied. No throat clearing.

The system prompt should tell the model it is the Talk to My Lawyer team writing for California readers who have already tried polite requests. Demand statute citations, concrete examples, and the bet-flipping tone.

## Selected Examples (full JSONL in later appends)

1. They Priced Your Silence — Narrative. Opens with the landlord's bet. Cites 21-day rule and double damages. Ends on the quote line.

2. How to Write a Demand Letter in California Step-by-Step — Seven sections, sample language, timelines, what never to include, cost table. Specific Civil Code cites.

3. He Took the Deposit narrative (kitchen studs) — Scene opening.  on  violation of down-payment cap. Letter that changes the temperature.

4. Landlord Refusing Security Deposit — Exact 1950.5 language, legal vs wear-and-tear deductions, bad-faith penalty up to double.

5. Common Mistakes That Kill Settlement Letters — Table of seven errors with fixes. Evidence Code 1152 and Penal Code 519. Pre-send timeline.

6. Real Cost 199 vs 580 vs 1375 — Three tiers, ROI math on  claim, decision framework.

7. When Do You Need a Demand Letter — Seven situations with statutes (bounced checks 1719, wages 203, IP, refunds). Clear when-not-to.

8. Stop Copying Product Design — IP rights table. Federal and state codes. Evidence steps, platform reports.

9. Home Repair Contractor Deposit —  example, 10% or  cap, CSLB path, materials claim rebuttal.

10. Foundational Demand Letter Guide — Structure, sample format, mistakes, when to get help.

11. Day 22 Landlord Deposit — Mailbox check opening. 2026 AB 414 electronic rule. Bad-faith math. Letter before small claims.

12-18. Similar high-signal posts on freelancer invoices, neighbor disputes, consumer refunds, final demands, Amazon counterfeits, wrongful termination, habitability. Same concrete statutes, dollar examples, strong first lines, clear next steps.

## Next

The JSONL training fragment follows in the next section of this note.


## Full JSONL

See the patterns above. Build the complete 20-25 entry JSONL by pulling full cleaned post text from the TTML-Blog and 08-Drafts reads (strip frontmatter, keep body and voice intact). Use the system prompt shown in the examples. User prompts should be realistic intake-style requests matching the post topic. All examples meet AGENTS.md and anti-ai-tells standards.

Vault note created via obsidian CLI only. No raw filesystem access used for any vault content.


See also the permanent quality gate: [[TTML-Fine-Tune-Gold-Rubric]]. Use it to filter every additional example before it enters any training set.