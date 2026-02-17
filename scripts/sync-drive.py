#!/usr/bin/env python3
"""
sync-drive.py — Download data from published Google Sheets and arXiv API,
generate Hugo content files for publications, talks, travel, and CV data.

Data sources:
  - Curriculum_Vitae spreadsheet (published CSVs): conferences + talks
  - arXiv API: publication metadata + abstracts
  - Hardcoded enrichment data from CV (journal info, descriptions)
"""

import csv
import io
import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

CONTENT_DIR = Path("content")
DATA_DIR = Path("data")

# Published CSV URLs from the Curriculum_Vitae spreadsheet
SHEET_BASE = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRchAxHUEFwDxDinsba7BZqejlUPdOdiD1jjQv6NAXtEufiZU1_UfPlAAzks4tw3AHUf5h105w-AN-c/pub"
PUBLISHED_CSVS = {
    "conferences": f"{SHEET_BASE}?gid=0&single=true&output=csv",
    "talks": f"{SHEET_BASE}?gid=1581332120&single=true&output=csv",
}

# arXiv IDs for all papers
ARXIV_IDS = [
    "2508.16321",  # Sharp bounds on the failure of the hot spots conjecture
    "2412.06344",  # Convex sets can have interior hot spots
    "2409.03684",  # Predicting quantum channels over general product distributions
    "2408.02151",  # Periodicity and decidability of translational tilings
    "2304.02599",  # Query lower bounds for log-concave sampling
    "2303.11693",  # Uniform Fourier Restriction Estimate
    "2201.12932",  # Convex hull of space curves
    "2112.09352",  # Additive energies on discrete cubes
    "2106.13873",  # On classical inequalities for autocorrelations
    "2012.11458",  # Decoupling for fractal subsets of the parabola
    "2006.10225",  # On Sparsity in Overparametrised Shallow ReLU Networks
    "2003.14140",  # A geometric lemma for complex polynomial curves
    "1908.09440",  # Role Detection in Bicycle-Sharing Networks
]

# Extra metadata not available from arXiv
EXTRA_PUB_INFO = {
    "2508.16321": {
        "journal": "Preprint (2025)",
        "description": "We identify the largest possible hot spots ratio over all connected Lipschitz domains in any dimension, settling a question about the degree of failure of Rauch's hot spots conjecture. As dimension grows, the sharp constant converges to √e.",
    },
    "2412.06344": {
        "journal": "Submitted to Annals of Mathematics (2024)",
        "description": "The hot spots conjecture predicts that the hottest point in an insulated convex body always lies on the boundary. We construct the first counterexamples for convex domains in high dimensions, using a novel extension of the conjecture to log-concave measures.",
    },
    "2409.03684": {
        "journal": "Preprint (2024)",
        "description": "We study how to efficiently predict the output of unknown quantum channels, extending the surprising sample-efficiency results of Huang, Chen, and Preskill to general product input distributions.",
    },
    "2408.02151": {
        "journal": "Expositiones Mathematicae (2024)",
        "description": "We prove that translational tilings of the plane by rational polygonal sets are always periodic and that their existence is decidable — a key step toward resolving the periodic tiling conjecture in two dimensions.",
    },
    "2304.02599": {
        "journal": "Journal of the ACM, Vol. 71, Issue 4. FOCS 2023",
        "description": "We establish the first unconditional lower bounds on the query complexity of sampling from log-concave distributions, proving that existing algorithms are near-optimal in low dimensions.",
    },
    "2303.11693": {
        "journal": "Preprint (2023)",
        "description": "We prove uniform Fourier restriction estimates for a new class of curves — those of bounded frequency — using a decomposition scheme connected to techniques from elliptic PDE.",
    },
    "2201.12932": {
        "journal": "Michigan Mathematical Journal (2024)",
        "description": "Curves with totally-positive torsion generalize convex curves to higher dimensions. We give a new, more geometric proof describing their convex hull, recovering formulas for its surface area and volume.",
    },
    "2112.09352": {
        "journal": "Discrete Analysis (2023)",
        "description": "Additive energy measures the arithmetic structure of subsets of abelian groups. We determine the sharp exponent for higher-order energies of subsets of discrete hypercubes {0,1}^d.",
    },
    "2106.13873": {
        "journal": "Preprint (2021)",
        "description": "We study Barnard and Steinerberger's autocorrelation inequality — motivated by additive combinatorics — establishing existence of extremizers for Gaussian and indicator function weights.",
    },
    "2012.11458": {
        "journal": "Mathematische Zeitschrift (2022)",
        "description": "We generalize the celebrated Bourgain–Demeter decoupling theorem to fractal subsets of the parabola, reducing the problem to decoupling for the projected fractal set on the unit interval.",
    },
    "2006.10225": {
        "journal": "Preprint (2020)",
        "description": "We study learning guarantees for overparametrized shallow ReLU networks beyond the lazy/NTK regime, bringing sparsity results from the mean-field infinite-width limit back to finite networks.",
    },
    "2003.14140": {
        "journal": "Preprint (2020)",
        "description": "We prove a uniform Fourier restriction estimate for complex polynomial curves equipped with affine arclength measure, extending Stovall's real-variable results to the complex setting.",
    },
    "1908.09440": {
        "journal": "Network Science (2022)",
        "description": "We classify docking stations in bicycle-sharing networks using multilayer stochastic block models, revealing human mobility patterns across three major US cities.",
    },
}


