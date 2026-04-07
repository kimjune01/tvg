"""
Adversarial rescue depth: what happens when the adversary controls
ALL timestamps (internal + cross) from a single permutation?

The previous experiment always placed V+ internals last, making them
trivially reachable. An adversary can interleave internal and cross
edge timestamps arbitrarily.

Also: construct worst-case matrices that maximize 2-hop failures
and test whether multi-hop rescues still work and at what depth.
"""

import random
from itertools import permutations


def build_temporal_graph_general(k, all_edges, timestamps):
    """Build temporal graph from arbitrary edge-timestamp assignment.
    all_edges: list of (u, v) pairs (0-indexed, n = 2k vertices)
    timestamps: list of timestamps, same length as all_edges
    Returns sorted list of (timestamp, u, v).
    """
    timed = [(t, u, v) for (u, v), t in zip(all_edges, timestamps)]
    timed.sort()
    return timed


def find_shortest_journey(timed_edges, n, src, dst):
    """Find temporal journey with fewest hops (BFS by hop count)."""
    if src == dst:
        return 0

    # BFS: current_level = {vertex: earliest_arrival_time}
    current_level = {src: 0}

    for hops in range(1, 2 * n + 1):
        next_arrivals = {}

        for v, t_avail in current_level.items():
            for t, u, w in timed_edges:
                if t < t_avail:
                    continue
                if u == v:
                    dest = w
                elif w == v:
                    dest = u
                else:
                    continue

                if dest not in next_arrivals or t < next_arrivals[dest]:
                    next_arrivals[dest] = t

        if dst in next_arrivals:
            return hops

        # Merge
        merged = dict(current_level)
        for v, t in next_arrivals.items():
            if v not in merged or t < merged[v]:
                merged[v] = t

        if merged == current_level:
            break
        current_level = merged

    return -1


def enumerate_edges(k):
    """All edges of K_{2k}: internal V-, cross, internal V+."""
    n = 2 * k
    edges = []
    edge_type = []

    # V- internal: pairs within {0, ..., k-1}
    for i1 in range(k):
        for i2 in range(i1 + 1, k):
            edges.append((i1, i2))
            edge_type.append('V-')

    # Cross: (a_i, b_j) = (i, k+j)
    for i in range(k):
        for j in range(k):
            edges.append((i, k + j))
            edge_type.append('cross')

    # V+ internal: pairs within {k, ..., 2k-1}
    for j1 in range(k):
        for j2 in range(j1 + 1, k):
            edges.append((k + j1, k + j2))
            edge_type.append('V+')

    return edges, edge_type


def extract_cross_matrix(edges, timestamps, k):
    """Extract k×k cross-edge timestamp matrix from full edge list."""
    M = [[0] * k for _ in range(k)]
    for (u, v), t in zip(edges, timestamps):
        if u < k and v >= k:
            M[u][v - k] = t
    return M


def check_2hop(M, k, j1, j2):
    """Check if 2-hop relay b_j1 -> a_i -> b_j2 exists."""
    return any(M[i][j1] <= M[i][j2] for i in range(k))


def run_fully_random(k, samples):
    """All n(n-1)/2 edge timestamps drawn from a single random permutation."""
    edges, etypes = enumerate_edges(k)
    m = len(edges)
    n = 2 * k

    depth_counts = {}
    total_2hop_ok = 0
    total_rescued = 0
    total_fail = 0

    for s in range(samples):
        timestamps = list(range(1, m + 1))
        random.shuffle(timestamps)

        M = extract_cross_matrix(edges, timestamps, k)
        timed = build_temporal_graph_general(k, edges, timestamps)

        for j1 in range(k):
            for j2 in range(k):
                if j1 == j2:
                    continue
                if check_2hop(M, k, j1, j2):
                    total_2hop_ok += 1
                else:
                    hops = find_shortest_journey(timed, n, k + j1, k + j2)
                    if hops > 0:
                        total_rescued += 1
                        depth_counts[hops] = depth_counts.get(hops, 0) + 1
                    else:
                        total_fail += 1

    return total_2hop_ok, total_rescued, total_fail, depth_counts


