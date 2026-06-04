# TVG: Temporal Spanner O(n) Conjecture

Every temporal clique K_n has a spanner with ≤ 2n-3 edges.
Open conjecture (Casteigts-Peters-Schoeters 2021).

## Status

The proof reduces to one algebraic lemma about the tropical semiring.
Everything else is either proved or in the literature.

**Proved in Lean (zero sorry):**
- `Tvg/ConnectedPair.lean`: non-dismountable bicliques always have a
  connected column pair (graph reachability via 2 relay columns)
- Budget: 2d + 4k-4 ≤ 2n-3 (omega)

**Literature:**
- Dismountability reduction, 2 edges per vertex (Carnevale et al. 2025)
- Non-dismountable residual = biclique with M⁻/M⁺ matchings (Theorem 3.10)
- Connected permutation ↔ complete order union (OEIS A003319, Stanley EC1)
- Angrick et al. ESA 2024: extended dismountability, linear spanners for large classes
- Dismountability Revisited (2025): arxiv:2502.01321
- Mertzios et al.: labeling perspective (2n-3 labels on tree edges, dual view)

**The gap (one lemma):**
Graph reachability ≠ temporal reachability. The connected pair gives
directed paths in the order union, but temporal journeys need non-decreasing
timestamps along the FULL path, including at intermediate vertices where
the journey switches relay columns. At vertex i' relaying between columns
j₁ and j₂: need M[i'][j₁] ≤ M[i'][j₂]. This is a semiring constraint.

**Non-dismountable residual always exists:** every all-distinct square
matrix has a connected column ordering graph (tested on 25k+ matrices).
Carnevale et al. reduce TO this case; it's never empty. The conjecture
lives or dies here.

**Two-column routing is insufficient (2026-04-04):** ConnectedPair gives
graph reachability through two relay columns, but temporal reachability
fails for ~40% of source-target pairs. Multi-hop within two columns can't
rescue (switching back contradicts the relay direction). The proof must
use more than two relay columns or the full K_n structure.
See `_drafts/semiring-fanout.md` for complete research log.

## The semiring gap in detail

The biclique timestamps form a k×k matrix M. Temporal reachability is
NOT graph reachability over column orderings. It is min-plus composition
in the tropical semiring:
- min = "first to arrive" (choose best relay)
- + = "accumulate delay" (timestamps compose along journeys)

A journey aᵢ → bⱼ₁ → aᵢ' → bⱼ₂ → aᵢ'' requires:
  M[i][j₁] ≤ M[i'][j₁] ≤ M[i'][j₂] ≤ M[i''][j₂]

The middle inequality M[i'][j₁] ≤ M[i'][j₂] is the semiring constraint.
It depends on VALUES, not orderings. The connected permutation result
handles everything except this one inequality.

Vertex potentials c : Fin k → ℤ might resolve it: if M[i][j] + cᵢ
guides relay selection, the composition constraint becomes algebraic.
Gradient descent on potentials achieves 100% empirically (n ≤ 10).

See `/temporal-compression` crosswalk: "tropical flows are potentials,
not conserved commodities, and no local edge-based cut notion can
restore duality. A global potential-barrier cut does restore it."

## Lean setup

```bash
~/.elan/bin/lake env lean Tvg/ConnectedPair.lean  # zero warnings
~/.elan/bin/lake env lean Tvg/ThreeCases.lean      # sorry warnings only
```

Lean 4 v4.29.0. Config in `lakefile.toml`.

## Key files

