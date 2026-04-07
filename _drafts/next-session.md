# TVG Next Session Bootstrap

Read `CLAUDE.md` first — it has the full dead-end catalog (27 hypotheses).

## Where we are (end of 2026-04-06 session)

The 2n-3 temporal spanner conjecture. 27 hypotheses tested across two sessions. The proof gap is one lemma wide.

### The construction

Star+tree: pick a hub vertex, connect it to all n-1 others (star), connect the remaining n-1 in a spanning tree (n-2 edges). Total: exactly 2n-3. Works 99.8% of instances through n=20. The 0.2% without a valid hub still have a non-star 2n-3 spanner.

### The proof tree

```
spanner ≤ 2n-3
├── dismount (Carnevale et al. 2025) ✓
├── biclique characterization (Thm 3.10) ✓
├── connected pair exists ← Lean, zero sorry ✓
├── budget arithmetic ← proved (omega) ✓
└── biclique spanner ≤ 4k-3 ← OPEN
    ├── star+tree: works 99.8% ✓
    └── non-star fallback: exists empirically, no proof
```

### Key findings from this session

1. **Sequential delegation kills the CPS log factor.** Parallel elimination overcounts (same collector missed by multiple emitters). Sequential: each collector missed exactly once (telescoping). Total O(n), not O(n log n).

2. **The conjecture is about one edge.** Lower bound = 2n-4 (packing). Upper = 2n-3. Most instances need 2n-4. Structured instances (identity, reverse permutation) hit 2n-3.

3. **Four structural antibodies kill every general technique:** asymmetry, non-locality, overcorrelation, no algebraic inverses.

4. **Minimal ≠ optimal.** Minimal spanners (no single edge removable) can exceed 2n-3 (n=7: size 13 > 11). Non-matroid signature.

5. **Landscape is mesa-shaped.** Lipschitz constant 1 (single swap → ±1 change). Flat at 2n-4 for most permutations, ridges at 2n-3 for structured ones.

6. **The hub selection problem = the non-locality problem.** You can't find the right hub without global reachability queries. Same wall as H7/H11.

## Unexplored leads (prioritized)

### 1. Two-hub construction (HIGHEST PRIORITY)
Previous session found: 2 hub pairs always suffice through k=15 on K_{k,k}. This session found star+tree works on K_n 99.8%. When one hub fails, do two hubs sharing the 2n-3 budget work? Test on K_n hub-less instances specifically.

### 2. Sequential delegation as formal proof
H26 showed telescoping gives O(n) total. The gap: the CPS biclique delegation model needs the precise timestamp compatibility accounting. H27 started this but the biclique model undercounts by ~40%. Finish the K_n accounting.

### 3. Birthday bound on hub existence
P(vertex v is a valid hub) = p(n). H27 found this is high but not 1. If p ≥ c/log(n), then P(no hub in n vertices) ≤ (1-c/log n)^n → 0. Prove p ≥ c/log n.

### 4. Dismountability Revisited (Theorem 5.2)
Claims recursively k-hop dismountable cliques admit 2n-3 spanners. Are ALL cliques recursively k-hop dismountable for bounded k? If yes, done.

### 5. Characterize the 0.2% hub-less instances
What structural property makes some K_n temporal cliques hub-less? If the property is rare enough (measure zero), an asymptotic argument suffices.

### 6. Information-theoretic tightness
Identity permutation needs exactly 2n-3. Characterize ALL tight instances. Is the set measure-zero in the space of timestamp assignments?

## Key files

- `CLAUDE.md` — full dead-end catalog, alive findings, proof tree
- `_drafts/farey-spanner.md` — session 2 research log (H1-H14)
- `Tvg/ConnectedPair.lean` — the proved lemma (zero sorry)
- `Tvg/PivotEdge.lean` — full-graph routing (corrected)
- `double_star.py`, `two_hub_exhaustive.py` — two-hub construction from session 1
- `/Users/junekim/Documents/june.kim/src/pages/reading/temporal-compression/ch-07/` — published chapter
- `/Users/junekim/Documents/june.kim/src/data/proof-manual.yml` — proof technique index

## Key papers

- Casteigts-Peters-Schoeters 2021 (arxiv:1810.00104): fireworks, O(n log n)
- Angrick et al ESA 2024 (arxiv:2402.13624): pivot-edges, SM(k), O(n) classes
- Carnevale-Casteigts-Corsini 2025 (arxiv:2502.01321): dismountability revisited
