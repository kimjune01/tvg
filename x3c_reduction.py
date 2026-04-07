"""
Attempt to reduce Exact Cover by 3-Sets (X3C) to minimum temporal clique spanner.

Approach: given an X3C instance, construct a temporal clique whose minimum
spanner encodes the exact cover. The critical covering hypergraph of the
biclique must match the X3C structure.

Key insight from H18: minimum spanner = minimum hitting set of the critical
covering hypergraph. If we can construct temporal cliques whose covering
hypergraphs encode X3C instances, we have the reduction.
"""

import itertools
import numpy as np
from itertools import permutations


def temporal_reachable(M, edges, src_side, src_idx, dst_side, dst_idx):
    """Check if (src_side, src_idx) can reach (dst_side, dst_idx) via edges.

    sides: 'A' or 'B'. Edges are (i, j) meaning a_i -- b_j with timestamp M[i][j].
    Journey: strictly increasing timestamps along alternating A-B hops.
    """
    k = M.shape[0]
    edge_set = set(edges)

    # BFS over (side, index, last_timestamp)
    # State: (side, idx, min_arrival_time)
    # We want to find if we can reach (dst_side, dst_idx) with any arrival time

    from heapq import heappush, heappop

    # Priority queue: (timestamp, side, idx)
    pq = []
    visited = {}  # (side, idx) -> min arrival time

    if src_side == 'A':
        # Can use any edge (src_idx, j) to reach B-side
        for j in range(k):
            if (src_idx, j) in edge_set:
                t = M[src_idx, j]
                heappush(pq, (t, 'B', j))
    else:  # src_side == 'B'
        for i in range(k):
            if (i, src_idx) in edge_set:
                t = M[i, src_idx]
                heappush(pq, (t, 'A', i))

    while pq:
        t, side, idx = heappop(pq)

        if side == dst_side and idx == dst_idx:
            return True

        key = (side, idx)
        if key in visited and visited[key] <= t:
            continue
        visited[key] = t

        # Extend journey
        if side == 'A':
            for j in range(k):
                if (idx, j) in edge_set and M[idx, j] > t:
                    heappush(pq, (M[idx, j], 'B', j))
        else:  # side == 'B'
            for i in range(k):
                if (i, idx) in edge_set and M[i, idx] > t:
                    heappush(pq, (M[i, idx], 'A', i))

    return False


def all_reachable(M, edges):
    """Check all-pairs temporal reachability."""
    k = M.shape[0]
    for s_side in ['A', 'B']:
        for s in range(k):
            for d_side in ['A', 'B']:
                for d in range(k):
                    if s_side == d_side and s == d:
                        continue
                    if not temporal_reachable(M, edges, s_side, s, d_side, d):
                        return False
    return True


def critical_covering(M):
    """Compute the critical covering hypergraph.

    For each pair (u, v), find the set of edges that can serve as relay.
    An edge e is critical for pair p if removing e from some minimum spanner
    breaks p's reachability.

    Simpler: for each pair, find ALL edges that appear on SOME minimum journey.
    """
    k = M.shape[0]
    all_edges = [(i, j) for i in range(k) for j in range(k)]

    # For each pair, find which edges are essential (removing them + checking)
    pair_critical = {}

    for s_side in ['A', 'B']:
        for s in range(k):
            for d_side in ['A', 'B']:
                for d in range(k):
                    if s_side == d_side and s == d:
                        continue
                    pair = (s_side, s, d_side, d)
                    critical = set()
                    for e in all_edges:
                        remaining = [x for x in all_edges if x != e]
                        if not temporal_reachable(M, remaining, s_side, s, d_side, d):
                            critical.add(e)
                    if critical:
                        pair_critical[pair] = critical

    return pair_critical


def min_spanner_brute(M):
    """Find minimum spanner by brute force."""
    k = M.shape[0]
    all_edges = [(i, j) for i in range(k) for j in range(k)]

    for size in range(1, len(all_edges) + 1):
        for subset in itertools.combinations(all_edges, size):
            if all_reachable(M, subset):
                return set(subset), size
    return set(all_edges), len(all_edges)


def covering_hypergraph(M):
    """Compute: for each unordered pair, what edges can route them?

    More useful framing: given M⁻ ∪ M⁺ as forced edges, which additional
    edges are needed and what do they cover?
    """
    k = M.shape[0]

    # M⁻: column minima, M⁺: row maxima
    m_minus = set()
    m_plus = set()
    for j in range(k):
        min_i = np.argmin(M[:, j])
        m_minus.add((min_i, j))
    for i in range(k):
        max_j = np.argmax(M[i, :])
        m_plus.add((i, max_j))

    forced = m_minus | m_plus

    # Find pairs NOT covered by forced edges alone
    uncovered_pairs = []
    for s_side in ['A', 'B']:
        for s in range(k):
            for d_side in ['A', 'B']:
                for d in range(k):
                    if s_side == d_side and s == d:
                        continue
                    if not temporal_reachable(M, forced, s_side, s, d_side, d):
                        uncovered_pairs.append((s_side, s, d_side, d))

    if not uncovered_pairs:
        return forced, uncovered_pairs, {}

    # For each uncovered pair, which NON-FORCED edges can rescue it?
    optional_edges = [(i, j) for i in range(k) for j in range(k) if (i, j) not in forced]

    rescue_map = {}  # edge -> set of pairs it rescues
    for e in optional_edges:
        test_edges = forced | {e}
        rescued = set()
        for p in uncovered_pairs:
            if temporal_reachable(M, test_edges, *p):
                rescued.add(p)
        if rescued:
            rescue_map[e] = rescued

    return forced, uncovered_pairs, rescue_map