- `Tvg/ConnectedPair.lean` — THE proved lemma (connected pair exists)
- `Tvg/ThreeCases.lean` — proof architecture (budget, journey algebra)
- `Tvg/Pigeonhole.lean` — no-injection lemma, fully proved
- `three_cases.py` — three-case route classification
- `bridge_analysis.py` — biclique bridge structure
- `tropical_rank.py` — reachability rank computation
- `crossing_proof.py` — bridge-less pair analysis
- `matching_spanner.py` — diagonal-based spanner tests
- `sm_exact.py` — exact minimum spanner for SM(k)
- `_drafts/semiring-fanout.md` — full research log from 2026-04-04 fan-out
- `direction_gap.py` — proves two-column routing insufficient (semiring gap)
- `lifted_kleene.py` — Praprotnik-Batagelj lifted semiring, Kleene star
- `mean_payoff_game.py` — compound tropical feasibility, GD solver
- `laman_check.py` — Laman sparsity check (disproved)
- `dijkstra_sweep.py` — monotone sweep vs greedy (overshoots)
- `primal_dual_spanner.py` — tree + repair + prune (zero cascades)
- `adversarial_rescue.py` — adversarial timestamp tests (1-hop rescue)
- `pivot_edge_search.py` — pivot-edge search on extremally matched bicliques
- `constrained_covering.py` — covering LP on condition-3 bicliques
- `vc_dim_proof.py` — VC dimension and shattering obstruction analysis
- `covering_design.py` — covering hypergraph structure analysis
- `vminus_connectivity.py` — V⁻ temporal connectivity (always 100%)
- `dual_labeling_test.py` — Mertzios dual labeling test (falsified)
- `bisect_quality.py` — git bisect quality on temporal bicliques
- `matching_overlap.py` — M⁻ ∩ M⁺ overlap (almost never, kills naive budget)
- `x3c_reduction.py` — X3C → temporal clique encoding attempt (failed, covering model wrong)
- `greedy_vs_optimal.py` — greedy vs optimal rescue: proved covering model broken (~70% invalid)
- `two_hub_kn.py` — double star on K_n (dead: fails 96% of hub-less)
- `hubless_verify.py` — greedy vs exhaustive tree search (greedy inflates hub-less 10×)
- `hubless_anatomy.py` — structural analysis of truly hub-less instances
- `non_star_structure.py` — degree patterns of optimal non-star spanners
- `forward_ratio_converse.py` — forward ratio tautology proof
- `hubless_rate.py` — true hub-less rate across K_n (vanishes by n=8)
- `birthday_bound.py` — set-cover analysis of hub rescue structure
- `birthday_best_hub.py` — interactive greedy best-hub analysis
- `adversarial_birthday.py` — adversarial minimize valid hubs
- `scale1_rescue.py` — scale-1 rescue lemma test (3-hop relays)
- `gap_analysis.py` — dead zone fraction by rank distance
- `adversarial_gap.py` — adversarial scale-1 gap blocking
- `deadzone_routes.py` — dead-zone routing and multi-hop mechanisms
- `greedy_trace.py` — trace of greedy tree selection (LIVE vs DZ edges)
- `live_edge_count.py` — LIVE edge degree per vertex
- `live_floor.py` — adversarial min max LIVE degree (n-3 to n-4)
- `floor_large_n.py` — LIVE floor at n=15,18,20
- `median_floor.py` — direct construction via extreme edges (DZ ≈ n/2)
- `optimal_pair.py` — structure of DZ=0 pairs
- `domination_pair.py` — comparison of pair selection strategies
- `deadzone_budget.py` — dead zone timestamp budget analysis

## Dead ends (don't retry)

- Star+tree on non-dismountable bicliques (no valid hub for SM(k))
- Inductive tree construction (global, not local — fails step-by-step)
- Three-case decomposition (valid for star+tree but star+tree is wrong for hard case)
- Graph reachability as proxy for temporal reachability (semiring gap)
- Connected permutations alone (graph result, not semiring result)
- All hub heuristics (no vertex metric predicts success)
- Barvinok tropical rank on full clique (wrong abstraction level)
- Diagonal-based biclique spanners (SM-specific, doesn't generalize)

### Dead ends from semiring fan-out (2026-04-04)

- **Two-column biclique routing** — the semiring gap is real. 2-hop relay
  fails ~40%; multi-hop within two columns can't rescue (switching back
  requires opposite relay, contradicts uniform ordering). ConnectedPair.lean
  gives undirected connectivity but temporal journeys are directed.
  17k-30k unrescued failures across k=3..7. (direction_gap.py)
- **Monge / Supnick / DLO matrix structure** — nothing in the temporal
  clique forces these. All-distinct matrices are generic, not structured.
- **Tropical convexity (Develin-Sturmfels)** — descriptive framework only,
  no tool to propagate constraints from connectivity to relay feasibility.
- **Categorical composition / monotone sweep** — Dijkstra forward AND
  reverse both overshoot by ~1.5×. O(n) backtracking needed. No monotone
  direction builds the spanner. (dijkstra_sweep.py)
- **Laman / rigidity matroid** — 2n-3 = Laman number is coincidence.
  SM(7) greedy spanner violates Laman sparsity. Random spanners fail
  sparsity 15-60%. (laman_check.py)
- **Forward + backward trees** — share zero edges, their union is not a
  spanner. Temporal directionality makes graph-theoretic MST irrelevant.
  (essential_structure.py)
