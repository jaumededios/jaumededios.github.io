#!/usr/bin/env python3

import json
import os
import re
from pathlib import Path

def parse_cv_papers_manually():
    """Manually parse the CV papers TSV file"""
    papers = []
    
    filepath = "/root/clawd/data/cv-master/cv-papers.tsv"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Skip first line (headers) and parse each subsequent line
    for line in lines[1:]:
        if not line.strip():
            continue
        
        # Split by tab and clean up
        parts = line.strip().split('\t')
        if len(parts) >= 6:
            paper = {
                'title': parts[1].strip() if len(parts) > 1 else '',
                'type': parts[2].strip() if len(parts) > 2 else '',
                'arxiv': parts[3].strip() if len(parts) > 3 else '',
                'url': parts[4].strip() if len(parts) > 4 else '',
                'abstract': parts[5].strip() if len(parts) > 5 else '',
                'authors': parts[6].strip() if len(parts) > 6 else ''
            }
            
            # Only add if we have a title
            if paper['title']:
                papers.append(paper)
    
    print(f"Parsed {len(papers)} papers from CV data")
    return papers

def title_to_slug(title):
    """Convert title to a filename-friendly slug"""
    slug = title.lower()
    # Remove punctuation and special characters
    slug = re.sub(r'[^\w\s-]', '', slug)
    # Replace spaces and multiple hyphens with single hyphens
    slug = re.sub(r'[-\s]+', '-', slug).strip('-')
    return slug

def extract_year_from_arxiv(arxiv_id):
    """Extract year from arXiv ID like 'arXiv:2412.06344'"""
    if not arxiv_id:
        return None
    
    # Remove arXiv: prefix if present
    clean_id = arxiv_id.replace('arXiv:', '').strip()
    
    # arXiv IDs like YYMM.NNNNN where YY is year (since 2007)
    if re.match(r'^\d{4}\.\d{4,5}$', clean_id):
        year_part = clean_id[:2]
        # Convert to full year (07-99 = 2007-2099, 00-06 = 2000-2006)
        if int(year_part) <= 6:
            return f"20{year_part:0>2}"
        else:
            return f"20{year_part}"
    
    return None

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

def create_publication_file(paper, output_dir, image_mapping=None):
    """Create a Hugo publication file for a paper"""
    
    title = paper.get('title', 'Untitled')
    if not title or title == 'Untitled':
        return False
    
    # Create filename
    slug = title_to_slug(title)
    year = extract_year_from_arxiv(paper.get('arxiv', '')) or 'unknown'
    filename = f"{year}-{slug}.md"
    
    file_path = output_dir / filename
    
    # Create frontmatter
    content = f"""---
title: "{title}"
date: {year}-01-01
type: "{paper.get('type', 'article').lower()}"
authors: "{paper.get('authors', '')}"
year: "{year}"
"""
    
    # Add optional fields
    if paper.get('arxiv', '').strip():
        arxiv_clean = paper.get('arxiv').replace('arXiv:', '').strip()
        content += f'arxiv: "{arxiv_clean}"\n'
        
    if paper.get('url', '').strip():
        content += f'url: "{paper.get("url")}"\n'
    
    # Try to find matching featured image
    featured_image = None
    if image_mapping:
        best_match = None
        best_similarity = 0.0
        
        for img_title, img_data in image_mapping.items():
            similarity = title_similarity(title, img_title)
            if similarity > best_similarity and similarity > 0.5:  # Lower threshold
                best_similarity = similarity
                best_match = img_data
        
        if best_match:
            content += f'featured_image: "{best_match["path"]}"\n'
            featured_image = best_match
            print(f"  → Matched image: {best_match['filename']} (similarity: {best_similarity:.2f})")
    
    content += "---\n\n"
    
    # Add featured image if found
    if featured_image:
        content += f"![Featured Image]({featured_image['path']})\n\n"
    
    # Add publication info
    authors = paper.get('authors', '')
    year_str = year if year != 'unknown' else ''
    
    if authors:
        content += f"**Authors:** {authors}\n\n"
    
    if paper.get('type', ''):
        content += f"**Type:** {paper.get('type')}"
        if year_str:
            content += f" ({year_str})"
        content += "\n\n"
    
    # Add arXiv link
    if paper.get('arxiv', '').strip():
        arxiv_clean = paper.get('arxiv').replace('arXiv:', '').strip()
        content += f"[arXiv:{arxiv_clean}](https://arxiv.org/abs/{arxiv_clean})\n\n"
    
    # Add URL link if it's not arXiv
    if paper.get('url', '').strip() and 'arxiv.org' not in paper.get('url', ''):
        content += f"[Publisher Link]({paper.get('url')})\n\n"
    
    # Add abstract
    if paper.get('abstract', '').strip():
        content += f"## Abstract\n\n{paper.get('abstract')}\n"
    
    # Write file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def main():
    """Create publication files from CV data with images"""
    
    output_dir = Path("/tmp/academic-site/content/publications")
    
    print("=== Creating Publications from CV Data with Images ===")
    
    # Parse CV papers manually
    cv_papers = parse_cv_papers_manually()
    
    if not cv_papers:
        print("No CV papers data found!")
        return False
    
    # Load image mapping
    image_mapping = None
    mapping_file = Path("/tmp/academic-site/static/img/papers/image_mapping.json")
    if mapping_file.exists():
        with open(mapping_file, 'r') as f:
            image_mapping = json.load(f)
        print(f"Loaded image mapping with {len(image_mapping)} images")
    
    # Clear existing publication files (except _index.md)
    for pub_file in output_dir.glob("*.md"):
        if pub_file.name != "_index.md":
            pub_file.unlink()
    
    # Create publication files
    created_count = 0
    for paper in cv_papers:
        if create_publication_file(paper, output_dir, image_mapping):
            title_display = paper.get('title', '')[:60] + '...' if len(paper.get('title', '')) > 60 else paper.get('title', '')
            print(f"✓ Created: {title_display}")
            created_count += 1
    
    print(f"\n=== Complete! Created {created_count} publication files with images ===")
    
    # Summary
    with_images = 0
    for pub_file in output_dir.glob("*.md"):
        if pub_file.name != "_index.md":
            with open(pub_file, 'r') as f:
                content = f.read()
                if 'featured_image:' in content:
                    with_images += 1
    
    print(f"Publications with featured images: {with_images}/{created_count}")
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)