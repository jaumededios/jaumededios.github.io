#!/usr/bin/env python3
"""
Sync Google Sheets spreadsheet data into the Hugo site.

Updates:
  - data/cv.json (publications, conferences/travel, talks)
  - content/_index.md (upcoming talks & travel sections)
  - content/talks/_index.md (full talks list page)
  - content/travel/_index.md (full travel list page)

Usage: python3 scripts/sync_spreadsheet.py [--cached]
"""

import csv
import io
import json
import os
import re
import sys
from datetime import datetime, date
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
CACHE_DIR = PROJECT_DIR / "cache"

SHEET_ID = "1X7VKV3pwBoYjQoUHpxckYJAgaErCYkevc47bJoMV0J0"

TABS = {
    "publications": "948751242",
    "talks": "508483272",
    "travel": "1947229337",
    "teaching": "733600881",
    "grants_awards": "534833029",
    "education": "741365414",
    "positions": "1595934787",
    "service": "756633452",
}

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def fetch_tab(tab_name):
    """Fetch a tab from Google Sheets via public CSV export."""
    import urllib.request

    cache_file = CACHE_DIR / f"{tab_name}.csv"

    if "--cached" in sys.argv and cache_file.exists():
        with open(cache_file) as f:
            return list(csv.DictReader(f))

    gid = TABS[tab_name]
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid={gid}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            text = resp.read().decode("utf-8")
    except Exception as e:
        print(f"ERROR fetching {tab_name}: {e}", file=sys.stderr)
        if cache_file.exists():
            print(f"  Falling back to cache", file=sys.stderr)
            with open(cache_file) as f:
                return list(csv.DictReader(f))
        sys.exit(1)

    records = list(csv.DictReader(io.StringIO(text)))

    CACHE_DIR.mkdir(exist_ok=True)
    with open(cache_file, "w", newline="") as f:
        f.write(text)

    return records


def parse_date(s):
    """Parse YYYY-MM-DD (possibly with time suffix) into a date object, or None."""
    if not s:
        return None
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return None


def format_month_day(d):
    """Format date as 'Mon DD', e.g. 'Feb 19'."""
    return f"{MONTHS[d.month - 1]} {d.day:02d}"


def format_date_full(d):
    """Format date as 'Mon DD, YYYY', e.g. 'Feb 19, 2026'."""
    return f"{MONTHS[d.month - 1]} {d.day:02d}, {d.year}"


def format_date_range(d1, d2):
    """Format a date range compactly, e.g. 'Feb 21 – Mar 08' or 'Mar 16–19'."""
    if d1.year == d2.year and d1.month == d2.month:
        return f"{MONTHS[d1.month - 1]} {d1.day:02d}–{d2.day:02d}"
    return f"{MONTHS[d1.month - 1]} {d1.day:02d} – {MONTHS[d2.month - 1]} {d2.day:02d}"


def format_date_range_full(d1, d2):
    """Format date range with year for list pages, e.g. 'Feb 21 – Mar 08, 2026'."""
    if d1.year == d2.year and d1.month == d2.month:
        return f"{MONTHS[d1.month - 1]} {d1.day:02d}–{d2.day:02d}, {d1.year}"
    if d1.year == d2.year:
        return f"{MONTHS[d1.month - 1]} {d1.day:02d} – {MONTHS[d2.month - 1]} {d2.day:02d}, {d1.year}"
    return f"{MONTHS[d1.month - 1]} {d1.day:02d}, {d1.year} – {MONTHS[d2.month - 1]} {d2.day:02d}, {d2.year}"


def extract_arxiv_from_url(url):
    """Extract arXiv ID from URL."""
    if url:
        m = re.search(r'arxiv\.org/abs/(\d{4}\.\d{4,5})', url)
        if m:
            return m.group(1)
    return ""


# ─── cv.json generation ───

