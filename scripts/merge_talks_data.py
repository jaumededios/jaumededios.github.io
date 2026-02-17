#!/usr/bin/env python3

import csv
import json
import os
import sys
import re
import subprocess
from datetime import datetime
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import time

def read_csv(filepath):
    """Read CSV file and return list of dictionaries"""
    data = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
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

def read_hugo_talks(talks_dir):
    """Read existing Hugo talk files and extract metadata"""
    data = []
    talks_path = Path(talks_dir)
    
    if not talks_path.exists():
        print(f"Warning: {talks_dir} not found")
        return data
    
    for md_file in talks_path.glob("*.md"):
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
                            
                            # Handle nested params
                            if key == 'params':
                                continue
                            elif line.startswith('  '):
                                # This is a param
                                param_key = key.strip()
                                metadata[param_key] = value
                            else:
                                metadata[key] = value
                    
                    # Extract abstract from body
                    abstract = ""
                    abstract_match = re.search(r'### Abstract\s*\n\n(.+?)(?:\n\n###|\Z)', body, re.DOTALL)
                    if abstract_match:
                        abstract = abstract_match.group(1).strip()
                    
                    # Convert to standard format
                    talk = {
                        'title': metadata.get('title', ''),
                        'type': metadata.get('type', ''),
                        'event': metadata.get('event', ''),
                        'date': metadata.get('date', ''),
                        'url': extract_url_from_body(body),
                        'abstract': abstract,
                        'tags': metadata.get('tags', ''),
                        'source': f'hugo:{md_file.name}'
                    }
                    data.append(talk)
        except Exception as e:
            print(f"Error reading {md_file}: {e}")
    
    print(f"Read {len(data)} records from Hugo files")
    return data

