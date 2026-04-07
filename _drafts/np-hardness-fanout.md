# NP-Hardness Fan-out: Minimum Temporal Clique Spanner

## Problem

INPUT: Temporal clique K_n (complete graph, one distinct timestamp per edge)
DECISION: Does K_n have a temporal spanner with ≤ t edges?

Equivalently (via Carnevale reduction): given k×k all-distinct matrix M,
forced edges F = M⁻ ��� M⁺, does there exist S with |F ∪ S| ≤ t such that
F ∪ S is a temporal spanner of the biclique?

## Known

- NP-hardness for general temporal graphs (Axiotis-Fotakis 2016, sparse + multi-label)
- NP-hardness does NOT transfer to temporal cliques (single label, all distinct)
- Complexity of temporal clique spanner is OPEN
- Growing edge interaction depth (triple/pairwise ratio: 0.05 → 0.20 → 0.43 at k=3,4,5)
- ~25% of pair constraints need >2 hop journeys (multi-hop = synergy source)
- Covering design model is wrong (edges interact, not independent)

## Hypotheses

### H1: Clique completion via small timestamps preserves minimum spanner (CONFIRMED)

**Experiment:** `clique_completion.py`

**Setup:** Given a sparse temporal graph G = (V, E) that is all-pairs temporally connected (single timestamp per edge, all distinct), complete it to K_n by assigning every missing edge a timestamp smaller than all original timestamps.

**Result:** Strategy B (small timestamps) preserves the minimum spanner with 100% success rate:
- n=4, 5 edges (exhaustive, 384 instances): 384/384 preserved
- n=4, 4 edges (exhaustive, 24 instances): 24/24 preserved
- n=5, 9 edges (sampled, 1601 instances): 1601/1601 preserved
- n=5, 7 edges (sampled, 2112 instances): 2112/2112 preserved

**Why it works (proof sketch):** New edges get timestamps t_new < min(original). A new edge can only be the *first* hop of any journey (everything after it must have t > t_new, which all originals satisfy). If the original graph is all-pairs connected, every journey that uses a new edge as first hop can be rerouted: the source vertex already reaches the destination via original edges alone. So any minimum spanner S of K_n that includes a new edge e can be transformed to S' = S - {e} + {e_orig} where e_orig is the first edge of an original-only journey. |S'| = |S|, so new edges are never *necessary*. The minimum spanner of K_n equals the minimum spanner of G.

By contrast, Strategy A (large timestamps) fails 23% of the time for n=4 — late edges create genuine shortcuts by serving as final hops in multi-edge journeys.

### H1.1: The reduction is blocked by source-graph constraints (CONFIRMED — dead end)

**The problem:** Strategy B proves that min_spanner(K_n) = min_spanner(G) when G is all-pairs connected with single labels. This means:

> If computing min_spanner(K_n) were polynomial, so would be computing min_spanner(G) for single-label, all-distinct sparse temporal graphs.

The contrapositive gives us the reduction direction we want: if single-label sparse is hard, then temporal clique is hard.

**But:** The known NP-hardness result (Axiotis-Fotakis 2016) is for *general* temporal graphs with **multiple labels per edge**. Single-label, all-distinct sparse temporal graphs are a *different* problem whose complexity is also open. We cannot embed multi-label instances into a temporal clique because the clique requires exactly one timestamp per edge.

**The gap:** We need NP-hardness of single-label sparse temporal spanner. This is itself an open problem. The clique completion embedding is valid but only reduces from one open problem to another.

**What would close the gap:**
1. Prove single-label sparse temporal spanner is NP-hard (then clique follows by Strategy B)
2. Find a different reduction that doesn't go through sparse graphs
3. Show that multi-label instances can be "compiled" into single-label instances (e.g., by splitting vertices)

**Key structural insight:** Small timestamps make new edges temporally inert because they can only serve as journey *prefixes*, never as shortcuts in the middle or as final hops. Large timestamps are dangerous because they serve as journey *suffixes*, enabling shorter paths for distant pairs.

### H1.2: Vertex splitting to compile multi-label into single-label (OPEN)

The gap from H1.1 can potentially be closed by compiling multi-label temporal graphs into single-label ones via vertex splitting.

