#!/usr/bin/env python3
"""
TTML Question Harvester v2 — Playwright scraper, 15-20 blog titles per run.

Sources (priority order):
  1. Reddit        — old.reddit.com browser (403-safe) + keyword search per sub
  2. FindQuestions — homepage form-fill + JS tree-walker (works reliably)
  3. AlsoAsked     — Google PAA question trees
  4. Google News   — trending legal topics

Usage:
  python harvest-questions.py
  python harvest-questions.py --output text --titles 18
  python harvest-questions.py --limit 60

Output:
  - Prints JSON (or text) to stdout
  - Writes .claude/daily-titles-YYYY-MM-DD.md  (15-20 blog titles)
  - Auto-syncs to .claude/all-daily-titles.md via sync-titles-to-master.py
"""

import asyncio, json, re, subprocess, sys, argparse
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

# ── PATHS ──────────────────────────────────────────────────────────────────────
REPO_ROOT  = Path(__file__).parent.parent
CLAUDE_DIR = REPO_ROOT / ".claude"

# ── CONFIG ─────────────────────────────────────────────────────────────────────

# Reddit: subreddits to browse (new posts) + keyword searches per sub
REDDIT_NEW_SUBS = ["legaladvice", "landlord", "Entrepreneur", "California", "legal"]
REDDIT_SEARCHES = [
    ("legaladvice", "california letter"),
    ("legaladvice", "CA demand"),
    ("landlord",    "california notice"),
    ("landlord",    "california eviction"),
    ("California",  "legal letter"),
    ("legal",       "california demand"),
]

# FindQuestions: mix of broad (gets hits) + specific (best quality)
FINDQUESTIONS_TERMS = [
    "demand letter",
    "lawyer letter",
    "legal letter",
    "demand letter california",
    "attorney letter tenant",
    "cease and desist",
    "legal notice california",
    "contractor payment dispute",
    "tenant rights letter",
    "landlord legal notice",
]

ALSOASKED_TERMS = [
    "demand letter california",
    "lawyer letter tenant california",
    "cease and desist letter california",
    "legal letter contractor payment",
]

GOOGLE_NEWS_TERMS = [
    "demand letter california",
    "tenant rights california legal",
    "cease and desist california",
    "contractor dispute california",
]

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")


# ── RELEVANCE FILTERS ──────────────────────────────────────────────────────────

# Must contain at least one TTML-core term
TTML_CORE = [
    "demand letter", "legal letter", "lawyer letter", "attorney letter",
    "cease and desist", "legal notice", "eviction notice", "pay or quit",
    "notice to vacate", "legal action", "small claims", "send a letter",
    "write a letter", "draft a letter", "legal demand",
]

# AND at least one context term
CONTEXT = [
    "california", " ca ", "[ca]", "tenant", "landlord", "rent", "lease",
    "contractor", "freelance", "invoice", "payment", "owed", "unpaid",
    "refund", "deposit", "dispute", "debt", "sue", "sued", "court",
    "dmca", "ip ", "trademark", "copyright", "nda", "contract",
    "employer", "employee", "harassment", "discrimination", "defamation",
    "business", "client", "vendor", "small business",
]

# Hard-exclude noise
EXCLUDE = [
    "cover letter for", "job application", "resume", "hiring manager",
    "applying to", "job seeker", "internship", "job offer", "for every job",
    "child custody", "criminal charge", "dui", "murder", "assault", "drug",
]

def is_ttml_relevant(text: str) -> bool:
    low = text.lower()
    if any(ex in low for ex in EXCLUDE):
        return False
    # FindQuestions / AlsoAsked: require core + context
    has_core    = any(kw in low for kw in TTML_CORE)
    has_context = any(kw in low for kw in CONTEXT)
    return has_core or has_context   # 'or' is intentional — Reddit posts often
                                     # have context without explicit "letter" terms


_CA_RE = re.compile(
    r'(\bcalifornia\b|\[ca\]|\(ca\)|[-/]ca\]|[-/]ca\b|us-ca\b|usa-ca\b'
    r'|los angeles|san francisco|san diego|san jose|sacramento)',
    re.I
)

