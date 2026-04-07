# TVG: NP-Hardness Mapping Session

Read `CLAUDE.md`, `_drafts/on-proof-sketch.md`, and `_drafts/next-session.md` first.

## Goal

Map our O(n) vs O(n log n) barrier to the known NP-hardness of temporal
clique spanners (Axiotis & Fotakis 2016). Write a conclusion connecting:

1. Our structural findings (non-domination, PivotEdge, cross-only spanning)
2. The known NP-hardness (minimum temporal clique spanner is NP-hard)
3. The O(n log n) constructive ceiling (Casteigts 2021)
4. The 2n-3 existential conjecture

## The connection we identified

The barrier between O(n log n) and O(n) has P vs NP structure:
- **Verification is easy:** given a set of O(n) edges, checking temporal
  reachability for all pairs is O(n²) (polynomial)
- **Construction is hard:** finding WHICH O(n) edges to pick requires
  global information (hub placement = optimal I-frame placement)
- **Greedy fails:** per-diagonal greedy, per-hub greedy both suboptimal
- **Post hoc vs ad hoc:** we can verify the hub works after the fact,
  but can't certify it will work before placing it

## What to establish

1. **Fetch Axiotis & Fotakis 2016.** Get the exact reduction. They reduce
   from Hamiltonian Path. Understand: does the NP-hardness apply to the
   DECISION problem (does a cn-edge spanner exist?) or just OPTIMIZATION
   (find the minimum)?

2. **Map our hub detection to their hard instances.** Our barrier:
   choosing the right hub pair (h, c) for the double star construction.
   Their hard instances: temporal cliques where the minimum spanner
   corresponds to a Hamiltonian path. Are these the same instances?

3. **Set Cover connection.** Our covering design formulation (H18-H19 in
   semiring-fanout.md) maps temporal spanner to set cover. Set cover has
   (1-ε)ln n inapproximability. Does this explain the log factor gap?

4. **Write the conclusion.** The three-part result:
   - Structural: non-domination + PivotEdge give the O(n) existence
     argument modulo hub certification (proved in Lean)
   - Computational: hub certification is NP-hard (Axiotis-Fotakis),
     explaining why constructive approaches plateau at O(n log n)
   - Conjectural: 2n-3 is the tight constant, but achieving it
     requires solving the optimization, not just the existence

## Key references

- Axiotis & Fotakis 2016: NP-hardness of min temporal clique spanner
- Akrida, Mertzios, Spirakis, Zamaraev 2020: NP-hardness general case
- Casteigts-Peters-Schoeters 2021: O(n log n) constructive bound
- Carnevale-Casteigts-Corsini 2025: dismountability, 2n-3 for easy case
- Angrick et al ESA 2024: pivot-edges, reverted edges, SM(k)

## Key files from this session

- `Tvg/PivotEdge.lean` — pivot > n/2 (zero sorry)
- `Tvg/NonDomination.lean` — row/col non-domination (zero sorry)
- `_drafts/on-proof-sketch.md` — O(n) proof sketch (gap identified)
- `double_star.py` — construction achieving 2n-4 for SM(k)
- `two_hub_exhaustive.py` — 2 hubs suffice through k=15
- `cross_only_spanner.py` — internal edges redundant
- `worklog/WORK_LOG.md` — full session log
