---
tags:
  - fine-tune
  - gold-standard
  - llm-training
  - ttml-voice
project: TTML Local LLM Fine-Tune
status: active
---
# TTML Fine-Tune Gold Curation Rubric

The model copies exactly what you feed it. Feed it anything with even a trace of the old voice and that trace becomes permanent.

Only finished pieces that already read like the author wrote them to one specific person under real pressure qualify as gold. Everything else teaches the wrong brain.


## What makes a strong target

It passes [[preflight-checklist]] with no boxes left unchecked. It obeys every rule in [[AGENTS.md]] and [[core-principles]]. It follows the exact structure of one [[award-winning-craft]] lens — usually Narrative Feature turning into Service — or the [[03-legal-explainer-pattern]] when the piece is pure explainer.

It contains real stakes, concrete numbers, physical scenes, and an unhedged opinion about why silence costs people money in California disputes. The prose varies in length on purpose. Verbs carry the load. Emotion arrives through what a person stood in or held in their hands.


## Anti-patterns that kill an example instantly

From [[anti-ai-tells]] and [[word-bank]]:

- Every Level 3 construction and word. Most Level 2.

- The fake antithesis and hollow three-part lists. Throat-clear openers. Summary closes.

- Banned vocabulary in any density: delve, tapestry, leverage (verb), robust, seamless, unlock, elevate, myriad, holistic, synergy, ever-evolving, fast-paced, and the rest of the cloud.

- Uniform sentence lengths. Over-hedging. Em-dashes as tic. Announced feelings instead of shown ones. Corporate filler.

If the 30-second scan in anti-ai-tells flags anything, the piece does not go in.


## Signals that must appear

- Opening line drops the reader into a specific bet, scene, or exact fact. No restating the topic as the first words.

- Rhythm that breathes: short sentence. Longer one that carries the weight. Then snap back.

- At least one detail no generic legal site would include — the chalk outline of an island, the Monday that never came, the exact statute number paired with the exact fear.

- Close that turns or lands. The best ones leave the reader with a different number in their head.

- A clear stance: the law already decided in your favor. The only question is whether you will make them feel it.


## Turning raw vault notes into training pairs

Start with a finished post from TTML-Blog or a clean draft from 08-Drafts that already passes the full gate.

Remove only the YAML frontmatter, status tags, and any internal commentary. Do not rewrite a single sentence of the body. Do not improve the voice. Do not add warmth or transitions.

The instruction half of the pair must be narrow and true to the piece's actual move. Write the TTML post about the contractor deposit cap using the kitchen scene and the 10 percent rule as the lever. Not Create a helpful article on contractor disputes.

The output half is the cleaned text verbatim. That pair teaches the model the precise mapping from topic to this texture, this stance, this rhythm.

Dilute the voice once and the entire fine-tune carries the dilution forward.


## The 5-point checklist

Every candidate must clear all five before it touches dataset.jsonl.

1. Anti-AI scan and preflight both return zero defects. No exceptions.

2. Opens with a hook that forces the read. Closes with a line that refuses to summarize.

3. Holds at least one concrete, surprising detail or number that proves a human wrote it for a human in trouble.

4. Obeys mechanics and core principles on every line: subject-verb early, strong verbs, concrete nouns, one idea per sentence, read-aloud clean.

5. Matches the TTML house shape — answer the fear first, name the exact cost of silence, deliver precision that earns the ask — or executes one award-winning lens without compromise.

Pieces like They Priced Your Silence and He Took the Deposit and the Kitchen Was Still Studs set the actual bar. If a new candidate does not feel like it belongs beside them, reject it.

The trainer only ever sees the version of you that you are willing to keep.

This is severe on purpose. Permanent brain updates do not forgive slop.


See also [[voice-fingerprint]] for the target texture, [[mechanics]] for sentence craft, and the three gold examples in the vault that set the floor.


See also the companion curation report and seed examples: [[fine-tune-ttml-gold-curation]].