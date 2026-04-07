# Work Log

## 2026-04-05

### 03:20 — Pivot-edge correction + cross-only spanning + B-frame construction

TVG session 2026-04-05: Pivot-edge correction + cross-only spanning + B-frame construction

## Corrections
- PivotEdge.lean was overstating its result. It proves full-graph routing (using V⁻/V⁺ internal edges), NOT Angrick's biclique-only pivot-edge. Angrick Lemma 6.4: SM(k) has trivial pivot-sets of size 2 under biclique-only definition. Updated Lean doc comments and CLAUDE.md.

## Key finding: cross-only spanning
- Cross edges alone span ALL pairs (including A-A and B-B) in every tested extremally matched biclique. 670 random bicliques + all SM(k) k=3..8. Zero failures. Always within 2n-3.
- **Non-domination theorem (proved):** M⁻ permutation → no row dominates another. M⁺ permutation → no column dominates another. Consequence: for any pair (i,i'), ∃ column j with M[i][j] < M[i'][j], giving 2-hop journey a_i → b_j → a_{i'}. Similarly for B-B pairs. Cross edges provide bidirectional relay. This is the B-frame.

## Optimal spanner structure (SM(k))
- Optimal spanners use ZERO internal edges. All cross.
- M⁻ ∪ M⁺ essential (2k edges, I-frames). Each intermediate diagonal d=1..k-2 needs ~2 edges (B-frames).
- Total: 2k + 2(k-2) = 4k-4 = 2n-4 for k≤7. SM(8) first to hit 2n-3.
- Exhaustive search confirms: valid 2-per-diagonal selections exist for all SM(k) k=3..7. Canonical form: d=1 uses rows (0,1); d>1 uses rows (1, k-d). Row 1 is a hub.

## B-frame analogy
- M⁻/M⁺ = I-frames. Intermediate diagonals = B-frames (bidirectional relay).
- Per-diagonal greedy fails (like per-frame R-D optimization). Joint optimization needed.
- The open problems (optimal B-frame placement, optimal spanner selection, covering design) are identical, not complementary.

## New scripts
- residual_analysis.py, pivot_construction.py, cross_only_spanner.py, domination_proof.py, optimal_structure.py, dyadic_spanner.py, joint_diagonal.py

## Next: rate-distortion duality
- Codec R-D Lagrangian framework might map to covering LP dual. 40 years of codec theory on this dual. Does it transfer?

### 05:15 — Double star construction + O(n) proof gap identified

Double star (M⁻ ∪ M⁺ ∪ star(h) ∪ star(c), m⁺(h)=c) gives 2n-4 for ALL SM(k) k=3..11. SM(8) was a search artifact — true optimal is 28=2n-4 not 29. 2 hub pairs suffice exhaustively through k=15 (earlier failures were sampling artifacts).

The O(n) proof reduces to one lemma: the failure set of the double star is O(k) not O(k log k). IVT argument gives existence of optimum between hub-only (4k) and all-I-frames (k²), but doesn't locate it. Coverage decay rate is the gap — each hub empirically covers all-but-O(k) pairs, but proving this requires bounding the concordant pairs under 2-column restriction plus multi-hop rescue through hub rows. Not cracked today.

### 05:50 — O(n) proof sketch completed

The O(n) argument closes via asymmetric recursion. PivotEdge (Lean, proved) gives >n/2 coverage per hub. One side is done, the other recurses. T(n) = T(n/2) + O(n) = O(n). No need to know which side recurses — the geometric series converges either way. Written up in `_drafts/on-proof-sketch.md`. Three lemmas (non-domination, pivot coverage, monotonicity) — all proved. The composition is the O(n) bound. Gap to 2n-3 is in the constant (6k vs 2k), not the order.

### 06:30 — O(n) proof doesn't close; barrier identified

The asymmetric recursion T(n)=T(n/2)+O(n) requires hub covering >n/2 pairs IN THE SPANNER. PivotEdge gives full-graph coverage; spanner uses only cross edges. Hub's spanner coverage is global, not locally detectable. Twist permutation σ=m⁺∘(m⁻)⁻¹ has O(log k) cycles → O(n log n), same as Casteigts. O(n) needs one hub to break all cycles. Empirically true post hoc, no ad hoc argument. Barrier: ad hoc hub certification. NonDomination.lean: 4 theorems, zero sorry.

### 16:45 — H3 cycle-breaking hardness: 7 experiments completed

`cycle_breaking.py` — 7 experiments on σ = m⁺ ∘ m⁻ (col→row→col).

**Finding 1: Valid hubs are almost always fixed points of σ.** At k≥5, 95-100% of valid hubs have σ(c)=c where c=m⁺(h). Fixed point means m⁺(m⁻(c))=c, i.e., the hub column's min-row has its max back in the same column. Self-reinforcing loop.

**Finding 2: Valid hubs cluster in short cycles (length 1).** Avg cycle length of valid hub's column: 1.00-1.15 at k≥5. Invalid hubs sit in long cycles (avg 3.8-4.8). The longer the cycle containing your hub column, the less likely you are to be a valid hub.

**Finding 3: More cycles in σ → more valid hubs.** At k=7: 1-cycle σ has 0% valid hubs; 4-cycle σ has 100%. At k=8: 1-cycle→1%, 4-cycles→94%. More cycles = more fixed points = more valid hubs. SM(k) is the extreme case: single k-cycle, ALL hubs valid (because circulant structure provides perfect temporal flow).

**Finding 4: FVS connection is BROKEN.** Valid hub columns form a FVS of σ only 1-2% of the time at k≥5. The valid hubs all come from the SAME cycle (100% across all k), typically the fixed-point "cycle." They don't hit other cycles at all. FVS requires hitting every cycle — valid hubs do the opposite.

**Finding 5: σ does NOT determine valid hubs.** Same σ, different M → different valid hubs (51/82 σ-values at k=5 show different valid hub sets across instances). The temporal values in M are load-bearing, not just the permutation structure.

**Finding 6: SM(k) is maximally easy.** σ is always a single k-cycle for SM(k), and every hub is valid. The circulant structure means σ has no short cycles to exploit, yet all hubs work because the timestamp values cooperate perfectly.

**Conclusion:** Hub selection is NOT reducible to FVS or any pure permutation problem. It's a feasibility problem over M's values, constrained but not determined by σ. The fixed-point predictor is strong but not perfect. The hardness (if any) comes from the interaction between σ's cycle structure and M's value structure — neither alone suffices.

### 18:30 — NP-hardness fan-out → fixed-point hub criterion → backward-pass architecture → crosswalk synopsis

TVG session: NP-hardness fan-out → fixed-point hub criterion → backward-pass architecture → expanded crosswalk synopsis. Key findings: (1) Fixed points of σ=m⁺∘m⁻ predict valid hubs 100% when they exist (~60% of instances). (2) Derangement-σ: no single hub works at k≥7, 2 hubs always suffice. (3) Certificate size Θ(k²) — hub certification requires 84% of matrix entries. (4) Backward pass: greedy forward + ≤2 hub stars, zero failures across 870 samples. (5) Deferred commit worse than naive — dismounting edges are the right edges. (6) Dismountability is order-independent (1-hop), but mixed k-hop is order-dependent. (7) The O(n log n) → O(n) gap is the cost of hub ignorance: recursive splitting doesn't know which half has the hub. (8) Built soap/S.md with 35-term crosswalk (10 genuine, 10 moderate, 15 structural). New scripts: adversarial_hub.py, query_complexity.py, cycle_breaking.py, fixed_point_algorithm.py, backward_pass.py, deferred_commit.py.
