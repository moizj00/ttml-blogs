---
epoch: 1780249406217
modelKey: "google/gemini-2.5-flash|openrouterai"
topic: "Question Mark Query"



tags:
  - copilot-conversation
---
<errorChunk>Something went wrong. Please check if you have set your API key.
Path: Settings > copilot plugin > Basic Tab > Set Keys.
Or check model config
Error Details: API key is not provided for the embedding model: openai/text-embedding-3-small|openrouterai</errorChunk>
**user**: ?
[Context: Notes: Clippings/05-Checklists/learnings.md]
[Timestamp: 2026/05/31 10:43:26]

**ai**: This note, "learnings," is a log for tracking what worked and what didn't after creating content or editing AI output. The goal is to identify patterns that can then be incorporated into [[voice-fingerprint]] and [[anti-ai-tells]].

It includes a log section where entries are added with a date, context, and what to do more or less of. When a pattern appears three or more times, it's promoted to a "Promoted patterns" section and added to the relevant rule file.

Currently, there's one entry in the log:
- 2026-05-30 — KB created — baseline scaffold. Next: add real samples to sharpen voice.

There are no promoted patterns yet.
[Timestamp: 2026/05/31 10:43:28]

**user**: what can you see in vault
[Context: Notes: Clippings/05-Checklists/learnings.md]
[Timestamp: 2026/05/31 10:43:59]

**ai**: The vault contains a comprehensive knowledge base for writing, particularly focused on generating human-like, high-quality content that avoids common AI tells. It's structured with several key components:

**Core Directives & Rules:**
- **[[AGENTS]]**: This is the primary operating contract for any AI agent, outlining 10 rules for writing, hard bans on certain constructions and vocabulary, and a self-editing process. The prime directive is to write indistinguishably from a human and in the user's voice [^1].
- **[[voice-fingerprint]]**: This file is meant to define the user's unique writing style, including a one-line voice statement, default register (e.g., conversational-professional, first person, contractions), sentence DNA, preferred words, words to avoid, how emotion is handled, structural habits, and things that are "NOT me" [^2]. It's designed to be populated from writing samples [^2].
- **[[anti-ai-tells]]**: This is a critical file for de-robotizing AI output, listing banned constructions (e.g., fake antithesis, throat-clearing openers), banned vocabulary (e.g., "delve," "tapestry," "leverage"), and banned rhythms/textures (e.g., uniform sentence length, over-hedging) [^3]. It also includes a severity-weighted forbidden list and a 30-second scan for quick draft triage [^3].
- **[[preflight-checklist]]**: A quality gate to be run before delivering any piece, covering voice & soul, anti-AI scan, mechanics, and structure & fit [^4].

**Organizational Structure:**
- The vault uses a numbered pipeline under `Clippings/` (e.g., `01-Voice` to `08-Drafts`) [^5].
- The `00 START HERE` note provides an overview and reading order for agents [^6].

**Content & Resources:**
- **`01-Voice/Samples/`**: This folder is intended to hold 3-5 writing samples from the user to help the agent learn their voice fingerprint [^7]. It also suggests creating an `_anti-samples.md` file for writing to avoid [^7].
- **`03-Genres/`**: Contains playbooks for different writing formats, such as:
    - **[[social-shortform]]**: Rules for X/Twitter, LinkedIn, and captions, emphasizing strong hooks and conciseness [^8].
    - **[[business-professional]]**: Guidelines for emails, proposals, and reports, focusing on clarity, conciseness, and plain English [^9].
    - **[[creative-narrative]]**: Focuses on making the reader *feel* something through experience, emphasizing showing over telling, scene craft, and rhythm [^10].
