---
title: "Predicting quantum channels over general product distributions"
date: 2024-09-01
type: "preprint"
authors: "Sitan Chen, Jaume de Dios Pont, Jun-Ting Hsieh, Hsin-Yuan Huang, Jane Lange, Jerry Li"
year: "2024"
arxiv: "2409.03684"
paper_url: "https://arxiv.org/abs/2409.03684"
featured_image: "/img/papers/predicting-quantum-channels-over-general-product-distributions.png"
description: "We investigate the problem of predicting the output behavior of unknown quantum channels. Given query access to an n-qubit channel E and an observable O, we aim to learn the mapping ρ↦Tr(OE[ρ]) to within a small error for most ρ sampled from a distribution D. Previously, Huang..."

---

![Featured Image](/img/papers/predicting-quantum-channels-over-general-product-distributions.png)

**Authors:** Sitan Chen, Jaume de Dios Pont, Jun-Ting Hsieh, Hsin-Yuan Huang, Jane Lange, Jerry Li

**Type:** Preprint (2024)

[arXiv:2409.03684](https://arxiv.org/abs/2409.03684)

## Abstract

We investigate the problem of predicting the output behavior of unknown quantum channels. Given query access to an n-qubit channel E and an observable O, we aim to learn the mapping ρ↦Tr(OE[ρ]) to within a small error for most ρ sampled from a distribution D. Previously, Huang, Chen, and Preskill proved a surprising result that even if E is arbitrary, this task can be solved in time roughly nO(log(1/ϵ)), where ϵ is the target prediction error. However, their guarantee applied only to input distributions D invariant under all single-qubit Clifford gates, and their algorithm fails for important cases such as general product distributions over product states ρ. In this work, we propose a new approach that achieves accurate prediction over essentially any product distribution D, provided it is not ``classical'' in which case there is a trivial exponential lower bound. Our method employs a ``biased Pauli analysis,'' analogous to classical biased Fourier analysis. Implementing this approach requires overcoming several challenges unique to the quantum setting, including the lack of a basis with appropriate orthogonality properties. The techniques we develop to address these issues may have broader applications in quantum information.
