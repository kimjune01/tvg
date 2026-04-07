# Synopsis: Temporal Spanner ↔ Codec Crosswalk

The 2n-3 temporal spanner conjecture and the codec compression problem share vocabulary at a depth far beyond the basic I-frame/P-frame analogy. This synopsis maps every term that has emerged from the research, graded by strength of correspondence.

---

## Glossary: Full Crosswalk

### Tier 1: Genuine (same formal primitive under relabeling)

| # | TVG term | Codec term | Identification | Source |
|---|----------|-----------|----------------|--------|
| 1 | **Temporal clique K_n** | **Raw video sequence** | Complete graph with one timestamp per edge = sequence of frames with all pairwise dependencies available | CLAUDE.md |
| 2 | **Temporal spanner** | **Compressed bitstream** | Sparse subgraph preserving all-pairs reachability = subset of frames/references preserving decodability | Casteigts-Peters-Schoeters 2021 |
| 3 | **I-frame (forced edge, M⁻/M⁺)** | **I-frame (intra-coded)** | Edge that is earliest in its column (M⁻) or latest in its row (M⁺). Removal breaks reachability. Self-contained reference point. | Carnevale et al. 2025; optimal_structure.py |
| 4 | **B-frame (intermediate cross edge)** | **P-frame / B-frame** | Non-forced cross edge that relays between I-frames. Provides bidirectional 2-hop journey. Each intermediate diagonal needs ~2 edges. | optimal_structure.py |
| 5 | **GOP (group of pictures)** | **GOP** | Hub star = set of edges centered on one vertex. Defines the scope within which P-frames can reference the hub I-frame. | double_star.py |
| 6 | **Dismountable vertex** | **Predictable frame** | Vertex whose reachability can be delegated to two neighbors at cost 2 edges. Peelable without affecting the rest. Like a P-frame that adds no independent information. | Carnevale et al. 2025, Theorem 2.1 |
| 7 | **Non-dismountable residual** | **Scene (irreducible segment)** | The biclique that remains after peeling all dismountable vertices. Cannot be further compressed by local delegation. The hard case. | Carnevale et al. 2025, §3 |
| 8 | **Chain fragility** | **Reference loss** | Temporal journey breaks when timestamp ordering fails at a relay vertex (M[i'][j₁] > M[i'][j₂]). Codec chain breaks when a reference frame is lost. Both: sequential dependency where any break severs the tail. | CROSSWALK.md; direction_gap.py |
| 9 | **Edge monotonicity** | **Monotone R-D** | Adding an edge to a temporal spanner never breaks existing reachability (zero cascades). Adding a reference frame to a bitstream never reduces decodability. Both: the feasible set is upward-closed. | primal_dual_spanner.py |
| 10 | **Tropical semiring (min, +)** | **Delay network** | First-arrival composition: min = choose best path, + = accumulate delay. The algebra of temporal reachability. Codecs use the same algebra for decode-order scheduling. | temporal state machines (PMC 9792072) |

### Tier 2: Moderate (same structural role, different state space)

