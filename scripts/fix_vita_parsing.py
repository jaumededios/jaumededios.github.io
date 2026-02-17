#!/usr/bin/env python3

import re
import csv
import json

def parse_vita_talks_manual(filepath):
    """Manually parse vita-talks.tsv which has complex multiline structure"""
    talks = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split into lines but be aware of multiline cells
    lines = content.split('\n')
    
    # First line is headers
    headers = lines[0].split('\t')
    print(f"Headers: {headers}")
    
    # Process each talk manually based on the structure I observed
    talk_entries = [
        {
            'tag': 'Decoupling_Exposition_MSR',
            'title': 'Decoupling and applications: from PDEs to Number Theory.',
            'type': 'Expository',
            'abstract': 'Decoupling estimates were introduced by Wolff in order to improve local smoothing estimates for the wave equation. Since then, they have found multiple applications in analysis: from PDEs and restriction theory, to additive number theory, where Bourgain, Demeter and Guth used decoupling-type estimates to prove the main conjecture of the Vinogradov mean value theorem for d>3.\nIn this talk I will explain what decoupling estimates are, I will talk about its applications to the Vinogradov Mean Value theorem and local smoothing, and I will explain the main ingredients that go into (most) decoupling proofs.',
            'topics': 'Harmonic Analysis',
            'tags': "['Decoupling']"
        },
        {
            'tag': 'Sampling_Hard',
            'title': 'Lower bounds for strongly Log-concave Sampling',
            'type': 'Research',
            'abstract': 'Log-concave sampling has witnessed remarkable algorithmic advances in recent years, but the corresponding problem of proving lower bounds for this task has remained elusive, with lower bounds previously known only in dimension one.\nIn this talk, I will establish query lower bounds for sampling from strongly log-concave and log-smooth distributions in dimension $d\\ge 2$, showing that it requires $\\Omega(\\log \\kappa)$ queries, which is sharp in any constant dimension.\nBased on joint work with Sinho Chewi, Jerry Li, Chen Lu, and Shyam Narayanan',
            'topics': 'Theoretical Computer Science',
            'tags': "['Sampling', 'Complexity Theory']"
        },
        {
            'tag': 'Decoupling_Additive',
            'title': 'Decoupling, Cantor sets, and additive combinatorics',
            'type': 'Research',
            'abstract': 'Decoupling and discrete restriction inequalities have been very fruitful in recent years to solve problems in additive combinatorics and analytic number theory. In this talk I will present some work in decoupling for Cantor sets, including Cantor sets on a parabola, decoupling for product sets, and give applications of these results to additive combinatorics. Time permitting, I will present some open problems.\nBased on joint work with Alan Chang, Rachel Greenfeld, Asgar Jamneshan, José Madrid, Zane Li and Paata Ivanisvili',
            'topics': 'Harmonic Analysis',
            'tags': "['Decoupling', 'Additive Combinatorics', 'Analysis on Fractals', 'Hypercube']"
        },
        {
            'tag': 'Decoupling_Cantor',
            'title': 'Decoupling for Cantor sets on the parabola',
            'type': 'Research',
            'abstract': 'Decoupling estimates aim to study the "amount of cancellation" that can occur when we add up functions whose Fourier transforms are supported in different regions of space. In this talk I will describe decoupling estimates for a Cantor set supported in the parabola. I will discuss how both curvature and sparsity (or lack of arithmetic structure) can separately give rise to decoupling estimates, and how these two sources of "cancellation" can be combined to obtain improved estimates for sets that have both sparsity and curvature. No knowledge of what a decoupling estimate is will be assumed.\nBased on joint work with Alan Chang, Rachel Greenfeld, Asgar Jamneshan, José Madrid and Zane Li',
            'topics': 'Harmonic Analysis',
            'tags': "['Decoupling', 'Analysis on Fractals']"
        },
        {
            'tag': 'Sensitivity',
            'title': 'The sensitivity theorem',
            'type': 'Expository',
            'abstract': 'The sensitivity theorem (former sensitivity conjecture) relates multiple ways to quantify the complexity, or lack of "smoothness", of a boolean function f:{0,1}^n -> f : The minimum degree of a polynomial p(x):R^n -> R that extends f, the sensitivity s(f), and the block sensitivity bs(f).\nIn 2019, H.Huang solved the conjecture with a remarkably short proof. I will give a self-contained explanation of this proof, and motivate the importance of the (former) conjecture by relating it to other measures of complexity for boolean functions.',
            'topics': 'Theoretical Computer Science',
            'tags': "['Hypercube', 'Complexity Theory']"
        },
        {
            'tag': 'Uniformity',
            'title': 'Uniform boundedness in operators parametrized by polynomial curves',
            'type': 'Research',
            'abstract': 'Multiple results in harmonic analysis involving integrals of functions over curves (such as restriction theorems, convolution estimates, maximal function estimates or decoupling estimates) depend strongly on the non-vanishing of the torsion of the associated curve. Over the past years there has been considerable interest in extending these results to a degenerate case where the torsion vanishes at a finite number of points by using the affine arc-length as an alternative integration measure. As a model case, multiple results have been proven in which the coordinate functions of the curve are polynomials. In this case one expects the bounds of the operators to depend only on the degree of the polynomial. In this talk I will introduce and motivate the concept of affine arclength measure, provide new decomposition theorems for polynomial curves over characteristic zero local fields, and provide some applications to uniformity results in harmonic analysis.',
            'topics': 'Harmonic Analysis',
            'tags': "['Restriction', 'Uniform estimates']"
        },
        {
            'tag': 'Decoupling_Exposition',
            'title': 'Decoupling and applications: from PDEs to Number Theory.',
            'type': 'Expository',
            'abstract': 'Decoupling estimates were introduced by Wolff [1] in order to improve local smoothing estimates for the wave equation. Since then, they have found multiple applications in analysis: from PDEs and restriction theory, to additive number theory, where Bourgain, Demeter and Guth[2] used decoupling-type estimates to prove the main conjecture of the Vinogradov mean value theorem for d>3.\nIn this talk I will explain what decoupling estimates are, I will talk about its applications to the Vinogradov Mean Value theorem and local smoothing, and I will explain the main ingredients that go into (most) decoupling proofs.\n[1] Wolff, T. (2000). Local smoothing type estimates on Lp for large p. Geometric & Functional Analysis GAFA [2] Bourgain, J., Demeter, C., & Guth, L. (2016). Proof of the main conjecture in Vinogradov\'s mean value theorem for degrees higher than three. Annals of Mathematics, 633-682.',
            'topics': 'Harmonic Analysis',
            'tags': "['Decoupling']"
        },
        {
            'tag': 'Sparsity_NN',
            'title': 'On Sparsity in Overparametrised Shallow ReLU Networks',
            'type': 'Research',
            'abstract': 'The analysis of neural network training beyond their linearization regime remains an outstanding open question, even in the simplest setup of a single hidden-layer. The limit of infinitely wide networks provides an appealing route forward through the mean-field perspective, but a key challenge is to bring learning guarantees back to the finite-neuron setting, where practical algorithms operate. Towards closing this gap, and focusing on shallow neural networks, in this work we study the ability of different regularisation strategies to capture solutions requiring only a finite amount of neurons, even on the infinitely wide regime. Specifically, we consider (i) a form of implicit regularisation obtained by injecting noise into training targets [Blanc et al.~19], and (ii) the variation-norm regularisation [Bach~17], compatible with the mean-field scaling. Under mild assumptions on the activation function (satisfied for instance with ReLUs), we establish that both schemes are minimised by functions having only a finite number of neurons, irrespective of the amount of overparametrisation. We study the consequences of such property and describe the settings where one form of regularisation is favorable over the other.',
            'topics': 'Theoretical Computer Science',
            'tags': "['Neural Networks']"
        }
    ]
    
    # Convert to standard format
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
        talks.append(converted)
    
    print(f"Parsed {len(talks)} talks from vita data")
    return talks

if __name__ == "__main__":
    talks = parse_vita_talks_manual('/root/clawd/data/website-rebuild/vita-talks.tsv')
    
    print("Sample talks:")
    for i, talk in enumerate(talks[:3]):
        print(f"\nTalk {i+1}:")
        print(f"Title: {talk['title']}")
        print(f"Type: {talk['type']}")
        print(f"Abstract: {talk['abstract'][:100]}...")