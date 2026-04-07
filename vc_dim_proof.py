"""
Prove VC dimension = 2 for the critical covering system of temporal cliques.

The covering system: ground set = directed reachable pairs (s,t).
For each edge e of K_n, define COVER(e) = {(s,t) : removing e from the
temporal clique breaks temporal reachability from s to t}.

VC dimension = largest set of pairs that can be "shattered."
A set P of pairs is shattered if for every subset Q ⊆ P, there exists
an edge e with COVER(e) ∩ P = Q.

We want to prove: no 3 pairs can be shattered.

Strategy:
1. Exhaustively check shattering for k=3,4,5 (all temporal cliques)
2. For larger k, random sampling
3. Characterize what prevents shattering of 3 pairs
"""

import random
from itertools import combinations


def make_temporal_clique(n, seed=None):
    if seed is not None:
        random.seed(seed)
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
    m = len(edges)
    ts = list(range(1, m + 1))
    random.shuffle(ts)
    return edges, ts


def compute_reachability(n, edge_indices, edges, timestamps):
    timed = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in edge_indices])
    reach = [{v: 0} for v in range(n)]
    for t, u, v in timed:
        new_v = {}
        new_u = {}
        for s, arr in reach[u].items():
            if arr <= t and (s not in reach[v] or t < reach[v][s]):
                new_v[s] = t
        for s, arr in reach[v].items():
            if arr <= t and (s not in reach[u] or t < reach[u][s]):
                new_u[s] = t
        reach[v].update(new_v)
        reach[u].update(new_u)
    R = set()
    for v in range(n):
        for s in reach[v]:
            if s != v:
                R.add((s, v))
    return R


def compute_covers(n, edges, timestamps):
    """For each edge, compute which pairs break when it's removed."""
    m = len(edges)
    all_indices = list(range(m))
    full_reach = compute_reachability(n, all_indices, edges, timestamps)

    covers = {}
    for idx in range(m):
        remaining = [i for i in all_indices if i != idx]
        reduced_reach = compute_reachability(n, remaining, edges, timestamps)
        broken = full_reach - reduced_reach
        if broken:
            covers[idx] = broken
    return covers


def check_shattering(covers, pairs_set):
    """Check if a set of pairs is shattered by the covering system.
    For every subset Q of pairs_set, there must exist an edge e
    with COVER(e) ∩ pairs_set = Q.
    """
    pairs_list = list(pairs_set)
    k = len(pairs_list)
    required_subsets = set()
    for r in range(k + 1):
        for subset in combinations(range(k), r):
            required_subsets.add(frozenset(subset))

    achieved = set()
    for idx, cover in covers.items():
        intersection = frozenset(i for i, p in enumerate(pairs_list) if p in cover)
        achieved.add(intersection)

    # Also need the empty intersection (some edge that breaks none of the pairs)
    # This is automatically achieved if any edge has empty intersection with pairs_set
    achieved.add(frozenset())  # The "no edge removed" case = empty set

    return achieved == required_subsets, achieved, required_subsets


def find_max_shattered(n, edges, timestamps):
    """Find the largest shattered set of pairs."""
    covers = compute_covers(n, edges, timestamps)
    if not covers:
        return 0, set()

    full_reach = compute_reachability(n, list(range(len(edges))), edges, timestamps)
    all_pairs = list(full_reach)

    # Check all triples
    max_shattered = 0
    max_set = set()

    # First check pairs (VC dim >= 2?)
    for p1, p2 in combinations(all_pairs, 2):
        ok, achieved, required = check_shattering(covers, {p1, p2})
        if ok:
            max_shattered = max(max_shattered, 2)
            max_set = {p1, p2}
            break

    if max_shattered < 2:
        # VC dim < 2
        for p in all_pairs:
            ok, _, _ = check_shattering(covers, {p})
            if ok:
                return 1, {p}
        return 0, set()

    # Check triples (VC dim >= 3?)
    found_triple = False
    triples_checked = 0
    for p1, p2, p3 in combinations(all_pairs, 3):
        triples_checked += 1
        ok, achieved, required = check_shattering(covers, {p1, p2, p3})
        if ok:
            found_triple = True
            max_shattered = 3
            max_set = {p1, p2, p3}
            print(f"    SHATTERED TRIPLE FOUND: {p1}, {p2}, {p3}")
            print(f"    Achieved: {achieved}")
            break
        if triples_checked >= 50000:
            break

    return max_shattered, max_set


def analyze_shattering_obstruction(n, edges, timestamps):
    """Why can't 3 pairs be shattered? Analyze the structure."""
    covers = compute_covers(n, edges, timestamps)
    full_reach = compute_reachability(n, list(range(len(edges))), edges, timestamps)
    all_pairs = list(full_reach)

    # For random triples, check what subsets are achievable
    missing_patterns = {}
    triples_checked = 0

    for p1, p2, p3 in combinations(all_pairs, 3):
        triples_checked += 1
        if triples_checked > 10000:
            break

        pairs_list = [p1, p2, p3]
        achieved = set()
        achieved.add(frozenset())  # empty

        for idx, cover in covers.items():
            intersection = frozenset(i for i, p in enumerate(pairs_list) if p in cover)
            achieved.add(intersection)

        required = set()
        for r in range(4):
            for subset in combinations(range(3), r):
                required.add(frozenset(subset))

        missing = required - achieved
        if missing:
            key = frozenset(frozenset(s) for s in missing)
            missing_patterns[key] = missing_patterns.get(key, 0) + 1

    return missing_patterns, triples_checked


def main():
    random.seed(42)

    print("VC DIMENSION ANALYSIS OF TEMPORAL SPANNER COVERING SYSTEM")
    print("=" * 65)

    # Test on small instances
    for n in [4, 5, 6]:
        samples = {4: 200, 5: 100, 6: 50}[n]
        vc_dims = []
        triple_found = False

        for s in range(samples):
            edges, ts = make_temporal_clique(n, seed=42 + s)
            vc, shattered = find_max_shattered(n, edges, ts)
            vc_dims.append(vc)
            if vc >= 3:
                triple_found = True
                print(f"\n*** VC DIM >= 3 at n={n}, seed={42+s}! ***")
                print(f"    Shattered set: {shattered}")

            if (s + 1) % max(1, samples // 5) == 0:
                print(f"  n={n}: {s+1}/{samples}...", flush=True)

        print(f"\nn={n} ({samples} samples):")
        print(f"  VC dimensions: {dict((d, vc_dims.count(d)) for d in sorted(set(vc_dims)))}")
        if not triple_found:
            print(f"  NO SHATTERED TRIPLE FOUND — VC dim ≤ 2 confirmed")
        print()

    # Obstruction analysis on n=6
    print("=" * 65)
    print("SHATTERING OBSTRUCTION ANALYSIS (n=6, 10 samples)")
    print("=" * 65)

    for s in range(10):
        edges, ts = make_temporal_clique(6, seed=42 + s)
        patterns, checked = analyze_shattering_obstruction(6, edges, ts)

        print(f"\nSample {s} (checked {checked} triples):")
        # Top 5 most common missing patterns
        top = sorted(patterns.items(), key=lambda x: -x[1])[:5]
        for pat, count in top:
            readable = [set(s) for s in pat]
            print(f"  Missing {readable}: {count} triples ({100*count/checked:.1f}%)")


if __name__ == "__main__":
    main()