def is_reddit_relevant(text: str) -> bool:
    """
    Strict two-path filter for Reddit posts:
      Path A: Post contains an explicit TTML core term (demand letter, cease & desist, etc.)
      Path B: Post references California + a legal indicator word

    Both paths hard-exclude job/criminal noise first.
    """
    low = text.lower()
    if any(ex in low for ex in EXCLUDE):
        return False

    # Path A — explicit TTML intent, no location requirement
    if any(kw in low for kw in TTML_CORE):
        return True

    # Path B — must be California AND involve a legal action
    if not _CA_RE.search(text):
        return False
    return any(w in low for w in [
        "legal", "lawyer", "attorney", "court", "letter",
        "notice", "evict", "sue", "sued", "dispute",
        "tenant", "landlord", "lease", "rent",
    ])


def looks_like_question(text: str) -> bool:
    t = text.strip()
    if len(t) < 20 or len(t) > 280:
        return False
    low = t.lower()
    starters = ["how", "what", "can", "does", "is", "why", "when", "who",
                 "which", "will", "do", "are", "should", "could", "my ", "i "]
    return any(low.startswith(w) for w in starters) or t.endswith("?")


def clean(text: str) -> str:
    t = " ".join(text.split()).strip()
    return t if t.endswith("?") else t.rstrip("?.!") + "?"


def to_blog_title(raw: str) -> str:
    t = raw.strip().rstrip("?").strip()
    # Strip Reddit flair brackets like [landlord US-CA], [tenant-US-California], (ca)
    t = re.sub(r'^\[.*?\]\s*', '', t)
    t = re.sub(r'^\(ca\)\s*', '', t, flags=re.I)
    t = t.strip().rstrip("?").strip()
    words = t.split()
    if words:
        words[0] = words[0].capitalize()
    return " ".join(words) + "?"


# ── SCRAPERS ───────────────────────────────────────────────────────────────────

async def scrape_reddit_new(page, subreddit: str) -> list[dict]:
    """Browse new posts on old.reddit.com — server-rendered, no JS needed."""
    results = []
    try:
        url = f"https://old.reddit.com/r/{subreddit}/?sort=new"
        await page.goto(url, timeout=20000, wait_until="domcontentloaded")
        await page.wait_for_timeout(1500)
        for el in await page.query_selector_all("a.title"):
            text = (await el.inner_text()).strip()
            if text and is_reddit_relevant(text) and len(text) > 20:
                results.append({"title": clean(text), "source": f"reddit/r/{subreddit}", "raw": text})
    except Exception as e:
        print(f"[WARN] Reddit new r/{subreddit}: {e}", file=sys.stderr)
    return results