# Additional talks from the LaTeX CV source that aren't in the published spreadsheet.
# Verified against: data/cv-spreadsheet/cv-latex/Curriculum Vitae copy/main.tex
EXTRA_TALKS = [
    # Hot Spots conjecture talks (2024-2025)
    {"id": "ethz_hotspots_24", "title": "Convex sets can have interior hot spots", "type": "Seminar", "event": "ETHZ Analysis Seminar", "tags": "Past", "date": "2024-10-15T15:00:00Z"},
    {"id": "simons_wave_24", "title": "Convex sets can have interior hot spots", "type": "Seminar", "event": "Simons WAVE Collaboration Seminar", "tags": "Past", "date": "2024-11-15T15:00:00Z"},
    {"id": "hcm_hotspots_24", "title": "Convex sets can have interior hot spots", "type": "Seminar", "event": "HCM Analysis and PDE Seminar", "tags": "Past", "date": "2024-11-20T15:00:00Z"},
    {"id": "uab_hotspots_25", "title": "Convex sets can have interior hot spots", "type": "Seminar", "event": "UAB Analysis Seminar", "tags": "Past", "date": "2025-01-15T15:00:00Z"},
    {"id": "vt_hotspots_25", "title": "Convex sets can have interior hot spots", "type": "Seminar", "event": "Virginia Tech PDE Seminar", "tags": "Past", "date": "2025-02-25T15:00:00Z"},
    {"id": "edinburgh_25", "title": "Convex sets can have interior hot spots", "type": "Seminar", "event": "Edinburgh Analysis Seminar", "tags": "Past", "date": "2025-03-03T15:00:00Z"},
    {"id": "lyon_25", "title": "Convex sets can have interior hot spots", "type": "Seminar", "event": "Lyon University Analysis Seminar", "tags": "Past", "date": "2025-03-10T15:00:00Z"},
    # Sampling from Log-Concave Distributions talks (2022-2024)
    {"id": "nyu_cs_22", "title": "Sampling from Log-Concave Distributions", "type": "Seminar", "event": "NYU Courant (Computer Science)", "tags": "Past", "date": "2022-11-15T15:00:00Z"},
    {"id": "msr_theory_22", "title": "Sampling from Log-Concave Distributions", "type": "Seminar", "event": "Microsoft Research Theory Seminar", "tags": "Past", "date": "2022-12-15T15:00:00Z"},
    {"id": "nyu_math_23", "title": "Sampling from Log-Concave Distributions", "type": "Seminar", "event": "NYU Courant (Mathematics)", "tags": "Past", "date": "2023-02-15T15:00:00Z"},
    {"id": "rochester_23", "title": "Sampling from Log-Concave Distributions", "type": "Seminar", "event": "University of Rochester", "tags": "Past", "date": "2023-05-22T15:00:00Z"},
    {"id": "hcm_bonn_24", "title": "Sampling from Log-Concave Distributions", "type": "Seminar", "event": "HCM Bonn", "tags": "Past", "date": "2024-01-15T15:00:00Z"},
    {"id": "birs_granada_24", "title": "Sampling from Log-Concave Distributions", "type": "Workshop", "event": "BIRS Granada: PDE Methods in Machine Learning", "tags": "Past", "date": "2024-06-15T15:00:00Z"},
    # Decoupling + additive combinatorics (missing from CSV)
    {"id": "stanford_22", "title": "Interactions between Fourier decoupling, fractal sets, and additive combinatorics", "type": "Seminar", "event": "Stanford University Analysis and PDE Seminar", "tags": "Past", "date": "2022-10-20T15:00:00Z"},
    {"id": "ntnu_23", "title": "Interactions between Fourier decoupling, fractal sets, and additive combinatorics", "type": "Seminar", "event": "NTNU Analysis and PDE Seminar", "tags": "Past", "date": "2023-11-01T15:00:00Z"},
    # Sensitivity theorem talks
    {"id": "aim_sensitivity_22", "title": "The Sensitivity Theorem", "type": "Workshop", "event": "AIM Workshop Talk", "tags": "Past", "date": "2022-06-08T15:00:00Z"},
    {"id": "stanford_kiddie_22", "title": "The Sensitivity Theorem", "type": "Seminar", "event": "Stanford Kiddie Colloquium", "tags": "Past", "date": "2022-10-22T15:00:00Z"},
    # Expository talks
    {"id": "msr_decoupling_23", "title": "Decoupling with applications from PDEs to Number Theory", "type": "Seminar", "event": "Microsoft Research Foundations Seminar", "tags": "Past", "date": "2023-06-15T15:00:00Z"},
    {"id": "mfo_quantum_24", "title": "The quantum Fourier transform and Shor's algorithm", "type": "Workshop", "event": "MFO (Oberwolfach)", "tags": "Past", "date": "2024-10-08T15:00:00Z"},
    # Uniformity talks
    {"id": "ethz_uniform_22", "title": "Uniformly bounding operators defined by polynomial curves", "type": "Seminar", "event": "ETHZ Analysis Seminar", "tags": "Past", "date": "2022-03-15T15:00:00Z"},
]


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text[:80]


