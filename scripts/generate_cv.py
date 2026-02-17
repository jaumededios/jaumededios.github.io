#!/usr/bin/env python3
"""
Generate LaTeX CV sections from the unified Google Sheets spreadsheet.

Usage: python3 scripts/generate_cv.py [--cached]
  --cached: use local TSV cache instead of fetching from Google Sheets

Outputs gen_*.tex files into tex/ directory.
"""

import subprocess
import json
import csv
import io
import os
import sys
import re
from pathlib import Path
from collections import defaultdict

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
TEX_DIR = PROJECT_DIR / "cv"
CACHE_DIR = PROJECT_DIR / "cache"

SHEET_ID = "1X7VKV3pwBoYjQoUHpxckYJAgaErCYkevc47bJoMV0J0"
ACCOUNT = "manolo.assistant@gmail.com"

# Tab name → gid (for fetching)
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


def fetch_tab(tab_name):
    """Fetch a tab from Google Sheets via public CSV export (no auth needed)."""
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

    # Cache locally
    CACHE_DIR.mkdir(exist_ok=True)
    with open(cache_file, "w", newline="") as f:
        f.write(text)

    return records


def tex_escape(s):
    """Escape special LaTeX characters."""
    if not s:
        return ""
    s = s.replace("\\", "\\textbackslash{}")
    s = s.replace("&", "\\&")
    s = s.replace("%", "\\%")
    s = s.replace("$", "\\$")
    s = s.replace("#", "\\#")
    s = s.replace("_", "\\_")
    s = s.replace("{", "\\{")
    s = s.replace("}", "\\}")
    s = s.replace("~", "\\textasciitilde{}")
    s = s.replace("^", "\\textasciicircum{}")
    # Restore \textbackslash
    return s


def tex_escape_light(s):
    """Light escape — only &, %, # (for fields that may contain intentional LaTeX)."""
    if not s:
        return ""
    s = s.replace("&", "\\&")
    s = s.replace("%", "\\%")
    s = s.replace("#", "\\#")
    return s


def format_authors(authors_str):
    """Format author string, highlighting Jaume's name."""
    if not authors_str:
        return ""
    # Replace Jaume's name variants with \me macro
    s = authors_str
    for pattern in [
        "Jaume de Dios Pont",
        "J. de Dios Pont",
        "de Dios Pont, J.",
        "de Dios Pont, Jaume",
        "Jaume de Dios",
        "J. de Dios",
    ]:
        s = s.replace(pattern, "\\me")
    # Convert semicolons to " & " for last author, ", " for others (LaTeX convention)
    parts = [p.strip() for p in s.split(";") if p.strip()]
    if len(parts) > 1:
        s = ", ".join(parts[:-1]) + " & " + parts[-1]
    elif parts:
        s = parts[0]
    return tex_escape_light(s)


def extract_arxiv_from_url(url, arxiv_field=""):
    """Extract arXiv ID from URL (more reliable than the arxiv column which Sheets mangles)."""
    if url:
        m = re.search(r'arxiv\.org/abs/(\d{4}\.\d{4,5})', url)
        if m:
            return m.group(1)
    # Fallback to arxiv field if URL didn't work
    if arxiv_field and re.match(r'\d{4}\.\d{4,5}$', arxiv_field):
        return arxiv_field
    return ""


def format_date_short(date_str):
    """Convert YYYY-MM-DD or YYYY-MM to short format like 'May 2023' or '9 Mar '22'.
    
    Dates ending in -01 are treated as month-only (YYYY-MM that got zero-padded).
    """
    if not date_str:
        return ""
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    m = re.match(r"(\d{4})-(\d{1,2})-(\d{1,2})$", date_str)
    if m:
        year = m.group(1)
        month = int(m.group(2))
        day = int(m.group(3))
        if day == 1:
            return f"{months[month-1]} {year}"
        return f"{day} {months[month-1]} '{year[2:]}"
    m = re.match(r"(\d{4})-(\d{1,2})$", date_str)
    if m:
        year = m.group(1)
        month = int(m.group(2))
        return f"{months[month-1]} {year}"
    m = re.match(r"(\d{4})$", date_str)
    if m:
        return m.group(1)
    return date_str