async def scrape_reddit_search(page, subreddit: str, query: str) -> list[dict]:
    """Search within a subreddit on old.reddit.com for California-specific posts."""
    results = []
    try:
        q   = query.replace(" ", "+")
        url = f"https://old.reddit.com/r/{subreddit}/search?q={q}&restrict_sr=1&sort=new"
        await page.goto(url, timeout=20000, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        for el in await page.query_selector_all("a.search-title, a.title"):
            text = (await el.inner_text()).strip()
            if text and is_reddit_relevant(text) and len(text) > 20:
                results.append({"title": clean(text), "source": f"reddit/r/{subreddit}", "raw": text})
    except Exception as e:
        print(f"[WARN] Reddit search r/{subreddit} '{query}': {e}", file=sys.stderr)
    return results


async def scrape_findquestions(page, term: str) -> list[dict]:
    """
    FindQuestions — homepage form fill + JS tree-walker for maximum coverage.
    Falls back to inner_text if evaluate fails.
    """
    results = []
    try:
        await page.goto("https://findquestions.com/", timeout=20000,
                        wait_until="domcontentloaded")
        await page.wait_for_timeout(1500)

        filled = False
        for sel in ['input[type="search"]', 'input[type="text"]',
                    'input[name="q"]', 'input[placeholder]', "input"]:
            try:
                await page.fill(sel, term)
                filled = True
                break
            except Exception:
                continue

        if filled:
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(5000)   # give JS results time to load
        else:
            # Try direct URL as last resort
            q = term.replace(" ", "+")
            await page.goto(f"https://findquestions.com/?q={q}", timeout=18000,
                            wait_until="domcontentloaded")
            await page.wait_for_timeout(4000)

        # JS tree-walker grabs every visible text node
        try:
            lines = await page.evaluate("""
                () => {
                    const out = [];
                    const walker = document.createTreeWalker(
                        document.body, NodeFilter.SHOW_TEXT, null
                    );
                    let node;
                    while ((node = walker.nextNode())) {
                        const t = (node.textContent || "").trim();
                        if (t.length >= 20 && t.length <= 280) out.push(t);
                    }
                    return out;
                }
            """)
        except Exception:
            lines = (await page.inner_text("body")).splitlines()

        for line in lines:
            line = line.strip()
            if looks_like_question(line) and is_ttml_relevant(line):
                results.append({"title": clean(line), "source": "findquestions.com", "raw": line})

    except Exception as e:
        print(f"[WARN] FindQuestions '{term}': {e}", file=sys.stderr)

    return results


async def scrape_alsoasked(page, term: str) -> list[dict]:
    results = []
    try:
        await page.goto("https://alsoasked.com/", timeout=20000, wait_until="domcontentloaded")
        await page.wait_for_timeout(1500)
        for sel in ['input[type="search"]', 'input[type="text"]', 'input[placeholder]', "input"]:
            try:
                await page.fill(sel, term)
                break
            except Exception:
                continue
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(7000)
        for line in (await page.inner_text("body")).splitlines():
            line = line.strip()
            if looks_like_question(line) and is_ttml_relevant(line):
                results.append({"title": clean(line), "source": "alsoasked.com", "raw": line})
    except Exception as e:
        print(f"[WARN] AlsoAsked '{term}': {e}", file=sys.stderr)
    return results


async def scrape_google_news(page, term: str) -> list[dict]:
    results = []
    try:
        q   = term.replace(" ", "+")
        url = f"https://news.google.com/search?q={q}&hl=en-US&gl=US&ceid=US:en"
        await page.goto(url, timeout=20000, wait_until="domcontentloaded")
        await page.wait_for_timeout(3500)
        for sel in ["h3", "h4", "article h2"]:
            for el in await page.query_selector_all(sel):
                text = (await el.inner_text()).strip()
                if text and len(text) > 15 and is_ttml_relevant(text):
                    results.append({"title": text, "source": "google_news", "raw": text})
    except Exception as e:
        print(f"[WARN] Google News '{term}': {e}", file=sys.stderr)
    return results


# ── TITLE GENERATION ───────────────────────────────────────────────────────────

def generate_blog_titles(questions: list[dict], count: int = 18) -> list[str]:
    """Pick best questions, deduplicate, format as blog titles."""
    priority = ["reddit", "findquestions", "alsoasked", "google_news"]
    sorted_qs = sorted(
        questions,
        key=lambda x: next((i for i, p in enumerate(priority) if p in x["source"]), 99)
    )
    seen:   set[str] = set()
    titles: list[str] = []
    for q in sorted_qs:
        if len(titles) >= count:
            break
        t   = to_blog_title(q["title"])
        key = " ".join(t.lower().split()[:6])
        if key not in seen:
            seen.add(key)
            titles.append(t)
    return titles[:count]


# ── DAILY FILE + SYNC ──────────────────────────────────────────────────────────

def write_daily_file(titles: list[str], stats: dict) -> Path:
    CLAUDE_DIR.mkdir(exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    path  = CLAUDE_DIR / f"daily-titles-{today}.md"
    lines = [
        f"# TTML Daily Titles — {today}", "",
        f"harvested_at: {stats['harvested_at']}",
        f"total_harvested: {stats['total']}",
        f"by_source: {stats['by_source']}",
        "", "## Blog Title Candidates", "",
    ]
    for i, t in enumerate(titles, 1):
        lines.append(f"{i}. {t}")
    lines += ["", "---", ""]
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[write] {path} — {len(titles)} titles", file=sys.stderr)
    return path


def run_sync():
    sync = Path(__file__).parent / "sync-titles-to-master.py"
    try:
        r = subprocess.run([sys.executable, str(sync)],
                           capture_output=True, text=True, timeout=30)
        if r.stdout:
            print(r.stdout.strip(), file=sys.stderr)
        if r.returncode != 0:
            print(f"[WARN] sync exited {r.returncode}: {r.stderr[:200]}", file=sys.stderr)
    except Exception as e:
        print(f"[WARN] sync-titles failed: {e}", file=sys.stderr)


# ── MAIN HARVEST ───────────────────────────────────────────────────────────────

async def harvest(limit: int = 60) -> dict:
    all_results: list[dict] = []
    seen: set[str] = set()

    def add(items: list[dict]):
        for item in items:
            key = item["title"].lower()[:80]
            if key not in seen:
                seen.add(key)
                all_results.append(item)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx     = await browser.new_context(user_agent=UA)
        page    = await ctx.new_page()

        # 1 ── REDDIT: browse new posts (old.reddit = no JS, very reliable) ────
        print("[1/4] Scraping Reddit (new posts)...", file=sys.stderr)
        for sub in REDDIT_NEW_SUBS:
            items = await scrape_reddit_new(page, sub)
            add(items)
            print(f"  r/{sub} new → {len(items)} hits", file=sys.stderr)
            await asyncio.sleep(1.2)

        # Reddit: keyword searches for California-specific content
        print("[1/4] Scraping Reddit (California keyword searches)...", file=sys.stderr)
        for sub, query in REDDIT_SEARCHES:
            items = await scrape_reddit_search(page, sub, query)
            add(items)
            print(f"  r/{sub} '{query}' → {len(items)} hits", file=sys.stderr)
            await asyncio.sleep(1.5)

        # 2 ── FINDQUESTIONS: all terms, form-fill approach ────────────────────
        print("[2/4] Scraping FindQuestions (all terms)...", file=sys.stderr)
        # Pre-warm: establish DNS + TLS once before the loop so first term doesn't fail
        try:
            await page.goto("https://findquestions.com/", timeout=15000,
                            wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)
            print("  [pre-warm] findquestions.com ready", file=sys.stderr)
        except Exception as e:
            print(f"  [pre-warm] findquestions.com: {e}", file=sys.stderr)
        for term in FINDQUESTIONS_TERMS:
            items = await scrape_findquestions(page, term)
            add(items)
            print(f"  findquestions '{term}' → {len(items)} hits", file=sys.stderr)
            await asyncio.sleep(2)

        # 3 ── ALSOASKED ───────────────────────────────────────────────────────
        print("[3/4] Scraping AlsoAsked...", file=sys.stderr)
        for term in ALSOASKED_TERMS[:3]:
            items = await scrape_alsoasked(page, term)
            add(items)
            print(f"  alsoasked '{term}' → {len(items)} hits", file=sys.stderr)
            await asyncio.sleep(2)

        # 4 ── GOOGLE NEWS ─────────────────────────────────────────────────────
        print("[4/4] Scraping Google News...", file=sys.stderr)
        for term in GOOGLE_NEWS_TERMS[:3]:
            items = await scrape_google_news(page, term)
            add(items)
            print(f"  news '{term}' → {len(items)} hits", file=sys.stderr)
            await asyncio.sleep(2)

        await browser.close()

    return {
        "harvested_at": datetime.now().isoformat(),
        "total": len(all_results),
        "by_source": {
            "reddit":        sum(1 for r in all_results if "reddit"        in r["source"]),
            "findquestions": sum(1 for r in all_results if "findquestions" in r["source"]),
            "alsoasked":     sum(1 for r in all_results if "alsoasked"     in r["source"]),
            "google_news":   sum(1 for r in all_results if "google_news"   in r["source"]),
        },
        "questions": all_results[:limit],
    }


def main():
    parser = argparse.ArgumentParser(description="TTML Question Harvester v2")
    parser.add_argument("--output",   choices=["json", "text"], default="json")
    parser.add_argument("--limit",    type=int, default=60)
    parser.add_argument("--titles",   type=int, default=18,
                        help="Blog titles to write (15-20, default 18)")
    parser.add_argument("--no-sync",  action="store_true")
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args()
    args.titles = max(15, min(args.titles, 20))  # clamp 15-20

    data   = asyncio.run(harvest(limit=args.limit))
    titles = generate_blog_titles(data["questions"], count=args.titles)

    if not args.no_write:
        write_daily_file(titles, data)
        if not args.no_sync:
            run_sync()

    if args.output == "text":
        print(f"\nHarvested {data['total']} questions | {data['harvested_at']}")
        print(f"By source: {data['by_source']}\n")
        print(f"-- {len(titles)} Blog Titles ------------------")
        for i, t in enumerate(titles, 1):
            print(f"  {i:>2}. {t}")
    else:
        data["blog_titles"] = titles
        print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
