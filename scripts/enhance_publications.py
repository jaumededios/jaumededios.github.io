#!/usr/bin/env python3

import csv
import json
import os
import sys
import re
from pathlib import Path

def read_tsv(filepath):
    """Read TSV file and return list of dictionaries"""
    data = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                # Clean up any empty string values
                cleaned_row = {k: v.strip() if v else '' for k, v in row.items()}
                data.append(cleaned_row)
        print(f"Read {len(data)} records from {filepath}")
    except FileNotFoundError:
        print(f"Warning: {filepath} not found")
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    return data

def read_hugo_publications(pubs_dir):
    """Read existing Hugo publication files and extract metadata"""
    data = []
    pubs_path = Path(pubs_dir)
    
    if not pubs_path.exists():
        print(f"Warning: {pubs_dir} not found")
        return data
    
    for md_file in pubs_path.glob("*.md"):
        if md_file.name == "_index.md":
            continue
        
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = parts[1].strip()
                    body = parts[2].strip()
                    
                    # Parse YAML-like frontmatter
                    metadata = {}
                    for line in frontmatter.split('\n'):
                        line = line.strip()
                        if ':' in line:
                            key, value = line.split(':', 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            metadata[key] = value
                    
                    # Extract abstract from body
                    abstract = ""
                    abstract_match = re.search(r'### Abstract\s*\n\n(.+?)(?:\n\n###|\Z)', body, re.DOTALL)
                    if abstract_match:
                        abstract = abstract_match.group(1).strip()
                    
                    # Extract arXiv ID
                    arxiv_id = ""
                    arxiv_match = re.search(r'arXiv:(\d{4}\.\d{4,5})', body)
                    if arxiv_match:
                        arxiv_id = arxiv_match.group(1)
                    
                    # Convert to standard format
                    paper = {
                        'title': metadata.get('title', ''),
                        'type': metadata.get('type', ''),
                        'authors': metadata.get('authors', ''),
                        'journal': metadata.get('journal', ''),
                        'year': metadata.get('year', ''),
                        'date': metadata.get('date', ''),
                        'arxiv': arxiv_id,
                        'url': metadata.get('url', ''),
                        'abstract': abstract,
                        'source': f'hugo:{md_file.name}'
                    }
                    data.append(paper)
        except Exception as e:
            print(f"Error reading {md_file}: {e}")
    
    print(f"Read {len(data)} records from Hugo publications")
    return data

def title_similarity(title1, title2):
    """Calculate simple similarity between two titles"""
    if not title1 or not title2:
        return 0.0
    
    # Normalize titles (lowercase, remove punctuation, extra spaces)
    def normalize_title(title):
        normalized = re.sub(r'[^\w\s]', '', title.lower())
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized
    
    norm1 = normalize_title(title1)
    norm2 = normalize_title(title2)
    
    if norm1 == norm2:
        return 1.0
    
    # Simple word overlap similarity
    words1 = set(norm1.split())
    words2 = set(norm2.split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    return intersection / union if union > 0 else 0.0

def merge_and_enhance_publications(unified_pubs, cv_pubs, hugo_pubs):
    """Merge publication data and enhance with CV abstracts"""
    
    # Create enhancement map from CV data
    cv_by_title = {}
    for paper in cv_pubs:
        title = paper.get('title', '').lower().strip()
        if title and (paper.get('abstract', '').strip() or paper.get('arxiv', '').strip()):
            cv_by_title[title] = paper
    
    print(f"CV papers available for enhancement: {len(cv_by_title)}")
    
    # Start with unified + hugo data
    all_papers = unified_pubs + hugo_pubs
    
    # Add any CV papers not already present
    seen_titles = {p.get('title', '').lower().strip() for p in all_papers}
    for cv_paper in cv_pubs:
        cv_title = cv_paper.get('title', '').lower().strip()
        if cv_title and cv_title not in seen_titles:
            cv_paper['source'] = 'cv_master'
            all_papers.append(cv_paper)
            print(f"Added new paper from CV: {cv_paper.get('title', '')}")
    
    # Enhance existing papers with CV data
    enhanced_count = 0
    for paper in all_papers:
        paper_title = paper.get('title', '').lower().strip()
        best_match = None
        best_similarity = 0.0
        
        # Find best matching CV paper
        for cv_title, cv_paper in cv_by_title.items():
            similarity = title_similarity(paper_title, cv_title)
            if similarity > best_similarity and similarity > 0.7:
                best_similarity = similarity
                best_match = cv_paper
        
        # Apply enhancements
        if best_match and best_similarity > 0.7:
            enhanced = False
            
            # Enhance abstract
            if (best_match.get('abstract', '').strip() and 
                len(best_match.get('abstract', '')) > len(paper.get('abstract', ''))):
                old_len = len(paper.get('abstract', ''))
                paper['abstract'] = best_match['abstract']
                print(f"Enhanced abstract for '{paper['title']}' ({old_len} → {len(paper['abstract'])} chars)")
                enhanced = True
            
            # Enhance arXiv ID
            if best_match.get('arxiv', '').strip() and not paper.get('arxiv', '').strip():
                paper['arxiv'] = best_match['arxiv']
                print(f"Enhanced arXiv ID for '{paper['title']}': {paper['arxiv']}")
                enhanced = True
            
            # Enhance URL
            if best_match.get('url', '').strip() and not paper.get('url', '').strip():
                paper['url'] = best_match['url']
                print(f"Enhanced URL for '{paper['title']}': {paper['url']}")
                enhanced = True
            
            # Enhance authors
            if best_match.get('authors', '').strip() and not paper.get('authors', '').strip():
                paper['authors'] = best_match['authors']
                print(f"Enhanced authors for '{paper['title']}': {paper['authors']}")
                enhanced = True
            
            if enhanced:
                enhanced_count += 1
    
    print(f"\nEnhanced {enhanced_count} papers with CV data")
    print(f"Papers with abstracts: {len([p for p in all_papers if len(p.get('abstract', '')) > 200])}")
    print(f"Papers with arXiv IDs: {len([p for p in all_papers if p.get('arxiv', '').strip()])}")
    
    return all_papers

def update_hugo_publications(papers_data, pubs_dir):
    """Update Hugo publication files"""
    pubs_path = Path(pubs_dir)
    
    # Clear existing files (except _index.md)
    for md_file in pubs_path.glob("*.md"):
        if md_file.name != "_index.md":
            md_file.unlink()
    
    # Create new files
    for i, paper in enumerate(papers_data):
        # Generate filename from title
        title_slug = re.sub(r'[^\w\s-]', '', paper.get('title', '').lower())
        title_slug = re.sub(r'[-\s]+', '-', title_slug).strip('-')
        year = paper.get('year', paper.get('date', '')[:4] if paper.get('date') else 'unknown')
        filename = f"{year}-{title_slug}.md" if title_slug else f"{year}-paper-{i}.md"
        filename = filename.replace('--', '-')
        
        file_path = pubs_path / filename
        
        # Create frontmatter
        content = f"""---
title: "{paper.get('title', '')}"
date: {paper.get('date', year + '-01-01' if year.isdigit() else '2000-01-01')}
type: "{paper.get('type', 'article')}"
authors: "{paper.get('authors', '')}"
journal: "{paper.get('journal', '')}"
year: "{year}"
"""
        
        # Add optional fields if present
        if paper.get('arxiv', '').strip():
            content += f'arxiv: "{paper.get("arxiv")}"\n'
        if paper.get('url', '').strip():
            content += f'url: "{paper.get("url")}"\n'
        
        content += "---\n\n"
        
        # Add publication info
        authors = paper.get('authors', '')
        journal = paper.get('journal', '')
        year = paper.get('year', '')
        
        if authors:
            content += f"**Authors:** {authors}\n\n"
        if journal:
            content += f"**Published in:** {journal}"
            if year:
                content += f" ({year})"
            content += "\n\n"
        
        # Add arXiv link
        if paper.get('arxiv', '').strip():
            arxiv_id = paper.get('arxiv')
            content += f"[arXiv:{arxiv_id}](https://arxiv.org/abs/{arxiv_id})\n\n"
        
        # Add URL link
        if paper.get('url', '').strip() and 'arxiv.org' not in paper.get('url', ''):
            content += f"[Publisher Link]({paper.get('url')})\n\n"
        
        # Add abstract
        if paper.get('abstract', '').strip():
            content += f"### Abstract\n\n{paper.get('abstract')}\n"
        
        # Write file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    print(f"Updated {len(papers_data)} Hugo publication files")

def main():
    # Paths
    cv_master_dir = "/root/clawd/data/cv-master"
    hugo_pubs_dir = "/tmp/academic-site/content/publications"
    
    print("=== Enhancing Publications with CV Master Data ===")
    
    # Read data sources
    unified_pubs = read_tsv(f"{cv_master_dir}/unified-publications.tsv")
    cv_pubs = read_tsv(f"{cv_master_dir}/cv-papers.tsv")
    hugo_pubs = read_hugo_publications(hugo_pubs_dir)
    
    # Debug: print what we have
    print(f"CV papers sample: {cv_pubs[0] if cv_pubs else 'None'}")
    
    # Merge and enhance
    enhanced_pubs = merge_and_enhance_publications(unified_pubs, cv_pubs, hugo_pubs)
    
    # Update Hugo files
    print("\n=== Updating Hugo publication files ===")
    update_hugo_publications(enhanced_pubs, hugo_pubs_dir)
    
    print(f"\n=== Complete! Processed {len(enhanced_pubs)} publications ===")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)