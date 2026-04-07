"""
Tree path → reverse pair matching, with max-run tracking.

For each winning tree:
1. Enumerate all tree paths (one per non-hub vertex pair)
2. Map each path to which reverse pair it covers
3. Is it a perfect matching? Or do some paths cover multiple pairs
   while others cover none?
4. Track max-run of the hub's incident edges — does the matching
   structure change between short-run (extreme) and long-run (balanced)?
"""

import random
from itertools import combinations
from collections import Counter, defaultdict


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


def hub_max_run(n, edges, timestamps, hub):
    """Max consecutive run of hub's edges in timestamp order."""
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


def find_tree_paths(n, hub, edges, tree_indices):
    """Find all paths in the tree between non-hub vertex pairs."""
    others = [v for v in range(n) if v != hub]
    # Build adjacency from tree edges
    adj = defaultdict(set)
    tree_edge_set = set()
    for idx in tree_indices:
        u, v = edges[idx]
        adj[u].add(v)
        adj[v].add(u)
        tree_edge_set.add((min(u, v), max(u, v)))

    paths = {}
    for a in others:
        for b in others:
            if a >= b:
                continue
            # BFS to find path a→b in tree
            parent = {a: None}
            queue = [a]
            found = False
            while queue and not found:
                node = queue.pop(0)
                for nbr in adj[node]:
                    if nbr not in parent:
                        parent[nbr] = node
                        if nbr == b:
                            found = True
                            break
                        queue.append(nbr)
            if found:
                path = []
                node = b
                while node is not None:
                    path.append(node)
                    node = parent[node]
                path.reverse()
                paths[(a, b)] = path

    return paths


def check_journey_on_path(n, edges, timestamps, hub, path, src, dst):
    """Check if there's a valid temporal journey from src to dst
    using star edges and tree path edges.

    Routes:
    1. Direct tree path: src→...→dst with non-decreasing timestamps
    2. Star-tree composition: src→hub→c→...→dst
    3. Tree-star composition: src→...→c→hub→dst
    4. Full composition: src→hub→c→...→d→hub→dst (but hub appears twice,
       needs two star edges with compatible times)
    """
    edge_map = {}
    for i, (u, v) in enumerate(edges):
        edge_map[(u, v)] = timestamps[i]
        edge_map[(v, u)] = timestamps[i]

    # Route 1: direct tree path with non-decreasing timestamps
    if len(path) >= 2:
        valid = True
        last_t = 0
        for i in range(len(path) - 1):
            t = edge_map[(path[i], path[i + 1])]
            if t < last_t:
                valid = False
                break
            last_t = t
        if valid:
            return 'direct_tree'

    # Route 1b: reverse tree path
    rev_path = list(reversed(path))
    if len(rev_path) >= 2:
        valid = True
        last_t = 0
        for i in range(len(rev_path) - 1):
            t = edge_map[(rev_path[i], rev_path[i + 1])]
            if t < last_t:
                valid = False
                break
            last_t = t
        if valid:
            return 'reverse_tree'

    # Route 2: src→hub then hub→(tree path to dst)
    t_src_hub = edge_map[(src, hub)]
    # Try entering tree at each node on the path
    for entry_idx in range(len(path)):
        entry = path[entry_idx]
        t_hub_entry = edge_map[(hub, entry)]
        if t_src_hub <= t_hub_entry:
            # Now follow tree path from entry to dst
            # Find subpath from entry to dst
            if entry == dst:
                return 'star_direct'
            start_in_path = path.index(entry) if entry in path else -1
            if start_in_path >= 0:
                # Try forward
                subpath = path[start_in_path:]
                if dst in subpath:
                    end_idx = subpath.index(dst)
                    sub = subpath[:end_idx + 1]
                    valid = True
                    last_t = t_hub_entry
                    for i in range(len(sub) - 1):
                        t = edge_map[(sub[i], sub[i + 1])]
                        if t < last_t:
                            valid = False
                            break
                        last_t = t
                    if valid:
                        return 'star_then_tree'
                # Try backward through path
                subpath_rev = list(reversed(path[:start_in_path + 1]))
                if dst in subpath_rev:
                    end_idx = subpath_rev.index(dst)
                    sub = subpath_rev[:end_idx + 1]
                    valid = True
                    last_t = t_hub_entry
                    for i in range(len(sub) - 1):
                        t = edge_map[(sub[i], sub[i + 1])]
                        if t < last_t:
                            valid = False
                            break
                        last_t = t
                    if valid:
                        return 'star_then_tree_rev'

    # Route 3: tree path to hub then hub→dst
    t_hub_dst = edge_map[(hub, dst)]
    for exit_idx in range(len(path)):
        exit_node = path[exit_idx]
        t_exit_hub = edge_map[(exit_node, hub)]
        if t_exit_hub <= t_hub_dst:
            # Follow tree path from src to exit_node
            if exit_node == src:
                return 'tree_then_star'
            start_in_path = path.index(src) if src in path else -1
            if start_in_path >= 0:
                end_in_path = path.index(exit_node) if exit_node in path else -1
                if end_in_path >= 0:
                    if start_in_path <= end_in_path:
                        sub = path[start_in_path:end_in_path + 1]
                    else:
                        sub = list(reversed(path[end_in_path:start_in_path + 1]))
                    valid = True
                    last_t = 0
                    for i in range(len(sub) - 1):
                        t = edge_map[(sub[i], sub[i + 1])]
                        if t < last_t:
                            valid = False
                            break
                        last_t = t
                    if valid and (not sub or edge_map.get((sub[-1], hub), 0) <= t_hub_dst):
                        return 'tree_then_star'

    return 'none'