- **Alteration method (tree + repairs)** — broken pairs grow O(n²),
  repairs fix O(1) each. Fails on SM instances. (alteration_bound.py)
- **KKM lemma** — identified as right topological tool, but superseded
  by simpler DAG argument (H11). Either way: proves matrix fact (column
  potentials exist) with zero temporal content. Potentials ≠ journeys.
- **Greedy-latest-first** — suboptimal. SM(7): gives 28, optimal is 24.
  Deterministic greedy is a red herring for the proof.
- **Non-dismountability as filter** — vacuous for square all-distinct
  matrices. Every row's sorted order is a path on all k columns →
  column ordering graph always connected. Doesn't narrow the problem.
- **Covering design / VC dim 2 (H18)** — the single-edge covering model
  doesn't capture temporal reachability. Edges interact: adding e₁ and e₂
  together covers pairs that neither covers alone (journey chains through
  both). Minimum cover of the rescue hypergraph doesn't produce a valid
  spanner (~70% broken at k=3). VC dim 2 was measured on the wrong object.
  The problem is interactive (submodular/CSP-like), not covering.
  (x3c_reduction.py, greedy_vs_optimal.py)
- **Recursive construction / O(n) proof sketch** — T(n) = T(n/2) + O(n)
  is greedy in disguise. Residual after hub removal loses extremal matching
  structure (M⁻/M⁺ change). Induction doesn't apply. Same barrier as all
  other greedy approaches. (on-proof-sketch.md)
- **NP-hardness via Set Cover reduction** — can't reduce from Set Cover
  if the problem isn't Set Cover. Axiotis-Fotakis (2016) also doesn't
  adapt: requires sparse graphs or multiple labels per edge. NP-hardness
  of min temporal clique spanner (single label, all distinct) is OPEN.

### Dead ends from Farey/distributed fan-out (2026-04-05)

- **Farey tree mappings (H1-H3)** — Farey trees are 1D structures on
  totally ordered sets. Temporal spanners are 2D (bipartite vertex-sharing
  + timestamp ordering). No mapping preserves both. Three variants tested
  (timestamp ranks, row ratios, mediant relay), all dead.
- **Online greedy (H4, H6)** — keeps nearly all k² edges. Each edge
  genuinely adds reachability. Competitive ratio Θ(k). Arrival order
  doesn't help.
- **Farey/mediant healing (H5, H5b)** — mediant healing 55% at k=6.
  Universal 1-healability was SM(k) artifact; 0-31% on random matrices.
- **Per-node O(1) Farey heuristic (H7)** — budget is right (3-4/row)
  but selection requires cross-row coordination. No fixed heuristic works.
- **Distributed Farey relaxation (H8)** — Farey adjacency vacuous on
  random timestamps (0.7-3.3% of pairs). Drop rule never fires.
- **BGP path-vector (H9)** — temporal routes are querier-dependent
  (arrival time matters). No route exists independent of the asker.
- **O(n) heuristics (H11)** — relay value is non-local. No local
  information predicts which edges are critical relays.
- **Union-find (H12)** — symmetric (bidirectional merge), but temporal
  reachability is asymmetric. 75% of same-component edges are temporally
  useful. Zero filtering power.
- **O(n) construction** — appears fundamentally impossible. Relay value
  is non-local; checking edge redundancy requires global reachability query.
- See `_drafts/farey-spanner.md` for full research log (13 hypotheses).

### Dead ends from proof manual fan-out (2026-04-06)

- **Double counting + PivotEdge (H-DC)** — relay sets overlap 100%.
  R_max = Θ(k²), one edge covers constant fraction of all pairs.
  Lower bound converges to ~4, not 4k-3. Volumetric arguments are dead.
- **FKG + probabilistic method (H15)** — edge monotonicity IS the FKG
  condition, positive correlation confirmed. But at budget density
  p=(4k-3)/k², bottleneck pair has P≈0.2, needs P>0.99. Random
  subgraphs with 4k-3 edges are almost never spanners (need 93% of edges).
- **LGV on temporal DAG (H16)** — LGV applies cleanly but answers wrong
  question (counts paths, not removable edges). Tropical determinant and
  non-intersecting journey count don't relate to 2n-3.
- **Lifted ring rank (H17)** — Praprotnik-Batagelj semiring has no
  additive inverses. Factor rank trivially 2k. Cancellation fails.
  Cannot do linear algebra over a semiring. All algebraic rank approaches dead.
