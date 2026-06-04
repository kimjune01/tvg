# TVG Next Session Bootstrap

Read `CLAUDE.md` first — full dead-end catalog (40+ hypotheses across 4 sessions).

## Where we are (end of 2026-04-07, session 4)

The 2n-3 temporal spanner conjecture remains open. Four sessions, 40+ hypotheses tested. The proof gap is understood but unsolved.

### The fundamental wall

Every proof strategy that fixes a hop count fails. The adversary forces journey lengths that grow with n (or k). Proved: max journey in K_{k,k} spanner grows as ~k. Therefore:

- **Local arguments are dead.** Any proof that reasons about k-hop relays for fixed k fails.
- **The proof must reason about GLOBAL reachability.** The correct argument must capture how the entire edge set composes into journeys of unbounded length.

### What IS proved (formally)

1. Dismount reduction to biclique (Carnevale et al. 2025)
2. Biclique characterization: V⁻/V⁺ with M⁻/M⁺ permutation matchings (Thm 3.10)
3. Connected pair exists in any biclique (Lean, zero sorry)
4. Budget arithmetic: 2d + 4k-4 ≤ 2n-3 (omega)
5. M⁻ covers all A-A pairs, M⁺ covers all B-B pairs (session 4)
6. Cross-only spanning: cross edges alone span all pairs (session 2)
7. Three-timestamp median: DZ characterization and double-counting identity

### What is NOT proved (the gap)

**Biclique spanner ≤ 4k-3** for extremally matched K_{k,k}. Equivalently: 2k-3 relay edges suffice beyond the M⁻ ∪ M⁺ essential edges.

This is the SAME gap from session 1. All approaches from sessions 2-4 either:
- Reduce to this same gap (dismountability, birthday bound)
- Hit the hop-count wall (relay analysis, median floor)
- Describe but don't bound (tropical semiring, three-timestamp framework)

### Dead-end summary by approach class

**Hub-based constructions:** Star+tree works empirically (99.8%+) but can't prove hub always exists. Double star fails. Greedy tree is suboptimal (inflates failure rate 10×). Birthday bound works for random timestamps but not adversarial.

**Relay analysis (fixed hop):** 3-hop relays can be fully blocked by adversary (dead-zone world). 4-hop works for small k but hop count grows. Any fixed-hop proof is dead.

**Algebraic/semiring:** Tropical semiring describes composition correctly. Lifted Kleene star computes reachability. But no rank-nullity → no edge count bound. Algebraic rank approaches dead (no additive inverses).

**Combinatorial:** Matroid theory dead (non-matroid structure). Exchange arguments dead. Covering design wrong model. Charging-discharging gives O(n) but not 2n-3.

**Probabilistic:** Birthday bound over hub choice gives exponentially small failure for random timestamps. Doesn't handle adversarial. LLL/FKG needs independence structure that doesn't exist.

### What's still alive

1. **Double-star on extremally matched bicliques: 100% through k=9.** The construction works. The proof doesn't follow.

2. **Sequential delegation (H26): 0.865k total missed.** Within budget for all k ≤ 500. The formal bound on the missed count is the closest to a proof of any approach. Needs: rigorous bound on |∪N| in the CPS delegation model.

3. **M⁻/M⁺ completeness: proved.** A-A and B-B pairs are fully covered by the essential matchings. Only A-B relay routing remains.

4. **Three-timestamp median framework: descriptive.** Average DZ = (n-2)/3 is exact. Useful for understanding structure. Doesn't yield a bound.

5. **Best-response dynamics (H10): publishable independently.** First distributed temporal spanner construction. Not a proof of the conjecture.

### Possible next directions

1. **Formalize sequential delegation bound.** The 0.865k figure is empirical. If the union bound on missed collectors can be made rigorous with the right concentration inequality, it might close the gap for the biclique.

2. **Seek external tools.** The problem might need techniques from: discrepancy theory, Ramsey theory, topological combinatorics, or communication complexity. The structure (permutation matchings on bicliques) connects to permutation patterns, Birkhoff polytope, Latin squares.

3. **Weaken the target.** Proving O(n) spanners (not 2n-3) would still improve the literature (CPS gives O(n log n)). The sequential delegation + union bound might give this.

4. **Write up the empirical contribution.** The dead-end catalog, the three-timestamp framework, the LIVE/DZ decomposition, and the journey-length growth result are all publishable observations that advance understanding even without the proof.

## Key files

- `CLAUDE.md` — full catalog (40+ hypotheses, dead ends, alive findings)
- `biclique_extremal.py` — double-star on extremally matched bicliques (100%)
- `journey_lengths.py` — journey hop counts grow with k
- `live_floor.py` — LIVE degree floor analysis
- `deadzone_routes.py` — dead-zone routing mechanisms
- `gap_analysis.py` — dead-zone width by rank distance
- `biclique_live.py` — LIVE/DZ framework on bicliques
- `_drafts/birthday-proof-sketch.md` — birthday bound proof sketch
- `_drafts/birthday-bound.md` — birthday bound analysis

## Key papers

- Casteigts-Peters-Schoeters 2021 (arxiv:1810.00104): fireworks, O(n log n)
- Angrick et al ESA 2024 (arxiv:2402.13624): pivot-edges, SM(k), O(n) classes
- Carnevale-Casteigts-Corsini 2025 (arxiv:2502.01321): dismountability revisited