def build_cv_json(publications, talks, travel):
    """Build cv.json structure matching existing format."""
    pubs = []
    for r in publications:
        url = r.get("url", "").strip()
        arxiv_id = extract_arxiv_from_url(url)
        authors = r.get("authors", "").replace(";", ",").strip()
        # Clean up author formatting
        authors = re.sub(r'\s*,\s*', ', ', authors)

        pub = {
            "id": arxiv_id or "",
            "title": r.get("title", "").strip(),
            "authors": authors,
            "journal": r.get("type", "Preprint").strip() or "Preprint",
            "date": r.get("date", "").strip(),
            "abstract": r.get("abstract", "").strip(),
            "description": "",
            "arxiv_url": f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else url,
            "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}" if arxiv_id else "",
        }
        pubs.append(pub)

    today = date.today()

    confs = []
    for r in travel:
        d = parse_date(r.get("date", ""))
        tags = "Current" if d and d >= today else "Past"
        conf = {
            "id": "",
            "title": r.get("title", "").strip(),
            "url": r.get("url", "").strip(),
            "location": r.get("location", "").strip(),
            "tags": tags,
            "date": r.get("date", "").strip(),
            "date_end": r.get("date_end", "").strip(),
        }
        confs.append(conf)

    talk_list = []
    for r in talks:
        d = parse_date(r.get("date", ""))
        tags = "Current" if d and d >= today else "Past"
        title = r.get("title", "").strip()
        talk = {
            "id": "",
            "title": title or "TBD",
            "type": r.get("type", "").strip() or "Seminar",
            "event": r.get("event", "").strip(),
            "short_location": r.get("short_location", "").strip(),
            "url": r.get("url", "").strip(),
            "abstract": r.get("abstract", "").strip(),
            "tags": tags,
            "date": r.get("date", "").strip(),
            "date_end": "",
            "time_zone": "",
        }
        talk_list.append(talk)

    return {
        "publications": pubs,
        "conferences": confs,
        "talks": talk_list,
    }


# ─── Homepage upcoming sections ───

def gen_upcoming_talks_html(talks, max_items=5):
    """Generate the upcoming talks HTML block for _index.md."""
    today = date.today()
    upcoming = []
    for r in talks:
        d = parse_date(r.get("date", ""))
        if d and d >= today:
            upcoming.append((d, r))
    upcoming.sort(key=lambda x: x[0])
    upcoming = upcoming[:max_items]

    lines = []
    lines.append('<!-- BEGIN UPCOMING_TALKS -->')
    lines.append('<div class="section-header"><h2>Upcoming Talks</h2><a class="see-all-btn" href="{{< ref \\"/talks\\" >}}">See all talks →</a></div>')
    lines.append('')
    lines.append('<div class="upcoming-compact">')

    for d, r in upcoming:
        title = r.get("title", "").strip() or "TBD"
        url = r.get("url", "").strip()
        event = r.get("event", "").strip()
        short_loc = r.get("short_location", "").strip() or event
        date_str = format_month_day(d)

        if title and title.upper() != "TBD" and url:
            title_html = f'<a href="{url}" target="_blank">{title}</a>'
        elif title.upper() == "TBD" or not title:
            # For TBD, link the event if we have a URL
            if url and event:
                title_html = "TBD"
                event = f'<a href="{url}" target="_blank">{event}</a>'
            else:
                title_html = "TBD"
        else:
            title_html = title

        meta = f"{short_loc} · {date_str}" if short_loc else date_str

        lines.append('  <div class="upcoming-row">')
        lines.append(f'    <span class="upcoming-row-title">{title_html}</span>')
        lines.append(f'    <span class="upcoming-row-meta">{meta}</span>')
        lines.append('  </div>')

    lines.append('</div>')
    lines.append('<!-- END UPCOMING_TALKS -->')
    return "\n".join(lines)


def gen_upcoming_travel_html(travel, max_items=5):
    """Generate the upcoming travel HTML block for _index.md."""
    today = date.today()
    upcoming = []
    for r in travel:
        d = parse_date(r.get("date", ""))
        if d and d >= today:
            upcoming.append((d, r))
    upcoming.sort(key=lambda x: x[0])
    upcoming = upcoming[:max_items]

    lines = []
    lines.append('<!-- BEGIN UPCOMING_TRAVEL -->')
    lines.append('<div class="section-header"><h2>Upcoming Travel</h2><a class="see-all-btn" href="{{< ref \\"/travel\\" >}}">See all travel →</a></div>')
    lines.append('')
    lines.append('<div class="upcoming-compact">')

    for d, r in upcoming:
        title = r.get("title", "").strip()
        url = r.get("url", "").strip()
        location = r.get("location", "").strip()
        d_end = parse_date(r.get("date_end", ""))

        if url:
            title_html = f'<a href="{url}" target="_blank">{title}</a>'
        else:
            title_html = title

        if d_end:
            date_str = format_date_range(d, d_end)
        else:
            date_str = format_month_day(d)

        meta = f"{location} · {date_str}" if location else date_str

        lines.append('  <div class="upcoming-row">')
        lines.append(f'    <span class="upcoming-row-title">{title_html}</span>')
        lines.append(f'    <span class="upcoming-row-meta">{meta}</span>')
        lines.append('  </div>')

    lines.append('</div>')
    lines.append('<!-- END UPCOMING_TRAVEL -->')
    return "\n".join(lines)


