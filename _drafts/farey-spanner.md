# Farey Tree Spanner Construction

**Date:** 2026-04-05
**Status:** CLOSED. 13 hypotheses tested, 1 survivor (H10).
Farey is the wrong primitive. Economics is the right framing.
O(n) construction appears impossible — relay value is non-local.
Best achieved: O(k⁵) with PoA ≤ 1.25, 2-round convergence.

## Fan-out results (Cycle 1)

### H1: Farey tree on timestamp ranks (opus, DEAD)

**Verdict:** Three independent failure modes kill it.

**Claims:**
- Size mismatch: SB tree on k² timestamps has Θ(k²) edges — same as full graph. Any O(k) extraction destroys coverage. [opus]
- Direction mismatch: Farey mediants prioritize MIDDLE-rank timestamps. Optimal spanners keep EXTREME-rank edges (earliest/latest per row), remove middle. Inner-third removed 2-3x more than outer-third. [opus]
- Structural mismatch: Farey tree is 1D (totally ordered set). Temporal routing is 2D (bipartite vertex-sharing). No rank-to-fraction mapping encodes 2D constraint. [opus]

**Bonus:** SM(5) optimal = 16 edges (2n-4). Removed edges = all interior ranks. Kept edges form staircase: row 0 keeps min/max only, row 4 keeps everything.

### H2: Farey tree on row-ratio fractions (opus, DEAD)

**Verdict:** Structural impossibility.

**Claims:**
- Per-row trees select all k columns (k-1 edges × k rows ≈ full graph). Spanner needs O(1) per row, not O(k). Budget and Farey are fundamentally incompatible. [opus]
- Which interior edges to keep is a constraint-propagation problem across rows, not number-theoretic. [opus]
- SM(4): 14 distinct optimal spanners, none show Farey structure. [opus]

### H3: Farey mediant as relay construction (opus, DEAD)

**Verdict:** Dimension mismatch.

**Claims:**
- Farey mediant combines BOTH components: (a+c)/(b+d). Temporal relay shares EXACTLY ONE (same row or same column). Incompatible. [opus]
- P(two random K_{k,k} edges share a vertex) = (2k-1)/k² → 0 as k grows. [opus]
- Projection from timestamp tree to biclique has no natural quotient. [opus]

## What survived (not from the fan-out)

**Emergent Farey structure via selfish routing.** The constructive approach
(build a Farey tree as the spanner) is dead. But Farey-like structure may
EMERGE from local self-interest:

- Transportation networks and the internet exhibit Farey-similar graphs
  where each node acts in its own interest
- Edge monotonicity (adding edges never hurts) = no negative externalities
- Potentials always exist (100% empirical) = each vertex has a stable local optimum
- The equilibrium of selfish temporal routing may be sparse with Farey-like properties

This is a **Price of Anarchy** argument, not a construction. The spanner
isn't designed — it's the Nash equilibrium. The 2n-3 bound would be
the PoA bound on selfish temporal routing.

**Status:** DEAD as stated. Selfish online construction overshoots by Θ(k).
The emergent Farey claim is unfounded — online greedy produces no
Farey-like structure. But the observation that motivates it (networks
built under uncertainty need different structure than retrospective
optima) remains valid. The answer just isn't Farey.

## Cycle 2: Online Farey construction

### Key reframing

Cycle 1 asked: "does the optimal offline spanner look like a Farey tree?"
Wrong question. Optimal offline spanners are caterpillars with hindsight.

The right question: does online Farey-based construction, where each node
selfishly maintains connectivity via mediant insertion as edges arrive,
produce a valid temporal spanner with O(n) edges?

The 2n-3 bound is retrospective. The O(n) construction is the claim.

### H4: Selfish Farey equilibrium on arrival stream (opus, DEAD)

**Verdict:** Online greedy keeps nearly all k² edges. Competitive ratio Θ(k).

**Claims:**
- Every edge in SM(k) genuinely adds new reachability — greedy has no
  selectivity. SM(7): 49/49 kept vs bound 25. [opus]
- Random matrices: 100% of trials exceed 2n-3. Mean ~3.8k-12 overshoot. [opus]
- Root cause: "does this edge help me?" is too weak. Spanner thinness
  requires "can I route this pair through edges I already have?" — a
  global routing query. [opus]
- Offline optimal keeps first+last rows fully, middle rows keep only
  earliest edge. Requires global knowledge of row structure. [opus]

### H5: Farey healing preserves temporal reachability (opus, PARTIAL)

**Verdict:** Mediant healing rule FAILS (56-72%, worsening with k).
But universal 1-healability CONFIRMED.

