#!/usr/bin/env python3

import json
import os
import re
from pathlib import Path

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

def update_publication_with_image(pub_file, image_path, alt_text):
    """Update a publication markdown file to include featured image"""
    
    with open(pub_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse frontmatter
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            frontmatter = parts[1].strip()
            body = parts[2].strip()
            
            # Add featured image to frontmatter
            if 'featured_image:' not in frontmatter:
                frontmatter += f'\nfeatured_image: "{image_path}"'
            
            # Reconstruct content
            new_content = f"---\n{frontmatter}\n---\n\n"
            
            # Add image to body if not already there
            if f'![{alt_text}]' not in body and '![Featured Image]' not in body:
                # Add featured image at the top of the body content
                image_markdown = f"![Featured Image]({image_path})\n\n"
                new_content += image_markdown + body
            else:
                new_content += body
            
            # Write updated content
            with open(pub_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return True
    
    return False

def main():
    """Update publication files with featured images"""
    
    # Load image mapping
    mapping_file = Path("/tmp/academic-site/static/img/papers/image_mapping.json")
    if not mapping_file.exists():
        print("Error: Image mapping file not found. Run download_publication_images.py first.")
        return False
    
    with open(mapping_file, 'r') as f:
        image_mapping = json.load(f)
    
    # Find publication files
    pub_dir = Path("/tmp/academic-site/content/publications")
    if not pub_dir.exists():
        print("Error: Publications directory not found")
        return False
    
    updated_files = 0
    
    for pub_file in pub_dir.glob("*.md"):
        if pub_file.name == "_index.md":
            continue
        
        # Read the publication file to get the title
        with open(pub_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract title from frontmatter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = parts[1].strip()
                
                # Find title
                pub_title = ""
                for line in frontmatter.split('\n'):
                    line = line.strip()
                    if line.startswith('title:'):
                        pub_title = line.split(':', 1)[1].strip().strip('"').strip("'")
                        break
                
                if not pub_title:
                    continue
                
                # Find best matching image
                best_match = None
                best_similarity = 0.0
                
                for img_title, img_data in image_mapping.items():
                    similarity = title_similarity(pub_title, img_title)
                    if similarity > best_similarity and similarity > 0.7:  # 70% similarity threshold
                        best_similarity = similarity
                        best_match = img_data
                
                if best_match:
                    if update_publication_with_image(pub_file, best_match['path'], best_match['alt']):
                        print(f"Updated '{pub_title}' with image {best_match['filename']} (similarity: {best_similarity:.2f})")
                        updated_files += 1
                    else:
                        print(f"Failed to update '{pub_title}'")
                else:
                    print(f"No matching image found for '{pub_title}'")
    
    print(f"\nUpdated {updated_files} publication files with featured images")
    
    # Create an index file if it doesn't exist
    index_file = pub_dir / "_index.md"
    if not index_file.exists():
        index_content = """---
title: "Publications"
date: 2024-01-01
---

# Publications

Research papers and preprints by Jaume de Dios Pont.
"""
        with open(index_file, 'w') as f:
            f.write(index_content)
        print("Created publications index file")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)