def format_date_compact(date_str):
    """Ultra-compact date: "Mar '25" or just "2025". For hint columns that need to be narrow."""
    if not date_str:
        return ""
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    m = re.match(r"(\d{4})-(\d{1,2})-(\d{1,2})$", date_str)
    if m:
        year = m.group(1)
        month = int(m.group(2))
        return f"{months[month-1]} '{year[2:]}"
    m = re.match(r"(\d{4})-(\d{1,2})$", date_str)
    if m:
        year = m.group(1)
        month = int(m.group(2))
        return f"{months[month-1]} '{year[2:]}"
    m = re.match(r"(\d{4})$", date_str)
    if m:
        return f"'{m.group(1)[2:]}"
    return date_str


def format_date_year(date_str):
    """Extract just the year."""
    if not date_str:
        return ""
    m = re.match(r"(\d{4})", date_str)
    return m.group(1) if m else date_str


# ─── Generators ───

def gen_positions(records):
    lines = ["\\section{Employment}", "  \\medskip"]
    for r in records:
        title = tex_escape_light(r.get("title", ""))
        institution = tex_escape_light(r.get("institution", ""))
        start = r.get("start", "")
        end = r.get("end", "")
        details = tex_escape_light(r.get("details", ""))

        # Compact date format for hint column
        start_fmt = format_date_compact(start) if "-" in start else start
        end_fmt = format_date_compact(end) if end and "-" in end else end
        
        date_str = start_fmt
        if end_fmt and end_fmt.lower() != "present":
            date_str += f" -- {end_fmt}"
        else:
            date_str += " -- "

        details_clean = details.rstrip('.')
        lines.append(f"  \\cventry{{show}}{{{date_str}\\phantom{{ --}}}}{{{institution}}}{{{title}}}{{{details_clean}}}{{}}{{}}%")
    return "\n".join(lines) + "\n"


def gen_education(records):
    lines = ["\\section{Education}", "  \\medskip"]
    for r in records:
        degree = tex_escape_light(r.get("degree", ""))
        institution = tex_escape_light(r.get("institution", ""))
        year = r.get("year", "")
        details = tex_escape_light(r.get("details", ""))
        rank = r.get("rank", "").strip()

        if rank:
            rank_str = f"\\hspace*{{\\fill}}({tex_escape_light(rank)})"
        else:
            rank_str = ""

        details_clean = details.rstrip('.')
        lines.append(
            f"  \\cventry{{show}}{{{year}}}{{{degree}}}{{{institution}}}"
            f"{{{rank_str}}}{{}}"
            f"{{{details_clean}}}%"
        )
    return "\n".join(lines) + "\n"


def gen_awards(records):
    lines = ["\\vspace{.5em}", "\\section{Postgraduate Awards and Scholarships}", "  \\medskip"]
    for r in records:
        award = tex_escape_light(r.get("award", ""))
        year = r.get("year", "")
        institution = tex_escape_light(r.get("institution", ""))
        details = tex_escape_light(r.get("details", ""))

        lines.append(
            f"  \\cventry{{show}}{{{year}}}{{{award}}}{{{institution}}}{{}}{{}}"
            f"{{{details}}}%"
        )
    return "\n".join(lines) + "\n"


def gen_publications(records):
    lines = [
        "\\vspace{1em}",
        "\\section{Papers and Preprints}",
    ]
    for i, r in enumerate(records):
        num = i + 1
        title = tex_escape_light(r.get("title", ""))
        authors = format_authors(r.get("authors", ""))
        arxiv_raw = r.get("arxiv", "").strip()
        pub_type = r.get("type", "").strip()
        date = r.get("date", "")
        url = r.get("url", "").strip()
        arxiv = extract_arxiv_from_url(url, arxiv_raw)

        # Publication status line
        year = format_date_year(date)
        if pub_type and pub_type.lower() != "preprint":
            status = tex_escape_light(pub_type)
        else:
            status = f"Preprint ({year})" if year else "Preprint"

        arxiv_str = ""
        if arxiv:
            arxiv_str = f"\\href{{https://arxiv.org/abs/{arxiv}}}{{arXiv:{arxiv}}}"

        lines.append(
            f"  \\cventry{{show}}{{[{num}]}}{{{title}}}{{{authors}}}"
            f"{{{status}}}{{{arxiv_str}}}{{}}%"
        )
    return "\n".join(lines) + "\n"


