"""
Trace the NONE pairs — reverse pairs where tree_only, SST, TSS all fail.
What route does the actual reachability algorithm use?

For each NONE pair, reconstruct the journey step by step.
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


def compute_reachability_with_trace(n, timed_edges):
    """Like compute_reachability but tracks the path."""
    reached_by = [dict() for _ in range(n)]
    path_to = [dict() for _ in range(n)]  # path_to[dst][src] = [(t, u, v), ...]
    for i in range(n):
        reached_by[i][i] = 0
        path_to[i][i] = []

    for t, u, v in timed_edges:
        # u→v direction
        sources_u = {s: arr for s, arr in reached_by[u].items() if arr <= t}
        for s, arr in sources_u.items():
            if s not in reached_by[v] or t < reached_by[v][s]:
                reached_by[v][s] = t
                path_to[v][s] = path_to[u][s] + [(t, u, v)]
        # v→u direction
        sources_v = {s: arr for s, arr in reached_by[v].items() if arr <= t}
        for s, arr in sources_v.items():
            if s not in reached_by[u] or t < reached_by[u][s]:
                reached_by[u][s] = t
                path_to[u][s] = path_to[v][s] + [(t, v, u)]

    return reached_by, path_to


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


def is_tree_edge(u, v, edges, tree_indices):
    tree_set = set(tree_indices)
    for idx in tree_set:
        eu, ev = edges[idx]
        if (eu == u and ev == v) or (eu == v and ev == u):
            return True
    return False


def classify_hop(hub, frm, to, edges, tree_indices):
    if frm == hub or to == hub:
        return 'S'
    if is_tree_edge(frm, to, edges, tree_indices):
        return 'T'
    return '?'


def run(n, num_samples):
    edges = make_edges(n)
    m = len(edges)
    print(f"\nK_{n}: {n} vertices, {m} edges")
    print("=" * 70)

    route_patterns = defaultdict(int)
    examples = []

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

        # Build spanner
        star_idx = set(i for i, (u, v) in enumerate(edges) if u == hub or v == hub)
        used = star_idx | set(tree)
        spanner_timed = sorted([(ts[i], edges[i][0], edges[i][1]) for i in used])

        # Trace all journeys
        _, path_to = compute_reachability_with_trace(n, spanner_timed)

        # Check tree paths for non-decreasing
        others = [v for v in range(n) if v != hub]
        tree_adj = defaultdict(set)
        for idx in tree:
            u, v = edges[idx]
            tree_adj[u].add(v)
            tree_adj[v].add(u)

        def find_tree_path(a, b):
            parent = {a: None}
            queue = [a]
            while queue:
                node = queue.pop(0)
                for nbr in tree_adj[node]:
                    if nbr not in parent:
                        parent[nbr] = node
                        if nbr == b:
                            path = []
                            nd = b
                            while nd is not None:
                                path.append(nd)
                                nd = parent[nd]
                            return list(reversed(path))
                        queue.append(nbr)
            return None

        for a in others:
            for b in others:
                if a != b and edge_map[(a, hub)] > edge_map[(hub, b)]:
                    # Check simple routes
                    tree_path = find_tree_path(a, b)
                    tree_ok = False
                    if tree_path:
                        times = [edge_map[(tree_path[i], tree_path[i+1])]
                                 for i in range(len(tree_path)-1)]
                        tree_ok = all(times[i] <= times[i+1]
                                     for i in range(len(times)-1))

                    sst_ok = False
                    for c in others:
                        if c != a and c != b:
                            if edge_map[(a, hub)] <= edge_map[(hub, c)]:
                                tp = find_tree_path(c, b)
                                if tp:
                                    tms = [edge_map[(tp[i], tp[i+1])]
                                           for i in range(len(tp)-1)]
                                    if (not tms or tms[0] >= edge_map[(hub, c)]) and \
                                       all(tms[i] <= tms[i+1] for i in range(len(tms)-1)):
                                        sst_ok = True
                                        break

                    tss_ok = False
                    for c in others:
                        if c != a and c != b:
                            if edge_map[(c, hub)] <= edge_map[(hub, b)]:
                                tp = find_tree_path(a, c)
                                if tp:
                                    tms = [edge_map[(tp[i], tp[i+1])]
                                           for i in range(len(tp)-1)]
                                    if all(tms[i] <= tms[i+1] for i in range(len(tms)-1)) and \
                                       (not tms or tms[-1] <= edge_map[(c, hub)]):
                                        tss_ok = True
                                        break

                    if not tree_ok and not sst_ok and not tss_ok:
                        # NONE case — trace the actual journey
                        journey = path_to[b].get(a, [])
                        if journey:
                            pattern = ''.join(
                                classify_hop(hub, frm, to, edges, tree)
                                for (t, frm, to) in journey
                            )
                            route_patterns[pattern] += 1
                            if len(examples) < 20:
                                examples.append({
                                    'hub': hub, 'a': a, 'b': b,
                                    'max_run': mr,
                                    't_a_hub': edge_map[(a, hub)],
                                    't_hub_b': edge_map[(hub, b)],
                                    'journey': journey,
                                    'pattern': pattern,
                                    'tree': tree,
                                    'ts': ts[:],
                                })

        if (trial + 1) % max(1, num_samples // 5) == 0:
            print(f"  {trial+1}/{num_samples}")

    print(f"\nNONE route patterns (S=star, T=tree, ?=unknown):")
    for pattern, count in sorted(route_patterns.items(), key=lambda x: -x[1]):
        print(f"  {pattern:>10s}: {count:>5d}")

    print(f"\nDetailed examples of NONE routes:")
    for ex in examples[:10]:
        print(f"\n  hub={ex['hub']}, pair=({ex['a']}→{ex['b']}), "
              f"max_run={ex['max_run']}")
        print(f"  t(a,hub)={ex['t_a_hub']}, t(hub,b)={ex['t_hub_b']}  [REVERSE]")
        print(f"  Journey: ", end="")
        for (t, frm, to) in ex['journey']:
            hop_type = classify_hop(ex['hub'], frm, to, edges, ex['tree'])
            print(f"{frm}→{to}@{t}({hop_type}) ", end="")
        print(f"\n  Pattern: {ex['pattern']}")


def main():
    random.seed(42)
    for n, samples in [(5, 5000), (6, 1000)]:
        run(n, samples)


if __name__ == "__main__":
    main()