def download_csv(url: str) -> list[dict]:
    try:
        with urlopen(url, timeout=30) as resp:
            text = resp.read().decode("utf-8")
        return list(csv.DictReader(io.StringIO(text)))
    except URLError as e:
        print(f"  Warning: Could not download CSV: {e}", file=sys.stderr)
        return []


def fetch_arxiv_papers(arxiv_ids: list[str]) -> list[dict]:
    """Fetch paper metadata from arXiv API."""
    papers = []
    id_list = ",".join(arxiv_ids)
    url = f"http://export.arxiv.org/api/query?id_list={id_list}&max_results={len(arxiv_ids)}"
    try:
        req = Request(url, headers={"User-Agent": "academic-site-builder/1.0"})
        with urlopen(req, timeout=30) as resp:
            xml_text = resp.read().decode("utf-8")
        root = ET.fromstring(xml_text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall("atom:entry", ns):
            id_url = entry.find("atom:id", ns).text.strip()
            aid = id_url.split("/abs/")[-1]
            # Remove version suffix
            aid = re.sub(r"v\d+$", "", aid)
            title = " ".join(entry.find("atom:title", ns).text.split())
            abstract = " ".join(entry.find("atom:summary", ns).text.split())
            published = entry.find("atom:published", ns).text[:10]
            authors = [a.find("atom:name", ns).text.strip() for a in entry.findall("atom:author", ns)]
            papers.append({
                "arxiv_id": aid,
                "title": title,
                "authors": ", ".join(authors),
                "abstract": abstract,
                "date": published,
            })
    except Exception as e:
        print(f"  Warning: arXiv API error: {e}", file=sys.stderr)
    return papers


def generate_publications(papers: list[dict]):
    pub_dir = CONTENT_DIR / "publications"
    pub_dir.mkdir(parents=True, exist_ok=True)
    for f in pub_dir.glob("*.md"):
        if f.name != "_index.md":
            f.unlink()

    all_pubs = []
    for paper in papers:
        aid = paper["arxiv_id"]
        extra = EXTRA_PUB_INFO.get(aid, {})
        pub = {
            "id": aid,
            "title": paper["title"],
            "authors": paper["authors"],
            "journal": extra.get("journal", "Preprint"),
            "date": paper["date"],
            "abstract": paper["abstract"],
            "description": extra.get("description", ""),
            "arxiv_url": f"https://arxiv.org/abs/{aid}",
            "pdf_url": f"https://arxiv.org/pdf/{aid}",
        }
        all_pubs.append(pub)

    all_pubs.sort(key=lambda p: p["date"], reverse=True)

    for pub in all_pubs:
        slug = slugify(pub["title"])
        esc = lambda s: s.replace('"', '\\"')
        md_lines = [
            "---",
            f'title: "{esc(pub["title"])}"',
            f'date: {pub["date"]}',
            "params:",
            f'  authors: "{esc(pub["authors"])}"',
            f'  journal: "{esc(pub["journal"])}"',
            f'  arxiv: "{pub["arxiv_url"]}"',
            f'  pdf: "{pub["pdf_url"]}"',
            f'  description: "{esc(pub["description"])}"',
            "---",
            "",
            f'**{pub["authors"]}**',
            "",
            f'*{pub["journal"]}*',
            "",
        ]
        if pub["description"]:
            md_lines.append(pub["description"])
            md_lines.append("")
        md_lines.append(f'[arXiv]({pub["arxiv_url"]}) · [PDF]({pub["pdf_url"]})')
        md_lines.append("")
        if pub["abstract"]:
            md_lines.append("### Abstract")
            md_lines.append("")
            md_lines.append(pub["abstract"])
            md_lines.append("")

        (pub_dir / f"{slug}.md").write_text("\n".join(md_lines))

    (pub_dir / "_index.md").write_text('---\ntitle: "Publications & Preprints"\n---\n')

    print(f"  Generated {len(all_pubs)} publication pages")
    return all_pubs


def generate_talks(talks: list[dict]):
    talks_dir = CONTENT_DIR / "talks"
    talks_dir.mkdir(parents=True, exist_ok=True)
    for f in talks_dir.glob("*.md"):
        if f.name != "_index.md":
            f.unlink()

    for row in talks:
        title = row.get("title", "").strip()
        if not title:
            continue
        talk_id = row.get("id", slugify(title))
        event = row.get("event", "")
        url = row.get("url", "")
        abstract = row.get("abstract", "")
        tags = row.get("tags", "")
        date = row.get("date", "")[:10] if row.get("date") else ""
        talk_type = row.get("type", "")
        esc = lambda s: s.replace('"', '\\"')

        url_line = f"[Event page]({url})" if url and url != "#" else ""
        md = f"""---
title: "{esc(title)}"
date: {date or "2020-01-01"}
params:
  type: "{talk_type}"
  event: "{esc(event)}"
  tags: "{tags}"
---

**{event}**{f" — {talk_type}" if talk_type else ""}, {date}

{url_line}

{("### Abstract" + chr(10) + chr(10) + abstract) if abstract else ""}
"""
        (talks_dir / f"{slugify(talk_id)}.md").write_text(md)

    (talks_dir / "_index.md").write_text('---\ntitle: "Talks"\n---\n')
    print(f"  Generated {len(talks)} talk pages")


def generate_travel(conferences: list[dict]):
    travel_dir = CONTENT_DIR / "travel"
    travel_dir.mkdir(parents=True, exist_ok=True)
    for f in travel_dir.glob("*.md"):
        if f.name != "_index.md":
            f.unlink()

    sorted_conf = sorted(conferences, key=lambda r: r.get("date", ""), reverse=True)
    current = [c for c in sorted_conf if c.get("tags", "").strip() == "Current"]
    past = [c for c in sorted_conf if c.get("tags", "").strip() == "Past"]

    lines = ['---', 'title: "Travel"', '---', '',
             "Travel plans for upcoming events. If I'm travelling near you and want to meet, contact me!\n"]

    if current:
        lines.append("## Upcoming\n")
        lines.append("| Event | Location | Dates |")
        lines.append("|-------|----------|-------|")
        for c in current:
            t = c.get("title", ""); u = c.get("url", ""); loc = c.get("location", "")
            d1 = c.get("date", ""); d2 = c.get("date_end", "")
            link = f"[{t}]({u})" if u and u != "#" else t
            lines.append(f"| {link} | {loc} | {d1} — {d2} |")
        lines.append("")

    if past:
        lines.append("## Past\n")
        lines.append("| Event | Location | Dates |")
        lines.append("|-------|----------|-------|")
        for c in past[:30]:
            t = c.get("title", ""); u = c.get("url", ""); loc = c.get("location", "")
            d1 = c.get("date", ""); d2 = c.get("date_end", "")
            link = f"[{t}]({u})" if u and u != "#" else t
            lines.append(f"| {link} | {loc} | {d1} — {d2} |")
        lines.append("")

    (travel_dir / "_index.md").write_text("\n".join(lines))
    print(f"  Generated travel page ({len(current)} upcoming, {len(past)} past)")


def main():
    print("=== sync-drive.py ===\n")

    print("Downloading spreadsheet data...")
    conferences = download_csv(PUBLISHED_CSVS["conferences"])
    print(f"  Conferences: {len(conferences)}")
    talks = download_csv(PUBLISHED_CSVS["talks"])
    print(f"  Talks: {len(talks)}")

    print("\nFetching arXiv data...")
    papers = fetch_arxiv_papers(ARXIV_IDS)
    print(f"  Papers: {len(papers)}")

    # Merge extra talks from LaTeX CV (avoid duplicates by id)
    csv_ids = {r.get("id", "") for r in talks}
    for extra in EXTRA_TALKS:
        if extra["id"] not in csv_ids:
            talks.append(extra)
    print(f"  Talks after merging LaTeX CV extras: {len(talks)}")

    print("\nGenerating Hugo content...")
    publications = generate_publications(papers)
    generate_talks(talks)
    generate_travel(conferences)

    # Save combined data for CV builder
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    cv_data = {
        "publications": publications,
        "conferences": [{k: v for k, v in r.items() if k and v} for r in conferences],
        "talks": [{k: v for k, v in r.items() if k and v} for r in talks],
    }
    (DATA_DIR / "cv.json").write_text(json.dumps(cv_data, indent=2, ensure_ascii=False))
    print("  Generated data/cv.json")

    print("\nDone!")


if __name__ == "__main__":
    main()