def update_index_md(talks, travel):
    """Update content/_index.md, replacing marker-delimited sections."""
    index_path = PROJECT_DIR / "content" / "_index.md"
    content = index_path.read_text(encoding="utf-8")

    talks_html = gen_upcoming_talks_html(talks)
    travel_html = gen_upcoming_travel_html(travel)

    # Replace or insert upcoming talks
    pattern_talks = r'<!-- BEGIN UPCOMING_TALKS -->.*?<!-- END UPCOMING_TALKS -->'
    if re.search(pattern_talks, content, re.DOTALL):
        content = re.sub(pattern_talks, talks_html, content, flags=re.DOTALL)
    else:
        # Match from section-header "Upcoming Talks" to next section-header or end
        old_talks_pattern = (
            r'<div class="section-header"><h2>Upcoming Talks</h2>.*?</div>\s*\n+'
            r'<div class="upcoming-compact">\s*\n'
            r'(?:.*?\n)*?'
            r'</div>'
        )
        if re.search(old_talks_pattern, content):
            content = re.sub(old_talks_pattern, talks_html, content)
        else:
            print("WARNING: Could not find upcoming talks section in _index.md", file=sys.stderr)

    # Replace or insert upcoming travel
    pattern_travel = r'<!-- BEGIN UPCOMING_TRAVEL -->.*?<!-- END UPCOMING_TRAVEL -->'
    if re.search(pattern_travel, content, re.DOTALL):
        content = re.sub(pattern_travel, travel_html, content, flags=re.DOTALL)
    else:
        old_travel_pattern = (
            r'<div class="section-header"><h2>Upcoming Travel</h2>.*?</div>\s*\n+'
            r'<div class="upcoming-compact">\s*\n'
            r'(?:.*?\n)*?'
            r'</div>'
        )
        if re.search(old_travel_pattern, content):
            content = re.sub(old_travel_pattern, travel_html, content)
        else:
            print("WARNING: Could not find upcoming travel section in _index.md", file=sys.stderr)

    index_path.write_text(content, encoding="utf-8")
    print(f"  Updated {index_path}")


# ─── Full talks page ───

def gen_talks_page(talks):
    """Generate the full content/talks/_index.md page."""
    today = date.today()
    upcoming = []
    past = []

    for r in talks:
        d = parse_date(r.get("date", ""))
        if d and d >= today:
            upcoming.append((d, r))
        elif d:
            past.append((d, r))

    upcoming.sort(key=lambda x: x[0])
    past.sort(key=lambda x: x[0], reverse=True)

    lines = ['---', 'title: "Talks"', 'date: 2024-01-01', '---', '', '# Talks', '']
    lines.append('<div class="upcoming-past-section">')
    lines.append('  <h2>Upcoming</h2>')
    lines.append('')

    for d, r in upcoming:
        title = r.get("title", "").strip() or "TBD"
        url = r.get("url", "").strip()
        talk_type = r.get("type", "").strip() or "Seminar"
        event = r.get("event", "").strip()
        date_str = format_date_full(d)

        if url and title.upper() != "TBD":
            title_html = f'<a href="{url}" target="_blank">{title}</a>'
        elif url:
            title_html = f'<a href="{url}" target="_blank">{title}</a>'
        else:
            title_html = title

        lines.append('<div class="talk-item">')
        lines.append(f'  <h3>{title_html}</h3>')
        lines.append('  <div class="talk-meta">')
        lines.append(f'    <span class="talk-type">{talk_type}</span>')
        lines.append(f'    <span class="talk-event">{event}</span>')
        lines.append(f'    <span class="talk-date">{date_str}</span>')
        lines.append('  </div>')
        lines.append('</div>')
        lines.append('')

    lines.append('</div>')
    lines.append('')
    lines.append('<div class="upcoming-past-section">')
    lines.append('  <h2>Past</h2>')
    lines.append('')

    for d, r in past:
        title = r.get("title", "").strip() or "TBD"
        url = r.get("url", "").strip()
        talk_type = r.get("type", "").strip() or "Seminar"
        event = r.get("event", "").strip()
        date_str = format_date_full(d)

        if url:
            title_html = f'<a href="{url}" target="_blank">{title}</a>'
        else:
            title_html = title

        lines.append('<div class="talk-item">')
        lines.append(f'  <h3>{title_html}</h3>')
        lines.append('  <div class="talk-meta">')
        lines.append(f'    <span class="talk-type">{talk_type}</span>')
        lines.append(f'    <span class="talk-event">{event}</span>')
        lines.append(f'    <span class="talk-date">{date_str}</span>')
        lines.append('  </div>')
        lines.append('</div>')
        lines.append('')

    lines.append('</div>')

    path = PROJECT_DIR / "content" / "talks" / "_index.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  Updated {path}")


