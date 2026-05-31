---
title: "Obsidian Flavored Markdown"
source: "https://obsidian.md/help/obsidian-flavored-markdown"
author:
published:
created: 2026-05-30
description: "Importer - Obsidian Help"
tags:
  - "clippings"
---
Obsidian strives for maximum capability without breaking any existing formats. As a result, we use a combination of flavors of [Markdown](https://obsidian.md/help/syntax).

Obsidian supports [CommonMark](https://commonmark.org/), [GitHub Flavored Markdown](https://github.github.com/gfm/), and [LaTeX](https://www.latex-project.org/).

> [!tip]- Markdown inside HTML
> Obsidian does not render Markdown syntax inside HTML elements. This is an intentional design choice for performance optimization and to keep parser complexity low when managing large documents.
> 
> For example, Markdown formatting like `**bold**` or `` `code` `` will not be processed inside `<div>`, `<span>`, `<table>`, or any other HTML tags.
> 
> ```md
> <div>
> This **will not** be bold.
> </div>
> ```

### Supported Markdown extensions

| Syntax | Description |
| --- | --- |
| `[[Link]]` | [Internal links](https://obsidian.md/help/links) |
| `![[Link]]` | [Embed files](https://obsidian.md/help/embeds) |
| `![[Link#^id]]` | [Block references](https://obsidian.md/help/links#Link%20to%20a%20block%20in%20a%20note) |
| `^id` | [Defining a block](https://obsidian.md/help/links#Link%20to%20a%20block%20in%20a%20note) |
| `[^id]` | [Footnotes](https://obsidian.md/help/syntax#Footnotes) |
| `%%Text%%` | [Comments](https://obsidian.md/help/syntax#Comments) |
| `~~Text~~` | [Strikethroughs](https://obsidian.md/help/syntax#Bold,%20italics,%20highlights) |
| `==Text==` | [Highlights](https://obsidian.md/help/syntax#Bold,%20italics,%20highlights) |
| ` ``` ` | [Code blocks](https://obsidian.md/help/syntax#Code%20blocks) |
| `- [ ]` | [Incomplete task](https://obsidian.md/help/syntax#Task%20lists) |
| `- [x]` | [Completed task](https://obsidian.md/help/syntax#Task%20lists) |
| `> [!note]` | [Callouts](https://obsidian.md/help/callouts) |
| (see link) | [Tables](https://obsidian.md/help/advanced-syntax#Tables) |