- **`04-Examples/before-after`**: Provides concrete rewrites demonstrating how to apply the rules, showing AI-default versions versus human versions [^11].
- **`05-Checklists/learnings.md`**: A log for tracking what worked and didn't, with patterns to be folded back into `voice-fingerprint` and `anti-ai-tells` [^12].
- **`06-Reference/word-bank.md`**: A quick lookup for word choice, including banned words, filler to cut, plain-English swaps, and corporate-speak to avoid [^13].
- **`07-Foundation/`**: This section contains "The Canon" or "Foundation-10," which are 10 articles every blog-writing agent should study [^14]. It includes:
    - **[[01-pg-write-like-you-talk]]**: A breakdown of Paul Graham's essay on writing plainly and conversationally [^15].
    - **[[03-legal-explainer-pattern]]**: A pattern study for high-converting legal explainers, outlining a structural backbone for blog posts [^16].
    - Slots for the user's own best pieces and famous pieces they admire [^14].
    - **[[_library-index]]**: An index to a wider "Library" of ~100 curated best-in-class pieces across various categories like essay craft, legal explainers, persuasion, social, and narrative [^17]. Specific catalogs include:
        - **[[legal-explainers]]**: Examples from Nolo, FindLaw, and other sources for plain-language legal content [^18].
        - **[[persuasion-copy]]**: Examples from advertising legends and modern frameworks on how to move a reader to act [^19].
        - **[[social-shortform-exemplars]]**: Examples of effective social media content and hooks [^20].
        - **[[narrative-voice]]**: Examples of literary nonfiction and story craft [^21].
        - **[[essay-craft]]**: A collection of essays and writing craft resources, including Paul Graham, Morgan Housel, and classic authors [^22].
- **`08-Drafts/`**: Contains draft articles, including three ready-to-publish blog posts:
    - [[2026-05-30-landlord-deposit-21-day-deadline-demand]]
    - [[2026-05-30-contractor-took-deposit-disappeared-california]]
    - [[_publishing-tracker]] shows the status of these drafts and explains publishing options [^23].
- **[[award-winning-craft]]**: Distilled from the [[Pulitzer Award-Winning Nonfiction Style Kit]], this outlines 6 lenses (Narrative Feature, Personal Essay, Argument, Investigative, Service, Literary Journalism) for high-craft pieces, each with specific hooks, structures, and evidence modes [^24].

#### Sources
[^1]: [[AGENTS]]
[^2]: [[voice-fingerprint]]
[^3]: [[anti-ai-tells]]
[^4]: [[preflight-checklist]]
[^5]: [[CLAUDE]]
[^6]: [[00 START HERE]]
[^7]: [[_README]]
[^8]: [[social-shortform]]
[^9]: [[business-professional]]
[^10]: [[creative-narrative]]
[^11]: [[before-after]]
[^12]: [[learnings]]
[^13]: [[word-bank]]
[^14]: [[_index]]
[^15]: [[01-pg-write-like-you-talk]]
[^16]: [[03-legal-explainer-pattern]]
[^17]: [[_library-index]]
[^18]: [[legal-explainers]]
[^19]: [[persuasion-copy]]
[^20]: [[social-shortform-exemplars]]
[^21]: [[narrative-voice]]
[^22]: [[essay-craft]]
[^23]: [[_publishing-tracker]]
[^24]: [[award-winning-craft]]
[Timestamp: 2026/05/31 10:44:17]

**user**: Explain {} in simple terms that a 5-year-old would understand:
    1. Use basic vocabulary
    2. Include simple analogies
    3. Break down complex concepts
    Return only the simplified explanation.
[Context: Notes: Clippings/05-Checklists/learnings.md]
[Timestamp: 2026/05/31 10:45:48]

**ai**: Imagine you have a special drawing book where you draw pictures. This note is like a special diary for your drawing book.

Every time you finish a drawing, you write down what you liked about it and what you didn't like. Maybe you liked the colors you used, or maybe you didn't like how a tree looked.

If you keep liking the same thing (like drawing happy suns) or keep not liking the same thing (like drawing wobbly houses), you write it down in a special "rules" book. This helps you remember to draw more happy suns and try to draw better houses next time!

So, this diary helps you get better and better at drawing over time, by remembering what works and what doesn't.
[Timestamp: 2026/05/31 10:46:02]

**user**: I understand the articles and blogs now tell me what is what grounding the truth in actuals
[Context: Notes: Clippings/05-Checklists/learnings.md]
[Timestamp: 2026/05/31 10:46:56]

**ai**: 
<errorChunk>Something went wrong. Please check if you have set your API key.
Path: Settings > copilot plugin > Basic Tab > Set Keys.
Or check model config
Error Details: API key is not provided for the embedding model: openai/text-embedding-3-small|openrouterai</errorChunk>
[Timestamp: 2026/05/31 11:40:57]