| # | TVG term | Codec term | Mapping | Grade rationale |
|---|----------|-----------|---------|-----------------|
| 11 | **Twist permutation σ = m⁺∘m⁻** | **Motion field** | σ maps column-to-column through the extremal matchings: "where does the earliest arrival in column c send its latest departure?" Motion vectors map pixel-to-pixel through prediction: "where does this block come from?" Both describe the flow of temporal reference through the structure. | Same role (reference flow), different objects (permutation vs. vector field) |
| 12 | **Fixed point of σ** | **Static region** | σ(c) = c: the column's min-row departs latest back to the same column. A self-referencing temporal loop. In codecs: static region where motion vector is zero — the block predicts itself. Both: the reference points back to its own origin. | cycle_breaking.py, fixed_point_algorithm.py |
| 13 | **Derangement (σ has no fixed point)** | **Full-motion scene** | Every column's reference flow points elsewhere. No self-referencing hub exists. In codecs: every block moves — no static region, scene-wide motion. Hardest case for both compression and hub selection. | fixed_point_algorithm.py |
| 14 | **Cycle structure of σ** | **Motion segmentation** | σ decomposes into cycles of varying length. Each cycle is a group of columns whose reference flow forms a closed loop. In codecs: motion field decomposes into coherent regions (rigid bodies, background, foreground). The number of cycles ≈ number of motion segments. | cycle_breaking.py: avg cycles ~ ln(k) |
| 15 | **Hub vertex (h, c)** | **Anchor frame / reference picture** | The vertex whose star edges provide temporal shortcuts that break all cycles of σ. In codecs: the reference frame that multiple P-frames point to. The choice of anchor determines GOP efficiency. Both: global optimality, local unpredictability. | double_star.py, two_hub_exhaustive.py |
| 16 | **Concordant pairs** | **Prediction residual** | Pair (i, i') where both hub columns agree on the ordering (M[i][c₁] > M[i'][c₁] AND M[i][c₂] > M[i'][c₂]). The pair can't be relayed through either column — a "prediction failure." In codecs: the residual after motion compensation — what prediction couldn't handle. | next-session.md |
| 17 | **Cross-only spanning** | **Inter-prediction sufficiency** | Cross edges alone span all pairs (A-A, B-B, A-B). Internal edges are redundant. In codecs: inter-frame prediction alone reconstructs the sequence; intra-coded blocks within P-frames are unnecessary when motion compensation works perfectly. | cross_only_spanner.py, domination_proof.py |
| 18 | **Non-domination theorem** | **No block is redundant** | M⁻ permutation → no row dominates another (∀ i≠i', ∃ j: M[i][j] < M[i'][j]). In codecs: no frame makes another frame completely predictable from every reference angle. Every frame contributes unique temporal information in at least one direction. | domination_proof.py |
| 19 | **Packing lower bound (2n-4)** | **Shannon converse** | Information-theoretic: edge-disjoint journey packing gives a lower bound on spanner size. In codecs: Shannon's converse gives a lower bound on bitrate. Both: you can't compress below the information content. The gap to the conjecture = 1 edge = integrality gap. | semiring-fanout.md H17 |
| 20 | **O(n log n) dismountability bound** | **Adaptive GOP sizing** | Recursive dismounting with log n depth gives O(n log n) edges. In codecs: adaptive GOP sizing (scene-change detection) gives log n overhead over optimal fixed-GOP. Both: the log factor is the cost of not knowing the scene structure in advance. | Casteigts et al. 2021; Angrick et al. ESA 2024 |

### Tier 3: Structural analogy (same problem shape, not same formalism)