**Idea:** Given edge {u,v} with labels t1 < t2 < ... < tk in a multi-label graph, replace it with a chain of k gadget vertices u—g1—g2—...—gk—v, where each gadget edge has a single unique timestamp encoding the original label.

**Problems:**
1. The resulting graph has more vertices, so completion to K_n produces a LARGER clique. The spanner relationship becomes unclear.
2. Gadget edges between non-original vertices must not create spurious shortcuts.
3. The spanner size relationship between the compiled graph and the original is non-trivial — each original edge becomes a path, so the minimum spanner changes by a factor.

**Status:** Not attempted experimentally. The vertex-inflation problem (n grows) makes this approach suspect. A polynomial blowup is acceptable for NP-hardness reduction, but the spanner-size relationship must be tight (not just polynomial).

### H2: Alternative approach — direct reduction from Set Cover (UNTESTED)

Instead of going through sparse temporal graphs, reduce directly from Set Cover or Hitting Set to temporal clique spanner.

**Idea:** Encode a Set Cover instance into the timestamp matrix M of a temporal clique, such that the covering structure of M encodes the set system. The critical covering hypergraph (from x3c_reduction.py) would then match the set system.

**Why this might work:** The covering hypergraph of a temporal clique already has a set-system structure (each edge "covers" certain pairs). If we can engineer M so that this structure matches an arbitrary set system, we get a direct reduction.

**Why this might fail:** The all-distinct constraint on M severely limits which covering hypergraphs can arise. Not every set system may be realizable as a covering hypergraph of some temporal clique.

### H3: 3-Dimensional Matching reduction (FAILED — structural obstruction)

**Experiment:** `reduction_3dm.py`

**Motivation:** 3DM is NP-complete and involves ternary relationships. The temporal biclique has three natural dimensions (rows, columns, timestamps). Chain inequalities M[i][j1] < M[i'][j1] < M[i'][j2] relate three edges in a ternary constraint. Map 3DM triple (x,y,z) to a cross edge that serves constraints along all three dimensions simultaneously.

**Five approaches tried:**

1. **Direct encoding** (row=x, col=y, timestamp~z): Multiple triples can map to the same (x,y) cell. A k×k matrix has k² entries but up to k³ triples. Fatal: can't encode the triple multiplicity.

2. **Gadget construction** (expanded matrix k = n+|T|): Underdetermined. No natural way to assign timestamps that forces the right covering structure. Switched to computational search.

3. **Chain-based encoding**: Traced actual journey chains in random matrices. Edges DO serve mixed pair types (A→A and B→B simultaneously) — the ternary structure exists. But coverage sizes are wildly non-uniform (range 1-10 at k=3), not the 3-uniform pattern 3DM needs.

4. **Exhaustive structural census** (k=3, 500 instances): Coverage size tuples are highly varied — 54 distinct structural types. Triple synergy exists (28/500 = 5.6% of instances) but is rare. Most instances are pairwise-decomposable.

5. **n=2 target search** (k=3,4,5, 5000 seeds each): Zero matrices found with 6 uncovered pairs and 4 rescue edges each covering exactly 3 pairs. Searched 15,000 random matrices total.

**Why 3-uniform covering never appears (50,001 permutations of k=3 checked, zero hits):**

The structural obstruction has two causes:

