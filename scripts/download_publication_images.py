#!/usr/bin/env python3

import requests
import os
import re
from pathlib import Path
import time

# Image data from browser extraction
publication_images = [
    {
        "src": "https://jaume.dedios.cat/publication/hotspots2024/featured_hu1278507089189442982.png",
        "alt": "Convex sets can have interior hot spots",
        "title": ""
    },
    {
        "src": "https://jaume.dedios.cat/publication/tiling2024/featured_hu7796568207230063441.png",
        "alt": "Periodicity and decidability of translational tilings by rational polygonal sets",
        "title": ""
    },
    {
        "src": "https://jaume.dedios.cat/publication/lowerbounds2023/featured_hu5700461784478294751.png",
        "alt": "Query lower bounds for log-concave sampling",
        "title": ""
    },
    {
        "src": "https://jaume.dedios.cat/publication/convexhull2022/featured_hu6553095740852176405.png",
        "alt": "A new proof of the description of the convex hull of space curves with totally positive torsion",
        "title": ""
    },
    {
        "src": "https://jaume.dedios.cat/publication/acorr2021/featured_hu14415168409685030709.png",
        "alt": "On classical inequalities for autocorrelations and autoconvolutions",
        "title": ""
    },
    {
        "src": "https://jaume.dedios.cat/publication/cantor2020/featured_hu13423700332841833467.png",
        "alt": "Decoupling for fractal subsets of the parabola",
        "title": ""
    },
    {
        "src": "https://jaume.dedios.cat/publication/bruna2020/featured_hu3354643144835629779.png",
        "alt": "On Sparsity in Overparametrised Shallow ReLU Networks",
        "title": ""
    },
    {
        "src": "https://jaume.dedios.cat/publication/curves2020/featured_hu1126761956328346450.png",
        "alt": "A geometric lemma for complex polynomial curves with applications in Fourier restriction theory",
        "title": ""
    },
    {
        "src": "https://jaume.dedios.cat/publication/bikes2019/featured_hu14834964260493575421.png",
        "alt": "Role Detection in Bicycle-Sharing Networks Using Multilayer Stochastic Block Models",
        "title": ""
    }
]

def download_image(url, filename):
    """Download an image from URL to filename"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        with open(filename, 'wb') as f:
            f.write(response.content)
        
        print(f"Downloaded: {filename}")
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def title_to_slug(title):
    """Convert title to a filename-friendly slug"""
    # Remove common title patterns and clean up
    slug = title.lower()
    # Remove punctuation and special characters
    slug = re.sub(r'[^\w\s-]', '', slug)
    # Replace spaces and multiple hyphens with single hyphens
    slug = re.sub(r'[-\s]+', '-', slug).strip('-')
    return slug

def main():
    """Download all publication images"""
    output_dir = Path("/tmp/academic-site/static/img/papers/")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    downloaded_images = {}
    
    for i, img_data in enumerate(publication_images):
        url = img_data['src']
        alt_text = img_data['alt']
        
        # Create filename from alt text
        slug = title_to_slug(alt_text)
        extension = url.split('.')[-1].split('?')[0]  # Get extension, remove query params
        filename = f"{slug}.{extension}"
        
        # Avoid filename collisions
        output_path = output_dir / filename
        counter = 1
        while output_path.exists():
            base_slug = slug.rsplit('-', 1)[0] if '-' in slug else slug
            filename = f"{base_slug}-{counter}.{extension}"
            output_path = output_dir / filename
            counter += 1
        
        # Download image
        if download_image(url, output_path):
            # Store mapping for later use
            downloaded_images[alt_text] = {
                'filename': filename,
                'path': f"/img/papers/{filename}",
                'alt': alt_text,
                'original_url': url
            }
            
            # Be nice to the server
            time.sleep(0.5)
    
    print(f"\nDownloaded {len(downloaded_images)} images successfully")
    
    # Save mapping for use in updating Hugo files
    import json
    mapping_file = output_dir / "image_mapping.json"
    with open(mapping_file, 'w') as f:
        json.dump(downloaded_images, f, indent=2)
    
    print(f"Saved image mapping to {mapping_file}")
    
    # Print summary
    print("\nImage mapping:")
    for alt_text, data in downloaded_images.items():
        print(f"  '{alt_text[:50]}...' → {data['path']}")

if __name__ == "__main__":
    main()