def exhaustive_first_tree(n, edges, timestamps, hub):
    """Find first working tree."""
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


def run(n, num_samples):
    edges = make_edges(n)
    m = len(edges)
    print(f"\nK_{n}: {n} vertices, {m} edges")
    print(f"  Non-hub pairs: {(n-1)*(n-2)//2} undirected, {(n-1)*(n-2)} directed")
    print("=" * 70)

    # Aggregate by max_run
    run_buckets = defaultdict(lambda: {
        'count': 0,
        'route_types': Counter(),
        'multi_covered': 0,
        'uncovered': 0,
        'perfect_match': 0,
    })

    route_type_totals = Counter()

    for trial in range(num_samples):
        ts = list(range(1, m + 1))
        random.shuffle(ts)

        edge_map = {}
        for i, (u, v) in enumerate(edges):
            edge_map[(u, v)] = ts[i]
            edge_map[(v, u)] = ts[i]

        # Find a working hub+tree
        for hub in range(n):
            tree = exhaustive_first_tree(n, edges, ts, hub)
            if tree is not None:
                break
        else:
            continue

        mr = hub_max_run(n, edges, ts, hub)
        bucket = run_buckets[mr]
        bucket['count'] += 1

        others = [v for v in range(n) if v != hub]
        # Identify reverse pairs (star can't cover)
        reverse_pairs = []
        forward_pairs = []
        for a in others:
            for b in others:
                if a != b:
                    if edge_map[(a, hub)] > edge_map[(hub, b)]:
                        reverse_pairs.append((a, b))
                    else:
                        forward_pairs.append((a, b))

        # Find tree paths
        paths = find_tree_paths(n, hub, edges, tree)

        # For each reverse pair, check how it's covered
        pair_routes = {}
        for (a, b) in reverse_pairs:
            key = (min(a, b), max(a, b))
            if key in paths:
                route = check_journey_on_path(n, edges, ts, hub, paths[key], a, b)
            else:
                route = 'none'
            pair_routes[(a, b)] = route
            route_type_totals[route] += 1
            bucket['route_types'][route] += 1

        # Coverage stats
        covered = sum(1 for r in pair_routes.values() if r != 'none')
        uncov = sum(1 for r in pair_routes.values() if r == 'none')
        if uncov > 0:
            bucket['uncovered'] += 1

        # Check: do multiple reverse pairs use the same tree path?
        path_usage = Counter()
        for (a, b), route in pair_routes.items():
            if route != 'none':
                key = (min(a, b), max(a, b))
                path_usage[key] += 1
        multi = sum(1 for v in path_usage.values() if v > 1)
        if multi > 0:
            bucket['multi_covered'] += 1

    print(f"\nRoute types for reverse pairs (total):")
    total_routes = sum(route_type_totals.values())
    for rtype, count in route_type_totals.most_common():
        print(f"  {rtype:>20s}: {count:>6d} ({count/total_routes*100:.1f}%)")

    print(f"\nBreakdown by hub max-run:")
    print(f"{'max_run':>8s}  {'count':>6s}  {'uncov%':>7s}  {'multi%':>7s}  "
          f"{'direct':>7s}  {'star→tree':>10s}  {'tree→star':>10s}  {'none':>6s}")
    print("-" * 75)
    for mr in sorted(run_buckets):
        b = run_buckets[mr]
        c = b['count']
        rt = b['route_types']
        total_rt = sum(rt.values()) or 1
        direct = rt.get('direct_tree', 0) + rt.get('reverse_tree', 0)
        star_tree = rt.get('star_then_tree', 0) + rt.get('star_then_tree_rev', 0) + rt.get('star_direct', 0)
        tree_star = rt.get('tree_then_star', 0)
        none_ct = rt.get('none', 0)
        print(f"{mr:>8d}  {c:>6d}  {b['uncovered']/c*100:>6.1f}%  {b['multi_covered']/c*100:>6.1f}%  "
              f"{direct/total_rt*100:>6.1f}%  {star_tree/total_rt*100:>9.1f}%  "
              f"{tree_star/total_rt*100:>9.1f}%  {none_ct/total_rt*100:>5.1f}%")


def main():
    random.seed(42)
    for n, samples in [(5, 5000), (6, 1000)]:
        run(n, samples)


if __name__ == "__main__":
    main()