def read_vita_talks(filepath):
    """Read vita-talks.tsv and convert to standard format (manual parsing due to multiline cells)"""
    
    # Manually define the vita talks data since TSV has multiline cells
    talk_entries = [
        {
            'tag': 'Decoupling_Exposition_MSR',
            'title': 'Decoupling and applications: from PDEs to Number Theory.',
            'type': 'Expository',
            'abstract': 'Decoupling estimates were introduced by Wolff in order to improve local smoothing estimates for the wave equation. Since then, they have found multiple applications in analysis: from PDEs and restriction theory, to additive number theory, where Bourgain, Demeter and Guth used decoupling-type estimates to prove the main conjecture of the Vinogradov mean value theorem for d>3. In this talk I will explain what decoupling estimates are, I will talk about its applications to the Vinogradov Mean Value theorem and local smoothing, and I will explain the main ingredients that go into (most) decoupling proofs.',
        },
        {
            'tag': 'Sampling_Hard',
            'title': 'Lower bounds for strongly Log-concave Sampling',
            'type': 'Research',
            'abstract': 'Log-concave sampling has witnessed remarkable algorithmic advances in recent years, but the corresponding problem of proving lower bounds for this task has remained elusive, with lower bounds previously known only in dimension one. In this talk, I will establish query lower bounds for sampling from strongly log-concave and log-smooth distributions in dimension d≥2, showing that it requires Ω(log κ) queries, which is sharp in any constant dimension. Based on joint work with Sinho Chewi, Jerry Li, Chen Lu, and Shyam Narayanan.',
        },
        {
            'tag': 'Decoupling_Additive',
            'title': 'Decoupling, Cantor sets, and additive combinatorics',
            'type': 'Research',
            'abstract': 'Decoupling and discrete restriction inequalities have been very fruitful in recent years to solve problems in additive combinatorics and analytic number theory. In this talk I will present some work in decoupling for Cantor sets, including Cantor sets on a parabola, decoupling for product sets, and give applications of these results to additive combinatorics. Time permitting, I will present some open problems. Based on joint work with Alan Chang, Rachel Greenfeld, Asgar Jamneshan, José Madrid, Zane Li and Paata Ivanisvili.',
        },
        {
            'tag': 'Decoupling_Cantor',
            'title': 'Decoupling for Cantor sets on the parabola',
            'type': 'Research',
            'abstract': 'Decoupling estimates aim to study the "amount of cancellation" that can occur when we add up functions whose Fourier transforms are supported in different regions of space. In this talk I will describe decoupling estimates for a Cantor set supported in the parabola. I will discuss how both curvature and sparsity (or lack of arithmetic structure) can separately give rise to decoupling estimates, and how these two sources of "cancellation" can be combined to obtain improved estimates for sets that have both sparsity and curvature. No knowledge of what a decoupling estimate is will be assumed. Based on joint work with Alan Chang, Rachel Greenfeld, Asgar Jamneshan, José Madrid and Zane Li.',
        },
        {
            'tag': 'Sensitivity',
            'title': 'The sensitivity theorem',
            'type': 'Expository',
            'abstract': 'The sensitivity theorem (former sensitivity conjecture) relates multiple ways to quantify the complexity, or lack of "smoothness", of a boolean function f:{0,1}^n -> f : The minimum degree of a polynomial p(x):R^n -> R that extends f, the sensitivity s(f), and the block sensitivity bs(f). In 2019, H.Huang solved the conjecture with a remarkably short proof. I will give a self-contained explanation of this proof, and motivate the importance of the (former) conjecture by relating it to other measures of complexity for boolean functions.',
        },
        {
            'tag': 'Uniformity',
            'title': 'Uniform boundedness in operators parametrized by polynomial curves',
            'type': 'Research',
            'abstract': 'Multiple results in harmonic analysis involving integrals of functions over curves (such as restriction theorems, convolution estimates, maximal function estimates or decoupling estimates) depend strongly on the non-vanishing of the torsion of the associated curve. Over the past years there has been considerable interest in extending these results to a degenerate case where the torsion vanishes at a finite number of points by using the affine arc-length as an alternative integration measure. As a model case, multiple results have been proven in which the coordinate functions of the curve are polynomials. In this case one expects the bounds of the operators to depend only on the degree of the polynomial. In this talk I will introduce and motivate the concept of affine arclength measure, provide new decomposition theorems for polynomial curves over characteristic zero local fields, and provide some applications to uniformity results in harmonic analysis.',
        },
        {
            'tag': 'Sparsity_NN',
            'title': 'On Sparsity in Overparametrised Shallow ReLU Networks',
            'type': 'Research',
            'abstract': 'The analysis of neural network training beyond their linearization regime remains an outstanding open question, even in the simplest setup of a single hidden-layer. The limit of infinitely wide networks provides an appealing route forward through the mean-field perspective, but a key challenge is to bring learning guarantees back to the finite-neuron setting, where practical algorithms operate. Towards closing this gap, and focusing on shallow neural networks, in this work we study the ability of different regularisation strategies to capture solutions requiring only a finite amount of neurons, even on the infinitely wide regime. Specifically, we consider (i) a form of implicit regularisation obtained by injecting noise into training targets, and (ii) the variation-norm regularisation, compatible with the mean-field scaling. Under mild assumptions on the activation function (satisfied for instance with ReLUs), we establish that both schemes are minimised by functions having only a finite number of neurons, irrespective of the amount of overparametrisation. We study the consequences of such property and describe the settings where one form of regularisation is favorable over the other.',
        }
    ]
    
    # Convert to standard format
    data = []
    for talk in talk_entries:
        converted = {
            'title': talk['title'],
            'type': talk['type'],
            'event': '',
            'date': '',
            'url': '',
            'abstract': talk['abstract'],
            'tags': '',
            'source': 'vita',
            'vita_tag': talk['tag']
        }
        data.append(converted)
    
    print(f"Read {len(data)} records from vita talks")
    return data

def extract_url_from_body(body):
    """Extract URL from markdown body"""
    # Look for [Event page](URL) pattern
    url_match = re.search(r'\[Event page\]\(([^)]+)\)', body)
    if url_match:
        return url_match.group(1)
    
    # Look for any markdown link
    url_match = re.search(r'\[([^\]]+)\]\(([^)]+)\)', body)
    if url_match:
        return url_match.group(2)
    
    return ""

