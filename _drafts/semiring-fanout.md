# Semiring Algebra Fan-out for TVG Relay Constraint

Date: 2026-04-04

## Problem

The temporal spanner conjecture (2n-3 edges) reduces to one gap: at relay
vertices in a non-dismountable biclique with k×k timestamp matrix M,
temporal journeys need M[i'][j₁] ≤ M[i'][j₂]. Graph reachability is
proved (ConnectedPair.lean). Temporal reachability additionally needs
this value-based row constraint.

## State of the art (H14)

| Result | Bound |
|--------|-------|
| Best general upper bound | O(n log n) — Casteigts-Peters-Schoeters 2019/2021 |
| Dismountable cliques | 2n-3 — Carnevale et al. 2025 |
| Conjecture | 2n-3 for ALL temporal K_n |
| Lower bound (tight) | 2n-3 (constructions exist) |
| Packing lower bound | 2n-4 (H17, information-theoretic) |

Non-dismountable bicliques always exist (every all-distinct square matrix
has connected column ordering graph — 25k+ samples). Carnevale et al.
reduce TO this case; it's never empty. The conjecture lives or dies at
the non-dismountable residual.

## The proof path (revised after 4 cycles of fan-out)

The original path assumed 2-hop relays through two columns suffice. They don't.
The ConnectedPair approach (route everything through two relay columns) is
**insufficient** — the semiring gap is real and cannot be closed at the
biclique level with two columns.

```
DEAD PATH (two-column routing):
k×k all-distinct matrix M
    ⟹  connected pair (j₁, j₂) exists           [ConnectedPair.lean]
    ⟹  graph reachability through j₁, j₂          [proved]
    ⟹  temporal reachability through j₁, j₂        [FALSE — semiring gap]
```

Why it fails (direction_gap.py, 50k+ samples):
- 2-hop relay in BOTH directions fails for many source-target pairs
- Multi-hop through two columns can't rescue (switching back requires
  the opposite relay, which contradicts uniform ordering)
- At k=3: 17,424 failures, 0 multi-hop rescues
- At k=7: 30,130 unrescued failures

The gap: ConnectedPair gives undirected graph connectivity, but temporal
journeys are directed (timestamps increase). A row with high ranks in
both columns can't reach a row with low ranks via either column ordering.

```
ALIVE PATH A: Full-graph rescue (Quoridor)
Temporal K_n (all edges, not just biclique)
    ⟹  full temporal graph is connected             [given]
    ⟹  2-hop biclique relay may fail
    ⟹  internal edges always rescue (1 hop)          [0 failures, 3k samples]
    ⟹  BUT: with adversarial timestamps too         [0 failures, adversarial]
    ⟹  budget still ≤ 2n-3                          [needs new budget argument]

ALIVE PATH B: Potentials (algebraic, but disconnected from temporal)
k×k all-distinct matrix M
    ⟹  column potentials exist (DAG argument)        [H11, proved]
    ⟹  row potentials exist (GD, 100% empirical)     [H4a]
    ⟹  but potentials ≠ temporal journeys            [gap]
```

Neither path closes the full proof. Path A needs a budget argument.
Path B proves potential existence but not journey existence.

## Cycle 1: Semiring algebra literature (4 hypotheses)

### H1: Kleene star / Johnson potentials (opus, dead)

Johnson potentials give edge-level feasibility (reduced costs ≥ 0), not
row-level ordering across two columns simultaneously.

### H2: Monge matrix structure (opus, dead as approach)

No structural theorem (Monge, Supnick, DLO, totally balanced) applies
to all-distinct matrices. Valuable reformulation: relay fails only if
column j₁ dominates j₂ in every row.

### H3: Tropical convexity / oriented matroids (opus, dead)

Descriptive framework only. Type theory characterizes feasible space
but doesn't propagate constraints.

### H4: Tropical LP duality / mean payoff games (opus, survive → H4a)

Best framework from cycle 1. Akian-Gaubert-Guterman 2012: tropical
feasibility ↔ mean payoff games. Vertex potentials = positional strategies.

## Cycle 2: Computational verification (3 hypotheses)

### Mean payoff game (25,000 matrices, k=3,4,5)
- c=0 fails ~40% (directed), ~25% (undirected)
- Gradient descent ALWAYS finds potentials (100%)
- Potentials are small and sparse (usually one nonzero entry)
- Non-dismountability is automatic for all-distinct square matrices

### Tropical rank vs dismountability (25,000 matrices, k=3..6)
- No dismountable matrices found (non-dismountability is vacuous)
- 2-hop relay failures common (~40%) due to uniform column ordering
- Uniform ordering + adjacency in column graph = relay wall