- **Charging-discharging (H18)** — max charge per edge ~1.9n, non-uniform.
  Certificate approach gives O(n) lower bound but not tight 2n-3 constant.
  Finding: optimal K_n spanners are I-frame-dominated (vertex extremes).
- **Exchange argument (H19)** — minimal spanners CAN exceed 2n-3
  (n=7: size 13 > 11). Non-matroid: locally irredundant ≠ globally optimal.
  Exchange graph disconnected. Matroid theory fully dead.
- **Deformation (H20)** — Lipschitz constant exactly 1 (single swap
  changes optimal by ±1). Landscape is mesa-shaped (flat at 2n-4, ridges
  at 2n-3). Zero slack kills deformation certificate.
- **Vertex-extreme spanner (H21)** — per-vertex min/max edges fail hard
  at n≥8 (0% success). Small-n artifact. Sharing → 0 by n=7.
- **SJT ordering on CPS residual (H24)** — min consecutive symmetric
  difference is O(log k), not O(1). Structural: timestamp independence
  means partner neighborhoods diverge by ~log(k).
- **Matroid exchange on matchings (H25)** — min step for Hamiltonian
  ordering is Θ(n). Collector neighborhoods aren't matroid bases.

### Alive from all fan-outs (2026-04-05 through 2026-04-07)

- **Best-response dynamics (H10)** — Nash equilibrium matches centralized
  greedy (PoA ≤ 1.25). 2-round convergence. Per-node degree O(1).
  Construction O(k⁵). First distributed temporal spanner construction
  (field is open). Not a proof of the conjecture but potentially publishable.
- **Forward reachability is transitive** (semiring). Backward is not.
  This asymmetry is the structural reason symmetric tools fail.
- **4k-3 budget fails at k≥7** for random K_{k,k}. CPS conjecture is
  for K_n, not K_{k,k}. ~6% genuinely infeasible at k=4.
- **Optimal K_{k,k} spanner size is O(k log k)**, not O(k).
- **Sequential delegation does NOT kill the log factor (H26, CORRECTED
  2026-04-07).** Root delegation tested: edges/k grows as log(k).
  k=10: 2.86, k=20: 3.30, k=50: 4.33. The temporal filtering at each
  relay vertex eats a constant fraction of the timestamp range, requiring
  O(log k) doublings. H26's telescoping claim was wrong — missed
  collectors are NOT shared across emitters. The CPS log factor is
  STRUCTURAL for their delegation framework, not an analysis artifact.
  A fundamentally different construction is needed for O(n).
  (delegation_test.py)
- **Star+tree construction (H27).** Pick hub, connect to all (n-1 edges),
  spanning tree on rest (n-2 edges). Total: exactly 2n-3. Greedy tree
  finds a valid hub for 99.8% of instances through n=20. Exhaustive tree
  search resolves most greedy failures. Conjecture confirmed exhaustively
  through n=12.
- **True hub-less rate (2026-04-07).** Greedy tree inflates hub-less rate
  10×. Exhaustive tree search: K_5=0%, K_6=0.026%, K_7=0.014%, K_8+=0%.
  Hub-less phenomenon appears small-n only, vanishes by n=8.
- **Hub-less instances are easier (2026-04-07).** Truly hub-less K_6
  instances have optimal spanners of size 2n-4 (below conjecture bound).
  Degree pattern [2,2,3,3,3,3], cycle rank 3. No hub needed — mesh works.
