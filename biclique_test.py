"""
Test three-case decomposition on non-dismountable bi-clique residuals.

From Carnevale et al. Theorem 3.10, the non-dismountable residual has:
- V+ and V- of equal size, partitioning V
- M- = perfect matching (earliest edges of V+ nodes to V- nodes)
- M+ = perfect matching (latest edges of V- nodes to V+ nodes)
- All cross edges (V+ to V-) sit between the internal edges temporally

Generate such bi-cliques and test:
1. Does star+tree with 2n-3 edges always span?
2. Do the three cases (flat/steep-in/steep-out) cover all reverse pairs?
3. Which hub works — one from V+ or V-?
"""

import random
from itertools import combinations, permutations
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


def exhaustive_hub_tree(n, edges, timestamps, hub):
    """Find first working tree for this hub (exhaustive)."""
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


def generate_shifted_matching(k):
    """Generate shifted matching SM(k): a known hard non-dismountable bi-clique.
    Vertices: a_0..a_{k-1} (V-), b_0..b_{k-1} (V+)
    Edge (a_i, b_j) gets label (j - i) mod k, mapped to timestamps 1..k^2.
    """
    n = 2 * k
    # a_i = i, b_j = k + j
    edges = make_edges(n)
    m = len(edges)
    timestamps = [0] * m

    edge_to_idx = {}
    for i, (u, v) in enumerate(edges):
        edge_to_idx[(u, v)] = i
        edge_to_idx[(v, u)] = i

    # Cross edges: (a_i, b_j) labeled by (j - i) mod k
    # Group by label value, assign timestamps in order
    t = 1
    # Internal edges (a-a and b-b) get early and late timestamps
    # Per theorem 3.10: internal V- edges are earliest, internal V+ edges are latest
    # Cross edges in the middle

    # V- internal edges (a_i, a_j): earliest timestamps
    internal_minus = []
    for i in range(k):
        for j in range(i + 1, k):
            internal_minus.append((i, j))
    random.shuffle(internal_minus)
    for (u, v) in internal_minus:
        idx = edge_to_idx[(u, v)]
        timestamps[idx] = t
        t += 1

    # Cross edges: middle timestamps, ordered by (j-i) mod k
    cross_edges = []
    for label_val in range(k):
        for i in range(k):
            j = (i + label_val) % k
            cross_edges.append((i, k + j))
    for (u, v) in cross_edges:
        idx = edge_to_idx[(min(u, v), max(u, v))]
        if timestamps[idx] == 0:
            timestamps[idx] = t
            t += 1

    # V+ internal edges (b_i, b_j): latest timestamps
    internal_plus = []
    for i in range(k):
        for j in range(i + 1, k):
            internal_plus.append((k + i, k + j))
    random.shuffle(internal_plus)
    for (u, v) in internal_plus:
        idx = edge_to_idx[(u, v)]
        if timestamps[idx] == 0:
            timestamps[idx] = t
            t += 1

    return n, edges, timestamps


def generate_random_biclique(k):
    """Generate a random non-dismountable-like bi-clique.
    V- = {0..k-1}, V+ = {k..2k-1}
    Internal V- edges: early timestamps
    Cross edges: middle timestamps
    Internal V+ edges: late timestamps
    """
    n = 2 * k
    edges = make_edges(n)
    m = len(edges)

    edge_to_idx = {}
    for i, (u, v) in enumerate(edges):
        edge_to_idx[(u, v)] = i
        edge_to_idx[(v, u)] = i

    # Classify edges
    internal_minus = [(u, v) for (u, v) in edges if u < k and v < k]
    cross = [(u, v) for (u, v) in edges if (u < k) != (v < k)]
    internal_plus = [(u, v) for (u, v) in edges if u >= k and v >= k]

    # Assign timestamps: internal- first, cross middle, internal+ last
    random.shuffle(internal_minus)
    random.shuffle(cross)
    random.shuffle(internal_plus)

    timestamps = [0] * m
    t = 1
    for (u, v) in internal_minus:
        timestamps[edge_to_idx[(u, v)]] = t
        t += 1
    for (u, v) in cross:
        timestamps[edge_to_idx[(u, v)]] = t
        t += 1
    for (u, v) in internal_plus:
        timestamps[edge_to_idx[(u, v)]] = t
        t += 1

    return n, edges, timestamps


def find_all_tree_paths(adj, a, b):
    results = []
    def dfs(node, target, visited, path):
        if node == target:
            results.append(list(path))
            return
        for nbr in adj.get(node, []):
            if nbr not in visited:
                visited.add(nbr)
                path.append(nbr)
                dfs(nbr, target, visited, path)
                path.pop()
                visited.discard(nbr)
    dfs(a, b, {a}, [a])
    return results


def path_timestamps(path, edge_map):
    return [edge_map[(path[i], path[i+1])] for i in range(len(path)-1)]


def is_nondecreasing(times):
    return all(times[i] <= times[i+1] for i in range(len(times)-1))


