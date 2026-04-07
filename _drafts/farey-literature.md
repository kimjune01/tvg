# Farey Tree Literature for Temporal Spanner Construction

**Date:** 2026-04-05

## Core structure (Stern-Brocot tree)

- Enumerates all positive rationals in lowest terms via mediant: (a+c)/(b+d)
- Adjacent pairs satisfy |ad - bc| = 1 (Farey neighbor criterion)
- Depth = sum of continued-fraction coefficients - 1
- Construction: O(n) by iterative mediant insertion
- **Source:** Graham, Knuth, Patashnik, *Concrete Mathematics*, Ch. 4

## Farey graphs as complex networks

- Zhang, Liu, Wu & Comellas (TCS 2011): Farey graphs are maximally
  outerplanar, uniquely Hamiltonian, minimally 3-colorable, perfect
- Diameter: O(log n), clustering coefficient → ln 2 ≈ 0.693,
  average path length: O(log n) — small-world
- **Standard Farey graphs are NOT scale-free** — exponential degree
  distribution, not power-law
- Liao, Hou, Shen (Scientific Reports 2018): Generalized Farey graphs
  restore scale-free (power-law) degree distributions

## Temporal spanners (state of the art)

- Bilò et al. (ESA 2022): O-tilde(n) edges for (1+ε)-stretch
  single-source temporal spanners; exact-distance = Ω(n²)
- Kurita (SAND 2025): polynomial-delay enumeration for one-to-all;
  hardness for all-to-all
- Casteigts et al. (2022): blackout-tolerant with hierarchical clustering

## The gap (our opportunity)

**No direct Farey-spanner connection exists in the literature.**

The mediant's |ad-bc|=1 invariant provides:
- Local repair rule (insert one fraction to restore neighbor property)
- O(n) constructible tree
- Logarithmic diameter with high clustering

These are exactly the properties a temporal spanner needs.

## Self-healing

- No Farey-specific self-healing results exist
- General: Pandurangan et al. (2011) — reconstruction trees, expander overlays
- Mediant insertion is a natural candidate: removing a node leaves a gap
  identifiable by the neighbor criterion, fillable in O(1) local ops

## Correction: scale-free claim

Standard Farey graphs have exponential degree distributions (small-world
but NOT scale-free). Generalized Farey graphs (Liao 2018) are scale-free.
Need to clarify which variant we're using.

## Sources

- Zhang et al., Farey Graphs as Models for Complex Networks (TCS 2011)
- Liao et al., Generalized Farey Graphs (Scientific Reports 2018)
- Bilò et al., Sparse Temporal Spanners (ESA 2022, arXiv:2206.11113)
- Kurita, Spanner Enumeration for Temporal Graphs (SAND 2025)
- Casteigts et al., Blackout-Tolerant Temporal Spanners (2022)
- Matula & Kornerup, Farey Series and Maximal Outerplanar Graphs (SIAM 1979)
- Label-based Routing for Small-World Farey Graphs (Scientific Reports 2016)