### Lifted Kleene star (3,000 matrices, k=3,4,5)
- With internal edges: 0 failures (multi-hop always rescues)
- Without internal edges: frequent failures
- Internal edges are load-bearing (V⁻ earliest, V⁺ latest)
- Rescue is always 1 hop (trivial: single internal edge)

## Cycle 3: Proof strategies (4 hypotheses)

### Categorical composition / monotone sweep (dead)

Dijkstra forward sweep: selects ~1.5× greedy minimum.
Reverse sweep: same overshoot. Neither direction builds the spanner.
Backtracking depth O(n) to go from sweep to greedy.
No monotone direction works → categorical framing is dead.

### Quoridor analogy (alive but tautological)

Every rescue is 1-hop = a direct internal edge. Any single edge is a
valid temporal journey. The "rescue" is just the existence of the internal
edge itself. The real question is budget: does keeping all needed internal
edges stay within 2n-3?

### Primal-dual alternating construction (alive, partially)

Tree + repair + prune converges in 1 round (zero cascades — edge addition
is monotone for temporal reachability). But repair oracle is loose: adds
one edge per broken pair. SM instances overshoot.

## Cycle 4: Closing attempts (4 hypotheses)

### H7: Laman / rigidity matroid (dead)

2n-3 = Laman number, but it's coincidence. SM(7) greedy spanner has 28
edges and violates Laman sparsity. Random spanners fail sparsity 15-60%.
The temporal spanner is NOT a rigidity matroid.

**But:** SM(7) actually has a 24-edge spanner (found by randomized search),
well within the 25 = 2n-3 bound. Greedy-latest-first is suboptimal.

### H8: KKM lemma for potential feasibility (superseded by H11)

KKM was identified as the right topological tool but turned out to be
unnecessary — the DAG argument (H11) is simpler.

### H9: Alteration method (dead on worst case)

Tree + repairs gives 2n-3 for random instances but fails on SM.
Broken pairs grow O(n²), repairs fix O(1) each. Cannot reach 2n-3
on adversarial instances.

### H10: Essential edge counting (key structural finding)

- Essential edges = n (Hamiltonian cycle), bridging = n-3
- Forward/backward tree hypothesis FALSIFIED (zero shared edges)
- Every edge in minimum spanner is essential (zero redundancy)
- Minimum spanners consistently hit 2n-4 (below the bound)

### H11: DAG difference constraints (correct but non-temporal)

Uniformly ordered column pairs form a DAG (transitivity of total orders).
Difference constraints on DAGs are always feasible. Column potentials exist.
**But:** column potentials ≠ temporal journeys. No temporal content.

### H12: Alteration repair bound (dead)

Best spanning tree still has O(n²) broken pairs. Cannot stay within
n-2 repairs on worst case. Alteration method is fundamentally broken
for adversarial instances.

### H13: Edge coverage overlap

Every minimum spanner edge is essential (coverage > 0). Singly-covered
pairs = 75-100%. No arborescence decomposition from single root.
Union of ALL source arborescences covers the spanner (but uses too many edges).

### H14: Literature survey

Best proven O(n log n). Dismountable → 2n-3 (Carnevale et al.).
Open: are all temporal cliques dismountable?

## Directionality analysis (after cycle 4)

ConnectedPair.lean gives columns j₁, j₂ where the special row r* is
max(column j₁) AND min(column j₂). Connected is SYMMETRIC in j₁, j₂.

Temporal journey through r*:
```
a_i → b_{j₁} → a_{r*} → b_{j₂} → a_{i'}
  M[i][j₁] ≤ M[r*][j₁] ✓     RELAY: M[r*][j₁] ≤ M[r*][j₂] ???
                                  M[r*][j₂] ≤ M[i'][j₂] ✓
```

Relay needs max(col j₁) ≤ min(col j₂). NOT generally true.

