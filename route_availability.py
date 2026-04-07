"""
For each reverse pair (a,b) in a winning spanner, which route types
are AVAILABLE? Not which one the BFS finds first — which ones COULD work.

Route types for reverse pair (a,b) where t(a,hub) > t(hub,b):

1. TREE-ONLY: tree path a→...→b with non-decreasing timestamps
2. SST: ∃c where t(a,hub) ≤ t(hub,c), then tree path c→...→b
   with non-decreasing timestamps starting ≥ t(hub,c)
3. TSS: tree path a→...→c with non-decreasing timestamps,
   then t(c,hub) ≤ t(hub,b)

For each pair, enumerate all three. Are there pairs where only one
type works? Are there structural conditions?

Track by max-run to see if the tvg shape determines which types fire.
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


def find_all_tree_paths(n, hub, edges, tree_indices, edge_map):
    """For each pair of non-hub vertices, find the unique tree path
    and check if it has non-decreasing timestamps in each direction."""
    others = [v for v in range(n) if v != hub]
    adj = defaultdict(set)
    for idx in tree_indices:
        u, v = edges[idx]
        adj[u].add(v)
        adj[v].add(u)

    results = {}
    for a in others:
        for b in others:
            if a == b:
                continue
            # BFS for path a→b
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
            if not found:
                results[(a, b)] = None
                continue

            path = []
            node = b
            while node is not None:
                path.append(node)
                node = parent[node]
            path.reverse()

            # Check timestamps along path
            times = []
            for i in range(len(path) - 1):
                times.append(edge_map[(path[i], path[i + 1])])

            non_decreasing = all(times[i] <= times[i + 1] for i in range(len(times) - 1))

            results[(a, b)] = {
                'path': path,
                'times': times,
                'non_decreasing': non_decreasing,
                'min_time': times[0] if times else 0,
                'max_time': times[-1] if times else 0,
            }

    return results


def check_route_availability(n, hub, edges, timestamps, tree_indices, a, b, tree_paths, edge_map):
    """Check which route types are available for reverse pair (a,b).
    Reverse means t(a,hub) > t(hub,b)."""
    others = [v for v in range(n) if v != hub]
    t_a_hub = edge_map[(a, hub)]
    t_hub_b = edge_map[(hub, b)]

    available = set()

    # Type 1: TREE-ONLY — tree path a→b with non-decreasing timestamps
    tp = tree_paths.get((a, b))
    if tp and tp['non_decreasing']:
        available.add('tree_only')

    # Type 2: SST — a→hub→c then tree c→...→b
    # Need: t(a,hub) ≤ t(hub,c), and tree path c→b starting ≥ t(hub,c)
    for c in others:
        if c == a or c == b:
            continue
        t_hub_c = edge_map[(hub, c)]
        if t_a_hub <= t_hub_c:
            # Check tree path c→b with timestamps ≥ t_hub_c and non-decreasing
            tp_cb = tree_paths.get((c, b))
            if tp_cb:
                if tp_cb['non_decreasing'] and tp_cb['min_time'] >= t_hub_c:
                    available.add('SST')
                    break
            # Also: c might BE b (then just star covers it)
        # Also check: a→hub at t_a_hub, hub→c at t_hub_c ≥ t_a_hub,
        # then c=b directly? No, c≠b above.

    # Also SST with c=b: a→hub→b. But this is the forward route,
    # and (a,b) is reverse, so t(a,hub) > t(hub,b). Doesn't work.

    # Type 3: TSS — tree a→...→c then c→hub→b
    # Need: tree path a→c non-decreasing, last time ≤ t(c,hub),
    # and t(c,hub) ≤ t(hub,b)
    for c in others:
        if c == a or c == b:
            continue
        t_c_hub = edge_map[(c, hub)]
        if t_c_hub <= t_hub_b:
            tp_ac = tree_paths.get((a, c))
            if tp_ac:
                if tp_ac['non_decreasing'] and tp_ac['max_time'] <= t_c_hub:
                    available.add('TSS')
                    break

    # Type 4: STTS — a→hub→c→...→d→hub→b (double star)
    # Need: t(a,hub) ≤ t(hub,c), tree c→d non-decreasing with times
    # between t(hub,c) and t(d,hub), then t(d,hub) ≤ t(hub,b)
    for c in others:
        if c == a or c == b:
            continue
        t_hub_c = edge_map[(hub, c)]
        if t_a_hub <= t_hub_c:
            for d in others:
                if d == a or d == b or d == c:
                    continue
                t_d_hub = edge_map[(d, hub)]
                if t_d_hub <= t_hub_b:
                    tp_cd = tree_paths.get((c, d))
                    if tp_cd and tp_cd['non_decreasing']:
                        if tp_cd['min_time'] >= t_hub_c and tp_cd['max_time'] <= t_d_hub:
                            available.add('STTS')
                            break
            if 'STTS' in available:
                break

    return available


def run(n, num_samples):
    edges = make_edges(n)
    m = len(edges)
    print(f"\nK_{n}: {n} vertices, {m} edges")
    print("=" * 70)

    # Track availability patterns
    availability_patterns = Counter()
    by_run = defaultdict(Counter)
    only_one_type = Counter()  # pairs where only 1 route type works
    no_route = 0
    total_pairs = 0

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
        tree_paths = find_all_tree_paths(n, hub, edges, tree, edge_map)

        others = [v for v in range(n) if v != hub]
        for a in others:
            for b in others:
                if a != b and edge_map[(a, hub)] > edge_map[(hub, b)]:
                    total_pairs += 1
                    avail = check_route_availability(
                        n, hub, edges, ts, tree, a, b, tree_paths, edge_map)

                    pattern = frozenset(avail) if avail else frozenset(['NONE'])
                    availability_patterns[pattern] += 1
                    by_run[mr][pattern] += 1

                    if len(avail) == 1:
                        only_one_type[next(iter(avail))] += 1
                    if not avail:
                        no_route += 1

        if (trial + 1) % max(1, num_samples // 5) == 0:
            print(f"  {trial+1}/{num_samples}")

    print(f"\nTotal reverse pairs analyzed: {total_pairs}")
    print(f"No route found: {no_route} ({no_route/total_pairs*100:.2f}%)")

    print(f"\nAvailability patterns:")
    for pattern, count in availability_patterns.most_common(20):
        types = sorted(pattern)
        print(f"  {str(types):>45s}: {count:>6d} ({count/total_pairs*100:.1f}%)")

    print(f"\nPairs where ONLY one route type works:")
    for rtype, count in only_one_type.most_common():
        print(f"  {rtype:>15s}: {count:>6d} ({count/total_pairs*100:.1f}%)")

    print(f"\nBy max-run (fraction of pairs with each available type):")
    all_types = ['tree_only', 'SST', 'TSS', 'STTS', 'NONE']
    print(f"{'run':>4s}  {'n_pairs':>7s}  ", end="")
    for t in all_types:
        print(f"{t:>10s}  ", end="")
    print()
    print("-" * (14 + 12 * len(all_types)))
    for mr in sorted(by_run):
        total_mr = sum(by_run[mr].values())
        type_counts = Counter()
        for pattern, count in by_run[mr].items():
            for t in pattern:
                type_counts[t] += count
        print(f"{mr:>4d}  {total_mr:>7d}  ", end="")
        for t in all_types:
            c = type_counts.get(t, 0)
            print(f"{c/total_mr*100:>9.1f}%  ", end="")
        print()


def main():
    random.seed(42)
    for n, samples in [(5, 3000), (6, 500)]:
        run(n, samples)


if __name__ == "__main__":
    main()
