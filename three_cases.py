"""
Three cases: flat, steep-in, steep-out.

For a reverse pair (a,b) where t(a,hub) > t(hub,b):

Case 1 (FLAT): tree path a→...→b, non-decreasing timestamps.
  No hub involvement.

Case 2 (STEEP IN): a→hub via star at time t(a,hub),
  then hub reaches b via star+tree with timestamps ≥ t(a,hub).
  "a is steep to hub, b is reachable from hub."

Case 3 (STEEP OUT): a reaches hub via tree+star with some arrival time τ,
  then hub→b via star at time t(hub,b) ≥ τ.
  "a reaches hub flat, b exits steep."

The decomposition: at the hub, the journey splits.
The inductive step adds one vertex and only needs to show
one of these three cases works for each new pair.

Also: track per max-run. Does the CASE distribution shift?
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


def find_all_tree_paths(adj, a, b, n):
    """DFS to find ALL simple paths from a to b in tree.
    In a tree there's exactly one, but the graph may have cycles
    from multiple tree edges. Return all simple paths."""
    results = []
    def dfs(node, target, visited, path):
        if node == target:
            results.append(list(path))
            return
        for nbr in adj[node]:
            if nbr not in visited:
                visited.add(nbr)
                path.append(nbr)
                dfs(nbr, target, visited, path)
                path.pop()
                visited.discard(nbr)
    dfs(a, b, {a}, [a])
    return results


def path_timestamps(path, edge_map):
    """Get timestamps along a path."""
    return [edge_map[(path[i], path[i+1])] for i in range(len(path)-1)]


def is_nondecreasing(times):
    return all(times[i] <= times[i+1] for i in range(len(times)-1))


def classify_pair(n, hub, a, b, tree_adj, edge_map, others):
    """Classify reverse pair (a,b) into one of three cases.

    Returns: 'flat', 'steep_in', 'steep_out', or 'none'
    Uses ALL tree paths between vertices, not just shortest.
    """
    t_a_hub = edge_map[(a, hub)]
    t_hub_b = edge_map[(hub, b)]

    # CASE 1: FLAT — tree path a→b with non-decreasing timestamps
    for path in find_all_tree_paths(tree_adj, a, b, n):
        times = path_timestamps(path, edge_map)
        if times and is_nondecreasing(times):
            return 'flat'

    # CASE 2: STEEP IN — a→hub (star), then hub→c (star), then tree c→b
    for c in others:
        if c == a or c == b:
            continue
        t_hub_c = edge_map[(hub, c)]
        if t_hub_c >= t_a_hub:
            for path in find_all_tree_paths(tree_adj, c, b, n):
                times = path_timestamps(path, edge_map)
                if times and times[0] >= t_hub_c and is_nondecreasing(times):
                    return 'steep_in'

    # CASE 3: STEEP OUT — tree a→c, then c→hub (star), then hub→b (star)
    for c in others:
        if c == a or c == b:
            continue
        t_c_hub = edge_map[(c, hub)]
        if t_c_hub <= t_hub_b:
            for path in find_all_tree_paths(tree_adj, a, c, n):
                times = path_timestamps(path, edge_map)
                if times and is_nondecreasing(times) and times[-1] <= t_c_hub:
                    return 'steep_out'

    # DECOMPOSE: steep_out + steep_in composed at hub
    for c1 in others:
        if c1 == a or c1 == b:
            continue
        t_c1_hub = edge_map[(c1, hub)]
        found_c1 = False
        for path1 in find_all_tree_paths(tree_adj, a, c1, n):
            times1 = path_timestamps(path1, edge_map)
            if times1 and is_nondecreasing(times1) and times1[-1] <= t_c1_hub:
                found_c1 = True
                break
        if not found_c1:
            continue
        for c2 in others:
            if c2 == a or c2 == b or c2 == c1:
                continue
            t_hub_c2 = edge_map[(hub, c2)]
            if t_hub_c2 >= t_c1_hub:
                for path2 in find_all_tree_paths(tree_adj, c2, b, n):
                    times2 = path_timestamps(path2, edge_map)
                    if times2 and times2[0] >= t_hub_c2 and is_nondecreasing(times2):
                        return 'decompose'

    return 'none'


def run(n, num_samples):
    edges = make_edges(n)
    m = len(edges)
    print(f"\nK_{n}: {n} vertices, {m} edges")
    print("=" * 70)

    case_counts = Counter()
    by_run = defaultdict(Counter)
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
        others = [v for v in range(n) if v != hub]

        tree_adj = defaultdict(set)
        for idx in tree:
            u, v = edges[idx]
            tree_adj[u].add(v)
            tree_adj[v].add(u)

        for a in others:
            for b in others:
                if a != b and edge_map[(a, hub)] > edge_map[(hub, b)]:
                    total_pairs += 1
                    case = classify_pair(n, hub, a, b, tree_adj, edge_map, others)
                    case_counts[case] += 1
                    by_run[mr][case] += 1

        if (trial + 1) % max(1, num_samples // 5) == 0:
            print(f"  {trial+1}/{num_samples}")

    print(f"\nTotal reverse pairs: {total_pairs}")
    print(f"\nCase distribution:")
    for case, count in case_counts.most_common():
        print(f"  {case:>12s}: {count:>6d} ({count/total_pairs*100:.1f}%)")

    print(f"\nBy max-run:")
    all_cases = ['flat', 'steep_in', 'steep_out', 'decompose', 'none']
    print(f"{'run':>4s}  {'n':>5s}  ", end="")
    for c in all_cases:
        print(f"{c:>12s}  ", end="")
    print()
    print("-" * (12 + 14 * len(all_cases)))
    for mr in sorted(by_run):
        total_mr = sum(by_run[mr].values())
        print(f"{mr:>4d}  {total_mr:>5d}  ", end="")
        for c in all_cases:
            ct = by_run[mr].get(c, 0)
            print(f"{ct/total_mr*100:>11.1f}%  ", end="")
        print()


def main():
    random.seed(42)
    for n, samples in [(5, 3000), (6, 500)]:
        run(n, samples)


if __name__ == "__main__":
    main()
