# Baligács 2606.05156 — verified re-implementation & verdict

**Paper:** Júlia Baligács, "Temporal Cliques Admit Linear Spanners"
(arXiv:2606.05156v1, 3 Jun 2026, Oxford). Resolves CPS Question 1: every
temporal clique admits an O(n) spanner. Theorem 2: size **7n**, polynomial time.

## What it does / how it relates to us

Same skeleton as our attack: clique→biclique reduction (§2.2), dismountability
→ extremally-matched core (§2.3, = our Carnevale/CCC25 machinery), simple star
(= our double-star, covers half the (s,t) pairs). The new piece is **extended
stars** (§4): a simple star bundled with a linear subset of its appendable
paths, with a dichotomy — either two extended stars (one at a source, one at a
target) cover a large subgraph, or some simple star admits Ω(n) appendable
paths. That is exactly the global-reachability argument our notes said was
needed and never found. Her proof is self-contained; on its own it yields 14n,
halved to 7n via CCC25.

## Our verified experiments

Faithful re-implementation, every spanner oracle-checked:
- `baligacs_construction.py` — biclique pipeline (dismount + Thm-18 recursion
  via Lemma 17 / extended stars). Source→target contract (Thm 3).
- `baligacs_clique.py` — clique via the Lemma 4 reduction (diagonal-0 biclique),
  all-to-all verified; plus greedy pruning.

### Findings

1. **The 7n bound is ~3.7× loose.** Her construction emits ~2.3n on random
   temporal cliques (n≤48), ~2.5n on the extremal SM(k) biclique.

2. **Greedy-pruned ∈ [2n-4, 2n-3] on 100% of random cliques through n=48.**
   pr.max never exceeds 2n-3; pr.min frequently hits the 2n-4 gossip floor.
   Strong evidence the 2n-3 conjecture is robust and tight (with exhaustive n≤12).

3. **Double-star is tighter but not general.** On SM(k) it gives exactly 2n-4
   (= 4k-4), beating her ~2.5n; on random bicliques its validity collapses to
   0% past k=4. Hers is universal but loose. Neither is both tight and general.

## What this changes for TVG

- The O(n) goal in the project header is **solved** (not by us).
- The tight 2n-3 constant is **still open** and now better-motivated: the only
  published upper bound (7n) is 3.7× off the floor.
- New concrete lead: the greedy prune is deterministic and hits 2n-3 every time.
  Turning "prune always succeeds" into "the extended-star spanner provably
  contains a removable set down to 2n-3" is a candidate proof of the tight bound.

## Caveats (honest)

- Clique experiments are on RANDOM temporal cliques; the conjecture's hard cases
  are adversarial. Random instances may be systematically easier. Worst-case
  coverage is only our exhaustive n≤12.
- Greedy prune gives an UPPER bound on OPT, not OPT. It shows OPT ≤ 2n-3 on each
  tested instance, not that some adversarial instance can't need more.
