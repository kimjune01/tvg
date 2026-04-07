### H1: Boolean coverage + chain routing (opus, ALIVE)

**Verdict:** Chain routing u→h₁→h₂→w rescues common inversions using NO extra edges. The strongest surviving hypothesis.

**Claims:**
- C_h[u][w] is a tournament matrix encoding σ_h's total order [H1, verified]
- D_{h₁,h₂}[u][w] = 1 iff M[u,h₁] ≤ t* ≤ M[h₂,w] is a rank-1 Boolean matrix [H1]
- On K₄ total dominance, h₁=0, h₂=3: C₀ ∪ C₃ ∪ D_{0,3} ∪ D_{3,0} covers ALL pairs [H1, verified computationally]
- The "dangerous" Case A (u late at both hubs) requires u ∈ L₁ ∩ L₂ [H1]
- On K₄, choosing dominated/dominant hubs makes L₁ = ∅, killing Case A [H1]
- Fails on 7% of K₅ instances — Case A is real for n ≥ 5 [verified computationally]

**Open questions:** Why does some hub pair always achieve full chain coverage? Is Case A avoidable for all n, or does the construction need to go beyond two hubs?

### H2: Barvinok rank (opus, DEAD)

**Verdict:** Barvinok rank of the earliest-arrival matrix ≠ spanner size. Dead end.

**Claims:**
- Earliest-arrival matrix A for total-dominance K₄ computed explicitly [H2]
- Barvinok rank of A = 2, spanner size = 5. Factor >2x mismatch [H2]
- Rank-1 tropical layers don't correspond to edges [H2]
- Spanner preserves binary reachability, not metric structure — wrong level of abstraction [H2]

**Dead:** The mapping from spanner to tropical rank is neither exact nor approximate.

### H3: Erdős-Szekeres / Ramsey (opus, DEAD)

**Verdict:** Missed multi-hop routing entirely. Conclusions invalid.

**Claims:**
- ES gives √n monotone subsequence in relative permutation [H3, correct but unused]
- "Total dominance K₄ requires all 6 edges" [H3, FALSE — missed 3-hop 2→0→3→1]
- "No Ramsey guarantee on permutation disagreement" [H3, correct but irrelevant given chain routing]

**Dead:** Critical error in reachability computation (only checked 2-hop). All downstream conclusions invalidated.

### H4: Monge / Robinson structure (opus, DEAD on structure, ALIVE on composition)

**Verdict:** Monge and Robinson are dead ends. But coverage matrix composition converges with H1.

**Claims:**
- Total-dominance K₄ matrix is NOT Monge-orderable [H4, proved]
- Total-dominance K₄ matrix is NOT Robinson-orderable [H4, proved via K₃ parity argument]
- Timestamp matrices are generically not Robinson-orderable [H4]
- Coverage matrix composition captures multi-hop routing [H4, convergent with H1]
- C_h is upper-triangular with consecutive-ones property under h's ordering [H4]

**Convergent with H1:** Both independently identified coverage matrix composition as the right framework.

## Convergent evidence

**Chain routing (H1 + H4):** Two independent agents found that 3-hop journeys u→h₁→h₂→w using two hub stars rescue common inversions. The mechanism uses NO extra edges beyond 2n-3 (the two stars share one edge).

**3-hop self-correction (H2 + H3 + H4):** Three agents initially made the same error (only checking 2-hop, concluding K₄ needs all 6 edges). H2 and H4 caught themselves; H3 didn't. The 3-hop journey 2→0→3→1 at times 2,3,5 is the critical example.

## Survivor for extension

**H1's chain coverage** is the sole survivor. The precise open question:

For any temporal clique K_n, do there exist hubs h₁, h₂ such that
C_{h₁} ∪ C_{h₂} ∪ D_{h₁,h₂} ∪ D_{h₂,h₁} covers all ordered pairs on V \ {h₁,h₂}?

Equivalently: for every pair (u,w), at least one of:
1. M[u,h₁] ≤ M[h₁,w] (2-hop via h₁)
2. M[u,h₂] ≤ M[h₂,w] (2-hop via h₂)
3. M[u,h₁] ≤ M[h₁,h₂] ≤ M[h₂,w] (3-hop chain h₁→h₂)
4. M[u,h₂] ≤ M[h₂,h₁] ≤ M[h₁,w] (3-hop chain h₂→h₁)

This fails for 7% of K₅ instances. Extension needed: understand failure mode.
