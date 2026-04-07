"""
Measure rescue depth: when 2-hop relay fails, how many hops does the
multi-hop rescue need? The categorical framing predicts this is the
grading on the composition — the search cost of the division.

If rescue depth is bounded (say ≤ 4 hops = one bisection), the budget
argument extends cleanly. If it grows with k, we need a different budget.
"""

import random


def build_temporal_graph(M, k, internal_minus, internal_plus):
    """Build list of (timestamp, u, v) for the full temporal graph."""
    n = 2 * k
    edges = []

    # Cross edges
    for i in range(k):
        for j in range(k):
            t = M[i][j]
            edges.append((t, i, k + j))

    # V- internal edges
    for (i1, i2), t in internal_minus.items():
        edges.append((t, i1, i2))

    # V+ internal edges
    for (j1, j2), t in internal_plus.items():
        edges.append((t, k + j1, k + j2))

    edges.sort()
    return edges, n


def find_shortest_journey(edges, n, src, dst):
    """Find temporal journey from src to dst with fewest hops.
    Uses BFS over (vertex, arrival_time) states.
    Returns hop count or -1 if unreachable.
    """
    from collections import deque

    # Build adjacency: for each timestamp, list of (u, v) pairs
    # Journey: sequence of edges with non-decreasing timestamps
    # BFS: state = (vertex, last_time_used), minimize hops

    # Since we want min hops, do BFS layer by layer
    # State: (vertex, earliest_time_available)
    # Initial: (src, 0) at 0 hops
    # Transition: from (v, t_avail), can use any edge (t, v, w) or (t, w, v) with t >= t_avail
    #             arrive at (w, t) or (v, t) with hops+1

    # For efficiency: edges are sorted by time
    # BFS with hop count as the level

    # State: (vertex, min_time_needed)
    # We want to track: for each vertex, what's the earliest arrival time at each hop count?

    max_hops = 2 * n  # upper bound

    # best_arrival[v] = earliest arrival time reaching v (with any number of hops)
    # But we want min hops, so BFS by hop count

    # For each hop level, track: {vertex: earliest_arrival_time}
    current_level = {src: 0}  # vertex -> earliest arrival time

    for hops in range(1, max_hops + 1):
        next_level = {}

        for v, t_avail in current_level.items():
            # Try all edges usable from v at time >= t_avail
            for t, u, w in edges:
                if t < t_avail:
                    continue

                # Edge (u, w) at time t — undirected
                if u == v:
                    dest = w
                elif w == v:
                    dest = u
                else:
                    continue

                # Arrive at dest at time t
                if dest not in next_level or t < next_level[dest]:
                    next_level[dest] = t

        # Also keep states from current_level (can wait)
        # Actually no — we want to count hops, so only new transitions count

        if dst in next_level:
            return hops

        # Merge: for vertices already reachable at this level or earlier,
        # keep the earliest arrival time
        merged = {}
        for v, t in current_level.items():
            merged[v] = t
        for v, t in next_level.items():
            if v not in merged or t < merged[v]:
                merged[v] = t

        if merged == current_level:
            break  # no progress

        current_level = merged

    return -1


def build_random(k):
    """Build random biclique with internal edges."""
    t = 1
    internal_minus = {}
    for i1 in range(k):
        for i2 in range(i1 + 1, k):
            internal_minus[(i1, i2)] = t
            t += 1

    cross_ts = list(range(t, t + k * k))
    random.shuffle(cross_ts)
    M = [[0] * k for _ in range(k)]
    idx = 0
    for i in range(k):
        for j in range(k):
            M[i][j] = cross_ts[idx]
            idx += 1
    t += k * k

    internal_plus = {}
    for j1 in range(k):
        for j2 in range(j1 + 1, k):
            internal_plus[(j1, j2)] = t
            t += 1

    return M, internal_minus, internal_plus


def run():
    random.seed(42)

    print("RESCUE DEPTH ANALYSIS")
    print("=" * 60)
    print("When 2-hop relay b_j1 -> a_i -> b_j2 fails, how many hops")
    print("does the multi-hop rescue need?")
    print("=" * 60)

    for k in range(3, 7):
        samples = {3: 2000, 4: 1000, 5: 500, 6: 200}[k]

        depth_counts = {}  # hop_count -> frequency
        total_2hop_ok = 0
        total_rescued = 0
        total_fail = 0

        for s in range(samples):
            M, im, ip = build_random(k)
            edges, n = build_temporal_graph(M, k, im, ip)

            for j1 in range(k):
                for j2 in range(k):
                    if j1 == j2:
                        continue

                    # 2-hop check
                    has_2hop = any(M[i][j1] <= M[i][j2] for i in range(k))

                    if has_2hop:
                        total_2hop_ok += 1
                    else:
                        # Need multi-hop rescue — find shortest journey
                        hops = find_shortest_journey(edges, n, k + j1, k + j2)

                        if hops > 0:
                            total_rescued += 1
                            depth_counts[hops] = depth_counts.get(hops, 0) + 1
                        else:
                            total_fail += 1

            if (s + 1) % max(1, samples // 5) == 0:
                print(f"  k={k}: {s+1}/{samples}...", flush=True)

        total_pairs = k * (k - 1) * samples
        print(f"\nk={k} ({samples} samples, {total_pairs} directed pairs):")
        print(f"  2-hop OK:     {total_2hop_ok} ({100*total_2hop_ok/total_pairs:.1f}%)")
        print(f"  Rescued:      {total_rescued} ({100*total_rescued/total_pairs:.1f}%)")
        print(f"  Failed:       {total_fail}")

        if depth_counts:
            print(f"  Rescue depth distribution:")
            for hops in sorted(depth_counts):
                pct = 100 * depth_counts[hops] / total_rescued if total_rescued else 0
                print(f"    {hops} hops: {depth_counts[hops]} ({pct:.1f}%)")
            max_depth = max(depth_counts.keys())
            avg_depth = sum(h * c for h, c in depth_counts.items()) / total_rescued
            print(f"  Max rescue depth: {max_depth}")
            print(f"  Avg rescue depth: {avg_depth:.2f}")
        print()


if __name__ == "__main__":
    run()
