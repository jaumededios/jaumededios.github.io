#!/usr/bin/env python3
"""
build-cv.py — Generate a moderncv LaTeX CV from data/cv.json and compile to PDF.
Generates the .tex from scratch (no external template needed).
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from collections import OrderedDict

ENABLED_SECTIONS = {
    "positions": True,
    "education": True,
    "awards": True,
    "interests": True,
    "publications": True,
    "talks": True,
    "teaching": True,
    "service": True,
    "conferences": True,
}


def tex_escape(s: str) -> str:
    for old, new in [
        ("&", r"\&"), ("%", r"\%"), ("$", r"\$"), ("#", r"\#"),
        ("_", r"\_"), ("{", r"\{"), ("}", r"\}"),
        ("~", r"\textasciitilde{}"), ("^", r"\textasciicircum{}"),
    ]:
        s = s.replace(old, new)
    return s


def highlight_name(authors: str) -> str:
    escaped = tex_escape(authors)
    for pat in ["Jaume de Dios Pont", "de Dios Pont, J.", "Jaume de Dios"]:
        esc_pat = tex_escape(pat)
        escaped = escaped.replace(esc_pat, r"\textbf{" + esc_pat + "}")
    return escaped


def build_publications_tex(pubs):
    if not pubs:
        return ""
    lines = [r"\section{Publications \& Preprints}", r"\begin{enumerate}[leftmargin=*, label={[\arabic*]}]"]
    for p in pubs:
        title = tex_escape(p.get("title", ""))
        authors = highlight_name(p.get("authors", ""))
        journal = tex_escape(p.get("journal", ""))
        arxiv_url = p.get("arxiv_url", "")
        link = f" \\href{{{arxiv_url}}}{{arXiv}}" if arxiv_url else ""
        lines.append(f"  \\item \\textit{{{title}}}. {authors}. {journal}.{link}")
    lines.append(r"\end{enumerate}")
    return "\n".join(lines)


def build_talks_tex(talks):
    if not talks:
        return ""
    grouped = OrderedDict()
    for t in sorted(talks, key=lambda x: x.get("date", ""), reverse=True):
        title = t.get("title", "").strip()
        if not title:
            continue
        if title not in grouped:
            grouped[title] = []
        event = t.get("event", "")
        date = t.get("date", "")[:10] if t.get("date") else ""
        grouped[title].append(f"{tex_escape(event)} ({date})")
    lines = [r"\section{Selected Talks}", r"\begin{itemize}[leftmargin=*, nosep]"]
    for title, venues in grouped.items():
        venues_str = "; ".join(venues[:5])
        if len(venues) > 5:
            venues_str += f" +{len(venues)-5} more"
        lines.append(f"  \\item \\textit{{{tex_escape(title)}}}. {venues_str}.")
    lines.append(r"\end{itemize}")
    return "\n".join(lines)


def build_conferences_tex(confs):
    if not confs:
        return ""
    lines = [r"\section{Conferences \& Workshops (selected)}", r"\begin{itemize}[leftmargin=*, nosep]"]
    for c in sorted(confs, key=lambda x: x.get("date", ""), reverse=True)[:15]:
        title = tex_escape(c.get("title", ""))
        location = tex_escape(c.get("location", ""))
        date = c.get("date", "")
        lines.append(f"  \\item {title}, {location}, {date}.")
    lines.append(r"\end{itemize}")
    return "\n".join(lines)


def generate_cv_tex(data):
    pubs = data.get("publications", [])
    talks = data.get("talks", [])
    confs = data.get("conferences", [])
    sections = []

    sections.append(r"""\documentclass[11pt,a4paper,sans]{moderncv}
\moderncvstyle{classic}
\moderncvcolor{blue}
\usepackage[utf8]{inputenc}
\usepackage[scale=0.78, top=1.2cm, bottom=1.2cm]{geometry}
\usepackage{multicol}
\usepackage{enumitem}