def check_three_cases(hub, a, b, tree_adj, edge_map, others):
    t_a_hub = edge_map[(a, hub)]
    t_hub_b = edge_map[(hub, b)]

    for path in find_all_tree_paths(tree_adj, a, b):
        times = path_timestamps(path, edge_map)
        if times and is_nondecreasing(times):
            return 'flat'

    for c in others:
        if c == a or c == b: continue
        if edge_map[(hub, c)] >= t_a_hub:
            for path in find_all_tree_paths(tree_adj, c, b):
                times = path_timestamps(path, edge_map)
                if times and times[0] >= edge_map[(hub, c)] and is_nondecreasing(times):
                    return 'steep_in'

    for c in others:
        if c == a or c == b: continue
        if edge_map[(c, hub)] <= t_hub_b:
            for path in find_all_tree_paths(tree_adj, a, c):
                times = path_timestamps(path, edge_map)
                if times and is_nondecreasing(times) and times[-1] <= edge_map[(c, hub)]:
                    return 'steep_out'

    for c1 in others:
        if c1 == a or c1 == b: continue
        t_c1_hub = edge_map[(c1, hub)]
        ok1 = False
        for path1 in find_all_tree_paths(tree_adj, a, c1):
            times1 = path_timestamps(path1, edge_map)
            if times1 and is_nondecreasing(times1) and times1[-1] <= t_c1_hub:
                ok1 = True; break
        if not ok1: continue
        for c2 in others:
            if c2 == a or c2 == b or c2 == c1: continue
            if edge_map[(hub, c2)] >= t_c1_hub:
                for path2 in find_all_tree_paths(tree_adj, c2, b):
                    times2 = path_timestamps(path2, edge_map)
                    if times2 and times2[0] >= edge_map[(hub, c2)] and is_nondecreasing(times2):
                        return 'decompose'

    return 'none'


def test_instance(n, edges, timestamps, label):
    m = len(edges)
    edge_map = {}
    for i, (u, v) in enumerate(edges):
        edge_map[(u, v)] = timestamps[i]
        edge_map[(v, u)] = timestamps[i]

    k = n // 2

    results = {'v_minus_hub': 0, 'v_plus_hub': 0, 'no_hub': 0,
               'cases': defaultdict(int), 'none_pairs': 0, 'total_reverse': 0}

    for hub in range(n):
        tree = exhaustive_hub_tree(n, edges, timestamps, hub)
        if tree is None:
            continue

        side = 'V-' if hub < k else 'V+'
        if hub < k:
            results['v_minus_hub'] += 1
        else:
            results['v_plus_hub'] += 1

        others = [v for v in range(n) if v != hub]
        tree_adj = defaultdict(set)
        for idx in tree:
            u, v = edges[idx]
            tree_adj[u].add(v)
            tree_adj[v].add(u)

        for a in others:
            for b in others:
                if a != b and edge_map[(a, hub)] > edge_map[(hub, b)]:
                    results['total_reverse'] += 1
                    case = check_three_cases(hub, a, b, tree_adj, edge_map, others)
                    results['cases'][case] += 1
                    if case == 'none':
                        results['none_pairs'] += 1

        # Only analyze first working hub
        return results

    results['no_hub'] = 1
    return results


def run_shifted_matching():
    print("=" * 70)
    print("SHIFTED MATCHING SM(k) — known hard non-dismountable bi-cliques")
    print("=" * 70)

    for k in [3, 4, 5, 6]:
        n, edges, ts = generate_shifted_matching(k)
        m = len(edges)
        print(f"\nSM({k}): n={n}, m={m}")

        r = test_instance(n, edges, ts, f"SM({k})")
        total_c = sum(r['cases'].values())
        print(f"  Hub found: V-={r['v_minus_hub']} V+={r['v_plus_hub']} none={r['no_hub']}")
        print(f"  Reverse pairs: {r['total_reverse']}")
        if total_c > 0:
            for case, count in sorted(r['cases'].items(), key=lambda x: -x[1]):
                print(f"    {case:>12s}: {count:>4d} ({count/total_c*100:.1f}%)")
        print(f"  NONE pairs: {r['none_pairs']}")


def run_random_bicliques():
    print("\n" + "=" * 70)
    print("RANDOM NON-DISMOUNTABLE BI-CLIQUES")
    print("=" * 70)

    for k, samples in [(3, 1000), (4, 500), (5, 200), (6, 50)]:
        n = 2 * k
        print(f"\nRandom bi-clique k={k} (n={n}), {samples} samples:")

        total_none = 0
        total_reverse = 0
        total_no_hub = 0
        case_totals = defaultdict(int)
        hub_side = {'V-': 0, 'V+': 0}

        for _ in range(samples):
            n2, edges, ts = generate_random_biclique(k)
            r = test_instance(n2, edges, ts, "random")
            total_reverse += r['total_reverse']
            total_none += r['none_pairs']
            total_no_hub += r['no_hub']
            hub_side['V-'] += r['v_minus_hub']
            hub_side['V+'] += r['v_plus_hub']
            for case, count in r['cases'].items():
                case_totals[case] += count

        total_c = sum(case_totals.values())
        print(f"  Hubs: V-={hub_side['V-']} V+={hub_side['V+']} none={total_no_hub}")
        print(f"  Total reverse pairs: {total_reverse}")
        if total_c > 0:
            for case, count in sorted(case_totals.items(), key=lambda x: -x[1]):
                print(f"    {case:>12s}: {count:>6d} ({count/total_c*100:.1f}%)")
        print(f"  NONE pairs: {total_none} ({total_none/total_reverse*100:.2f}%)" if total_reverse > 0 else "")


def main():
    random.seed(42)
    run_shifted_matching()
    run_random_bicliques()


if __name__ == "__main__":
    main()