def analyze_instance(k, seed=None):
    """Analyze the covering structure for a random temporal clique."""
    rng = np.random.default_rng(seed)
    vals = rng.permutation(k * k)
    M = vals.reshape(k, k)

    forced, uncovered, rescue_map = covering_hypergraph(M)

    print(f"\n=== k={k}, seed={seed} ===")
    print(f"Forced edges (M⁻ ∪ M⁺): {len(forced)}")
    print(f"Uncovered pairs: {len(uncovered)}")
    print(f"Optional edges that rescue: {len(rescue_map)}")

    if rescue_map:
        # This is the Set Cover instance:
        # Universe = uncovered pairs
        # Sets = rescue_map values (each optional edge covers some pairs)
        print(f"\nCovering structure:")
        for e, pairs in sorted(rescue_map.items()):
            print(f"  Edge {e}: covers {len(pairs)} pairs")

        # What's the min cover?
        universe = set(uncovered)
        # Greedy set cover
        remaining = set(uncovered)
        cover = []
        available = dict(rescue_map)
        while remaining:
            best_e = max(available, key=lambda e: len(available[e] & remaining))
            cover.append(best_e)
            remaining -= available[best_e]
            del available[best_e]
            if not available:
                break

        if remaining:
            print(f"  Greedy cover FAILED, {len(remaining)} uncovered")
        else:
            print(f"  Greedy cover: {len(cover)} edges")

    return forced, uncovered, rescue_map


# === Try to encode a tiny X3C instance ===

def try_x3c_encoding():
    """
    Tiny X3C: Universe = {0,1,2,3,4,5},
    Sets = {{0,1,2}, {3,4,5}, {0,3,4}, {1,2,5}}
    Exact cover: {0,1,2} ∪ {3,4,5} = U (size 2)

    Can we build a temporal clique where:
    - 6 uncovered pairs ↔ universe elements
    - 4 optional edges ↔ sets
    - Each edge covers exactly its 3 pairs?
    """
    print("\n" + "="*60)
    print("SEARCHING FOR X3C ENCODING")
    print("="*60)

    # Try random matrices, check if covering structure matches X3C
    target_sets = [
        frozenset([0, 1, 2]),
        frozenset([3, 4, 5]),
        frozenset([0, 3, 4]),
        frozenset([1, 2, 5]),
    ]

    for k in range(3, 7):
        print(f"\nTrying k={k}...")
        hits = 0
        for seed in range(1000):
            rng = np.random.default_rng(seed)
            vals = rng.permutation(k * k)
            M = vals.reshape(k, k)

            forced, uncovered, rescue_map = covering_hypergraph(M)

            if len(uncovered) == 0:
                continue

            # Check if any subset of rescue edges has the X3C structure
            # i.e., 4 edges covering exactly 6 pairs in a 3-3-3-3 pattern
            coverage_sizes = sorted([len(v) for v in rescue_map.values()])

            # Count edges that cover exactly 3 pairs
            three_covers = [e for e, p in rescue_map.items() if len(p) == 3]

            if len(three_covers) >= 4 and len(uncovered) == 6:
                hits += 1
                print(f"  seed={seed}: {len(uncovered)} pairs, "
                      f"{len(three_covers)} edges cover exactly 3")
                # Check if they form an exact cover
                for combo in itertools.combinations(three_covers, 2):
                    covered = rescue_map[combo[0]] | rescue_map[combo[1]]
                    if len(covered) == 6:
                        print(f"    EXACT COVER FOUND: {combo}")

        print(f"  Total hits (6 pairs, ≥4 three-covers): {hits}/1000")


def survey_covering_structure():
    """Survey the covering structure across many random instances."""
    print("\n" + "="*60)
    print("COVERING STRUCTURE SURVEY")
    print("="*60)

    for k in [3, 4, 5]:
        pair_counts = []
        edge_counts = []
        coverage_distributions = []

        for seed in range(200):
            rng = np.random.default_rng(seed)
            vals = rng.permutation(k * k)
            M = vals.reshape(k, k)

            forced, uncovered, rescue_map = covering_hypergraph(M)
            pair_counts.append(len(uncovered))
            edge_counts.append(len(rescue_map))

            if rescue_map:
                sizes = [len(v) for v in rescue_map.values()]
                coverage_distributions.append(sizes)

        print(f"\nk={k} (200 instances):")
        print(f"  Uncovered pairs: min={min(pair_counts)}, "
              f"max={max(pair_counts)}, mean={np.mean(pair_counts):.1f}")
        print(f"  Rescue edges: min={min(edge_counts)}, "
              f"max={max(edge_counts)}, mean={np.mean(edge_counts):.1f}")

        if coverage_distributions:
            all_sizes = [s for dist in coverage_distributions for s in dist]
            from collections import Counter
            size_counts = Counter(all_sizes)
            print(f"  Coverage sizes: {dict(sorted(size_counts.items()))}")


if __name__ == "__main__":
    # First: survey what the covering structure looks like
    survey_covering_structure()

    # Then: try to find X3C-like structure
    try_x3c_encoding()