def normalize_date(date_str):
    """Normalize date to ISO format YYYY-MM-DDTHH:MM:SSZ"""
    if not date_str:
        return ""
    
    # If already in ISO format, return as is
    if re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z?', date_str):
        if not date_str.endswith('Z'):
            date_str += 'Z'
        return date_str
    
    # Handle YYYY-MM-DD format
    if re.match(r'\d{4}-\d{2}-\d{2}$', date_str):
        return f"{date_str}T12:00:00Z"
    
    return date_str

def create_dedup_key(talk):
    """Create a key for deduplication based on title + date"""
    title = talk.get('title', '').lower().strip()
    date = talk.get('date', '')
    
    # Extract just the date part (YYYY-MM-DD)
    date_match = re.match(r'(\d{4}-\d{2}-\d{2})', date)
    if date_match:
        date_part = date_match.group(1)
    else:
        date_part = date
    
    return f"{title}|{date_part}"

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

def merge_and_deduplicate(unified_data, cv_data, hugo_data, vita_data):
    """Merge all data sources and deduplicate, prioritizing vita abstracts"""
    all_talks = []
    seen_keys = set()
    
    # Add source information
    for talk in unified_data:
        talk['source'] = 'unified'
    for talk in cv_data:
        talk['source'] = 'cv'
    # hugo_data already has source info
    # vita_data already has source info
    
    # First, create a map of vita talks by normalized title for abstract enhancement
    vita_by_title = {}
    for vita_talk in vita_data:
        title = vita_talk.get('title', '').lower().strip()
        if title and vita_talk.get('abstract', '').strip():
            vita_by_title[title] = vita_talk
    
    # Merge non-vita data first
    all_data = unified_data + cv_data + hugo_data
    
    for talk in all_data:
        # Normalize date
        talk['date'] = normalize_date(talk.get('date', ''))
        
        # Try to enhance abstract from vita data
        talk_title = talk.get('title', '').lower().strip()
        best_match = None
        best_similarity = 0.0
        
        # Look for exact or similar title match in vita data
        for vita_title, vita_talk in vita_by_title.items():
            similarity = title_similarity(talk_title, vita_title)
            if similarity > best_similarity and similarity > 0.7:  # 70% similarity threshold
                best_similarity = similarity
                best_match = vita_talk
        
        # Use vita abstract if we found a good match and current abstract is weak
        if (best_match and 
            best_match.get('abstract', '').strip() and 
            len(best_match.get('abstract', '')) > len(talk.get('abstract', ''))):
            
            old_abstract = talk.get('abstract', '')[:50] + "..." if talk.get('abstract', '') else "None"
            talk['abstract'] = best_match['abstract']
            print(f"Enhanced abstract for '{talk['title']}' (similarity: {best_similarity:.2f})")
            print(f"  Old: {old_abstract}")
            print(f"  New: {best_match['abstract'][:100]}...")
        
        # Create dedup key
        key = create_dedup_key(talk)
        
        if key not in seen_keys:
            seen_keys.add(key)
            all_talks.append(talk)
        else:
            print(f"Duplicate found: {talk['title']} on {talk['date']} (source: {talk['source']})")
    
    # Sort by date (newest first)
    all_talks.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    print(f"After deduplication: {len(all_talks)} unique talks")
    print(f"Abstract enhancements: {len([t for t in all_talks if len(t.get('abstract', '')) > 200])} talks have substantial abstracts")
    return all_talks