The 2-hop route in direction j₂→j₁ (relay free if j₁ > j₂ uniformly)
needs rank_j₁(i') ≥ rank_j₂(i). Fails for "temporally reversed" pairs
where source has high ranks and target has low ranks.

Multi-hop through two columns CANNOT rescue because switching back
requires the opposite relay direction (contradicts uniform ordering).

**Data (direction_gap.py):**
- k=3: 17,424 failures, 0 multi-hop rescues within biclique
- k=7: 30,130 unrescued failures within biclique
- Confirms: the semiring gap is real for two-column routing

The proof cannot close at the biclique level with two relay columns.
It must use either more columns or the full temporal graph structure.

## Cycle 5: Crosswalk angle (codec / sheaf / R-D)

### H15: Potential-barrier tropical cut (opus, dead)

**Verdict:** Restates the spanner problem from the complement side. No
independent leverage. Single-edge criticality is surprisingly weak —
many sources have zero critical edges. The duality that matters is
covering/packing, not flow/cut.

**Claims:**
- Potential-barrier cut = m minus min spanner. Not a fixed quantity. [opus H15]
- Krishnan's per-pair flow=cut doesn't compose into a global bound.
  The gap: how do O(n²) per-pair min-cuts overlap enough that their
  union ≤ 2n-3? That's covering design, not flow-cut. [opus H15]

### H16: Sheaf exactness = reachability (opus, alive as language)

**Verdict:** H¹ of the tropical sheaf on the event graph = relay
constraint violations. Clean restatement. But tropical semirings lack
rank-nullity — can't convert vanishing cohomology to edge count.

**Claims:**
- H⁰ = consistent earliest-arrival potentials. H⁰ ≠ 0 iff temporal
  connectivity from that source. [opus H16]
- H¹ = local temporal connections that fail to globalize = relay
  constraint violations. Matches Krishnan Thm 5.12. [opus H16]
- Tropical semiring lacks: additive inverses, rank-nullity, Hodge
  inner products. Cannot extract edge-count bound from H¹. [opus H16]
- Seely's Hodge decomposition requires Hilbert space — doesn't transfer
  to tropical setting. [opus H16]

### H17: R-D converse gives 2n-4 (opus, tight but off by one)

**Verdict:** Packing argument gives lower bound 2n-4. Matches empirical
minimum. The conjecture's 2n-3 is an upper bound; R-D proves you NEED
at least 2n-4. Gap = 1 edge = integrality gap of covering LP.

**Claims:**
- Naive counting: each edge covers O(n) pairs → Ω(n) lower bound. [opus H17]
- Packing: 2n-4 pairs with edge-disjoint certifying journeys exist in
  worst case → lower bound 2n-4. [opus H17]
- The (2n-3)th edge provides redundant coverage required by the global
  covering constraint. Information-theoretic counting cannot detect
  this redundancy requirement. [opus H17]
- Checkpoint formula gives ~1.41n, undershoots due to non-uniform
  essential edge spacing. [opus H17]

## Final assessment

### The precise gap (after 5 cycles, 17 hypotheses)

```
2n-4  ≤  min temporal spanner  ≤  2n-3 (conjectured)
 ↑                                  ↑
packing lower bound              O(n log n) proved
(H17, tight)                     (Casteigts et al.)
```

The problem is a **covering design** problem: why does the union of
O(n²) per-pair critical edge sets stay bounded by 2n-3? This is
combinatorial — no algebraic, topological, or information-theoretic
shortcut exists.

### What's alive

1. **Full-graph temporal connectivity** — internal edges always rescue
   biclique failures (0 failures across all tests). The proof must account
   for the full K_n, not just the biclique reduction.

2. **Potentials always exist** — 100% across 25k matrices. The algebraic
   fact is true but disconnected from the temporal journey construction.

3. **The covering design question** — why do per-pair critical edges
   overlap enough? This is the right formulation of the remaining gap.

4. **H¹ = relay failure** — the sheaf language correctly identifies
   what the spanner preserves (exactness of the tropical reachability
   sheaf). Might guide a combinatorial proof even if it can't produce one.

5. **Non-dismountable residual always exists** — every all-distinct matrix
   has connected column ordering. The reduction never empties. The
   conjecture lives or dies at spanning this residual.

## What's dead

| Approach | Cause of death |
|----------|---------------|
| Two-column biclique routing | Semiring gap real, multi-hop can't rescue |
| Monge / Supnick / DLO | Don't apply to all-distinct matrices |
| Tropical convexity | Descriptive only |
| Categorical composition | No monotone direction builds the spanner |
| Laman / rigidity matroid | SM(7) violates sparsity |
| Forward + backward trees | Zero shared edges |
| Alteration method | O(n²) broken pairs, O(1) fix rate |
| KKM lemma | Non-temporal; DAG argument is simpler |
| Greedy-latest-first | Suboptimal (SM(7): 28 vs optimal 24) |
| Potential-barrier cut | Restates spanner problem, no new structure |
| Tropical sheaf H¹ → edge bound | No rank-nullity over tropical semiring |
| R-D converse → 2n-3 | Gets 2n-4 only; integrality gap of 1 edge |
| Directionality closing gap | Graph reachability fails in forced direction |

## Cycle 6: Covering design (the right framing)

### H18: Covering design structure (opus, DEAD — wrong model)

**Verdict:** The critical covering hypergraph has VC dimension 2, LP
integrality gap 0 or 1, and empty-core sunflowers only.

**Claims:**
- Min spanners = 2n-4 consistently (SM and random). [opus H18]
- Every spanner edge is essential (COVER(e) > 0). [opus H18]
- Critical covering LP gap = 0 on SM, 1 on random. [opus H18]
- VC dimension = 2 universally. [opus H18]
- Sunflowers have empty cores only (no 3-way hub). [opus H18]
- Coverage overlap ~45-50% pairwise, sum/pairs ratio ~1.3-2.1. [opus H18]

**Dead (2026-04-04).** The single-edge covering model doesn't capture
temporal reachability. Edges interact: adding e₁ and e₂ together can
cover pairs that neither covers alone (journey chains through both).
The minimum cover of the rescue hypergraph doesn't produce a valid
spanner — verified broken on ~70% of instances at k=3.
(greedy_vs_optimal.py, x3c_reduction.py)

This also kills the VC dim 2 finding — it was measured on the wrong
object. And the NP-hardness reduction via Set Cover — can't reduce
from Set Cover if the problem isn't Set Cover.

The real structure has synergies between edges (submodular/CSP-like),
not independent coverage.

### H19: Journey covering LP (opus, wrong formulation)

**Dead:** The journey-based covering LP (A[p,e]=1 if e on some journey
for p) has integrality gap up to 5x. This is the wrong LP — it lets
fractional solutions exploit journey redundancy. The CRITICAL covering
LP (A[p,e]=1 if removing e breaks p) is the right formulation.

### H20: Turán / extremal (opus, no classical result applies)

**Verdict:** No classical extremal bound gives 2n-3. Tournament
two-arborescence intuition explains 2n-3 but doesn't prove it.

**Claims:**
- No temporal Turán theorem exists. [opus H20]
- Bollobás set-pairs, KK, VC ε-nets all give wrong order. [opus H20]
- Tournament bidirectional = 2 arborescences - 1 shared = 2n-3. [opus H20]
- Full dismountability gives 2n-3 exactly. Open: is it always achievable? [opus H20]

**New papers found:**
- Angrick et al. ESA 2024: "How to Reduce Temporal Cliques to Find
  Sparse Spanners" (arxiv:2402.13624)
- Dismountability Revisited 2025 (arxiv:2502.01321)
- Mertzios et al.: labeling perspective (2n-3 labels on tree edges)

## Summary after 6 cycles (20 hypotheses)

The covering design path (H18) is dead. The single-edge covering model
doesn't capture temporal reachability — edges have synergies (adding
two edges together covers pairs that neither covers alone). VC dim 2
was measured on the wrong object.