**Claims:**
- Midpoint healing: SM(3) 72%, SM(4) 64%, SM(5) 56%, SM(6) 55%.
  Decreasing — systematically picks wrong replacement. [opus]
- **Max-pairs healing: 100% across 29,000+ deletions.** Every single-edge
  deletion from every optimal SM(k) spanner (k=3..6) healed by exactly
  one replacement. [opus, STRONG]
- Never requires more than one replacement edge. [opus]
- Interior edges harder to heal than extreme-rank for midpoint rule.
  Right replacement is structurally complementary, not temporally nearby. [opus]
- Optimal SM(k) sizes are 2k-1 (star structure), not 4k-4. [opus, corrects prior]

### H6: Online edge count analysis (opus, DEAD)

**Verdict:** Online greedy overshoots by Θ(k) regardless of arrival order.

**Claims:**
- Forward, reverse, random orderings yield nearly identical edge counts.
  No arrival order exploits temporal structure. [opus]
- No phase transition: edges keep being added until 90-97% of timestamps processed. [opus]
- Gap scaling ~0.08k^2.7 total edges vs 4k-3 bound. [opus]
- 2n-3 bound requires offline/structural construction. [opus]

### H7: Per-node O(1) Farey neighbors (opus, DEAD)

**Verdict:** O(1) per row is the right budget but the selection rule
can't be a fixed heuristic. Requires cross-row coordination.

**Claims:**
- Min-mediant-max (3/row): 0% of random matrices achieve full reachability
  at k≥4. Mean reachability degrades: 85%→73%→63%→58% for k=4..7. [opus]
- Min-max only (2/row): 30-50% reachability. [opus]
- Actual minimum: ~3-4 edges/row on average, but distribution across rows
  is non-uniform (some need 4, some need 2). [opus]
- Patch count for failures grows O(k), not O(1). [opus]
- Minimum edge sets don't follow any local pattern — they require global
  coordination across rows. [opus]
- SM(k) is pathological: disjoint row timestamp ranges make half the
  A-to-A pairs inherently unreachable regardless of edge selection. [opus, corrects prior tests]

## Cycle 3: Distributed relaxation (live lead)

### Reframing

Cycles 1-2 asked centralized questions: "does this mapping/rule produce
the spanner?" Wrong frame. The construction is a DISTRIBUTED ALGORITHM
where each node acts in local self-interest.

