"""
Find ALL routes for every reverse pair in a winning spanner.

The previous checker missed some routes. This time: for each reverse
pair (a,b), compute the actual temporal journey through the spanner
edges (star + tree) using the full reachability algorithm. Then trace
back HOW that pair is reached — which edges are used?
"""

import random
from itertools import combinations
from collections import defaultdict, Counter


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


def trace_journey(n, timed_edges, src, dst):
    """Trace the actual journey from src to dst.
    Returns list of (time, from, to) hops."""
    # BFS on (vertex, arrival_time) states
    # State: (current_vertex, arrival_time, path)
    reached = {}  # vertex -> (earliest_arrival, path)
    reached[src] = (0, [])
    queue = [(0, src)]

    while queue:
        queue.sort()  # process earliest arrivals first
        arr_time, node = queue.pop(0)

        if node == dst:
            return reached[dst][1]

        for t, u, v in timed_edges:
            if t < arr_time:
                continue
            if u == node:
                next_node = v
            elif v == node:
                next_node = u
            else:
                continue

            if next_node not in reached or t < reached[next_node][0]:
                new_path = reached[node][1] + [(t, node, next_node)]
                reached[next_node] = (t, new_path)
                queue.append((t, next_node))

    return reached.get(dst, (None, []))[1]


def classify_journey(hub, journey):
    """Classify a journey by which edges involve the hub."""
    if not journey:
        return 'empty'

    hops = len(journey)
    uses_hub = [hub in (frm, to) for (t, frm, to) in journey]

    if not any(uses_hub):
        return f'tree_only_{hops}hop'
    if all(uses_hub):
        return f'star_only_{hops}hop'

    # Mixed: describe pattern
    pattern = ''.join('S' if h else 'T' for h in uses_hub)
    return f'mixed_{pattern}'


def exhaustive_first_tree(n, edges, timestamps, hub):
    m = len(edges)
    timed = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in range(m)])
    target = compute_reachability(n, timed)
    star_idx = set(i for i, (u, v) in enumerate(edges) if u == hub or v == hub)
    tree_candidates = [i for i in range(m) if i not in star_idx]
    for subset in combinations(tree_candidates, n - 2):
        used = star_idx | set(subset)
        sub = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in used])
        if compute_reachability(n, sub) == target:
            return list(subset)
    return None


def hub_max_run(n, edges, timestamps, hub):
    m = len(edges)
    ordered = sorted(range(m), key=lambda i: timestamps[i])
    involves_hub = [(edges[i][0] == hub or edges[i][1] == hub) for i in ordered]
    max_run = 0
    cur = 0
    for b in involves_hub:
        if b:
            cur += 1
            max_run = max(max_run, cur)
        else:
            cur = 0
    return max_run


def run(n, num_samples):
    edges = make_edges(n)
    m = len(edges)
    print(f"\nK_{n}: {n} vertices, {m} edges")
    print("=" * 70)

    route_types = Counter()
    route_by_run = defaultdict(Counter)
    hop_counts = Counter()

    for trial in range(num_samples):
        ts = list(range(1, m + 1))
        random.shuffle(ts)

        edge_map = {}
        for i, (u, v) in enumerate(edges):
            edge_map[(u, v)] = ts[i]
            edge_map[(v, u)] = ts[i]

        for hub in range(n):
            tree = exhaustive_first_tree(n, edges, ts, hub)
            if tree is not None:
                break
        else:
            continue

        mr = hub_max_run(n, edges, ts, hub)

        # Build spanner edges
        star_idx = set(i for i, (u, v) in enumerate(edges) if u == hub or v == hub)
        used = star_idx | set(tree)
        spanner_timed = sorted([(ts[i], edges[i][0], edges[i][1]) for i in used])

        # Identify reverse pairs
        others = [v for v in range(n) if v != hub]
        for a in others:
            for b in others:
                if a != b and edge_map[(a, hub)] > edge_map[(hub, b)]:
                    # Reverse pair — trace the journey
                    journey = trace_journey(n, spanner_timed, a, b)
                    route = classify_journey(hub, journey)
                    route_types[route] += 1
                    route_by_run[mr][route] += 1
                    hop_counts[len(journey)] += 1

        if (trial + 1) % max(1, num_samples // 5) == 0:
            print(f"  {trial+1}/{num_samples}")

    print(f"\nAll route types for reverse pairs:")
    total = sum(route_types.values())
    for rtype, count in route_types.most_common():
        print(f"  {rtype:>25s}: {count:>6d} ({count/total*100:.1f}%)")

    print(f"\nHop counts:")
    for hops, count in sorted(hop_counts.items()):
        print(f"  {hops} hops: {count:>6d} ({count/total*100:.1f}%)")

    print(f"\nBy max-run:")
    print(f"{'run':>4s}  ", end="")
    all_types = sorted(route_types.keys(), key=lambda x: -route_types[x])[:6]
    for rt in all_types:
        print(f"{rt:>18s}  ", end="")
    print()
    print("-" * (6 + 20 * len(all_types)))
    for mr in sorted(route_by_run):
        total_mr = sum(route_by_run[mr].values())
        print(f"{mr:>4d}  ", end="")
        for rt in all_types:
            c = route_by_run[mr].get(rt, 0)
            print(f"{c/total_mr*100:>17.1f}%  ", end="")
        print()


def main():
    random.seed(42)
    for n, samples in [(5, 5000), (6, 500)]:
        run(n, samples)


if __name__ == "__main__":
    main()
