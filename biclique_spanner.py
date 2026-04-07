"""
Study the non-dismountable bi-clique directly.

Structure (Theorem 3.10):
- V- = {0..k-1}, V+ = {k..2k-1}, n = 2k
- M- = perfect matching: earliest edges of V+ nodes to V- nodes
- M+ = perfect matching: latest edges of V- nodes to V+ nodes
- Internal V- edges: earliest timestamps
- Cross edges: middle timestamps
- Internal V+ edges: latest timestamps

Questions:
1. What does the minimum spanner look like? (not star+tree)
2. Does a pivot edge exist? (edge e where in-tree(e) + out-tree(e) spans)
3. What's the actual structure of 2n-3 spanners on shifted matchings?
4. Can we find a 2n-3 spanner for SM(k) constructively?
"""

import random
from itertools import combinations
from collections import defaultdict


def make_edges(n):
    return [(i, j) for i in range(n) for j in range(i + 1, n)]


def compute_reachability(n, timed_edges):
    reached_by = [dict() for _ in range(n)]
    for i in range(n):
        reached_by[i][i] = 0
    for t, u, v in timed_edges:
        sources_u = {s: arr for s, arr in reached_by[u].items() if arr <= t}
        sources_v = {s: arr for s, arr in reached_by[v].items() if arr <= t}
        for s, arr in sources_u.items():
            if s not in reached_by[v] or t < reached_by[v][s]:
                reached_by[v][s] = t
        for s, arr in sources_v.items():
            if s not in reached_by[u] or t < reached_by[u][s]:
                reached_by[u][s] = t
    reach = [0] * n
    for v in range(n):
        for s in reached_by[v]:
            if s != v:
                reach[s] |= (1 << v)
    return reach


def generate_shifted_matching(k):
    """SM(k): a_i=i, b_j=k+j. Cross edge (a_i, b_j) labeled (j-i) mod k."""
    n = 2 * k
    edges = make_edges(n)
    m = len(edges)
    edge_to_idx = {}
    for i, (u, v) in enumerate(edges):
        edge_to_idx[(u, v)] = i
        edge_to_idx[(v, u)] = i

    timestamps = [0] * m
    t = 1

    # V- internal (a_i, a_j): earliest
    for i in range(k):
        for j in range(i + 1, k):
            timestamps[edge_to_idx[(i, j)]] = t; t += 1

    # Cross edges ordered by (j-i) mod k
    for label_val in range(k):
        for i in range(k):
            j = (i + label_val) % k
            idx = edge_to_idx[(min(i, k+j), max(i, k+j))]
            if timestamps[idx] == 0:
                timestamps[idx] = t; t += 1

    # V+ internal (b_i, b_j): latest
    for i in range(k):
        for j in range(i + 1, k):
            timestamps[edge_to_idx[(k+i, k+j)]] = t; t += 1

    return n, edges, timestamps


def find_minimum_spanner(n, edges, timestamps):
    """Greedy edge removal to find minimum spanner."""
    m = len(edges)
    timed = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in range(m)])
    target = compute_reachability(n, timed)

    included = list(range(m))
    for idx in sorted(range(m), key=lambda i: -timestamps[i]):
        candidate = [i for i in included if i != idx]
        sub = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in candidate])
        if compute_reachability(n, sub) == target:
            included = candidate

    return included


def find_exact_minimum(n, edges, timestamps, greedy_size):
    """Try to find smaller spanners below greedy size."""
    m = len(edges)
    timed = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in range(m)])
    target = compute_reachability(n, timed)

    for size in range(n - 1, greedy_size):
        for subset in combinations(range(m), size):
            sub = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in subset])
            if compute_reachability(n, sub) == target:
                return list(subset)
    return None