\firstname{Jaume}
\familyname{de Dios Pont}
\title{Curriculum Vitae}
\address{60 5th Ave}{New York, NY 10011}
\email{jdedios@nyu.edu}
\homepage{jaume.dedios.cat}
\extrainfo{\href{https://scholar.google.com/citations?user=gYj6GRoAAAAJ}{Google Scholar}}

\begin{document}
\makecvtitle""")

    if ENABLED_SECTIONS.get("positions"):
        sections.append(r"""\section{Positions}
\cventry{2026--present}{CDS Faculty Fellow}{NYU Center for Data Science}{New York}{}{}
\cventry{2023--2025}{Postdoctoral Researcher}{ETH Zurich}{}{with Svitlana Mayboroda}{Funded by the Simons Collaboration on Localization of Waves}
\cventry{2023}{Research Intern}{Microsoft Research}{Seattle}{ML Foundations group}{}""")

    if ENABLED_SECTIONS.get("education"):
        sections.append(r"""\section{Education}
\cventry{2023}{PhD Mathematics}{UCLA}{}{Advisor: Terence Tao}{Thesis: Uniform Estimates for Operators Involving Polynomial Curves; Decoupling Estimates for Fractal and Product Sets}
\cventry{2018}{MSc Mathematics}{ETH Zurich}{}{}{}
\cventry{2017}{BSc Mathematics \& BSc Physics}{Universitat Aut\`onoma de Barcelona}{}{(\#1 Rank in both)}{}""")

    if ENABLED_SECTIONS.get("awards"):
        sections.append(r"""\section{Awards \& Fellowships}
\cvlistitem{UCLA Dissertation Year Fellowship (2022--2023)}
\cvlistitem{``La Caixa'' Postgraduate Fellowship (2018--2020)}
\cvlistitem{ESOP Excellence Scholarship, ETH Zurich (2017--2018)}""")

    if ENABLED_SECTIONS.get("interests"):
        sections.append(r"""\section{Research Interests}
Harmonic Analysis, Elliptic PDEs \& Spectral Theory, Convex Geometry, AI for Mathematics.""")

    if ENABLED_SECTIONS.get("publications"):
        sections.append(build_publications_tex(pubs))
    if ENABLED_SECTIONS.get("talks"):
        sections.append(build_talks_tex(talks))

    if ENABLED_SECTIONS.get("teaching"):
        sections.append(r"""\section{Teaching}
\subsection{Main Instructor}
\cventry{Spring 2025}{Formalizing Mathematics in Lean}{ETH Zurich}{}{}{}
\subsection{Teaching Assistant (UCLA)}
\begin{multicols}{2}
\begin{itemize}[nosep]
\item Math 131A (Analysis) \hfill Fall '20, Spr '22
\item Math 134/135 (ODEs/PDEs) \hfill Fall '21
\item Math 33B (Linear Algebra II) \hfill Spring '21
\item Math 32A/B (Calculus) \hfill Fall '20, Win '21
\end{itemize}
\end{multicols}
\subsection{Teaching Assistant (ETH Zurich)}
\cventry{Spring 2024}{Differential Geometry}{ETH Zurich}{}{}{}""")

    if ENABLED_SECTIONS.get("service"):
        sections.append(r"""\section{Service}
Referee for: Transactions of the AMS, Proceedings of the AMS, Mathematical Statistics and Learning, Discrete Mathematics, Journal of the London Mathematical Society, AMS Contemporary Mathematics.""")

    if ENABLED_SECTIONS.get("conferences"):
        sections.append(build_conferences_tex(confs))

    sections.append(r"\end{document}")
    return "\n\n".join(sections)


def main():
    data_file = Path("data/cv.json")
    output_dir = Path("cv/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    data = json.loads(data_file.read_text()) if data_file.exists() else {}
    tex_content = generate_cv_tex(data)

    processed = output_dir / "cv.tex"
    processed.write_text(tex_content)
    print(f"Generated {processed}")

    # Compile
    for compiler in ["pdflatex"]:
        if shutil.which(compiler):
            try:
                for _ in range(2):
                    subprocess.run(
                        [compiler, "-interaction=nonstopmode",
                         "-output-directory", str(output_dir), str(processed)],
                        check=True, capture_output=True,
                    )
                pdf = output_dir / "cv.pdf"
                if pdf.exists():
                    Path("static").mkdir(exist_ok=True)
                    shutil.copy(pdf, Path("static/cv.pdf"))
                    print(f"CV compiled: static/cv.pdf")
                    return
            except subprocess.CalledProcessError as e:
                stderr = e.stderr.decode() if e.stderr else ""
                print(f"Warning: {compiler} failed: {stderr[:500]}", file=sys.stderr)

    print("Warning: pdflatex not found, skipping PDF.", file=sys.stderr)


if __name__ == "__main__":
    main()
