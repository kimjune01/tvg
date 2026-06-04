# Birthday Bound on Hub Existence

## The argument

**Claim.** For every temporal clique K_n with distinct timestamps, at least one vertex h admits a star+tree spanner of size exactly 2n-3.

**Proof strategy.** Show that the probability a random vertex h is a valid hub is bounded below by a constant p > 0 that increases with n. With n candidates, the probability that none works is at most (1-p)^n → 0.

### Definitions

- **Star(h)**: the n-1 edges incident to h. Always included.
- **Backward pairs B(h)**: ordered pairs (a,b) with a,b ≠ h where t(a,h) > t(h,b). The star alone cannot route these. |B(h)| = C(n-1,2) = (n-1)(n-2)/2 for every h (tautology from distinct timestamps).
- **Tree budget**: n-2 non-star edges.
- **Valid hub**: ∃ set of n-2 non-star edges such that star ∪ tree covers all n(n-1) directed pairs.

### Key empirical quantities

| n | P(random h valid) | Best hub ≤ budget | Birthday P(none) |
|---|---|---|---|
| 6 | 63.8% | 99.7% | 0.23% |
| 8 | 64.5% | 99.9% | 0.026% |
| 10 | 68.5% | 100% | 0.001% |
| 12 | 74.3% | 100% | ~0 |
| 15 | 82.3% | 100% | ~0 |

P(random h valid) measured via interactive greedy — an upper bound on true minimum cover. Yet greedy is tight at K_12+ (best hub = exactly n-2 tree edges, no excess).

### Why P increases with n

**Edge interactions (synergy).** Adding tree edge e to star ∪ {existing tree edges} rescues more backward pairs than e would rescue alone, because multi-hop journeys chain through existing edges. Synergy is positive for ~15-25% of edge pairs.

**Average load.** Each tree edge must cover B(h)/budget = (n-1)/2 backward pairs on average. Mean rescue per edge grows with n (from 1.8 at K_6 to 4.5 at K_20), keeping pace with the load. Interactions amplify this: the k-th edge rescues more than the 1st because it chains through the previous k-1.

**Budget tightness.** At K_12+, greedy cover = exactly n-2 for every hub that works. The construction is tight but feasible. The surplus capacity (mean rescue / load) converges from above.

### Formalization gap

The empirical P(random h valid) ≥ 0.64 applies to random timestamps. For a worst-case proof, need one of:
1. **Adversarial P ≥ c:** prove that even adversarially chosen timestamps leave P ≥ c > 0
2. **Hub existence for large n:** prove that for n ≥ n₀, every K_n has a valid hub (not just with high probability)
3. **Hub-less backup:** prove that hub-less instances also have ≤ 2n-3 spanners (confirmed for n ≤ 12)

Option (1) would close the conjecture via birthday bound + finite verification.
Option (2) would close it directly for n ≥ n₀.
Option (3) would close it for all n if the non-star spanner proof is constructive.

### Structural observations

- Hub-less K_6 instances: degree [2,2,3,3,3,3], size 2n-4, cycle rank 3. Mesh topology, no dominant vertex. Every vertex at 50% forward (tautology).
- The interactive greedy always terminates in exactly n-2 steps when it succeeds — no surplus edges, no deficit. This suggests the budget 2n-3 is not arbitrary but matches the structural dimensionality of the problem.
- The forced-edge analysis (independent rescue) overcounts by 2-3× at large n because it ignores journey chaining. Synergy is load-bearing.
