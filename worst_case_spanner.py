"""
Worst-case temporal spanner computation on temporal cliques.

For each K_n, sample random single-label timestamp assignments,
compute the minimum spanner via greedy edge removal, and report
the worst-case labeling found.

Optimized for larger n (up to ~20) using numpy-free bitset reachability.
"""

import time
import random
import math
from itertools import permutations, combinations


def make_edges(n: int) -> list[tuple[int, int]]:
    return [(i, j) for i in range(n) for j in range(i + 1, n)]


def compute_reachability_bits(n: int, timed_edges: list[tuple[int, int, int]]) -> list[int]:
    """
    Compute reachability using bitmasks. Returns list of n bitmasks,
    where reach[u] has bit v set if u can reach v.

    timed_edges: list of (timestamp, u, v) sorted by timestamp.
    """
    # reach[u] = bitmask of vertices reachable from u
    reach = [1 << i for i in range(n)]

    # Process edges in timestamp order. Repeat until stable.
    changed = True
    while changed:
        changed = False
        for t, u, v in timed_edges:
            # u and v are connected at time t.
            # Any vertex that can reach u by time <= t can now reach everything v can reach at time >= t.
            # But we need time-awareness. Bitmask approach loses time info.
            pass

    # Bitmask without time doesn't work. Fall back to time-aware approach.
    # For each source, track (vertex -> earliest arrival time)
    reach_pairs = [0] * n  # bitmask per source

    for src in range(n):
        # earliest[v] = earliest time we can be at v (and use edges at time >= earliest[v])
        earliest = [None] * n
        earliest[src] = 0  # can use any edge

        changed = True
        while changed:
            changed = False
            for t, u, v in timed_edges:
                if earliest[u] is not None and t >= earliest[u]:
                    if earliest[v] is None or t < earliest[v]:
                        earliest[v] = t
                        changed = True
                if earliest[v] is not None and t >= earliest[v]:
                    if earliest[u] is None or t < earliest[u]:
                        earliest[u] = t
                        changed = True

        bits = 0
        for v in range(n):
            if v != src and earliest[v] is not None:
                bits |= (1 << v)
        reach_pairs[src] = bits

    return reach_pairs


def compute_reachability_fast(n: int, timed_edges: list[tuple[int, int, int]]) -> list[int]:
    """
    Faster reachability: process edges in time order, propagate reachability.

    Key insight: process edges sorted by timestamp. For each edge (t, u, v),
    merge the "reachable-from" sets: anything that reached u or v by time <= t
    can now reach both u and v.

    We track: for each vertex, the set of sources that can reach it,
    along with the arrival time from each source.
    """
    # reached_by[v] = dict: source -> earliest arrival time at v
    reached_by = [dict() for _ in range(n)]
    for i in range(n):
        reached_by[i][i] = 0

    # Process edges in timestamp order
    for t, u, v in timed_edges:
        # Sources that can reach u by time t
        sources_u = {s: arr for s, arr in reached_by[u].items() if arr <= t}
        # Sources that can reach v by time t
        sources_v = {s: arr for s, arr in reached_by[v].items() if arr <= t}

        # Propagate: sources reaching u can now reach v, and vice versa
        for s, arr in sources_u.items():
            if s not in reached_by[v] or t < reached_by[v][s]:
                reached_by[v][s] = t
        for s, arr in sources_v.items():
            if s not in reached_by[u] or t < reached_by[u][s]:
                reached_by[u][s] = t

    # But this single-pass approach misses multi-hop propagation within the same timestamp.
    # Since all timestamps are distinct (single-label), each edge fires once.
    # Multi-hop: edge at t=3 connects a-b, edge at t=5 connects b-c.
    # After processing t=3: b is reached from a. After processing t=5: c is reached from a (via b).
    # Single pass in timestamp order handles this correctly!

    # Convert to bitmasks
    reach = [0] * n
    for v in range(n):
        for s in reached_by[v]:
            if s != v:
                reach[s] |= (1 << v)

    return reach


def reachability_equal(r1: list[int], r2: list[int]) -> bool:
    return r1 == r2


def greedy_minimum_spanner(n: int, edges: list[tuple[int, int]], timestamps: list[int]) -> int:
    """
    Greedy edge removal: try removing each edge (most timestamped first),
    keep it only if removal breaks reachability.
    """
    m = len(edges)
    timed = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in range(m)])
    target = compute_reachability_fast(n, timed)

    included = list(range(m))

    # Try removing edges, highest timestamp first (heuristic: late edges more likely redundant)
    order = sorted(range(m), key=lambda i: -timestamps[i])

    for idx in order:
        candidate = [i for i in included if i != idx]
        sub_timed = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in candidate])
        reach = compute_reachability_fast(n, sub_timed)
        if reachability_equal(reach, target):
            included = candidate

    return len(included)


