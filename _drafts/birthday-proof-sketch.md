# Birthday Bound: Proof Sketch

## Setup

Fix temporal K_n with distinct timestamps σ. Fix hub h. Let T_v = σ({h,v}) for non-hub v.

Order non-hub vertices: T_{v_1} < T_{v_2} < ... < T_{v_{n-1}}. Write rank(v) = position in this order.

**Forward pair** (v_i, v_j) with i < j: routes via v_i → h → v_j at times (T_i, T_j). Works since T_i < T_j.

**Backward pair** (v_i, v_j) with i > j: needs rescue. |B(h)| = C(n-1,2).

## Rescue routes

For backward pair (v_i, v_j) with i > j (source has HIGH star time, target has LOW):

**Route A (early relay):** v_i → v_a (tree) → h (star) → v_j (star).
Timestamps: τ_{ia} ≤ T_a ≤ T_j.
Constraint: a ≤ j (so T_a ≤ T_j) AND τ_{ia} ≤ T_a.
Available relays: {v_1, ..., v_j} — there are j of them.

**Route B (late relay):** v_i → h (star) → v_a (star) → v_j (tree).
Timestamps: T_i ≤ T_a and τ_{aj} ≥ T_a.
Constraint: a ≥ i (so T_a ≥ T_i) AND τ_{aj} ≥ T_a.
Available relays: {v_i, v_{i+1}, ..., v_{n-1}} — there are n-1-i+1 of them.

Wait: a ≥ i AND a ≠ i, so {v_{i+1}, ..., v_{n-1}} — there are n-1-i of them.

**Route C (two-tree bridge):** v_i → v_a (tree) → v_b (tree) → h (star) → v_j (star).
Timestamps: τ_{ia} ≤ τ_{ab} ≤ T_b ≤ T_j.
Constraint: b ≤ j AND τ_{ia} ≤ τ_{ab} ≤ T_b.

**Route D (star-tree-star):** v_i → h → v_a → v_j through tree path.
Uses star edges to get to h, then tree edges to get from h's neighborhood to target.
But T_i ≤ T_a required (so a ≥ i), then need tree path from v_a to v_j with non-decreasing timestamps ≥ T_a. Since a ≥ i > j, this is routing "downward" in star rank purely through tree edges.

## Scale decomposition

Define scale of backward pair (v_i, v_j) as k = i - j.

| Scale k | Count | Route A relays | Route B relays |
|---------|-------|---------------|---------------|
| 1       | n-2   | j ≥ 1         | n-1-i ≥ 0    |
| k       | n-1-k | j             | n-1-i         |
| n-2     | 1     | 1             | 0             |

### Relay counts by scale

For a pair at scale k with target rank j:
- Route A: j relays (vertices with rank < j, wrong: vertices with rank ≤ j)
- Route B: n-1-i = n-1-(j+k) relays

Sum of relay options = j + (n-1-j-k) = n-1-k.

**Key: total relay count = n-1-k, depends only on scale.** At scale 1: n-2 relays. At scale n-2: 1 relay.

### The adversary's dilemma

For each backward pair, the adversary must block all n-1-k relays. To block a Route A relay a ≤ j: need τ_{ia} > T_a (tree edge too late). To block Route B relay a ≥ i: need τ_{aj} < T_a (tree edge too early).

The adversary controls the full timestamp assignment. But each non-star edge {u,w} has exactly ONE timestamp τ_{uw}. This timestamp either blocks or doesn't block each route it participates in.

**Blocking cost:** To block all n-1-k relays for one scale-k pair, the adversary needs n-1-k specific timestamp inequalities to all go the wrong way.

**Total blocking demand:** Sum over all backward pairs of (relays to block) = Σ_{k=1}^{n-2} (n-1-k) × (count at scale k) = Σ_{k=1}^{n-2} (n-1-k)(n-1-k) = Σ_{m=1}^{n-2} m² ≈ n³/3.

But each tree-edge timestamp controls at most O(n) blocking events (it participates in routes for O(n) backward pairs across different hubs/scales). Total supply of "blocking power" = C(n-1,2) non-star edges = O(n²).

**Demand O(n³) > Supply O(n²) for large n.** The adversary cannot simultaneously block all routes.

## The continuous sieve

In the continuous limit (timestamps ∈ [0,1]):

Star timestamps partition [0,1] into n-2 intervals. Each interval has width ~1/n. A backward pair at scale k spans k intervals, total width ~k/n.

A tree edge {v_i, v_a} with timestamp τ acts as a bridge if τ falls in the right interval. The "right interval" has width ~1/n. With C(n-1,2) ≈ n²/2 tree edges available, and each having an independent timestamp:

P(no tree edge bridges a given gap of width 1/n) ≈ (1 - 1/n)^{n²/2} ≈ e^{-n/2} → 0.

Even the narrowest gap (scale 1) has exponentially many bridges.

## The multi-scale argument

The Weierstrass analogy: the adversary makes σ jagged at every scale. But:

1. **Large-scale pairs (k ≫ 1):** n-1-k relays. P(all blocked) ≤ p^{n-1-k} for some p < 1. Exponentially easy.

2. **Small-scale pairs (k = O(1)):** j relays via Route A, n-1-i via Route B. At least one direction has ≥ (n-1-k)/2 relays. Still exponentially many.

3. **Scale-1 pairs:** These dominate the budget. There are n-2 of them. Each needs ~1 tree edge. Budget = n-2. Tight match.

4. **Synergy:** Tree edges chosen for scale-1 pairs also rescue larger-scale pairs via journey chaining. The "free rider" effect means larger scales don't consume additional budget.

## What remains to prove

1. **Each backward pair has ≥ 1 compatible relay** (with high probability over hub choice, or worst-case for all timestamp assignments)

2. **The rescue sets can be simultaneously satisfied with n-2 tree edges** (the set cover fits within budget)

3. **Hub selection:** at least one of n vertices is a valid hub

Item (2) is the hardest. The data shows interactive greedy = exactly n-2 for n ≥ 12. The set cover fits because:
- Scale-1 pairs each need ~1 dedicated tree edge (n-2 total)
- Larger-scale pairs chain through these edges (synergy, 0 additional budget)
- The tree edges for scale-1 form a matching-like structure on the non-hub vertices

Item (3) follows from (1)+(2) via birthday bound: if P(h valid) ≥ p > 0, then P(no hub) ≤ (1-p)^n → 0.

## Conjectured lemma

**Lemma (Scale-1 rescue).** For any temporal K_n and any hub h, every scale-1 backward pair (v_{j+1}, v_j) has at least one compatible Route A or Route B relay among the non-star edges.

If true, this gives: every backward pair (i,j) with i = j+1 can be rescued by one tree edge. These n-2 pairs need n-2 tree edges (possibly shared). The tree edges that rescue scale-1 pairs also rescue larger-scale pairs by chaining.

**This lemma is the load-bearing claim.** It converts the continuous sieve intuition into a discrete statement. Scale-1 pairs have minimum relay count (n-2), but the relay conditions are weakest (small timestamp gaps to bridge).