def gen_talks(records):
    """Generate talks section grouped by block, matching the original CV layout.
    
    Original format uses \talk{}{Bold Title}{} then \talkplace{venue}{date} inline.
    The \talkplace macro produces: "venue (date)," as inline text with \leftskip indentation.
    """
    lines = [
        "\\section{Talks}",
        "",
    ]

    from datetime import date as _date
    today = _date.today()
    # Filter empty rows and future talks
    records = [r for r in records if r.get("title", "").strip()]
    records = [r for r in records if not r.get("date", "") or r.get("date", "")[:10] <= today.isoformat()]

    # Group by block
    blocks = defaultdict(list)
    block_order = []
    for r in records:
        block = r.get("block", "").strip() or "Other"
        if block not in blocks:
            block_order.append(block)
        blocks[block].append(r)

    # Separate research vs expository/minicourse
    research_blocks = [b for b in block_order if b not in ("Expository", "Minicourse")]
    expository_blocks = [b for b in block_order if b in ("Expository", "Minicourse")]

    # Map block names to display titles
    block_titles = {
        "The Hot Spots Conjecture": "Spectral theory and the hot spots conjecture",
        "Sampling lower bounds": "Lower bounds for sampling",
    }

    def emit_block(block_name, talks):
        display_title = block_titles.get(block_name, 
                        tex_escape_light(talks[0].get("title", block_name)))
        lines.append(f"\\textbf{{{display_title}}}")
        lines.append("\\nopagebreak")
        lines.append("\\begin{small}")
        lines.append("\\begin{multicols}{2}")
        lines.append("\\begin{itemize}\\setlength\\itemsep{0pt}")
        for t in talks:
            event = tex_escape_light(t.get("event", ""))
            date = format_date_compact(t.get("date", ""))
            lines.append(f"  \\item {event} ({date})")
        lines.append("\\end{itemize}")
        lines.append("\\end{multicols}")
        lines.append("\\end{small}")
        lines.append("")

    if research_blocks:
        lines.append("\\subsection{\\textbf{\\color{color1} Research talks}}")
        lines.append("")
        for b in research_blocks:
            emit_block(b, blocks[b])

    if expository_blocks:
        lines.append("\\subsection{\\textbf{\\color{color1} Expository talks}}")
        lines.append("")
        # Expository: flat list with title, venue, date — no grouping by topic
        lines.append("\\begin{small}")
        lines.append("\\begin{itemize}\\setlength\\itemsep{0pt}")
        for b in expository_blocks:
            for t in blocks[b]:
                title = tex_escape_light(t.get("title", ""))
                event = tex_escape_light(t.get("event", ""))
                date = format_date_compact(t.get("date", ""))
                lines.append(f"  \\item \\textbf{{{title}}}, {event} ({date})")
        lines.append("\\end{itemize}")
        lines.append("\\end{small}")
        lines.append("")

    lines.append("\\emph{Talks are grouped by topic, even when the covered material changed between instances.}")
    lines.append("")

    return "\n".join(lines) + "\n"


def gen_travel(records):
    from datetime import datetime, date as _date
    today = _date.today()
    # Filter out future travel
    records = [r for r in records if not r.get("date", "") or r.get("date", "")[:10] <= today.isoformat()]
    lines = [
        "\\vspace{1em}",
        "\\section{Research Visits ($> 1$ week)}",
    ]
    for r in records:
        title = tex_escape_light(r.get("title", ""))
        location = tex_escape_light(r.get("location", ""))
        date_raw = r.get("date", "")
        date_end_raw = r.get("date_end", "")
        
        # Strictly filter: must be > 7 days
        if date_raw and date_end_raw:
            try:
                d1 = datetime.strptime(date_raw[:10], "%Y-%m-%d")
                d2 = datetime.strptime(date_end_raw[:10], "%Y-%m-%d")
                if (d2 - d1).days < 8:
                    continue
            except (ValueError, TypeError):
                pass

        # Compact date format for hint column
        date_str = format_date_compact(date_raw)
        if date_end_raw:
            end_compact = format_date_compact(date_end_raw)
            # If same month, just show "Mon 'YY"
            if date_str == end_compact:
                pass  # just use single date
            else:
                date_str += f" -- {end_compact}"

        lines.append(
            f"  \\cventry{{show}}{{{date_str}}}{{{location}}}{{{title}}}{{}}{{}}{{}}%"
        )
    return "\n".join(lines) + "\n"