def exact_minimum_spanner(n: int, edges: list[tuple[int, int]], timestamps: list[int]) -> int:
    """
    Exact minimum spanner via pruning search.
    Start from greedy solution, then try to find smaller subsets.
    """
    m = len(edges)
    timed = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in range(m)])
    target = compute_reachability_fast(n, timed)

    # Start with greedy upper bound
    greedy_size = greedy_minimum_spanner(n, edges, timestamps)

    # For small m, try exact enumeration below greedy size
    if m <= 15:
        for size in range(n - 1, greedy_size):
            for subset in combinations(range(m), size):
                sub_timed = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in subset])
                reach = compute_reachability_fast(n, sub_timed)
                if reachability_equal(reach, target):
                    return size

    return greedy_size


def adversarial_search(n: int, edges: list[tuple[int, int]], num_samples: int = 10000) -> tuple[int, list[int]]:
    """
    Search for worst-case labeling via random sampling + local search.
    """
    m = len(edges)
    worst_size = 0
    worst_labeling = None
    best_size = m
    total_size = 0

    start = time.time()

    for i in range(num_samples):
        timestamps = list(range(1, m + 1))
        random.shuffle(timestamps)

        size = greedy_minimum_spanner(n, edges, timestamps)

        total_size += size
        if size > worst_size:
            worst_size = size
            worst_labeling = timestamps[:]

        if size < best_size:
            best_size = size

        if (i + 1) % max(1, num_samples // 10) == 0:
            elapsed = time.time() - start
            print(f"  {i+1}/{num_samples}: worst={worst_size}, best={best_size}, "
                  f"avg={total_size/(i+1):.1f} ({elapsed:.1f}s)")

    return worst_size, best_size, total_size / num_samples, worst_labeling


def also_try_shifted_matching(n: int, edges: list[tuple[int, int]]):
    """Try the shifted matching graph construction (known hard case)."""
    if n % 2 != 0:
        return None

    half = n // 2
    # SM(half): A = {0..half-1}, B = {half..n-1}
    # Edge (a_i, b_j) gets label (j - i) mod half
    # Map to our edge indexing
    m = len(edges)
    edge_to_idx = {e: i for i, e in enumerate(edges)}
    timestamps = [0] * m

    t = 1
    for label_val in range(half):
        for i in range(half):
            j = (i + label_val) % half
            a, b = i, half + j
            e = (min(a, b), max(a, b))
            if e in edge_to_idx:
                timestamps[edge_to_idx[e]] = t
                t += 1

    # Fill remaining edges (within A, within B) with remaining timestamps
    for idx in range(m):
        if timestamps[idx] == 0:
            timestamps[idx] = t
            t += 1

    size = greedy_minimum_spanner(n, edges, timestamps)
    return size


def main():
    print("Worst-case temporal spanner analysis (optimized)")
    print("=" * 60)

    results = {}

    configs = [
        (4,  10000, True),
        (5,  10000, True),
        (6,  10000, False),
        (7,  5000, False),
        (8,  3000, False),
        (9,  2000, False),
        (10, 1000, False),
        (12, 500, False),
        (15, 200, False),
        (20, 100, False),
    ]

    for n, samples, exact in configs:
        edges = make_edges(n)
        m = len(edges)
        print(f"\nK_{n}: {n} vertices, {m} edges")
        print("-" * 40)

        worst, best, avg, labeling = adversarial_search(n, edges, samples)

        # Also try shifted matching for even n
        sm_size = also_try_shifted_matching(n, edges)
        if sm_size is not None:
            print(f"  Shifted matching: {sm_size} edges")
            if sm_size > worst:
                worst = sm_size

        log2n = math.log2(n) if n > 1 else 1
        results[n] = (worst, best, avg)

        print(f"  Worst: {worst} (ratio={worst/n:.2f}, /(n·lg n)={worst/(n*log2n):.3f})")
        print(f"  Best:  {best} (ratio={best/n:.2f})")
        print(f"  Avg:   {avg:.1f} (ratio={avg/n:.2f})")

    print("\n" + "=" * 60)
    print(f"{'n':>4} {'worst':>6} {'best':>6} {'avg':>7} {'w/n':>6} {'w/(n·lgn)':>10} {'2(n-1)':>7}")
    print("-" * 55)
    for n, (worst, best, avg) in sorted(results.items()):
        log2n = math.log2(n) if n > 1 else 1
        print(f"{n:>4} {worst:>6} {best:>6} {avg:>7.1f} {worst/n:>6.2f} {worst/(n*log2n):>10.3f} {2*(n-1):>7}")


if __name__ == "__main__":
    main()
