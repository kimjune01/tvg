# TVG Next Session Bootstrap

Read `CLAUDE.md` and `_drafts/semiring-fanout.md` first.

## Where we left off (2026-04-05)

### Proved
- **Non-domination theorem**: M⁻ permutation → no row dominates another.
  M⁺ → no column dominates. Cross edges alone span all pairs (A-A, B-B, A-B)
  via 2-hop relay. This is the B-frame mechanism. (domination_proof.py)
- **Cross-only spanning**: 100% across 670 random bicliques + all SM(k) k=3..8.
  Internal edges are redundant. (cross_only_spanner.py)
- **PivotEdge.lean corrected**: full-graph routing, NOT Angrick's biclique-only
  pivot-edge. SM(k) has trivial pivot-sets under Angrick (Lemma 6.4).

### Double star construction (empirical, not proved)
- M⁻ ∪ M⁺ ∪ star(row h) ∪ star(col c), with m⁺(h) = c.
- Gives exactly 2n-4 edges for ALL SM(k) k=3..11 (SM(8)=29 was a search artifact).
- 2 hub pairs suffice exhaustively through k=15. Zero failures.
- Total ≤ 6k = 3n = O(n). (double_star.py, two_hub_exhaustive.py)

### The gap: O(n) vs O(n log n)
The proof reduces to one lemma: **the failure set of the double star
construction is O(k), not O(k log k).**

IVT argument: the minimum spanner cost lives between hub-only (4k, works
~60% of the time) and all-I-frames (k², always works). Both endpoints
exist. But IVT doesn't locate the minimum — it could be O(n) or O(n log n).

The codec framing: each hub star is a GOP. Failures are chain breaks.
I-frame patches fix breaks. The question is whether break density is O(1)
per vertex or O(log k) per vertex.

Empirically: break density is O(1). 2 hub pairs always suffice.
Analytically: not proved.

### What to try next

1. **Concordant pair bound.** For 2 hub columns c₁, c₂: how many ordered
   pairs (i, i') have M[i][c₁] > M[i'][c₁] AND M[i][c₂] > M[i'][c₂]?
   (Kendall tau concordance.) If this is O(k) for well-chosen columns,
   the multi-hop rescue through hub rows closes the gap.

2. **Multi-hop rescue analysis.** When 2-hop through hub columns fails
   (concordant pair), the 4-hop a_i → b_{M⁻} → a_h → b_c → a_{i'} might
   rescue. Prove this always works, or characterize when it fails.

3. **Probabilistic argument.** Random hub columns have ~k(k-1)/4 concordant
   pairs (expected). Is there always a pair of columns with O(k) concordant
   pairs? Lovász Local Lemma or second moment method.

4. **Direct Lean formalization.** The non-domination theorem is 2 lines.
   The double star construction is explicit. Formalize the construction
   and reduce to the concordant pair lemma.

## Key files

- `Tvg/PivotEdge.lean` — full-graph routing lemma (corrected)
- `domination_proof.py` — non-domination verification + proof sketch
- `cross_only_spanner.py` — cross-only spanning verification
- `double_star.py` — double star construction on SM(k)
- `double_star_general.py` — double star on random bicliques
- `two_hub_exhaustive.py` — 2 hub pairs exhaustive search
- `two_hub_proof.py` — hub count scaling analysis
- `optimal_structure.py` — optimal spanner diagonal structure
- `joint_diagonal.py` — joint diagonal optimization
- `_drafts/semiring-fanout.md` — full research log (22 hypotheses, 13 dead)

## Key papers

- Carnevale-Casteigts-Corsini 2025: arxiv:2502.01321 (dismountability)
- Angrick et al ESA 2024: arxiv:2402.13624 (pivot-edge, reverted edges, SM(k))
- Casteigts-Peters-Schoeters 2021: O(n log n) bound