def analyze_spanner(n, edges, timestamps, spanner_idx, k):
    """Analyze the structure of a spanner."""
    edge_map = {}
    for i, (u, v) in enumerate(edges):
        edge_map[(u, v)] = timestamps[i]
        edge_map[(v, u)] = timestamps[i]

    spanner_edges = [edges[i] for i in spanner_idx]

    # Classify edges
    internal_minus = [(u, v) for (u, v) in spanner_edges if u < k and v < k]
    internal_plus = [(u, v) for (u, v) in spanner_edges if u >= k and v >= k]
    cross = [(u, v) for (u, v) in spanner_edges if (u < k) != (v < k)]

    print(f"    Spanner: {len(spanner_idx)} edges "
          f"(V-:{len(internal_minus)} cross:{len(cross)} V+:{len(internal_plus)})")

    # Degree distribution
    deg = [0] * n
    for (u, v) in spanner_edges:
        deg[u] += 1; deg[v] += 1

    v_minus_degs = [deg[i] for i in range(k)]
    v_plus_degs = [deg[k+i] for i in range(k)]
    print(f"    V- degrees: {v_minus_degs}")
    print(f"    V+ degrees: {v_plus_degs}")

    # Is there a high-degree vertex? (pivot-like)
    max_deg_v = max(range(n), key=lambda v: deg[v])
    side = "V-" if max_deg_v < k else "V+"
    print(f"    Max degree: vertex {max_deg_v} ({side}), deg={deg[max_deg_v]}")

    # Check pivot edge: for each edge, can in-tree + out-tree span?
    # In-tree(e): edges reachable by journeys ENDING at e
    # Out-tree(e): edges reachable by journeys STARTING at e
    print(f"    Cross edges in spanner (sorted by time):")
    cross_sorted = sorted(cross, key=lambda e: edge_map[e])
    for (u, v) in cross_sorted:
        t = edge_map[(u, v)]
        u_side = "a" if u < k else "b"
        v_side = "a" if v < k else "b"
        print(f"      ({u_side}{u%k},{v_side}{v%k}) @ t={t}")

    return {
        'size': len(spanner_idx),
        'internal_minus': len(internal_minus),
        'cross': len(cross),
        'internal_plus': len(internal_plus),
        'max_deg': deg[max_deg_v],
    }


def run():
    print("Non-dismountable bi-clique spanner analysis")
    print("=" * 70)

    for k in [3, 4, 5]:
        n, edges, ts = generate_shifted_matching(k)
        m = len(edges)
        print(f"\nSM({k}): n={n}, m={m}, 2n-3={2*n-3}")

        # Show timestamp matrix
        edge_map = {}
        for i, (u, v) in enumerate(edges):
            edge_map[(u, v)] = ts[i]
            edge_map[(v, u)] = ts[i]

        print(f"\n  Timestamp matrix (a_i rows, b_j cols for cross block):")
        header = "       " + "".join(f"b{j:>3d}" for j in range(k))
        print(f"  {header}")
        for i in range(k):
            row = f"  a{i:>2d}: "
            for j in range(k):
                row += f"{edge_map[(i, k+j)]:>4d}"
            print(row)

        # Find minimum spanner
        greedy = find_minimum_spanner(n, edges, ts)
        print(f"\n  Greedy spanner: {len(greedy)} edges")

        if n <= 10:
            exact = find_exact_minimum(n, edges, ts, len(greedy))
            if exact:
                print(f"  Exact minimum: {len(exact)} edges")
                analyze_spanner(n, edges, ts, exact, k)
            else:
                print(f"  Exact minimum: {len(greedy)} edges (greedy is optimal)")
                analyze_spanner(n, edges, ts, greedy, k)
        else:
            analyze_spanner(n, edges, ts, greedy, k)

    # Also test random bi-cliques
    print(f"\n{'='*70}")
    print("Random non-dismountable bi-cliques")
    print("=" * 70)

    random.seed(42)
    for k in [3, 4, 5]:
        n = 2 * k
        sizes = []
        for _ in range(200 if k <= 4 else 50):
            edges = make_edges(n)
            m = len(edges)
            edge_to_idx = {}
            for i, (u, v) in enumerate(edges):
                edge_to_idx[(u, v)] = i
                edge_to_idx[(v, u)] = i

            ts = [0] * m
            t = 1
            # V- internal
            internal_m = [(u, v) for (u, v) in edges if u < k and v < k]
            random.shuffle(internal_m)
            for (u, v) in internal_m:
                ts[edge_to_idx[(u, v)]] = t; t += 1
            # Cross
            cross = [(u, v) for (u, v) in edges if (u < k) != (v < k)]
            random.shuffle(cross)
            for (u, v) in cross:
                ts[edge_to_idx[(u, v)]] = t; t += 1
            # V+ internal
            internal_p = [(u, v) for (u, v) in edges if u >= k and v >= k]
            random.shuffle(internal_p)
            for (u, v) in internal_p:
                ts[edge_to_idx[(u, v)]] = t; t += 1

            greedy = find_minimum_spanner(n, edges, ts)
            sizes.append(len(greedy))

        avg = sum(sizes) / len(sizes)
        print(f"\n  Random bi-clique k={k}: min={min(sizes)} avg={avg:.1f} max={max(sizes)} "
              f"(2n-3={2*n-3})")


if __name__ == "__main__":
    run()
