#!/usr/bin/env python3
"""
TTML Title Master Sync
======================
Merges every .claude/daily-titles-YYYY-MM-DD.md into a single rolling file:
.claude/all-daily-titles.md (grouped by date, newest first), then DELETES the
per-day files so titles only ever live in one place.

Idempotent — safe to run multiple times. If no per-day files exist on a given
run, the master is left untouched (because there's nothing new to merge).

Usage:
    python sync-titles-to-master.py
    python sync-titles-to-master.py --keep-per-day        # don't delete daily files
    python sync-titles-to-master.py --claude-dir <path>
"""
import argparse
import re
from pathlib import Path
from datetime import datetime

DEFAULT_CLAUDE_DIR = str(Path(__file__).resolve().parent.parent / ".claude")
DAILY_PATTERN = re.compile(r"^daily-titles-(\d{4}-\d{2}-\d{2})\.md$")


DATE_HEADER_RE = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2})\s*$")


def parse_daily_file(path: Path):
    """Extract metadata header and numbered title lines from a daily-titles file."""
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    header_lines, title_lines = [], []
    in_titles_section = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(("harvested_at:", "total_harvested:", "by_source:")):
            header_lines.append(stripped)
            continue
        if re.match(r"^\d+\.\s+", stripped):
            in_titles_section = True
            title_lines.append(stripped)
            continue
        if stripped.startswith(("## EDITORIAL", "## NOTES")) and in_titles_section:
            in_titles_section = False

    return {"header": " | ".join(header_lines), "titles": title_lines}


def parse_existing_master(master_path: Path):
    """Read the existing master and return {date_str: {'header': str, 'titles': [str]}}.

    This is what preserves history once per-day files have been deleted.
    """
    if not master_path.exists():
        return {}

    blocks = {}
    current_date = None
    current = None

    for raw in master_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.rstrip()
        m = DATE_HEADER_RE.match(line.strip())
        if m:
            if current_date and current is not None:
                blocks[current_date] = current
            current_date = m.group(1)
            current = {"header": "", "titles": []}
            continue
        if current_date is None:
            continue  # preamble — skip
        stripped = line.strip()
        if stripped.startswith(("harvested_at:", "total_harvested:", "by_source:")):
            # Inline pipe-joined header line — keep as-is
            current["header"] = stripped
            continue
        if re.match(r"^\d+\.\s+", stripped):
            current["titles"].append(stripped)
            continue
        # End block on next "---" line — flush current
        if stripped == "---" and current_date is not None and (current["titles"] or current["header"]):
            blocks[current_date] = current
            current_date = None
            current = None

    if current_date and current is not None:
        blocks[current_date] = current

    return blocks


def build_master(claude_dir: Path, master_path: Path) -> str:
    """Build master content by merging existing master + any per-day files.

    Per-day files OVERRIDE existing master blocks for the same date.
    """
    # Start with whatever history is already in the master
    blocks = parse_existing_master(master_path)

    # Layer per-day files on top (newer per-day data wins for that date)
    for f in claude_dir.iterdir():
        m = DAILY_PATTERN.match(f.name)
        if not m:
            continue
        date_str = m.group(1)
        blocks[date_str] = parse_daily_file(f)

    # Render — newest date first
    parts = [
        "# TTML Daily Titles — Master Log",
        "",
        "All harvested blog title candidates, grouped by date only.",
        "Newest date appears first. Single source of truth — per-day files are merged in and removed.",
        "",
        f"_Last synced: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_",
        "",
        "---",
        "",
    ]

    for date_str in sorted(blocks.keys(), reverse=True):
        b = blocks[date_str]
        parts.append(f"## {date_str}")
        if b.get("header"):
            parts.append(b["header"])
        parts.append("")
        if b.get("titles"):
            parts.extend(b["titles"])
        else:
            parts.append("_No titles recorded for this date._")
        parts.append("")
        parts.append("---")
        parts.append("")

    parts.append("*Master log maintained by `scripts/sync-titles-to-master.py`. New harvests are merged into this file and per-day files are deleted, so titles live in one place.*")
    return "\n".join(parts) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Sync per-day TTML title files into a single master log.")
    parser.add_argument("--claude-dir", default=DEFAULT_CLAUDE_DIR,
                        help="Path to the .claude directory containing daily-titles-*.md files")
    parser.add_argument("--out", default=None,
                        help="Output master file path (default: <claude-dir>/all-daily-titles.md)")
    parser.add_argument("--keep-per-day", action="store_true",
                        help="Keep daily-titles-*.md files after merging (default: delete them)")
    args = parser.parse_args()

    claude_dir = Path(args.claude_dir)
    if not claude_dir.is_dir():
        raise SystemExit(f"ERROR: directory not found: {claude_dir}")

    out_path = Path(args.out) if args.out else claude_dir / "all-daily-titles.md"

    # Identify per-day files BEFORE writing the master so we know what to delete after.
    per_day_files = [
        f for f in claude_dir.iterdir()
        if DAILY_PATTERN.match(f.name)
    ]

    content = build_master(claude_dir, out_path)
    out_path.write_text(content, encoding="utf-8")

    block_count = content.count("\n## 2")
    print(f"[sync-titles] Wrote {out_path} ({len(content)} bytes, ~{block_count} date blocks).")

    # Collapse: master is the only file — delete the per-day files we just consumed.
    if not args.keep_per_day:
        deleted = 0
        for f in per_day_files:
            try:
                f.unlink()
                deleted += 1
            except Exception as e:
                print(f"[sync-titles] WARN: could not delete {f.name}: {e}")
        if deleted:
            print(f"[sync-titles] Cleaned up {deleted} per-day file(s).")


if __name__ == "__main__":
    main()
