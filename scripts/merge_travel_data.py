#!/usr/bin/env python3

import csv
import json
import os
import sys
import re
import subprocess
from datetime import datetime
from pathlib import Path

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

def read_hugo_travel(travel_dir):
    """Read existing Hugo travel files and extract metadata"""
    data = []
    travel_path = Path(travel_dir)
    
    if not travel_path.exists():
        print(f"Warning: {travel_dir} not found")
        return data
    
    for md_file in travel_path.glob("*.md"):
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
                    
                    # Extract URL from body if available
                    url = extract_url_from_body(body)
                    
                    # Convert to standard format
                    travel = {
                        'title': metadata.get('title', ''),
                        'location': metadata.get('location', ''),
                        'date': metadata.get('date', ''),
                        'date_end': metadata.get('date_end', ''),
                        'url': url,
                        'tags': metadata.get('tags', ''),
                        'source': f'hugo:{md_file.name}'
                    }
                    data.append(travel)
        except Exception as e:
            print(f"Error reading {md_file}: {e}")
    
    print(f"Read {len(data)} records from Hugo files")
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
    """Normalize date to YYYY-MM-DD format"""
    if not date_str:
        return ""
    
    # If already in YYYY-MM-DD format, return as is
    if re.match(r'\d{4}-\d{2}-\d{2}$', date_str):
        return date_str
    
    # Handle ISO datetime format (extract date part)
    if re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z?', date_str):
        return date_str[:10]
    
    return date_str

def create_dedup_key(travel):
    """Create a key for deduplication based on location + start date"""
    location = travel.get('location', '').lower().strip()
    date = normalize_date(travel.get('date', ''))
    
    return f"{location}|{date}"

def merge_and_deduplicate(unified_data, cv_data, hugo_data):
    """Merge all data sources and deduplicate"""
    all_travel = []
    seen_keys = set()
    
    # Add source information
    for travel in unified_data:
        travel['source'] = 'unified'
    for travel in cv_data:
        travel['source'] = 'cv'
    # hugo_data already has source info
    
    # Merge all data
    all_data = unified_data + cv_data + hugo_data
    
    for travel in all_data:
        # Normalize dates
        travel['date'] = normalize_date(travel.get('date', ''))
        travel['date_end'] = normalize_date(travel.get('date_end', ''))
        
        # Create dedup key
        key = create_dedup_key(travel)
        
        if key not in seen_keys:
            seen_keys.add(key)
            all_travel.append(travel)
        else:
            print(f"Duplicate found: {travel['location']} on {travel['date']} (source: {travel['source']})")
    
    # Sort by start date (newest first)
    all_travel.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    print(f"After deduplication: {len(all_travel)} unique travel entries")
    return all_travel

def update_google_sheet(travel_data):
    """Update the Google Sheet with merged travel data"""
    # Prepare data for Google Sheets
    sheet_rows = []
    
    # Header row
    sheet_rows.append(['title', 'location', 'date', 'date_end', 'url', 'tags'])
    
    for travel in travel_data:
        row = [
            travel.get('title', ''),
            travel.get('location', ''),
            travel.get('date', ''),
            travel.get('date_end', ''),
            travel.get('url', ''),
            travel.get('tags', '')
        ]
        sheet_rows.append(row)
    
    print(f"Prepared {len(sheet_rows)-1} data rows for Google Sheets")
    
    # Construct the range - use sheet name "travel"
    spreadsheet_id = "1X7VKV3pwBoYjQoUHpxckYJAgaErCYkevc47bJoMV0J0"
    range_name = "travel!A:F"  # Clear all columns A through F
    
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
        
        # Now update with new data using row-by-row approach
        print("Updating sheet with new data...")
        
        for i, row in enumerate(sheet_rows):
            # Construct range for this specific row  
            start_col = 'A'
            end_col = chr(ord('A') + len(row) - 1)  # F for 6 columns
            row_range = f"travel!{start_col}{i+1}:{end_col}{i+1}"
            
            # Convert row values to strings and escape any quotes
            escaped_values = [str(cell).replace('"', '""') for cell in row]
            
            # Create command with separate arguments for each cell value
            cmd_parts = [
                'bash', '-c',
                f'source ~/.bashrc && '
                f'GOG_KEYRING_PASSWORD="$GOG_KEYRING_PASSWORD" '
                f'gog sheets update "{spreadsheet_id}" "{row_range}" '
            ]
            
            # Add each value as a separate argument
            cmd_args = ' '.join(f'"{val}"' for val in escaped_values)
            cmd_parts[2] += cmd_args + f' --account manolo.assistant@gmail.com'
            
            result = subprocess.run(cmd_parts, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Failed to update row {i+1}: {result.stderr}")
                print(f"Command: {' '.join(cmd_parts)}")
                return False
        
        print(f"Successfully updated {len(sheet_rows)} rows")
        return True
            
    except Exception as e:
        print(f"Error updating Google Sheet: {e}")
        return False

def update_hugo_files(travel_data, travel_dir):
    """Update Hugo content files based on merged data"""
    travel_path = Path(travel_dir)
    
    # Clear existing files (except _index.md)
    for md_file in travel_path.glob("*.md"):
        if md_file.name != "_index.md":
            md_file.unlink()
            
    # Create new files
    for i, travel in enumerate(travel_data):
        # Generate filename
        title_slug = re.sub(r'[^\w\s-]', '', travel.get('title', '').lower())
        title_slug = re.sub(r'[-\s]+', '-', title_slug).strip('-')
        date_part = travel.get('date', '') if travel.get('date') else f"unknown-{i}"
        filename = f"{date_part}-{title_slug}.md" if title_slug else f"{date_part}-travel-{i}.md"
        filename = filename.replace('--', '-')
        
        file_path = travel_path / filename
        
        # Create content
        content = f"""---
title: "{travel.get('title', '')}"
date: {travel.get('date', '') if travel.get('date') else '2000-01-01'}
params:
  location: "{travel.get('location', '')}"
  date_end: "{travel.get('date_end', '')}"
  tags: "{travel.get('tags', 'Past')}"
---

**{travel.get('location', '')}** — {travel.get('date', '')} to {travel.get('date_end', '') if travel.get('date_end') else 'TBD'}

"""
        
        # Add URL if available
        if travel.get('url') and travel.get('url') not in ['#', '']:
            content += f"[Event page]({travel.get('url')})\n\n"
        
        # Write file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    print(f"Updated {len(travel_data)} Hugo travel files")

def main():
    # Paths
    data_dir = "/root/clawd/data/website-rebuild"
    hugo_travel_dir = "/tmp/academic-site/content/travel"
    
    print("=== Merging Travel Data ===")
    
    # Read data from all sources
    unified_data = read_csv(f"{data_dir}/unified-travel.csv")
    cv_data = read_csv(f"{data_dir}/cv-travel.csv") 
    hugo_data = read_hugo_travel(hugo_travel_dir)
    
    # Merge and deduplicate
    merged_travel = merge_and_deduplicate(unified_data, cv_data, hugo_data)
    
    # Update Google Sheet
    print("\n=== Updating Google Sheet ===")
    if update_google_sheet(merged_travel):
        print("Google Sheet updated successfully")
    else:
        print("Failed to update Google Sheet, but continuing with Hugo file updates...")
    
    # Update Hugo files
    print("\n=== Updating Hugo files ===")
    update_hugo_files(merged_travel, hugo_travel_dir)
    
    print(f"\n=== Complete! Processed {len(merged_travel)} travel entries ===")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)