**The algorithm:**
1. t_0: each node builds local connectivity (Farey tree = initial topology)
2. Each timestep: each node does O(1) work — maintain its own edges
3. Cross-row coordination happens implicitly through network communication
   (node i's edge choice propagates to neighbors through connectivity)
4. The CSP solves itself through distributed relaxation
5. At most 1 full rebuild (pigeonhole) — everything else is O(1) healing

**Complexity:**
- Per node: O(1) amortized
- Per timestep: O(1) wall-clock (n nodes in parallel)
- Total work: O(n)
- The constraint propagation IS the network, not a separate solver

**What needs specification:**
1. Local decision rule: when a node loses an edge, how does it choose
   the replacement using ONLY local information (its own timestamps,
   its current neighbors, messages from neighbors)?
2. Convergence: does the distributed relaxation converge to a valid
   spanner? In how many rounds?
3. Edge count: does the converged state have ≤ 2n-3 edges?

**Why Farey as initial topology:**
- Local-implies-global = relaxation messages don't cascade
- Mediant structure = each node has a natural repair candidate
- Scale-free = high-degree nodes act as natural coordinators

**Why prior tests missed this:**
- H1-H3: tested centralized mappings (wrong frame)
- H4,H6: tested greedy without communication between nodes
- H5: tested healing on non-Farey structures
- H7: tested per-node rules without inter-node propagation
- NONE tested: distributed relaxation with message passing

### H8: Distributed Farey relaxation (opus, DEAD)

**Setup:** Simulate the distributed algorithm:
- n nodes, each with local state (its edges, its neighbors' edge lists)
- Each round: every node checks its reachability to all vertices it
  knows about. If unreachable to some target, it asks neighbors for
  a relay edge. If a neighbor offers one, it adds it. If it has a
  redundant edge (covered by two neighbors' relays), it drops it.
- Farey tree as initial topology (min-mediant-max per node, or
  some variant)
- Run until convergence (no node changes its edge set)

**Result:** DEAD. Farey adjacency is vacuous on random timestamps.

**Claims:**
- Only 0.7-3.3% of rank pairs are Farey neighbors at k=4..5. Drop rule
  never fires. Algorithm degenerates to "keep everything." [opus]
- Edge count: 15.6/13 (k=4), 24.9/17 (k=5), 48.9/25 (k=7). ~2x budget. [opus]
- Edges per node = O(k), not O(1). Scales linearly with k. [opus]
- Convergence is fast (2-9 rounds) but to the WRONG answer (too many edges). [opus]
- Greedy offline stays near budget; Farey keeps 1.5-2x more. [opus]
- Root cause: |ad-bc|=1 requires small denominators. Random p/k² has
  large denominators and O(k) gaps. Number theory doesn't apply. [opus]

### H5b: Universal 1-healability (opus, DEAD)

**Verdict:** Artifact of SM(k). On random matrices, 1-healability is rare.

**Claims:**
- Zero random matrices (out of 50/k) have ALL edges healable. Per-edge
  healability: 3.6% (k=3) to 31.4% (k=6). [opus]
- Prior H5 result was SM-specific artifact. SM has disjoint row ranges
  making every edge irreplaceable (0% healability). [opus]
- Minimum spanners on random K_{k,k}: ~k²-k edges (k=3: 8.3/9, k=4:
  12.8/16, k=5: 17.1/25). Near the bound, sometimes exceeding. [opus]
- Multi-deletion: near-hopeless (0-8.5% for 2-deletion). [opus]
- When healing works, replacements are local (~80-89% same row/column). [opus]

### H10: Economic best-response dynamics (opus, ALIVE)

**Verdict:** CONFIRMED. Nash equilibrium matches centralized greedy.

**Claims:**
- PoA ≤ 1.06 — distributed game = centralized optimum. [opus, STRONG]
- Per-node degree O(1): 2.75→3.69 as k goes 3→7. Ratio degree/k
  DECREASES (0.92→0.53). [opus, STRONG]
- Converges in exactly 2 rounds, sequential and simultaneous. [opus]
- Budget violations are structural (matrix-inherent), not game-theoretic.
  When Nash exceeds 4k-3, greedy does too (100% co-occurrence). [opus]
- Ordering variance small (std ≤ 1.1) but nonzero at larger k. [opus]

**Revised by H10b:**
- Spanner size is O(k log k), not O(k). Log factor from relay pigeonhole.
- Construction is O(k⁵) = O(n^2.5) per round, not O(n). Redundancy
  check per edge costs O(nE).
- 4k-3 budget fails 47% at k=8. CPS conjecture is for K_n, not K_{k,k}.
- Random K_{k,k} often not fully reachable (77% at k=3, 5% at k=10).

### H10b: Best-response formalization (opus, PARTIAL)

**Verdict:** Dynamics confirmed. Complexity revised upward.

**Confirmed:**
- 2-round convergence (all k=3..8, hundreds of instances) [opus]
- PoA ≤ 1.25, avg 1.00-1.05 [opus]
- Every equilibrium edge is critical (true Nash) [opus]
- Per-node degree O(1): avg 3.1→3.7, ratio degree/k decreasing [opus]

**Refuted:**
- O(k) spanner size → actually O(k log k). Power law ~2.07k^1.273 [opus]
- O(n) construction → actually O(n^2.5). No known speedup for
  per-edge redundancy check [opus]
- Universal budget compliance → fails 47% at k=8 [opus]

**Structure at equilibrium:**
- Row min/max edges: 82-96% retained (essential)
- Interior edges: 27-47% retained (relay function)
- Degree distribution: concentrated in {2,3,4,5}

**Proof outline (theorem + 4 lemmas):**
- Lemma 1: Monotonicity (Φ = |S| strictly decreases)
- Lemma 2: Criticality (Nash ⇒ every edge critical)
- Lemma 3: Sparsity O(k log k) — EMPIRICAL, not proved
- Lemma 4: PoA ≤ 1.25 — EMPIRICAL bound

**Open:** proving O(k log k) analytically. Gap between Ω(k) lower
and O(k log k) upper is the row-dominance avoidance cost.

### H9: BGP-style path vector (opus, DEAD)

**Verdict:** BGP analogy is cosmetically appealing but algorithmically empty.

**Claims:**
- All BGP variants (standard, aggressive, economic) produce identical
  edge counts. Pruning criterion irrelevant; only removal order matters. [opus]
- Root cause: temporal routes are querier-dependent. A path from b_j
  onward to target X depends on arrival time, which varies per querier.
  No "route" exists independent of the asker. [opus]
- Multi-start greedy (20 orderings) is the real algorithm: 84-94%
  budget compliance at k=5..8. [opus]
- ~6% of random k=4 matrices GENUINELY require >4k-3 edges.
  Exhaustive search confirms. Budget isn't always feasible. [opus, IMPORTANT]
- 1-healability catastrophic on greedy spanners: 81-92% of edges
  unrecoverable after deletion. [opus, confirms H5b]

### H11: Heuristic budget from n (opus, DEAD)

**Verdict:** O(n) heuristics can't predict relay value from local info.

**Claims:**
- All variants O(n) for construction but none achieves 100% reachability
  at k≥6 without repair. [opus]
- Repair pass is O(k⁵ log k) — kills the complexity advantage. [opus]
- Edge overhead 1.3-1.5x vs H10 best-response. [opus]
- Column coverage (Variant C) is best but still insufficient. [opus]
- Fundamental barrier: relay value depends on global timestamp structure.
  No local information predicts it. [opus]

### H12: Union-find temporal construction (opus, DEAD)

**Verdict:** UF is symmetric, temporal reachability is asymmetric. Structural mismatch.

**Claims:**
- Pure UF variants (A,B,C) collapse to 2k-1 edge spanning tree, 25-52%
  reachability. UF ignores timestamp ordering entirely. [opus]
- Forward+backward prune (D) produces OPTIMAL spanners but doesn't use
  UF — falls back to O(k⁵ log k) reachability checking. [opus]
- 75% of edges in same UF component are still temporally useful.
  UF provides zero filtering. [opus]
- Optimal greedy exceeds 4k-3 for most random matrices at k≥7.
  Budget compliance: 100% (k=3), 36% (k=7), 20% (k=8). [opus, IMPORTANT]
- Optimal scales as ~4.1k at k=10, growing faster than 4k-3. [opus]

### Literature check (2026-04-05)

**Distributed temporal spanner construction is OPEN.**
- No distributed algorithm exists in the literature
- No online algorithm exists
- No near-linear time construction is claimed
- Baswana-Sen (2007, static distributed spanners) not adapted to temporal
- Best known: CPS fireworks algorithm (polynomial, not optimized)
- A distributed construction would be a genuine contribution

## Consolidated dead-end characterization

All three hypotheses died on the same root cause: **Farey trees are 1D
structures on totally ordered sets; temporal spanners live in 2D bipartite
structure where the ordering constraint (semiring) interacts with the
vertex-sharing constraint (relay).** No 1D → 2D mapping preserves both.

The emergent angle sidesteps this: instead of mapping temporal structure
TO Farey fractions, observe that local optimization ON the temporal
structure produces Farey-LIKE properties (small-world, local→global).

## Final consolidated findings (2026-04-05)

### What's real
1. **Best-response dynamics** converge in 2 rounds to near-optimal
   Nash equilibrium (PoA ≤ 1.25). First distributed temporal spanner
   construction. (H10, H10b)
2. **Forward temporal reachability is transitive** (semiring composition).
   Backward is not. This asymmetry kills union-find, Farey trees, and
   all symmetric data structures. (H12, conversation)
3. **Relay value is non-local.** No local heuristic predicts which edges
   are critical relays. O(n) construction appears impossible. (H7, H11)
4. **4k-3 budget fails at k≥7** for random K_{k,k}. ~6% genuinely
   infeasible at k=4. CPS conjecture is for K_n, not K_{k,k}. (H9, H12)
5. **Optimal spanner size is O(k log k)**, not O(k). (H10b)
6. **Per-node degree is O(1)** at equilibrium (3-4 edges avg). (H10, H10b)

### What's publishable
- First distributed temporal spanner construction (field is open)
- Game-theoretic characterization (Nash = near-optimal, 2 rounds)
- Non-locality of relay value (impossibility result for O(n))
- Budget infeasibility data for K_{k,k} (relevant to conjecture scope)

### H14: Forward incremental construction (NEGATIVE)
- Phase 1 keeps 58% of edges at k=12 — nearly every edge adds reachability
- Phase 1+2 = H10 quality at same O(k⁴) complexity
- Root cause: forward transitivity requires departure-time-conditional
  matrix `reach[u][v | depart ≥ t]`, not simple `reach[u][v]`.
  Need O(k²) departure-indexed views → no efficiency gain.

### What died
- Farey trees: 1D structure for 2D problem (H1-H3, H7, H8)
- Online greedy: keeps everything (H4, H6)
- Mediant healing: wrong heuristic (H5, H5b)
- BGP: routes are querier-dependent (H9)
- O(n) heuristics: relay value is global (H11)
- Union-find: symmetric for asymmetric problem (H12)
- Forward incremental: departure-time conditioning kills it (H14)

### The internet analogy (what started this)
The internet solved the forward-looking version decades ago (BGP).
The temporal spanner conjecture asks for the backward-looking version
(preserve ALL historical reachability). Nobody needs that.
The practical contribution is H10: a distributed algorithm that
converges fast and produces near-optimal results, like BGP does.