def gen_teaching(records):
    lines = ["\\section{Teaching Experience}"]

    # Group by institution
    by_inst = defaultdict(list)
    inst_order = []
    for r in records:
        inst = r.get("institution", "").strip()
        if inst not in by_inst:
            inst_order.append(inst)
        by_inst[inst].append(r)

    # Group by (institution, role) to separate TA from Main Instructor
    for inst in inst_order:
        courses = by_inst[inst]
        roles = defaultdict(list)
        role_order = []
        for c in courses:
            role = c.get("role", "Teaching Assistant")
            if role not in roles:
                role_order.append(role)
            roles[role].append(c)

        for role in role_order:
            role_courses = roles[role]
            lines.append(f"\\subsection{{\\textbf{{\\color{{color1}} {tex_escape_light(inst)} ({tex_escape_light(role)})}}}}")

            if len(role_courses) > 3:
                lines.append("\\begin{minipage}{\\textwidth}")
                lines.append("\\begin{multicols}{2}")
                lines.append("\\begin{itemize}")
                for c in role_courses:
                    name = tex_escape_light(c.get("course", ""))
                    term = tex_escape_light(c.get("term", ""))
                    lines.append(f"  \\item \\textbf{{{name}}} \\hfill {term}")
                lines.append("\\end{itemize}")
                lines.append("\\end{multicols}")
                lines.append("\\end{minipage}")
            else:
                lines.append("\\begin{itemize}")
                for c in role_courses:
                    name = tex_escape_light(c.get("course", ""))
                    term = tex_escape_light(c.get("term", ""))
                    lines.append(f"  \\item \\textbf{{{name}}} \\qquad {term}")
                lines.append("\\end{itemize}")

        lines.append("\\vspace{1em}")

    return "\n".join(lines) + "\n"


def gen_service(records):
    lines = ["\\section{Reviewing}"]
    # Service sheet has columns: type, details, year
    # Filter out placeholder rows
    skip_phrases = ["to be populated", "add reviewing", "(to be populated)"]
    journals = [tex_escape_light(r.get("details", "")) for r in records
                if r.get("details") and not any(p in r.get("details", "").lower() for p in skip_phrases)]
    if journals:
        lines.append("Reviewer for: " + ", ".join(journals) + ".")
    else:
        # Hardcode from known data since sheet may be sparse
        lines.append("Reviewer for: Transactions of the AMS, Proceedings of the AMS, "
                      "Mathematical Statistics and Learning, Discrete Mathematics, "
                      "Journal of the London Mathematical Society, AMS Contemporary Mathematics.")
    return "\n".join(lines) + "\n"


# ─── Main ───

def main():
    print("Fetching spreadsheet data...")

    generators = {
        "gen_positions": ("positions", gen_positions),
        "gen_education": ("education", gen_education),
        "gen_awards": ("grants_awards", gen_awards),
        "gen_publications": ("publications", gen_publications),
        "gen_talks": ("talks", gen_talks),
        "gen_travel": ("travel", gen_travel),
        "gen_teaching": ("teaching", gen_teaching),
        "gen_service": ("service", gen_service),
    }

    for output_name, (tab_name, gen_func) in generators.items():
        print(f"  {tab_name} → {output_name}.tex")
        records = fetch_tab(tab_name)
        tex = gen_func(records)
        out_path = TEX_DIR / f"{output_name}.tex"
        out_path.write_text(tex, encoding="utf-8")

    print(f"\nDone! Generated {len(generators)} files in {TEX_DIR}/")
    print("Next: cd tex && pdflatex main.tex")


if __name__ == "__main__":
    main()