| # | TVG term | Codec term | Analogy | Why not higher |
|---|----------|-----------|---------|----------------|
| 21 | **Backward pass (hub repair)** | **Two-pass encoding** | Forward: dismount greedily. Backward: add hub stars to fix failures. In codecs: first pass collects statistics, second pass optimizes bit allocation. Both: forward pass commits without full information, backward pass repairs with global view. | Different optimization targets (reachability vs. bits) |
| 22 | **Certificate size Θ(k²)** | **Decode complexity** | Verifying a hub requires reading ~84% of the matrix. Decoding a P-frame requires the full reference frame. Both: verification/decoding requires global information even though the compressed representation is small. | query_complexity.py |
| 23 | **SM(k) (shift matrix)** | **Uniform motion (pan/scroll)** | Circulant timestamp structure where every vertex is a valid hub. In codecs: uniform camera pan where every frame predicts equally well from its neighbor. The easiest case for both — high regularity makes compression trivial. | SM is a specific construction, not a general phenomenon |
| 24 | **Greedy-latest-first (suboptimal)** | **CBR encoding (suboptimal)** | Deterministic greedy gives SM(7): 28 edges, optimal is 24. In codecs: constant bitrate encoding wastes bits on easy scenes, starves hard scenes. Both: uniform resource allocation ignores scene structure. | greedy_vs_optimal.py |
| 25 | **Joint diagonal optimization** | **Rate-distortion optimization** | Optimal spanner requires joint selection across all intermediate diagonals. Per-diagonal greedy fails. In codecs: R-D optimization over the full GOP, not per-frame. Both: the optimization is global, not decomposable. | joint_diagonal.py |
| 26 | **Covering hypergraph** | **Dependency graph** | Each cross edge "covers" certain source-target pairs via the journeys it enables. The covering structure has edge interactions (adding e₁ and e₂ together covers pairs that neither covers alone). In codecs: the dependency graph between frames has the same non-decomposable structure. | x3c_reduction.py, greedy_vs_optimal.py |
| 27 | **Dismounting order** | **Encoding order** | The order in which vertices are dismounted doesn't affect the residual (1-hop is order-independent). But mixed k-hop dismounting is order-dependent. In codecs: encoding order matters for B-frames (decode order ≠ display order) but not for pure P-frame chains. | backward_pass.py; Carnevale et al. 2025 p.9 |
| 28 | **Extremal matchings M⁻, M⁺** | **First/last reference** | M⁻: earliest edge per column (first time each target is reachable). M⁺: latest edge per row (last time each source can still transmit). In codecs: first and last references in a GOP — the temporal anchors. | Carnevale et al. 2025, Corollary 3.3 |
| 29 | **V⁻/V⁺ partition** | **Sources / sinks** | Non-dismountable residual partitions into V⁻ (earliest neighbors) and V⁺ (latest neighbors). V⁻ are temporal sources, V⁺ are temporal sinks. In codecs: the first and last frames of a scene. | Carnevale et al. 2025, Theorem 3.9 |
| 30 | **Temporal composition (right pre-semiring)** | **Prediction chain** | Journey composition: a_i → b_j at t₁, then b_j → a_{i'} at t₂ requires t₂ ≥ t₁. Praprotnik-Batagelj lift to temporal quantities restores semiring structure. In codecs: prediction chains compose only if decode dependencies are satisfied. | lifted_kleene.py |
| 31 | **Keyframe rate** | **Keyframe rate** | The ratio of I-frames to total edges in the spanner. For SM(k): 2k forced / (4k-4 total) → 50% as k grows. In codecs: I-frame interval, the GOP length. The survival parameter of temporal compression. | timekeeping-parameter.md |
| 32 | **Error accumulation (chain length)** | **Drift** | Long P-frame chains accumulate timestamp ordering violations. Long codec chains accumulate quantization error. Both: the mechanism that makes keyframes necessary. | timekeeping-parameter.md |
| 33 | **2 backward passes suffice** | **2-pass VBR encoding** | Empirically: at most 2 hub stars repair any greedy forward construction. In codecs: 2-pass variable bitrate gives near-optimal quality. Both: two passes capture enough global information. | backward_pass.py |
| 34 | **Hub as fixed point of σ** | **Scene anchor as motion fixed point** | The hub is the vertex where temporal reference flow is stationary. The scene anchor is the frame where motion is zero. Both: the natural center of a temporal structure, identifiable by self-reference. | fixed_point_algorithm.py |
| 35 | **σ² fixed points (2-cycles)** | **Bidirectional prediction** | Elements in 2-cycles of σ: two columns whose reference flow ping-pongs between them. In codecs: B-frames that predict from both past and future. Both: bidirectional reference structure. | fixed_point_algorithm.py |

---

## Structural claims (in the subject's vocabulary)

### From temporal graph theory

1. **Every temporal clique K_n has a spanner with O(n log n) edges.** Constructive, via dismountability + fireworks (Casteigts et al. 2021). Simplified to dismountability alone (Carnevale et al. 2025). [Casteigts-Peters-Schoeters 2021]

2. **Dismountable cliques admit 2n-3 spanners.** Each dismountable vertex costs exactly 2 edges. Recursively dismountable = solved. [Carnevale et al. 2025, Figure 2]

3. **Non-dismountable residual is a biclique with extremal matchings.** V⁻/V⁺ partition, M⁻/M⁺ perfect matchings, reciprocity between earliest/latest neighbors. This is the hard case. [Carnevale et al. 2025, Theorem 3.10]

4. **1-hop dismountability is order-independent.** Any dismountable vertex can be removed in any order. The recursion is "oblivious." [Carnevale et al. 2025, §2]

5. **Mixed k-hop dismounting is order-dependent.** Choosing a {1,2,3}-hop dismountable vertex at the wrong step can block future dismounts. [Carnevale et al. 2025, p. 9]

6. **k-hop for k > 3 reduces to {1,2,3}-hop.** No new structural types beyond hop distance 3. [Carnevale et al. 2025, Theorem 3.7]

7. **NP-hardness of minimum temporal spanner is open for temporal cliques.** Known for general temporal graphs (multi-label, Axiotis-Fotakis 2016). Single-label all-distinct case is open. [np-hardness-fanout.md]

### From the computational investigation

8. **Cross edges alone span all pairs.** Non-domination theorem: M⁻ permutation → no row dominates another. Every pair has a 2-hop cross-edge relay. Internal edges are redundant. [domination_proof.py, cross_only_spanner.py; 670 random + all SM(k) k=3..8]

9. **Optimal SM(k) spanners use zero internal edges.** M⁻∪M⁺ (2k forced) + ~2 per intermediate diagonal = 4k-4 = 2n-4 for k≤7. SM(8) first to hit 2n-3. [optimal_structure.py]

10. **2 hub pairs always suffice.** Exhaustive through k=15, zero failures. Total ≤ 6k = 3n = O(n). [two_hub_exhaustive.py]

11. **Fixed points of σ = m⁺∘m⁻ predict valid hubs.** 100% success rate at k=7 when fixed points exist (~60% of instances). When σ is a derangement, no single hub works (0% at k≥7). [fixed_point_algorithm.py, cycle_breaking.py]

12. **Certificate size is Θ(k²).** ~84% of matrix entries must be read to certify a hub. Bottleneck: verifying M⁻/M⁺ identities requires column-by-column comparison. [query_complexity.py]

13. **Edge monotonicity holds.** Adding edges never breaks temporal reachability. Zero cascading failures in primal-dual construction. [primal_dual_spanner.py]

14. **2 backward passes always suffice.** Forward: greedy dismount. Backward 1: single hub star. Backward 2: second hub star. Zero failures across 870 samples. [backward_pass.py]

15. **Dismounting order does not affect residual.** 0/100 instances produced different residuals from different 1-hop dismounting orders. [backward_pass.py]

16. **The O(n log n) → O(n) gap is the cost of hub ignorance.** The log factor comes from recursive splitting without knowing which half contains the valid hub. Hub location depends on global structure (full M, not local vertex properties). [CLAUDE.md; this session]

### From the crosswalk

17. **The semiring gap = the temporal reachability gap.** Graph reachability ≠ temporal reachability because temporal journeys require non-decreasing timestamps at relay vertices. This is a tropical semiring constraint (min-plus composition), not a graph connectivity constraint. ConnectedPair.lean proves graph connectivity; temporal connectivity additionally needs M[i'][j₁] ≤ M[i'][j₂]. [direction_gap.py, semiring-fanout.md]

18. **Tropical MFMC breaks on event graphs.** Naive tropicalization of sheaf max-flow/min-cut fails because tropical flows are potentials, not conserved commodities. No subtraction in the tropical semiring. [CROSSWALK.md, Finding 1]

19. **Potentials always exist but don't produce journeys.** Gradient descent finds row potentials 100% of the time (25k matrices). Column potentials exist by DAG argument. But potentials are algebraic certificates, not temporal paths. [mean_payoff_game.py]

20. **The keyframe rate is the survival parameter.** Systems that get the checkpoint frequency wrong die — too few keyframes: drift kills (Boeing 737, Kodak, Qing Dynasty). Too many: overhead kills (France 1791-1870, Mao). The temporal spanner conjecture asks: what is the minimum keyframe rate that prevents drift? Answer: 2n-3 edges in a graph with n(n-1)/2 timestamps. [timekeeping-parameter.md]

---

## Open questions (in the subject's vocabulary)

1. **Why do 2 hubs always suffice?** Exhaustive through k=15, but no proof. What property of all-distinct matrices guarantees this?

2. **What identifies the second hub when σ is a derangement?** Fixed points find the first hub. σ² fixed points partially help (~30%). No complete criterion for the second.

3. **Can the dismounting order be chosen to create a fixed point in the residual σ?** If the forward pass can steer the residual toward having a fixed point, the backward pass becomes deterministic.

4. **Is the problem in P?** Finding the minimum temporal clique spanner is open. Brute force is exponential (2^(k²-2k)), but no polynomial algorithm or NP-hardness proof exists for the single-label all-distinct case.

5. **Does the covering LP have a combinatorial dual?** The critical covering LP is integral but too loose (LP ~5 vs IP ~13 at k=4). Is there a tighter LP relaxation, or is the right dual not a covering problem at all?

6. **What is the correct notion of tropical cut?** Naive tropical flow-cut duality breaks. Krishnan's equalizer formulation avoids subtraction but hasn't been tested on event graphs.

7. **Can the backward-pass architecture be proved correct?** Forward greedy + 2 backward hub passes works empirically. Can the repair budget be bounded analytically?

---

## Dead ends (preserved for completeness)

See CLAUDE.md "Dead ends" section. 20+ approaches tried and characterized. Key structural obstructions:
- Two-column routing insufficient (semiring gap, direction_gap.py)
- 3DM reduction structurally blocked (coverage non-uniform, reduction_3dm.py)  
- Covering design model wrong (edges interact, not independent, greedy_vs_optimal.py)
- Recursive O(n) proof greedy in disguise (residual loses extremal matching structure)
- Laman/rigidity coincidental (2n-3 = Laman number, but spanners violate Laman sparsity)
- All hub heuristics fail (no single local vertex metric predicts hub success)
