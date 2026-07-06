---
title: "Query lower bounds for log-concave sampling"
date: 2023-04-01
type: "jacm vol.71 issue 4 / focs 2023"
authors: "Sinho Chewi, Jaume de Dios Pont, Jerry Li, Chen Lu, Shyam Narayanan"
year: "2023"
arxiv: "2304.02599"
paper_url: "https://arxiv.org/abs/2304.02599"
featured_image: "/images/papers/query-lower-bounds-for-log-concave-sampling.png"
description: "Log-concave sampling has witnessed remarkable algorithmic advances in recent years, but the corresponding problem of proving lower bounds for this task has remained elusive, with lower bounds previously known only in dimension one. In this work, we establish the following quer..."

---

![Featured Image](/images/papers/query-lower-bounds-for-log-concave-sampling.png)

**Authors:** Sinho Chewi, Jaume de Dios Pont, Jerry Li, Chen Lu, Shyam Narayanan

**Type:** JACM Vol.71 Issue 4 / FOCS 2023 (2023)

[arXiv:2304.02599](https://arxiv.org/abs/2304.02599)

## Abstract

Log-concave sampling has witnessed remarkable algorithmic advances in recent years, but the corresponding problem of proving lower bounds for this task has remained elusive, with lower bounds previously known only in dimension one. In this work, we establish the following query lower bounds: (1) sampling from strongly log-concave and log-smooth distributions in dimension d≥2 requires Ω(logκ) queries, which is sharp in any constant dimension, and (2) sampling from Gaussians in dimension d (hence also from general log-concave and log-smooth distributions in dimension d) requires Ω˜(min(κ√logd,d)) queries, which is nearly sharp for the class of Gaussians. Here κ denotes the condition number of the target distribution. Our proofs rely upon (1) a multiscale construction inspired by work on the Kakeya conjecture in geometric measure theory, and (2) a novel reduction that demonstrates that block Krylov algorithms are optimal for this problem, as well as connections to lower bound techniques based on Wishart matrices developed in the matrix-vector query literature.
