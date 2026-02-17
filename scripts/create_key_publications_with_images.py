#!/usr/bin/env python3

import json
from pathlib import Path

def main():
    """Create key publications with their corresponding images"""
    
    # Manually define the key publications that have images
    publications = [
        {
            'title': 'Convex sets can have interior hot spots',
            'authors': 'Jaume de Dios',
            'type': 'Preprint',
            'arxiv': '2412.06344',
            'url': 'https://arxiv.org/abs/2412.06344',
            'year': '2024',
            'abstract': 'The hot spots conjecture asserts that for any convex bounded domain Ω in R^d, the first non-trivial Neumann eigenfunction of the Laplace operator in Ω attains its maximum at the boundary. We construct counterexamples to the conjecture for all sufficiently large values of d. The construction is based on an extension of the conjecture from convex sets to log-concave measures.',
            'image': '/img/papers/convex-sets-can-have-interior-hot-spots.png'
        },
        {
            'title': 'Predicting quantum channels over general product distributions',
            'authors': 'Sitan Chen, Jaume de Dios, Jun-Ting Hsieh, Hsin-Yuan Huang, Jane Lange, Jerry Li',
            'type': 'Paper',
            'arxiv': '2409.03684',
            'url': 'https://arxiv.org/abs/2409.03684',
            'year': '2024',
            'abstract': 'We investigate the problem of predicting the output behavior of unknown quantum channels. Given query access to an n-qubit channel E and an observable O, we aim to learn the mapping ρ↦Tr(OE[ρ]) to within a small error for most ρ sampled from a distribution D.',
            'image': None  # No corresponding image found
        },
        {
            'title': 'Periodicity and decidability of translational tilings by rational polygonal sets',
            'authors': 'Jaume de Dios, José Madrid, Jan Grebík, Rachel Greenfeld',
            'type': 'Preprint',
            'arxiv': '2408.02151',
            'url': 'https://arxiv.org/abs/2408.02151',
            'year': '2024',
            'abstract': 'The periodic tiling conjecture asserts that if a region Σ⊂R^d tiles R^d by translations then it admits at least one fully periodic tiling.',
            'image': '/img/papers/periodicity-and-decidability-of-translational-tilings-by-rational-polygonal-sets.png'
        },
        {
            'title': 'Query lower bounds for log-concave sampling',
            'authors': 'Sinho Chewi, Jaume de Dios Pont, Jerry Li, Chen Lu, Shyam Narayanan',
            'type': 'Preprint',
            'arxiv': '2304.02599',
            'url': 'https://arxiv.org/abs/2304.02599',
            'year': '2023',
            'abstract': 'Log-concave sampling has witnessed remarkable algorithmic advances in recent years, but the corresponding problem of proving lower bounds for this task has remained elusive, with lower bounds previously known only in dimension one.',
            'image': '/img/papers/query-lower-bounds-for-log-concave-sampling.png'
        },
        {
            'title': 'Uniform Fourier Restriction Estimate for Simple Curves of Bounded Frequency',
            'authors': 'Jaume de Dios, Helge Jørgen Samuelsen',
            'type': 'Preprint',
            'arxiv': '2303.11693',
            'url': 'https://arxiv.org/abs/2303.11693',
            'year': '2023',
            'abstract': 'In this paper we prove a uniform Fourier restriction estimate over the class of simple curves where the last coordinate function can be written as a polynomial of bounded degree and frequency.',
            'image': None
        },
        {
            'title': 'A new proof of the description of the convex hull of space curves with totally positive torsion',
            'authors': 'Jaume de Dios, Paata Ivanisvili, José Madrid',
            'type': 'Preprint',
            'arxiv': '2201.12932',
            'url': 'https://arxiv.org/abs/2201.12932',
            'year': '2022',
            'abstract': 'We give new proofs of the description convex hulls of space curves γ:[a,b]→R^d having totally positive torsion.',
            'image': '/img/papers/a-new-proof-of-the-description-of-the-convex-hull-of-space-curves-with-totally-positive-torsion.png'
        },
        {
            'title': 'Additive energies on discrete cubes',
            'authors': 'Jaume de Dios, Rachel Greenfeld, Paata Ivanisvili, José Madrid',
            'type': 'Preprint',
            'arxiv': '2112.09352',
            'url': 'https://arxiv.org/abs/2112.09352',
            'year': '2021',
            'abstract': 'We prove that for d≥0 and k≥2, for any subset A of a discrete cube {0,1}^d, the k-higher energy of A is bounded.',
            'image': None
        },
        {
            'title': 'On classical inequalities for autocorrelations and autoconvolutions',
            'authors': 'Jaume de Dios, José Madrid',
            'type': 'Preprint',
            'arxiv': '2106.13873',
            'url': 'https://arxiv.org/abs/2106.13873',
            'year': '2021',
            'abstract': 'In this paper we study an autocorrelation inequality proposed by Barnard and Steinerberger. The study of these problems is motivated by applications to the Fourier transform.',
            'image': '/img/papers/on-classical-inequalities-for-autocorrelations-and-autoconvolutions.png'
        },
        {
            'title': 'Decoupling for fractal subsets of the parabola',
            'authors': 'Alan Chang, Jaume de Dios, Rachel Greenfeld, Asgar Jamneshan, Zane Kun Li, José Madrid',
            'type': 'Preprint',
            'arxiv': '2012.11458',
            'url': 'https://arxiv.org/abs/2012.11458',
            'year': '2020',
            'abstract': 'We consider decoupling for a fractal subset of the parabola. We reduce studying l^2L^p decoupling for a fractal subset on the parabola to studying decoupling for arithmetic progressions.',
            'image': '/img/papers/decoupling-for-fractal-subsets-of-the-parabola.png'
        },
        {
            'title': 'On Sparsity in Overparametrised Shallow ReLU Networks',
            'authors': 'Joan Bruna, Jaume de Dios',
            'type': 'Preprint',
            'arxiv': '2006.10225',
            'url': 'https://arxiv.org/abs/2006.10225',
            'year': '2020',
            'abstract': 'The analysis of neural network training beyond their linearization regime remains an outstanding open question, even in the simplest setup of a single hidden-layer.',
            'image': '/img/papers/on-sparsity-in-overparametrised-shallow-relu-networks.png'
        },
        {
            'title': 'A geometric lemma for complex polynomial curves with applications in Fourier restriction theory',
            'authors': 'Jaume de Dios',
            'type': 'Preprint',
            'arxiv': '2003.14140',
            'url': 'https://arxiv.org/abs/2003.14140',
            'year': '2020',
            'abstract': 'The aim of this paper is to prove a uniform Fourier restriction estimate for certain 2−dimensional surfaces in R^{2n}.',
            'image': '/img/papers/a-geometric-lemma-for-complex-polynomial-curves-with-applications-in-fourier-restriction-theory.png'
        },
        {
            'title': 'Role Detection in Bicycle-Sharing Networks Using Multilayer Stochastic Block Models',
            'authors': 'Jane Carlen, Jaume de Dios, Cassidy Mentus, Shyr-Shea Chang, Stephanie Wang, Mason A. Porter',
            'type': 'Preprint',
            'arxiv': '1908.09440',
            'url': 'https://arxiv.org/abs/1908.09440',
            'year': '2019',
            'abstract': 'Urban spatial networks are complex systems with interdependent roles of neighborhoods and methods of transportation between them.',
            'image': '/img/papers/role-detection-in-bicycle-sharing-networks-using-multilayer-stochastic-block-models.png'
        }
    ]
    
    output_dir = Path("/tmp/academic-site/content/publications")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Clear existing files (except _index.md)
    for pub_file in output_dir.glob("*.md"):
        if pub_file.name != "_index.md":
            pub_file.unlink()
    
    created_count = 0
    with_images = 0
    
    for pub in publications:
        # Create filename
        title_slug = pub['title'].lower()
        title_slug = ''.join(c if c.isalnum() or c.isspace() else '' for c in title_slug)
        title_slug = '-'.join(title_slug.split())
        filename = f"{pub['year']}-{title_slug}.md"
        
        file_path = output_dir / filename
        
        # Create content
        content = f"""---
title: "{pub['title']}"
date: {pub['year']}-01-01
type: "{pub['type'].lower()}"
authors: "{pub['authors']}"
year: "{pub['year']}"
arxiv: "{pub['arxiv']}"
url: "{pub['url']}"
"""
        
        if pub['image']:
            content += f'featured_image: "{pub["image"]}"\n'
            with_images += 1
        
        content += "---\n\n"
        
        # Add featured image
        if pub['image']:
            content += f"![Featured Image]({pub['image']})\n\n"
        
        # Add publication info
        content += f"**Authors:** {pub['authors']}\n\n"
        content += f"**Type:** {pub['type']} ({pub['year']})\n\n"
        content += f"[arXiv:{pub['arxiv']}](https://arxiv.org/abs/{pub['arxiv']})\n\n"
        
        if pub['url'] and 'arxiv.org' not in pub['url']:
            content += f"[Publisher Link]({pub['url']})\n\n"
        
        # Add abstract
        content += f"## Abstract\n\n{pub['abstract']}\n"
        
        # Write file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        created_count += 1
        print(f"✓ Created: {pub['title']}")
        if pub['image']:
            print(f"  → With featured image: {pub['image']}")
    
    print(f"\n=== Complete! ===")
    print(f"Created {created_count} publications")
    print(f"Publications with featured images: {with_images}/{created_count}")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)