1. **Transitivity of column ordering.** If column j covers pair (a_i → a_{i'}) via M[i][j] < M[i'][j], and also covers (a_{i'} → a_{i''}), then it automatically covers (a_i → a_{i''}). A single rescue edge that opens one column-pair automatically opens the transitive closure. This inflates coverage sizes unpredictably — some edges cover 1 pair, others cover 8 — destroying the uniform-3 structure 3DM requires.

2. **Coverage overlap is forced, not free.** In 3DM, each element appears in multiple triples but is covered by exactly one in the matching. The covering structure needs disjoint-coverage to make the decision hard. In temporal bicliques, the overlap pattern is dictated by the matrix's total order structure. At k=3 with 3 rescue edges covering 10 pairs, the overlap ratio is ~1.20 (12 coverage slots / 10 unique pairs). But the overlap pattern is rigid — determined by the matrix, not by our choice.

**The deeper issue:** 3DM requires a **3-partite, 3-uniform** hypergraph: n×n×n universe partitioned into 3 groups of n, each hyperedge touching exactly one from each group. The temporal biclique's covering hypergraph is NOT 3-partite. Pairs like (A0→A1) and (B2→A0) don't fall into clean dimension-separated groups. The "third dimension" (timestamps) doesn't act as an independent dimension — it determines which pairs exist in the first place, creating circular dependence.

**Verdict:** 3DM reduction to minimum temporal clique spanner appears structurally blocked. The covering hypergraph of temporal bicliques lacks the regularity (uniform coverage, partition into dimensions) that 3DM requires. The ternary interactions DO exist (triple synergy at 5.6%) but are too sparse and irregular to encode arbitrary 3DM instances.

**What this rules out:** Any reduction that maps 3DM triples to individual cross edges and expects each edge to cover a fixed number of constraints. The coverage-per-edge is an emergent property of the matrix's total order, not a tunable parameter.

**What remains open:** Reductions from problems with NON-uniform structure — e.g., Minimum Set Cover (where sets have varying sizes, matching the observed coverage distributions), or from graph problems where the constraint graph itself has the overlapping, transitive structure that temporal bicliques naturally produce.

### H4: Brute-force solve time scales exponentially with k (CONFIRMED)

**Experiment:** `timing_probe.py`

**Setup:** For each k in {3, 4, 5}, generate 20 random instances (k×k matrix with values = random permutation of k²). Find the minimum spanner by brute force: compute forced edges F = M⁻ ∪ M⁺, then enumerate subsets of non-forced edges from smallest to largest, checking all-pairs temporal reachability. Stop at the first valid spanner. Record solve time and number of subsets checked. k=6 attempted but a single instance exceeded 5 minutes; k=7 infeasible (2³⁵ ≈ 34 billion subsets).

**Results (20 instances per k):**

| k | optional edges | median time (s) | median subsets checked | time ratio |
|---|----------------|-----------------|----------------------|------------|
| 3 | ~3             | 0.000200        | 8                    | —          |
| 4 | ~8             | 0.00765         | 256                  | 38×        |
| 5 | ~15            | 0.942           | 27,526               | 123×       |
| 6 | ~24            | >300 (timeout)  | —                    | >300×      |

The number of optional (non-forced) edges grows as k² − 2k, so the brute-force search space is 2^(k²−2k). Observed: 2³ → 2⁸ → 2¹⁵ → 2²⁴.

**Model fitting (median solve time vs k, log-space):**

- **Exponential fit** (a·2^(bk)): slope 6.10 in log₂ space. Each unit increase in k multiplies solve time by ~2⁶·¹ ≈ 69×. Log-space residual: 0.47.
- **Polynomial fit** (a·k^b): requires degree ~16.4 to explain the data. Log-space residual: 1.73.
- Exponential fits 3.6× better in log space. The polynomial model's degree 16.4 is implausibly high — no known polynomial algorithm for set cover variants has degree >3.

**Extrapolations from exponential model:**
- k=6: ~116s (consistent with observed >300s timeout on one hard instance)
- k=7: ~14,275s (~4 hours)

**Interpretation:** The brute-force scaling is consistent with NP-hard behavior. The search space grows as 2^(k²−2k), and early termination (finding a small spanner before exhausting all subsets) provides only moderate speedup — the median subsets checked at k=5 is 27,526 out of 32,768 (84% of the space). Most instances at k=5 require searching nearly the entire space because the minimum spanner uses all or nearly all edges (spanner size = k² = 25 in 10/20 instances).

**Caveats:**
1. Exponential brute-force scaling does NOT prove NP-hardness. Many polynomial problems have exponential brute-force solvers. What matters is whether a polynomial algorithm exists.
2. Three data points (k=3,4,5) are too few for robust model discrimination. Both models achieve R²=1.0 in linear space.
3. The high rate of "all edges needed" instances at k=5 (50%) suggests many random instances are trivially hard — the spanner IS the complete biclique. The interesting instances are those where the spanner is strictly smaller.
4. A smarter algorithm (ILP, SAT, dynamic programming on the covering hypergraph) might solve these instances in polynomial time. This experiment only shows brute force is exponential, not that the problem is.

**Next steps:**
- Encode as ILP/SAT and measure scaling with a proper solver to distinguish problem hardness from algorithm stupidity.
- Focus on instances where spanner < k² (the non-trivial regime) and measure scaling there.
- Look for polynomial-time structure in the covering hypergraph that a smarter algorithm could exploit.