The recursive construction (proof sketch) is also dead. T(n) = T(n/2) + O(n)
is greedy in disguise — the residual after hub removal loses extremal
matching structure, so induction doesn't apply.

**What survives:** structural lemmas (non-domination, PivotEdge > n/2,
cross-only spanning, edge monotonicity) and the 2n-3 existential
conjecture. The problem's true structure is interactive (edges interact),
not covering (edges independent). Closer to submodular optimization
or constraint satisfaction than Set Cover.

**Complexity status (2026-04-04):** NP-hardness of minimum temporal
clique spanner (K_n, one label per edge, all distinct) is OPEN. Known
hardness results (Axiotis-Fotakis 2016, Akrida et al.) require sparse
graphs or multiple labels — their reductions don't adapt to temporal
cliques. Neither NP-hard nor in P is established for this setting.

## Key references (new to TVG)

- Akian, Gaubert, Guterman (2012). Tropical polyhedra ↔ mean payoff games.
- Butkovič (2010). Max-linear Systems. Springer.
- Develin, Santos, Sturmfels (2005). Tropical rank.
- Praprotnik & Batagelj (2016). Semirings for temporal network analysis.
- Gaubert & Katz (2011). Tropical Farkas lemma.
- Gondran & Minoux (2008). Graphs, Dioids and Semirings.
- Mohri (2002). Semiring frameworks for shortest-distance problems.
- Sobrinho / Gurney-Griffin. Algebraic routing over right-distributive structures.

## Scripts produced

| Script | Purpose |
|--------|---------|
| mean_payoff_game.py | Compound tropical feasibility + GD solver |
| tropical_rank_dismount.py | Tropical rank vs non-dismountability |
| lifted_kleene.py | Praprotnik-Batagelj lifted semiring Kleene star |
| rescue_depth.py | Multi-hop rescue depth measurement |
| adversarial_rescue.py | Adversarial timestamp ordering tests |
| dijkstra_sweep.py | Monotone sweep spanner construction |
| primal_dual_spanner.py | Alternating prune/traverse construction |
| essential_structure.py | Essential edge counting and decomposition |
| edge_coverage.py | Edge coverage overlap analysis |
| alteration_bound.py | Alteration method repair bound |
| laman_check.py | Laman sparsity verification |
| direction_gap.py | Directionality analysis for connected pairs |
| potential_barrier_cut.py | Potential-barrier cut computation |
| covering_design.py | Covering hypergraph structure, VC dim, LP |
| covering_lp.py | Journey-based covering LP (wrong formulation) |
