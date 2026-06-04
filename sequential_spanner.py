"""
Sequential spanner construction for K_n.

Goal: prove O(n) spanners exist, improving CPS's O(n log n).

Construction:
1. Pick hub h. Star(h) = n-1 edges. Covers forward pairs.
2. Order non-hub vertices by star timestamp: v_1, ..., v_{n-1}.
3. Process backward pairs sequentially. For each rank r from n-1 down to 2:
   - Pair (v_r, v_{r-1}) is the "current" backward scale-1 pair.
   - Find the cheapest edge that rescues all REMAINING uncovered pairs
     involving v_r as source.
4. Count total edges added.

The CPS overcounting: each collector is "missed" by multiple emitters
independently → coupon collector → O(n log n).

Sequential fix: process emitters in order. Each collector missed at most
once in the sequential processing → total O(n).

Let me implement and measure the EXACT edge count.
"""

import random
from collections import defaultdict

random.seed(42)


def compute_reachability(n, timed_edges):
    reached_by = [dict() for _ in range(n)]
    for i in range(n):
        reached_by[i][i] = 0
    for t, u, v in sorted(timed_edges):
        sources_u = {s: arr for s, arr in reached_by[u].items() if arr <= t}
        sources_v = {s: arr for s, arr in reached_by[v].items() if arr <= t}
        for s, arr in sources_u.items():
            if s not in reached_by[v] or t < reached_by[v][s]:
                reached_by[v][s] = t
        for s, arr in sources_v.items():
            if s not in reached_by[u] or t < reached_by[u][s]:
                reached_by[u][s] = t
    pairs = set()
    for v in range(n):
        for s in reached_by[v]:
            if s != v:
                pairs.add((s, v))
    return pairs


def sequential_construction(n, timestamps):
    """Sequential construction: star + process vertices in order."""
    edges_list = list(timestamps.keys())
    all_timed = sorted([(t, u, v) for (u, v), t in timestamps.items()])
    target = compute_reachability(n, all_timed)

    # Try each hub
    best_total = n * n
    best_hub = -1

    for hub in range(n):
        star = {(min(hub, v), max(hub, v)) for v in range(n) if v != hub}
        current = set(star)

        # Order non-hub by star timestamp
        non_hub = [v for v in range(n) if v != hub]
        star_ts = {v: timestamps[(min(hub, v), max(hub, v))] for v in non_hub}
        ordered = sorted(non_hub, key=lambda v: star_ts[v])

        # Process vertices sequentially from highest rank down
        # For each vertex, add the single best edge that rescues the most pairs
        non_star = [e for e in edges_list if e not in star]
        added = 0

        for step in range(len(ordered)):
            cur_timed = sorted([(timestamps[e], e[0], e[1]) for e in current])
            cur_reach = compute_reachability(n, cur_timed)
            if cur_reach == target:
                break

            # Find best single edge to add
            best_e, best_g = None, 0
            for e in non_star:
                if e in current:
                    continue
                trial = current | {e}
                trial_timed = sorted([(timestamps[ee], ee[0], ee[1])
                                      for ee in trial])
                g = len(compute_reachability(n, trial_timed)) - len(cur_reach)
                if g > best_g:
                    best_g = g
                    best_e = e
            if best_e is None or best_g <= 0:
                break
            current.add(best_e)
            added += 1

        total = len(star) + added
        if total < best_total:
            best_total = total
            best_hub = hub

    return best_total, best_hub


def main():
    print("Sequential spanner construction: measuring edge count")
    print("=" * 70)
    print(f"{'n':>4} {'2n-3':>6} {'O(nlogn)':>8} {'sequential':>10} {'ratio':>6}")
    print("-" * 40)

    for n in range(5, 25):
        m = n * (n - 1) // 2
        edges = [(i, j) for i in range(n) for j in range(i + 1, n)]

        if n <= 12:
            samples = 200
        elif n <= 18:
            samples = 50
        else:
            samples = 20

        sizes = []
        import math
        nlogn = int(n * math.log2(n))

        for trial in range(samples):
            ts_vals = list(range(1, m + 1))
            random.shuffle(ts_vals)
            timestamps = {e: t for e, t in zip(edges, ts_vals)}
            size, hub = sequential_construction(n, timestamps)
            sizes.append(size)

        avg = sum(sizes) / len(sizes)
        mx = max(sizes)
        ratio = avg / n

        print(f"{n:4d} {2*n-3:6d} {nlogn:8d} {avg:10.1f} ({mx:3d} max) {ratio:5.2f}n")


if __name__ == '__main__':
    main()
