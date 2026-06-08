#!/usr/bin/env python3
"""
curate-titles.py — TTML Title Curation Engine. Stdlib only (no pip install).

The harvester (harvest-questions.py) dumps a RAW, noisy pool of candidate
questions into .claude/all-daily-titles.md: out-of-state posts, off-topic
chatter, near-duplicates day-to-day, and zero structure. That is garbage-in at
the front of the funnel. This engine turns that raw pool into the *rich title
file* the blog batch reads — clean, deduped, on-niche, SEO-rewritten, and
barrel-balanced so every post is genuinely unique.

Pipeline:
  1. Load raw candidates        (.claude/all-daily-titles.md, newest dates first)
  2. Filter to on-niche intent  (CA legal-letter; drop out-of-state + noise)
  3. Dedup                       against published slugs, the topic ledger, and
                                 anything already sitting in the drip queue
  4. Assign barrel + keyword + intent for each survivor
  5. SEO-rewrite the raw question into a publishable working title
  6. Score + balance            (under-served barrels float to the top)
  7. Emit the rich title file   .claude/curated-titles-YYYY-MM-DD.md
                                 Sections A (SHORT picks) · B (LONG picks)
                                 · C (barrel coverage) · D (ranked pool)

Dedup ledger:
  .claude/published-slugs.txt is the durable slug ledger (survives blog/ cleanup).
  On first run it is auto-seeded from every slug in TTML-Blog/.

Usage:
  python curate-titles.py                       # read master log, write today's file
  python curate-titles.py --from-file X.md      # curate a specific raw file
  python curate-titles.py --short 5 --long 5    # picks per section (default 5/5)
  python curate-titles.py --pool 40             # size of Section D ranked pool
  python curate-titles.py --stdout              # also print the file to stdout
  python curate-titles.py --seed-only           # just (re)seed the slug ledger
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

# ── PATHS ────────────────────────────────────────────────────────────────────
REPO_ROOT   = Path(__file__).resolve().parent.parent
CLAUDE_DIR  = REPO_ROOT / ".claude"
BLOG_DIR    = REPO_ROOT / "TTML-Blog"
QUEUE_DIR   = REPO_ROOT / "blog-queue"
MASTER_LOG  = CLAUDE_DIR / "all-daily-titles.md"
SLUG_LEDGER = CLAUDE_DIR / "published-slugs.txt"
TOPICS_LOG  = CLAUDE_DIR / "published-topics.md"

# ── BARREL TAXONOMY ──────────────────────────────────────────────────────────
# Canonical 10 barrels (mirrors .claude/theme-weights.json). Order = specificity:
# the first barrel whose cues match wins, so put narrow barrels before broad ones.
BARRELS: dict[str, list[str]] = {
    "cease-and-desist": [
        "cease and desist", "cease-and-desist", "stop using my", "defamation",
        "slander", "libel", "harassment letter", "stop contacting",
    ],
    "intellectual-property": [
        "trademark", "copyright", "dmca", "patent", "trade dress", "infringe",
        "counterfeit", "knockoff", "brand name", "logo", "stole my design",
        "cybersquat", "domain name", "trademark application", "uspto",
    ],
    "eviction-notices": [
        "eviction", "evict", "notice to vacate", "pay or quit", "3-day notice",
        "three day notice", "unlawful detainer", "notice to quit",
    ],
    "landlord-tenant": [
        "landlord", "tenant", "security deposit", "deposit", "lease", "rent ",
        "renter", "habitability", "repairs", "mold", "sublet", "roommate",
    ],
    "employment-disputes": [
        "employer", "employee", "wrongful termination", "fired", "unpaid wages",
        "final paycheck", "non-compete", "noncompete", "severance", "overtime",
        "wage theft", "hostile work", "discrimination", "retaliation",
    ],
    "contract-disputes": [
        "breach of contract", "contractor", "construction", "didn't finish",
        "down payment", "vendor", "service agreement", "subcontractor",
        "unfinished work", "deposit refund", "did not complete",
    ],
    "demand-letters": [
        "demand letter", "money owed", "owes me", "unpaid invoice", "collect",
        "pay me back", "loan", "won't pay", "wont pay", "money back", "reimburse",
    ],
    "consumer-complaints": [
        "refund", "warranty", "defective", "scam", "chargeback", "consumer",
        "false advertising", "deceptive", "lemon", "return policy", "overcharged",
    ],
    "pricing-and-roi": [
        "how much", "cost of", "worth it", " vs ", "versus", "fee", "price of",
        "cheaper", "do i need a lawyer", "diy",
    ],
    "general": [],  # fallback
}

# Suggested target keyword per barrel (used when no stronger phrase is present).
BARREL_KEYWORD: dict[str, str] = {
    "cease-and-desist": "cease and desist letter california",
    "intellectual-property": "trademark infringement california",
    "eviction-notices": "eviction notice california",
    "landlord-tenant": "security deposit california",
    "employment-disputes": "final paycheck california",
    "contract-disputes": "breach of contract letter california",
    "demand-letters": "demand letter california",
    "consumer-complaints": "refund demand letter california",
    "pricing-and-roi": "demand letter cost california",
    "general": "legal letter california",
}

# ── RELEVANCE FILTERS ────────────────────────────────────────────────────────
TTML_CORE = [
    "demand letter", "legal letter", "lawyer letter", "attorney letter",
    "cease and desist", "legal notice", "eviction notice", "pay or quit",
    "notice to vacate", "legal action", "small claims", "send a letter",
    "write a letter", "draft a letter", "legal demand", "trademark", "copyright",
    "dmca", "security deposit", "unpaid invoice", "breach of contract",
    "wrongful termination", "final paycheck", "refund",
]
CONTEXT = [
    "california", "tenant", "landlord", "rent", "lease", "contractor",
    "freelance", "invoice", "payment", "owed", "unpaid", "refund", "deposit",
    "dispute", "debt", "sue", "sued", "court", "trademark", "copyright", "nda",
    "contract", "employer", "employee", "wages", "business", "client", "vendor",
]
EXCLUDE = [
    "cover letter for", "job application", "resume", "hiring manager",
    "applying to", "job seeker", "internship", "job offer", "for every job",
    "child custody", "criminal charge", "dui", "murder", "assault", "drug",
    "proofread", "off-topic and anecdotal", "read before commenting",
    "governor", "election", "judicial removal", "emancipate",
]

# California signals.
_CA_RE = re.compile(
    r'(\bcalifornia\b|\bca\b|\[ca\]|\(ca\)|us[\s\-]*ca\b|[-/]ca\]|'
    r'los angeles|san francisco|san diego|san jose|sacramento|orange county|'
    r'oakland|fresno|long beach|bay area)',
    re.I,
)

# Other US states / countries — if one of these is flagged and California is NOT,
# the post is about the wrong jurisdiction (TTML is California-only).
_OTHER_STATE_RE = re.compile(
    r'\bus[\s\-]*('
    r'tx|texas|fl|florida|ny|new york|nj|il|illinois|pa|penn|oh|ohio|ga|georgia|'
    r'nc|sc|va|virginia|wa|washington|az|arizona|co|colorado|mi|michigan|mn|mo|'
    r'missouri|ks|kansas|ct|connecticut|tn|tennessee|ma|md|wi|in|al|ky|or|nv|ut|'
    r'ok|ar|ia|ms|ne|nm|wv|id|hi|me|nh|ri|mt|de|sd|nd|ak|vt|wy'
    r')\b',
    re.I,
)
_NON_US_RE = re.compile(r'\b(canada|england|uk|ontario|alberta|london|australia)\b', re.I)
# Bare spelled-out non-CA states (multi-letter only, so no false hits on short words).
_BARE_STATE_RE = re.compile(
    r'\b(texas|florida|new york|new jersey|illinois|pennsylvania|ohio|georgia|'
    r'virginia|washington|arizona|colorado|michigan|minnesota|missouri|kansas|'
    r'connecticut|tennessee|massachusetts|maryland|wisconsin|indiana|alabama|'
    r'kentucky|oregon|nevada|utah|oklahoma|arkansas|iowa|mississippi|nebraska)\b',
    re.I,
)

# Personal-anecdote chatter that is NOT a blog topic with search intent.
CHATTER = [
    "mentorship", "ask anything", "banking option", "anticipation for",
    "killing me", "thoughts on", "advice?", "should i be worried", "kick rocks",
    "struggle with explaining", "moving into rental", "buy property in one",
    "smells like", "rip the house apart", "ai generated content", "first contract",
]

# Search-intent signals: a real informational/transactional query.
_INTENT_STARTERS = ("how ", "what ", "can ", "do ", "does ", "is ", "are ",
                    "should ", "when ", "why ", "who ", "which ", "where ")
_LEGAL_NOUNS = [
    "letter", "notice", "demand", "evict", "deposit", "refund", "sue", "lawsuit",
    "small claims", "claim", "contract", "wage", "paycheck", "trademark",
    "copyright", "dmca", "cease", "lien", "breach", "invoice", "settlement",
    "statute of limitation", "non-compete", "severance", "habitability",
]


def has_topic_intent(text: str) -> bool:
    """A publishable topic, not anecdotal chatter: real query + a legal noun."""
    low = text.lower().strip()
    if any(c in low for c in CHATTER):
        return False
    has_core = any(kw in low for kw in TTML_CORE)
    has_noun = any(n in low for n in _LEGAL_NOUNS)
    is_query = low.startswith(_INTENT_STARTERS) or low.endswith("?")
    # Core term alone qualifies; otherwise need a legal noun AND a question framing.
    return has_core or (has_noun and is_query)


def is_wrong_jurisdiction(text: str) -> bool:
    """True if the post is clearly about a non-California jurisdiction."""
    has_ca = bool(_CA_RE.search(text))
    if has_ca:
        return False
    return bool(_OTHER_STATE_RE.search(text) or _NON_US_RE.search(text)
                or _BARE_STATE_RE.search(text))


def is_on_niche(text: str) -> bool:
    low = text.lower()
    if any(ex in low for ex in EXCLUDE):
        return False
    if is_wrong_jurisdiction(text):
        return False
    if not has_topic_intent(text):
        return False
    has_core = any(kw in low for kw in TTML_CORE)
    has_context = any(kw in low for kw in CONTEXT)
    return has_core or has_context


# ── CLASSIFICATION ───────────────────────────────────────────────────────────
def assign_barrel(text: str) -> str:
    low = " " + text.lower() + " "
    for barrel, cues in BARRELS.items():
        if barrel == "general":
            continue
        if any(cue in low for cue in cues):
            return barrel
    return "general"


def target_keyword(text: str, barrel: str) -> str:
    """Pick the strongest matching core phrase, else the barrel default."""
    low = text.lower()
    best = ""
    for phrase in sorted(BARRELS.get(barrel, []) + TTML_CORE, key=len, reverse=True):
        p = phrase.strip()
        if p and p in low and len(p) > len(best):
            best = p
    if not best:
        return BARREL_KEYWORD[barrel]
    kw = best
    if "california" not in kw:
        kw += " california"
    return kw


def classify_intent(text: str) -> str:
    low = text.lower()
    if any(w in low for w in [" vs ", "versus", "difference between", " or ", "cheaper", "worth it", "how much", "cost"]):
        return "comparison"
    if any(low.startswith(w) for w in ["how to", "how do", "how can"]) or \
       any(w in low for w in ["how to write", "how to send", "template", "what to do", "respond to", "what do i do", "steps to", "how long"]):
        return "transactional"
    return "informational"


# ── SEO TITLE REWRITE ────────────────────────────────────────────────────────
_FLAIR_RE = re.compile(r'^\s*[\[\(][^\]\)]*[\]\)]\s*[:\-]?\s*', re.I)
_SMALL_WORDS = {"a", "an", "and", "as", "at", "but", "by", "for", "in", "of",
                "on", "or", "the", "to", "vs", "with"}


def _titlecase(s: str) -> str:
    words = s.split()
    out = []
    for i, w in enumerate(words):
        lw = w.lower()
        if lw in ("i", "i'm", "i've", "i'll", "i'd"):   # first person always capitalized
            out.append("I" + w[1:])
        elif i != 0 and lw in _SMALL_WORDS:
            out.append(lw)
        elif w.isupper() and len(w) <= 5:   # keep TM, CA, DMCA, USPTO, ROI, ADU
            out.append(w)
        else:
            out.append(w[:1].upper() + w[1:])
    return " ".join(out)


def seo_rewrite(raw: str, barrel: str) -> str:
    """
    Heuristic SEO working-title. The writing pipeline finalizes the headline;
    this gives the batch a clean, on-brand starting point (never raw Reddit text).
    """
    t = raw.strip()
    # strip leading subreddit flair like "[Tenant US-CA]" or "(CA)"
    prev = None
    while prev != t:
        prev = t
        t = _FLAIR_RE.sub("", t)
    t = t.strip().rstrip("?.! ").strip()
    t = re.sub(r'\s+', ' ', t)
    # collapse first-person framing into a topic ("my landlord won't" -> "landlord won't")
    t = re.sub(r'^(can|do|does|is|are|should|how do|how can)\s+i\b', '', t, flags=re.I).strip()
    if not t:
        t = BARREL_KEYWORD[barrel]
    # ensure a California anchor for SEO
    if "california" not in t.lower() and not _CA_RE.search(t):
        t = f"{t} in California"
    return _titlecase(t)


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return re.sub(r"-{2,}", "-", s)


# ── DEDUP SOURCES ────────────────────────────────────────────────────────────
def slug_from_frontmatter(path: Path) -> str | None:
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines()[:15]:
            m = re.match(r"\s*slug:\s*(.+?)\s*$", line)
            if m:
                return m.group(1).strip().strip('"').strip("'")
    except Exception:
        pass
    return None


def published_slugs() -> set[str]:
    slugs: set[str] = set()
    if BLOG_DIR.is_dir():
        for p in BLOG_DIR.glob("*.md"):
            s = slug_from_frontmatter(p)
            if s:
                slugs.add(s)
            # also the date-stripped filename stem as a fallback slug
            stem = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", p.stem)
            slugs.add(stem)
    return slugs


def queued_slugs() -> set[str]:
    slugs: set[str] = set()
    if QUEUE_DIR.is_dir():
        for p in QUEUE_DIR.rglob("*.md"):
            s = slug_from_frontmatter(p)
            if s:
                slugs.add(s)
            slugs.add(re.sub(r"^\d{4}-\d{2}-\d{2}-", "", p.stem))
    return slugs


def ledger_slugs() -> set[str]:
    if SLUG_LEDGER.is_file():
        return {ln.strip() for ln in SLUG_LEDGER.read_text(encoding="utf-8").splitlines()
                if ln.strip() and not ln.startswith("#")}
    return set()


def seed_ledger() -> int:
    """Seed/refresh the durable slug ledger from everything published so far."""
    CLAUDE_DIR.mkdir(exist_ok=True)
    existing = ledger_slugs()
    live = {s for s in published_slugs() if s}
    merged = sorted(existing | live)
    header = ("# published-slugs.txt — durable dedup ledger for curate-titles.py\n"
              "# One slug per line. Survives blog/ file cleanup. Auto-seeded from TTML-Blog/.\n")
    SLUG_LEDGER.write_text(header + "\n".join(merged) + "\n", encoding="utf-8")
    return len(merged)


def topic_tokens() -> set[str]:
    """Coarse topic fingerprints from the published-topics ledger (title lines)."""
    toks: set[str] = set()
    if TOPICS_LOG.is_file():
        for ln in TOPICS_LOG.read_text(encoding="utf-8", errors="replace").splitlines():
            ln = ln.strip().lstrip("-* ").strip()
            if len(ln) > 15 and not ln.startswith("#"):
                toks.add(" ".join(slugify(ln).split("-")[:6]))
    return toks


# ── RAW CANDIDATE LOADING ────────────────────────────────────────────────────
def load_raw_candidates(from_file: Path | None) -> list[str]:
    src = from_file or MASTER_LOG
    if not src.is_file():
        sys.exit(f"ERROR: raw title source not found: {src}\n"
                 f"Run harvest-questions.py first, or pass --from-file.")
    out: list[str] = []
    for line in src.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"\s*\d+\.\s+(.*\S)\s*$", line)   # "12. <question>"
        if m:
            out.append(m.group(1).strip())
    return out


# ── SCORING ──────────────────────────────────────────────────────────────────
def specificity_bonus(text: str) -> int:
    low = text.lower()
    b = 0
    if _CA_RE.search(text):
        b += 3
    if re.search(r"\$[\d,]+|\b\d{3,}\b|\bsection\b|§|\bccp\b|\bcivil code\b", low):
        b += 2   # dollar figures / statutes = concrete
    if 30 <= len(text) <= 160:
        b += 1
    return b


def score(cand: dict, barrel_counts: Counter) -> float:
    # Under-served barrels float up: fewer published in that barrel => bigger bonus.
    published = barrel_counts.get(cand["barrel"], 0)
    gap_bonus = max(0.0, 6.0 - published * 0.18)
    intent_bonus = {"transactional": 2.0, "comparison": 1.5, "informational": 1.0}[cand["intent"]]
    low = cand["raw"].lower()
    core_bonus = 3.0 if any(kw in low for kw in TTML_CORE) else 0.0
    return gap_bonus + intent_bonus + core_bonus + specificity_bonus(cand["raw"])


# ── CURATION ─────────────────────────────────────────────────────────────────
def curate(raw: list[str]) -> list[dict]:
    blocked = published_slugs() | queued_slugs() | ledger_slugs()
    topics = topic_tokens()
    seen_keys: set[str] = set()
    out: list[dict] = []
    for raw_title in raw:
        if not is_on_niche(raw_title):
            continue
        barrel = assign_barrel(raw_title)
        title = seo_rewrite(raw_title, barrel)
        slug = slugify(title)
        # near-duplicate key: first 6 slug tokens
        key = " ".join(slug.split("-")[:6])
        if key in seen_keys or key in topics:
            continue
        if slug in blocked or any(slug in b or b in slug for b in blocked if len(b) > 12):
            continue
        seen_keys.add(key)
        out.append({
            "raw": raw_title,
            "title": title,
            "slug": slug,
            "barrel": barrel,
            "keyword": target_keyword(raw_title, barrel),
            "intent": classify_intent(raw_title),
        })
    return out


def current_barrel_counts() -> Counter:
    counts: Counter = Counter()
    if BLOG_DIR.is_dir():
        for p in BLOG_DIR.glob("*.md"):
            try:
                for line in p.read_text(encoding="utf-8", errors="replace").splitlines()[:15]:
                    m = re.match(r"\s*category:\s*(.+?)\s*$", line)
                    if m:
                        counts[m.group(1).strip().strip('"').strip("'").lower()] += 1
                        break
            except Exception:
                pass
    return counts


def balance_pick(cands: list[dict], n: int, taken: set[str]) -> list[dict]:
    """Round-robin across barrels (rarest first) so no single barrel dominates."""
    by_barrel: dict[str, list[dict]] = {}
    for c in cands:
        if c["slug"] in taken:
            continue
        by_barrel.setdefault(c["barrel"], []).append(c)
    # order barrels by how few candidates remain published (rarest barrel first)
    counts = current_barrel_counts()
    order = sorted(by_barrel.keys(), key=lambda b: counts.get(b, 0))
    picks: list[dict] = []
    while len(picks) < n and any(by_barrel.values()):
        for b in order:
            if by_barrel.get(b):
                c = by_barrel[b].pop(0)
                picks.append(c)
                taken.add(c["slug"])
                if len(picks) >= n:
                    break
    return picks


# ── OUTPUT ───────────────────────────────────────────────────────────────────
def render(short: list[dict], long: list[dict], pool: list[dict],
           counts: Counter, stats: dict) -> str:
    today = date.today().isoformat()
    L: list[str] = []
    L.append(f"# TTML Curated Titles — {today}")
    L.append("")
    L.append("> Rich title file produced by curate-titles.py from the raw harvest.")
    L.append("> The blog batch reads this — NOT the raw all-daily-titles.md.")
    L.append(f"> raw_candidates: {stats['raw']} · on-niche survivors: {stats['survivors']} "
             f"· deduped pool: {stats['pool']}")
    L.append("")

    def block(title: str, items: list[dict]) -> None:
        L.append(f"## {title}")
        L.append("")
        if not items:
            L.append("_(none — pool exhausted; run the harvester for fresh candidates)_")
            L.append("")
            return
        for i, c in enumerate(items, 1):
            L.append(f"{i}. **{c['title']}**")
            L.append(f"   - barrel: `{c['barrel']}` · intent: `{c['intent']}` · keyword: `{c['keyword']}`")
            L.append(f"   - slug: `{c['slug']}`")
            L.append(f"   - source question: _{c['raw'][:140]}_")
        L.append("")

    block("Section A — SHORT picks (quick-answer, high-intent)", short)
    block("Section B — LONG picks (deep guides)", long)

    # Section C — barrel coverage
    L.append("## Section C — Barrel coverage & balance")
    L.append("")
    L.append("| Barrel | Published | Picked today | Status |")
    L.append("|---|---|---|---|")
    picked_counts = Counter(c["barrel"] for c in short + long)
    for barrel in BARRELS:
        pub = counts.get(barrel, 0)
        pk = picked_counts.get(barrel, 0)
        status = "under-served (priority)" if pub < 8 else ("saturated" if pub > 25 else "ok")
        L.append(f"| {barrel} | {pub} | {pk} | {status} |")
    L.append("")

    # Section D — ranked overflow pool
    L.append("## Section D — Ranked candidate pool")
    L.append("")
    chosen = {c["slug"] for c in short + long}
    rest = [c for c in pool if c["slug"] not in chosen]
    if not rest:
        L.append("_(all survivors promoted to Sections A/B)_")
    for i, c in enumerate(rest, 1):
        L.append(f"{i}. {c['title']}  —  `{c['barrel']}` / `{c['intent']}` / kw:`{c['keyword']}`")
    L.append("")
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="TTML Title Curation Engine")
    ap.add_argument("--from-file", help="raw title source (default: .claude/all-daily-titles.md)")
    ap.add_argument("--short", type=int, default=5)
    ap.add_argument("--long", type=int, default=5)
    ap.add_argument("--pool", type=int, default=40)
    ap.add_argument("--out", help="output path (default: .claude/curated-titles-YYYY-MM-DD.md)")
    ap.add_argument("--stdout", action="store_true", help="also print the file to stdout")
    ap.add_argument("--seed-only", action="store_true", help="just (re)seed the slug ledger and exit")
    args = ap.parse_args()

    # Windows consoles default to cp1252; force UTF-8 so --stdout never crashes.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

    n_seeded = seed_ledger()
    print(f"[ledger] {n_seeded} published slugs in {SLUG_LEDGER.name}", file=sys.stderr)
    if args.seed_only:
        return 0

    raw = load_raw_candidates(Path(args.from_file).resolve() if args.from_file else None)
    cands = curate(raw)
    counts = current_barrel_counts()

    # rank the whole pool, then balance-pick SHORT and LONG so barrels stay even
    cands.sort(key=lambda c: score(c, counts), reverse=True)
    pool = cands[: args.pool]
    taken: set[str] = set()
    short = balance_pick(pool, args.short, taken)
    long = balance_pick(pool, args.long, taken)

    stats = {"raw": len(raw), "survivors": len(cands), "pool": len(pool)}
    doc = render(short, long, pool, counts, stats)

    out_path = Path(args.out).resolve() if args.out else CLAUDE_DIR / f"curated-titles-{date.today().isoformat()}.md"
    out_path.write_text(doc, encoding="utf-8")
    print(f"[write] {out_path}  (A:{len(short)} B:{len(long)} pool:{len(pool)} "
          f"from {len(raw)} raw -> {len(cands)} survivors)", file=sys.stderr)
    if args.stdout:
        print(doc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