def search_for_abstract(talk):
    """Search online for talk abstract if missing"""
    if talk.get('abstract', '').strip():
        return talk['abstract']  # Already has abstract
    
    url = talk.get('url', '')
    if not url or url in ['#', '']:
        return ""
    
    try:
        print(f"Searching for abstract: {talk['title']} at {url}")
        
        # Add User-Agent to avoid blocks
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text()
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            
            # Look for abstracts - search for paragraphs that mention the speaker or contain mathematical terms
            title_words = talk['title'].lower().split()
            abstract_indicators = ['abstract', 'summary', talk['title'].lower()]
            
            potential_abstracts = []
            for i, line in enumerate(lines):
                line_lower = line.lower()
                if any(indicator in line_lower for indicator in abstract_indicators):
                    # Look for a substantial paragraph nearby
                    for j in range(max(0, i-3), min(len(lines), i+5)):
                        candidate = lines[j]
                        if len(candidate) > 100:  # Substantial text
                            potential_abstracts.append(candidate)
            
            if potential_abstracts:
                # Return the longest candidate
                abstract = max(potential_abstracts, key=len)
                if len(abstract) > 50:
                    print(f"Found abstract for {talk['title']}")
                    return abstract[:1000]  # Limit length
        
        time.sleep(1)  # Be nice to servers
        
    except Exception as e:
        print(f"Error searching for abstract at {url}: {e}")
    
    return ""