def run_adversarial_interleave(k, samples):
    """Adversarial: place internal edge timestamps to maximize interference.
    Strategy: interleave V- and V+ timestamps among cross edges
    so internal edges are NOT trivially first/last.
    """
    edges, etypes = enumerate_edges(k)
    m = len(edges)
    n = 2 * k

    depth_counts = {}
    total_2hop_ok = 0
    total_rescued = 0
    total_fail = 0

    for s in range(samples):
        # Assign timestamps: shuffle ALL edges together
        # But bias: put V+ internal edges EARLY (adversarial — they can't rescue late)
        # and V- internal edges LATE (adversarial — they can't enable early starts)

        v_minus_idx = [i for i, et in enumerate(etypes) if et == 'V-']
        cross_idx = [i for i, et in enumerate(etypes) if et == 'cross']
        v_plus_idx = [i for i, et in enumerate(etypes) if et == 'V+']

        # Adversarial ordering: V+ first, then cross, then V-
        # This makes V+ edges happen before cross (can't rescue AFTER cross)
        # and V- edges happen after cross (can't enable BEFORE cross)
        order = v_plus_idx + cross_idx + v_minus_idx
        random.shuffle(cross_idx)  # randomize within cross

        timestamps = [0] * m
        t = 1
        # V+ edges get earliest timestamps
        random.shuffle(v_plus_idx)
        for idx in v_plus_idx:
            timestamps[idx] = t
            t += 1
        # Cross edges get middle timestamps (randomized)
        random.shuffle(cross_idx)
        for idx in cross_idx:
            timestamps[idx] = t
            t += 1
        # V- edges get latest timestamps
        random.shuffle(v_minus_idx)
        for idx in v_minus_idx:
            timestamps[idx] = t
            t += 1

        M = extract_cross_matrix(edges, timestamps, k)
        timed = build_temporal_graph_general(k, edges, timestamps)

        for j1 in range(k):
            for j2 in range(k):
                if j1 == j2:
                    continue
                if check_2hop(M, k, j1, j2):
                    total_2hop_ok += 1
                else:
                    hops = find_shortest_journey(timed, n, k + j1, k + j2)
                    if hops > 0:
                        total_rescued += 1
                        depth_counts[hops] = depth_counts.get(hops, 0) + 1
                    else:
                        total_fail += 1

    return total_2hop_ok, total_rescued, total_fail, depth_counts


def run_worst_case_search(k, samples):
    """Try to find matrices that maximize rescue depth.
    Strategy: for each random full-permutation assignment,
    measure the max rescue depth. Track the worst case found.
    """
    edges, etypes = enumerate_edges(k)
    m = len(edges)
    n = 2 * k

    worst_depth = 0
    worst_timestamps = None
    worst_pair = None

    for s in range(samples):
        timestamps = list(range(1, m + 1))
        random.shuffle(timestamps)

        M = extract_cross_matrix(edges, timestamps, k)
        timed = build_temporal_graph_general(k, edges, timestamps)

        for j1 in range(k):
            for j2 in range(k):
                if j1 == j2:
                    continue
                if not check_2hop(M, k, j1, j2):
                    hops = find_shortest_journey(timed, n, k + j1, k + j2)
                    if hops > worst_depth:
                        worst_depth = hops
                        worst_timestamps = list(timestamps)
                        worst_pair = (j1, j2)
                    if hops == -1:
                        # ACTUAL FAILURE — conjecture broken
                        return worst_depth, timestamps, (j1, j2), True

    return worst_depth, worst_timestamps, worst_pair, False