# ─── Full travel page ───

def gen_travel_page(travel):
    """Generate the full content/travel/_index.md page."""
    today = date.today()
    upcoming = []
    past = []

    for r in travel:
        d = parse_date(r.get("date", ""))
        if d and d >= today:
            upcoming.append((d, r))
        elif d:
            past.append((d, r))

    upcoming.sort(key=lambda x: x[0])
    past.sort(key=lambda x: x[0], reverse=True)

    lines = ['---', 'title: "Travel"', 'date: 2024-01-01', '---', '', '# Travel', '']
    lines.append('<div class="upcoming-past-section">')
    lines.append('  <h2>Upcoming</h2>')
    lines.append('')

    for d, r in upcoming:
        title = r.get("title", "").strip()
        url = r.get("url", "").strip()
        location = r.get("location", "").strip()
        d_end = parse_date(r.get("date_end", ""))
        date_str = format_date_range_full(d, d_end) if d_end else format_date_full(d)

        if url:
            title_html = f'<a href="{url}" target="_blank">{title}</a>'
        else:
            title_html = title

        lines.append('<div class="travel-item">')
        lines.append(f'  <h3>{title_html}</h3>')
        lines.append('  <div class="travel-meta">')
        lines.append(f'    <span class="travel-location">{location}</span>')
        lines.append(f'    <span class="travel-date">{date_str}</span>')
        lines.append('  </div>')
        lines.append('</div>')
        lines.append('')

    lines.append('</div>')
    lines.append('')
    lines.append('<div class="upcoming-past-section">')
    lines.append('  <h2>Past</h2>')
    lines.append('')

    for d, r in past:
        title = r.get("title", "").strip()
        url = r.get("url", "").strip()
        location = r.get("location", "").strip()
        d_end = parse_date(r.get("date_end", ""))
        date_str = format_date_range_full(d, d_end) if d_end else format_date_full(d)

        if url:
            title_html = f'<a href="{url}" target="_blank">{title}</a>'
        else:
            title_html = title

        lines.append('<div class="travel-item">')
        lines.append(f'  <h3>{title_html}</h3>')
        lines.append('  <div class="travel-meta">')
        lines.append(f'    <span class="travel-location">{location}</span>')
        lines.append(f'    <span class="travel-date">{date_str}</span>')
        lines.append('  </div>')
        lines.append('</div>')
        lines.append('')

    lines.append('</div>')

    path = PROJECT_DIR / "content" / "travel" / "_index.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  Updated {path}")


# ─── Main ───

def main():
    print("Syncing spreadsheet data...")

    # Fetch data
    print("  Fetching publications...")
    publications = fetch_tab("publications")
    print(f"    {len(publications)} rows")

    print("  Fetching talks...")
    talks = fetch_tab("talks")
    print(f"    {len(talks)} rows")

    print("  Fetching travel...")
    travel = fetch_tab("travel")
    print(f"    {len(travel)} rows")

    # Update data/cv.json
    print("  Building cv.json...")
    cv = build_cv_json(publications, talks, travel)
    cv_path = PROJECT_DIR / "data" / "cv.json"
    cv_path.parent.mkdir(exist_ok=True)
    with open(cv_path, "w", encoding="utf-8") as f:
        json.dump(cv, f, indent=2, ensure_ascii=False)
    print(f"  Updated {cv_path}")

    # Update homepage upcoming sections
    print("  Updating homepage...")
    update_index_md(talks, travel)

    # Update full talks page
    print("  Updating talks page...")
    gen_talks_page(talks)

    # Update full travel page
    print("  Updating travel page...")
    gen_travel_page(travel)

    print("\nDone!")


if __name__ == "__main__":
    main()