def update_google_sheet(talks_data):
    """Update the Google Sheet with merged talks data"""
    # Prepare data for Google Sheets - convert to flat list of values for each row
    sheet_rows = []
    
    # Header row
    sheet_rows.append(['title', 'type', 'event', 'date', 'url', 'abstract'])
    
    for talk in talks_data:
        row = [
            talk.get('title', ''),
            talk.get('type', ''),
            talk.get('event', ''),
            talk.get('date', ''),
            talk.get('url', ''),
            talk.get('abstract', '')
        ]
        sheet_rows.append(row)
    
    print(f"Prepared {len(sheet_rows)-1} data rows for Google Sheets")
    
    # Construct the range - assuming gid 508483272 corresponds to a sheet name
    # We need to clear a large range first and then update
    spreadsheet_id = "1X7VKV3pwBoYjQoUHpxckYJAgaErCYkevc47bJoMV0J0"
    range_name = "Talks!A:F"  # Clear all columns A through F
    
    try:
        # First clear the existing data
        print("Clearing existing sheet data...")
        clear_cmd = [
            'bash', '-c',
            f'source ~/.bashrc && '
            f'GOG_KEYRING_PASSWORD="$GOG_KEYRING_PASSWORD" '
            f'gog sheets clear "{spreadsheet_id}" "{range_name}" '
            f'--account manolo.assistant@gmail.com'
        ]
        result = subprocess.run(clear_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Clear command failed: {result.stderr}")
            return False
        
        # Now update with new data using the update command
        print("Updating sheet with new data...")
        
        # Prepare the values as command line arguments
        values_args = []
        for row in sheet_rows:
            # Each row becomes a separate argument, with cells separated by tabs
            row_str = '\t'.join(str(cell) for cell in row)
            values_args.append(row_str)
        
        # Use a range starting from A1
        update_range = "Talks!A1:F"
        
        # Create the command
        update_cmd = [
            'bash', '-c',
            f'source ~/.bashrc && '
            f'GOG_KEYRING_PASSWORD="$GOG_KEYRING_PASSWORD" '
            f'gog sheets update "{spreadsheet_id}" "{update_range}" '
        ] + values_args + [
            f'--account manolo.assistant@gmail.com'
        ]
        
        # Actually, let me use a different approach with a temp file
        temp_file = '/tmp/talks_update.tsv'
        with open(temp_file, 'w', encoding='utf-8') as f:
            for row in sheet_rows:
                f.write('\t'.join(str(cell) for cell in row) + '\n')
        
        # Use the file as input
        update_cmd = [
            'bash', '-c',
            f'source ~/.bashrc && '
            f'GOG_KEYRING_PASSWORD="$GOG_KEYRING_PASSWORD" '
            f'gog sheets update "{spreadsheet_id}" "{update_range}" '
            f'"$(cat {temp_file})" '
            f'--account manolo.assistant@gmail.com'
        ]
        
        result = subprocess.run(update_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Update command failed: {result.stderr}")
            # Try a different approach - update row by row
            return update_sheet_row_by_row(spreadsheet_id, sheet_rows)
        
        print("Google Sheet updated successfully")
        
        # Clean up temp file
        try:
            os.remove(temp_file)
        except:
            pass
            
    except Exception as e:
        print(f"Error updating Google Sheet: {e}")
        return False
    
    return True

def update_sheet_row_by_row(spreadsheet_id, sheet_rows):
    """Fallback method to update sheet row by row"""
    print("Trying row-by-row update approach...")
    try:
        for i, row in enumerate(sheet_rows):
            row_range = f"Talks!A{i+1}:F{i+1}"
            row_str = '\t'.join(str(cell) for cell in row)
            
            cmd = [
                'bash', '-c',
                f'source ~/.bashrc && '
                f'GOG_KEYRING_PASSWORD="$GOG_KEYRING_PASSWORD" '
                f'gog sheets update "{spreadsheet_id}" "{row_range}" '
                f'"{row_str}" '
                f'--account manolo.assistant@gmail.com'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Failed to update row {i+1}: {result.stderr}")
                return False
        
        print(f"Successfully updated {len(sheet_rows)} rows")
        return True
        
    except Exception as e:
        print(f"Row-by-row update failed: {e}")
        return False

def update_hugo_files(talks_data, talks_dir):
    """Update Hugo content files based on merged data"""
    talks_path = Path(talks_dir)
    
    # Clear existing files (except _index.md)
    for md_file in talks_path.glob("*.md"):
        if md_file.name != "_index.md":
            md_file.unlink()
            
    # Create new files
    for i, talk in enumerate(talks_data):
        # Generate filename
        title_slug = re.sub(r'[^\w\s-]', '', talk.get('title', '').lower())
        title_slug = re.sub(r'[-\s]+', '-', title_slug).strip('-')
        date_part = talk.get('date', '')[:10] if talk.get('date') else f"unknown-{i}"
        filename = f"{date_part}-{title_slug}.md" if title_slug else f"{date_part}-talk-{i}.md"
        filename = filename.replace('--', '-')
        
        file_path = talks_path / filename
        
        # Create content
        content = f"""---
title: "{talk.get('title', '')}"
date: {talk.get('date', '')[:10] if talk.get('date') else '2000-01-01'}
params:
  type: "{talk.get('type', '')}"
  event: "{talk.get('event', '')}"
  tags: "{talk.get('tags', 'Past')}"
---

**{talk.get('event', '')}** — {talk.get('type', '')}, {talk.get('date', '')[:10] if talk.get('date') else 'Date TBD'}

"""
        
        # Add URL if available
        if talk.get('url') and talk.get('url') not in ['#', '']:
            content += f"[Event page]({talk.get('url')})\n\n"
        
        # Add abstract if available
        if talk.get('abstract', '').strip():
            content += f"### Abstract\n\n{talk.get('abstract')}\n"
        
        # Write file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    print(f"Updated {len(talks_data)} Hugo talk files")

def main():
    # Paths
    data_dir = "/root/clawd/data/website-rebuild"
    hugo_talks_dir = "/tmp/academic-site/content/talks"
    
    print("=== Merging Talks Data ===")
    
    # Read data from all sources
    unified_data = read_csv(f"{data_dir}/unified-talks.csv")
    cv_data = read_csv(f"{data_dir}/cv-talks.csv") 
    hugo_data = read_hugo_talks(hugo_talks_dir)
    vita_data = read_vita_talks(f"{data_dir}/vita-talks.tsv")
    
    # Merge and deduplicate
    merged_talks = merge_and_deduplicate(unified_data, cv_data, hugo_data, vita_data)
    
    # Search for missing abstracts (only for talks with URLs)
    print("\n=== Searching for missing abstracts ===")
    for talk in merged_talks:
        if not talk.get('abstract', '').strip() and talk.get('url') and talk.get('url') not in ['#', '']:
            abstract = search_for_abstract(talk)
            if abstract:
                talk['abstract'] = abstract
    
    # Update Google Sheet
    print("\n=== Updating Google Sheet ===")
    if update_google_sheet(merged_talks):
        print("Google Sheet updated successfully")
    else:
        print("Failed to update Google Sheet")
        return False
    
    # Update Hugo files
    print("\n=== Updating Hugo files ===")
    update_hugo_files(merged_talks, hugo_talks_dir)
    
    print(f"\n=== Complete! Processed {len(merged_talks)} talks ===")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)