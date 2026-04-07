"""
Inductive tree construction with three-case verification.

At each step k:
- k vertices in the tree, adding vertex w via edge (w, c)
- This creates k new undirected pairs {w, v_i}, i.e. 2k directed pairs
- Some are forward (star covers), some are reverse
- For each candidate edge (w, c): do ALL new reverse pairs involving w
  fall into flat/steep-in/steep-out?

If yes at every step for some choice of edge: the induction works.
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


def find_all_tree_paths(adj, a, b):
    """All simple paths from a to b."""
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
    """Check if reverse pair (a,b) is covered by flat/steep-in/steep-out."""
    t_a_hub = edge_map[(a, hub)]
    t_hub_b = edge_map[(hub, b)]

    # FLAT
    for path in find_all_tree_paths(tree_adj, a, b):
        times = path_timestamps(path, edge_map)
        if times and is_nondecreasing(times):
            return 'flat'

    # STEEP IN: a→hub→c, tree c→b
    for c in others:
        if c == a or c == b:
            continue
        t_hub_c = edge_map[(hub, c)]
        if t_hub_c >= t_a_hub:
            for path in find_all_tree_paths(tree_adj, c, b):
                times = path_timestamps(path, edge_map)
                if times and times[0] >= t_hub_c and is_nondecreasing(times):
                    return 'steep_in'

    # STEEP OUT: tree a→c, c→hub→b
    for c in others:
        if c == a or c == b:
            continue
        t_c_hub = edge_map[(c, hub)]
        if t_c_hub <= t_hub_b:
            for path in find_all_tree_paths(tree_adj, a, c):
                times = path_timestamps(path, edge_map)
                if times and is_nondecreasing(times) and times[-1] <= t_c_hub:
                    return 'steep_out'

    # DECOMPOSE: steep_out ∘ steep_in
    for c1 in others:
        if c1 == a or c1 == b:
            continue
        t_c1_hub = edge_map[(c1, hub)]
        found_c1 = False
        for path1 in find_all_tree_paths(tree_adj, a, c1):
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
                for path2 in find_all_tree_paths(tree_adj, c2, b):
                    times2 = path_timestamps(path2, edge_map)
                    if times2 and times2[0] >= t_hub_c2 and is_nondecreasing(times2):
                        return 'decompose'

    return 'none'


def run(n, num_samples):
    edges = make_edges(n)
    m = len(edges)
    edge_idx = {}
    for i, (u, v) in enumerate(edges):
        edge_idx[(u, v)] = i
        edge_idx[(v, u)] = i

    print(f"\nK_{n}: {n} vertices, {m} edges")
    print("=" * 70)

    step_stats = defaultdict(lambda: {
        'total': 0,
        'has_valid_edge': 0,
        'min_valid_edges': float('inf'),
        'max_valid_edges': 0,
        'all_covered': 0,
    })

    total_success = 0
    total_fail = 0

    for trial in range(num_samples):
        ts = list(range(1, m + 1))
        random.shuffle(ts)

        edge_map = {}
        for i, (u, v) in enumerate(edges):
            edge_map[(u, v)] = ts[i]
            edge_map[(v, u)] = ts[i]

        # Try each hub
        found_hub = False
        for hub in range(n):
            others = [v for v in range(n) if v != hub]
            star_idx = set(i for i, (u, v) in enumerate(edges) if u == hub or v == hub)

            # Build tree inductively
            in_tree = set()
            tree_adj = defaultdict(set)
            tree_edge_indices = set()
            all_steps_ok = True

            for step in range(n - 2):
                not_in_tree = [w for w in others if w not in in_tree]
                if not not_in_tree:
                    break

                # For each candidate (w, c): check if ALL new reverse pairs are covered
                valid_edges = []

                for w in not_in_tree:
                    candidates = list(in_tree) if in_tree else [x for x in others if x != w]
                    for c in candidates:
                        # Temporarily add edge (w, c)
                        trial_adj = defaultdict(set, {k: set(v) for k, v in tree_adj.items()})
                        trial_adj[w].add(c)
                        trial_adj[c].add(w)
                        trial_in_tree = in_tree | {w}

                        # Check all NEW reverse pairs involving w
                        all_ok = True
                        for v2 in trial_in_tree:
                            if v2 == w:
                                continue
                            for (a, b) in [(w, v2), (v2, w)]:
                                if edge_map[(a, hub)] > edge_map[(hub, b)]:
                                    # Reverse pair
                                    case = check_three_cases(
                                        hub, a, b, trial_adj, edge_map,
                                        list(trial_in_tree))
                                    if case == 'none':
                                        all_ok = False
                                        break
                            if not all_ok:
                                break

                        if all_ok:
                            valid_edges.append((w, c))

                stats = step_stats[step + 1]
                stats['total'] += 1
                stats['min_valid_edges'] = min(stats['min_valid_edges'], len(valid_edges))
                stats['max_valid_edges'] = max(stats['max_valid_edges'], len(valid_edges))

                if valid_edges:
                    stats['has_valid_edge'] += 1
                    # Pick the first valid edge
                    w, c = valid_edges[0]
                    in_tree.add(w)
                    tree_adj[w].add(c)
                    tree_adj[c].add(w)
                    idx = edge_idx.get((w, c)) or edge_idx.get((c, w))
                    tree_edge_indices.add(idx)
                else:
                    all_steps_ok = False
                    break

            if all_steps_ok and len(in_tree) == n - 2:
                # Verify: does this tree actually span?
                all_edges = star_idx | tree_edge_indices
                timed = sorted([(ts[i], edges[i][0], edges[i][1]) for i in range(m)])
                target = compute_reachability(n, timed)
                sub = sorted([(ts[i], edges[i][0], edges[i][1]) for i in all_edges])
                if compute_reachability(n, sub) == target:
                    total_success += 1
                    found_hub = True
                    break

            # Also check: did we get stuck at some step?
            if not all_steps_ok:
                # Try remaining vertices with ANY edge
                pass

        if not found_hub:
            total_fail += 1

        if (trial + 1) % max(1, num_samples // 5) == 0:
            print(f"  {trial+1}/{num_samples}: success={total_success} fail={total_fail}")

    total = total_success + total_fail
    print(f"\nResults: {total_success}/{total} ({total_success/total*100:.1f}%)")

    print(f"\nPer-step statistics:")
    print(f"{'step':>5s}  {'total':>6s}  {'has_valid':>10s}  {'min_valid':>10s}  {'max_valid':>10s}")
    print("-" * 50)
    for step in sorted(step_stats):
        s = step_stats[step]
        mv = s['min_valid_edges'] if s['min_valid_edges'] < float('inf') else 0
        print(f"{step:>5d}  {s['total']:>6d}  {s['has_valid_edge']:>10d}  "
              f"{mv:>10d}  {s['max_valid_edges']:>10d}")


def main():
    random.seed(42)
    for n, samples in [(5, 2000), (6, 500), (7, 100)]:
        run(n, samples)


if __name__ == "__main__":
    main()