- **M⁻ covers all A-A pairs, M⁺ covers all B-B pairs (2026-04-07,
  proved).** In any extremally matched biclique: M⁻[j] = column min
  is a permutation. Edge (m⁻(j), j) has min timestamp in column j, so
  relay a_{m⁻(j)} → b_j → a_{i'} works for all i'. Similarly M⁺
  covers all B-B pairs via row maxima. This is exact, not approximate.
  Remaining gap: A-B/B-A pairs not directly in M⁻ ∪ M⁺.
- **Double-star on extremally matched bicliques: 100% through k=9
  (2026-04-07).** Star(row h) ∪ star(col c) = 2k-1 edges + 2k-2
  relay edges = 4k-3 = budget. Greedy always fits within budget on
  extremally matched bicliques. This is the correct target (from
  dismount reduction), unlike random K_{k,k} which fails at k≥7.
  (biclique_extremal.py)
- **Three-timestamp median framework (2026-04-07, descriptive only).**
  For triangle {h,v,w}: edge {v,w} is LIVE for hub h iff σ({v,w}) is
  NOT the median of three timestamps. Average DZ degree = (n-2)/3.
  Useful for understanding structure but doesn't yield a proof — the
  Median Floor Conjecture (min DZ ≤ C) requires tools that don't exist
  in the literature. See dead ends below.

### Dead ends from 2026-04-07 session (birthday bound + median + biclique)

**The fundamental wall:** every proof strategy that fixes a hop count fails.
The adversary forces journey lengths that grow with n (or k). At K_{k,k}:
max journey = 3-4 at k=3, 5-8 at k=8, growing as ~k. Any argument that
reasons about k-hop relays for fixed k is dead. The proof must reason about
GLOBAL reachability structure, not local relay conditions.

**Proof strategies attempted and why they fail:**

- **3-hop relay birthday bound** — adversary CAN put all non-star edges in
  dead zones (T_a < τ < T_b). Route A and Route B both fail completely.
  Verified: K_4 admits full dead-zone assignment. 3-hop analysis gives the
  adversary too much power. (deadzone_routes.py)
- **4-hop relay on bicliques** — works for small k but hop count grows.
  Max journey in K_{k,k} spanner: 4 at k=3, 6 at k=4, 8 at k=5, 9 at k=6.
  Any fixed-hop argument is a dead end. (journey_lengths.py)
- **Sequential delegation / CPS improvement** — root delegation gives
  Θ(k log k), NOT O(k). The log is structural: temporal filtering at relay
  vertices consumes O(1/log k) fraction of timestamp range per step,
  requiring O(log k) steps. H26 telescoping was wrong — missed collectors
  aren't shared. CPS framework cannot yield O(n). (delegation_test.py)
- **K-early+late construction (K=3, ~5n edges)** — 100% empirical success
  through n=30 but unprovable. The 4-hop analysis only covers 20% of
  backward pairs; the rest use multi-hop chains of unbounded length.
  Same wall as every other approach. (cn_spanner.py, prove_5n.py)
- **Induction on k (add row+column)** — budget increase is 4 edges per
  step. Works 100% at k=5,6 but avg extra edges grows as k². At k=10:
  avg=45, max=121. The adversary can make the new row/column expensive
  to integrate because the base spanner isn't extension-compatible.
  (induction_test.py, induction_scale.py)
- **Median Floor Conjecture** — clean statement (∃ (h,v) with DZ ≤ C) but
  unprovable with current tools. Average DZ = (n-2)/3 (proved by double
  counting). Min DZ ≤ 2 empirically. But no extremal argument closes the
  gap from average to minimum. Tree domination literature too thin.
  Complementarity DZ(h,v)+DZ(v,h)=n-2 gives min ≤ (n-2)/2, far from ≤ 2.
  (median_floor.py, live_floor.py, optimal_pair.py, domination_pair.py)
- **LIVE degree floor = n-O(1)** — empirically n-3 to n-4, but "empirical"
  doesn't help. The adversary can push max LIVE to n-4 at K_18.
  (floor_large_n.py, live_edge_count.py)
- **Dismountability revisited (Theorem 5.2)** — recursively k-hop
  dismountable → pivotable → 2n-3. But NOT all cliques are k-hop
  dismountable (explicit counterexamples, Thm 3.10). The gap remains
  at the biclique spanner ≤ 4k-3 lemma. (arxiv:2502.01321)
- **Forward ratio / star coverage** — both always exactly 50% for any
  vertex in any K_n. Tautologies. Not diagnostic. (forward_ratio_converse.py)
- **Double star on K_n** — star(h1) ∪ star(h2) = 2n-3 edges (exactly at
  budget). Fails 96% of hub-less K_7 instances. All routing forced through
  h1/h2; no flexibility for non-hub-to-non-hub paths. Budget fully consumed
  by stars, zero tree edges. (two_hub_kn.py)
- **Forward ratio as hub-less diagnostic** — forward ratio (fraction of
  pairs routable via 2-hop through v) is ALWAYS exactly 50% for every
  vertex in every K_n with distinct timestamps. It's a tautology from
  C(n-1,2)/(n-1)(n-2) = 1/2. Not informative. (forward_ratio_converse.py)
- **Star 2-hop coverage** — also always exactly 50% (10/20 at K_6).
  Every hub covers exactly the same number of pairs via direct star routing.
  The distinguishing factor is tree compatibility, not star coverage.

### Findings that are alive but don't close the gap

- **Potentials always exist** — GD finds row potentials 100% of the time
  (25k matrices). Column potentials exist by DAG argument (H11). But
  potentials don't produce temporal journeys.
- **Internal edges always rescue** — lifted Kleene star shows 0 failures
  with internal edges across 3k samples, even adversarial timestamps.
  Rescue is always 1 hop (direct internal edge). But budget argument
  is missing.
- **Temporal composition = right pre-semiring** — Praprotnik-Batagelj
  lift to temporal quantities restores full semiring structure. Kleene
  star computes all-pairs reachability in lifted semiring. But doesn't
  give the 2n-3 bound.
- **Edge monotonicity** — adding an edge never breaks temporal reachability
  (zero cascades in primal-dual). Repairs are safe but the oracle is loose.
- **H¹ of tropical sheaf = relay failure** — sheaf language correctly
  identifies what the spanner preserves (exactness). Can't give edge count
  (no rank-nullity over tropical semiring) but guides the right question.
- **Packing lower bound = 2n-4** — information-theoretic converse via
  edge-disjoint journey packing. Tight. Gap to conjecture = 1 edge
  (integrality gap of covering LP).
- **Critical covering LP** — integral but too loose (LP value ~5 vs
  IP ~13 at k=4). Gap grows linearly. Dead as a proof tool.
- **PIVOT-EDGE (2026-04-04, corrected 2026-04-05).** PivotEdge.lean proves
  any M⁻ cross edge has |In∩Out| ≥ k+1 in the FULL temporal graph (using
  V⁻/V⁺ internal edges for routing). This is NOT Angrick's biclique-only
  pivot-edge: under Angrick's definition (cross edges only), SM(k) has
  trivial pivot-sets of size 2 (Lemma 6.4). Our k+1 result depends on
  internal edges — sandwich property is load-bearing.
  Angrick's framework gives (8/c)n with recursive pivot-edges, but SM(k)
  requires a different mechanism (e-reverted edges, Theorem 6.6, giving 4n-4).
  Product graphs SM(m)×SM(k) defeat both pivot-edges and reverted edges.
- **CROSS-ONLY SPANNING (2026-04-05, proved).** Cross edges alone span ALL
  pairs (A-A, B-B, A-B) in any extremally matched biclique. 670 random +
  all SM(k) k=3..8: zero failures, always ≤ 2n-3. Internal edges redundant.
  Proof: M⁻ permutation → no row dominates another (column j with
  m⁻(j)=i gives M[i][j] < M[i'][j] for all i'). M⁺ → no column dominates.
  2-hop relay: a_i → b_j → a_{i'} (B-frame). This is the codec connection.
- **OPTIMAL SM(k) STRUCTURE (2026-04-05).** Optimal spanners for SM(k) are
  ALL cross edges (zero internal). M⁻∪M⁺ (2k edges) are essential (I-frames).
  Each intermediate diagonal d=1,...,k-2 needs ~2 edges (B-frames).
  Total: 2k + 2(k-2) = 4k-4 = 2n-4 for k≤7. SM(8) first to hit 2n-3.
  Exhaustive: valid 2-per-diagonal selections exist for SM(k) k=3..7.
  Canonical form: d=1→(0,1), d>1→(1,k-d). Per-diagonal greedy fails;
  joint optimization required (= R-D optimization over GOP in codec terms).

## O(n) proof sketch (2026-04-05, DEAD 2026-04-04)

See `_drafts/on-proof-sketch.md`. The argument:
1. Non-domination: cross edges span all pairs (Lemma 1, proved)
2. PivotEdge: any M⁻ edge covers > n/2 vertices in full graph (Lemma 2, Lean)
3. Edge monotonicity: adding edges never breaks reachability (Lemma 3, proved)
4. Asymmetric recursion: pivot covers > half → T(n) = T(n/2) + O(n) = O(n)

**Dead:** The recursion is greedy in disguise. The residual after removing
covered vertices loses extremal matching structure — M⁻/M⁺ of the submatrix
differ from restrictions of the original. Induction hypothesis doesn't apply.
Same barrier as all other greedy approaches in this problem.

## Context

Started from Prof. Peters' email about his temporal spanners paper.
The blog post `/temporal-compression` connects temporal graphs to
video codecs and sheaf cohomology via the tropical semiring. The
three-field gap identified there is exactly where this proof lives.