def exhaustive_small(k):
    """For k=3: exhaustively check ALL timestamp permutations."""
    edges, etypes = enumerate_edges(k)
    m = len(edges)
    n = 2 * k

    max_depth = 0
    total_fail = 0
    total_checked = 0
    depth_hist = {}

    # m = C(6,2) = 15 edges for k=3. 15! is too large.
    # But we only need to consider relative order, and many are equivalent.
    # Instead, sample exhaustively from a large pool.
    # Actually for k=3, n=6, m=15. 15! ~ 1.3 trillion. Too large.
    # Let's do heavy random sampling instead.
    samples = 50000

    for s in range(samples):
        timestamps = list(range(1, m + 1))
        random.shuffle(timestamps)

        M = extract_cross_matrix(edges, timestamps, k)
        timed = build_temporal_graph_general(k, edges, timestamps)

        for j1 in range(k):
            for j2 in range(k):
                if j1 == j2:
                    continue
                total_checked += 1
                if not check_2hop(M, k, j1, j2):
                    hops = find_shortest_journey(timed, n, k + j1, k + j2)
                    if hops > 0:
                        depth_hist[hops] = depth_hist.get(hops, 0) + 1
                        if hops > max_depth:
                            max_depth = hops
                    elif hops == -1:
                        total_fail += 1

    return max_depth, total_fail, total_checked, depth_hist


def print_results(label, ok, rescued, fail, depths, total_pairs):
    print(f"\n  {label}:")
    print(f"    2-hop OK:  {ok} ({100*ok/total_pairs:.1f}%)")
    print(f"    Rescued:   {rescued} ({100*rescued/total_pairs:.1f}%)")
    print(f"    Failed:    {fail}")
    if depths:
        print(f"    Rescue depths:")
        for h in sorted(depths):
            pct = 100 * depths[h] / rescued if rescued else 0
            print(f"      {h} hops: {depths[h]} ({pct:.1f}%)")
        print(f"    Max depth: {max(depths.keys())}")


def main():
    random.seed(42)

    print("ADVERSARIAL RESCUE DEPTH ANALYSIS")
    print("=" * 65)

    for k in [3, 4, 5]:
        s_rand = {3: 5000, 4: 2000, 5: 500}[k]
        s_adv = {3: 5000, 4: 2000, 5: 500}[k]
        pairs_per = k * (k - 1)

        print(f"\n{'='*65}")
        print(f"k = {k}")
        print(f"{'='*65}")

        # Fully random timestamps
        ok, resc, fail, depths = run_fully_random(k, s_rand)
        print_results(f"Fully random ({s_rand} samples)",
                      ok, resc, fail, depths, pairs_per * s_rand)

        # Adversarial interleave (V+ early, V- late)
        ok, resc, fail, depths = run_adversarial_interleave(k, s_adv)
        print_results(f"Adversarial V+ early / V- late ({s_adv} samples)",
                      ok, resc, fail, depths, pairs_per * s_adv)

        # Worst case search
        print(f"\n  Worst-case search ({s_rand} samples)...")
        worst_d, worst_ts, worst_pair, broken = run_worst_case_search(k, s_rand)
        if broken:
            print(f"    *** CONJECTURE BROKEN: no temporal path found! ***")
            print(f"    Timestamps: {worst_ts}")
            print(f"    Pair: {worst_pair}")
        elif worst_d > 0:
            print(f"    Worst rescue depth found: {worst_d} hops")
            print(f"    Pair: b_{worst_pair[0]} -> b_{worst_pair[1]}")
        else:
            print(f"    All pairs had 2-hop relays (no rescue needed)")

    # Heavy sampling for k=3
    print(f"\n{'='*65}")
    print(f"Heavy sampling k=3 (50000 random timestamp permutations)")
    print(f"{'='*65}")
    max_d, fails, checked, hist = exhaustive_small(3)
    print(f"  Max rescue depth: {max_d}")
    print(f"  Total failures: {fails}")
    print(f"  Total pairs checked: {checked}")
    if hist:
        print(f"  Depth distribution:")
        for h in sorted(hist):
            print(f"    {h} hops: {hist[h]}")


if __name__ == "__main__":
    main()
