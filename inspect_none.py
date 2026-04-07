"""
Inspect the 'none' pairs that don't fit flat, steep_in, steep_out, or decompose.

For each none pair, trace the actual journey and show every detail:
- The hub, the tree, the star
- The timestamp matrix
- Why each of the three cases fails
- What route the reachability algorithm actually uses
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
    reached_by = [dict() for _ in range(n)]
    path_to = [dict() for _ in range(n)]
    for i in range(n):
        reached_by[i][i] = 0
        path_to[i][i] = []
    for t, u, v in timed_edges:
        sources_u = {s: arr for s, arr in reached_by[u].items() if arr <= t}
        for s, arr in sources_u.items():
            if s not in reached_by[v] or t < reached_by[v][s]:
                reached_by[v][s] = t
                path_to[v][s] = path_to[u][s] + [(t, u, v)]
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


def find_tree_path(adj, a, b):
    parent = {a: None}
    queue = [a]
    while queue:
        node = queue.pop(0)
        for nbr in adj[node]:
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


def path_timestamps(path, edge_map):
    return [edge_map[(path[i], path[i+1])] for i in range(len(path)-1)]


def is_nondecreasing(times):
    return all(times[i] <= times[i+1] for i in range(len(times)-1))


def is_none_pair(n, hub, a, b, tree_adj, edge_map, others):
    """Check all three cases + decompose. Return True if none work."""
    t_a_hub = edge_map[(a, hub)]
    t_hub_b = edge_map[(hub, b)]

    # FLAT
    tp = find_tree_path(tree_adj, a, b)
    if tp:
        times = path_timestamps(tp, edge_map)
        if times and is_nondecreasing(times):
            return False

    # STEEP IN
    for c in others:
        if c == a or c == b:
            continue
        t_hub_c = edge_map[(hub, c)]
        if t_hub_c >= t_a_hub:
            tp2 = find_tree_path(tree_adj, c, b)
            if tp2:
                times2 = path_timestamps(tp2, edge_map)
                if times2 and times2[0] >= t_hub_c and is_nondecreasing(times2):
                    return False

    # STEEP OUT
    for c in others:
        if c == a or c == b:
            continue
        t_c_hub = edge_map[(c, hub)]
        if t_c_hub <= t_hub_b:
            tp2 = find_tree_path(tree_adj, a, c)
            if tp2:
                times2 = path_timestamps(tp2, edge_map)
                if times2 and is_nondecreasing(times2) and times2[-1] <= t_c_hub:
                    return False

    # DECOMPOSE
    for c1 in others:
        if c1 == a or c1 == b:
            continue
        t_c1_hub = edge_map[(c1, hub)]
        tp1 = find_tree_path(tree_adj, a, c1)
        if not tp1:
            continue
        times1 = path_timestamps(tp1, edge_map)
        if not (times1 and is_nondecreasing(times1) and times1[-1] <= t_c1_hub):
            continue
        for c2 in others:
            if c2 == a or c2 == b or c2 == c1:
                continue
            t_hub_c2 = edge_map[(hub, c2)]
            if t_hub_c2 >= t_c1_hub:
                tp2 = find_tree_path(tree_adj, c2, b)
                if tp2:
                    times2 = path_timestamps(tp2, edge_map)
                    if times2 and times2[0] >= t_hub_c2 and is_nondecreasing(times2):
                        return False

    return True


def run(n, num_samples):
    edges = make_edges(n)
    m = len(edges)
    print(f"\nK_{n}: {n} vertices, {m} edges")
    print("=" * 70)

    none_examples = []

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

        others = [v for v in range(n) if v != hub]
        tree_adj = defaultdict(set)
        for idx in tree:
            u, v = edges[idx]
            tree_adj[u].add(v)
            tree_adj[v].add(u)

        star_idx = set(i for i, (u, v) in enumerate(edges) if u == hub or v == hub)
        used = star_idx | set(tree)
        spanner_timed = sorted([(ts[i], edges[i][0], edges[i][1]) for i in used])
        _, path_to = compute_reachability_with_trace(n, spanner_timed)

        for a in others:
            for b in others:
                if a != b and edge_map[(a, hub)] > edge_map[(hub, b)]:
                    if is_none_pair(n, hub, a, b, tree_adj, edge_map, others):
                        journey = path_to[b].get(a, [])
                        none_examples.append({
                            'hub': hub, 'a': a, 'b': b,
                            'ts': ts[:], 'tree': tree[:],
                            'journey': journey,
                            'edge_map': dict(edge_map),
                            'others': others[:],
                            'tree_adj': {k: list(v) for k, v in tree_adj.items()},
                        })

    print(f"\nFound {len(none_examples)} 'none' pairs")

    for idx, ex in enumerate(none_examples[:10]):
        hub = ex['hub']
        a, b = ex['a'], ex['b']
        em = ex['edge_map']
        others = ex['others']
        ta = ex['tree_adj']

        print(f"\n{'='*60}")
        print(f"Example {idx+1}: hub={hub}, pair=({a}→{b})")
        print(f"  t(a,hub)={em[(a,hub)]}, t(hub,b)={em[(hub,b)]}  [REVERSE]")

        # Show timestamp matrix
        print(f"\n  Timestamp matrix:")
        header = "     " + "".join(f"{j:>4d}" for j in range(n))
        print(f"  {header}")
        for i in range(n):
            row = f"  {i:>3d}:"
            for j in range(n):
                if i == j:
                    row += "   ."
                else:
                    row += f"{em[(i,j)]:>4d}"
            marker = " <-- HUB" if i == hub else ""
            print(f"  {row}{marker}")

        # Show star and tree edges
        star_edges = [(hub, u, em[(hub,u)]) for u in others]
        star_edges.sort(key=lambda x: x[2])
        print(f"\n  Star edges (sorted by time): ", end="")
        for _, u, t in star_edges:
            print(f"hub-{u}@{t} ", end="")
        print()

        tree_edges = []
        for idx2 in ex['tree']:
            u, v = edges[idx2]
            tree_edges.append((u, v, em[(u,v)]))
        tree_edges.sort(key=lambda x: x[2])
        print(f"  Tree edges (sorted by time): ", end="")
        for u, v, t in tree_edges:
            print(f"{u}-{v}@{t} ", end="")
        print()

        # Show why each case fails
        print(f"\n  Why FLAT fails:")
        tp = find_tree_path(ta, a, b)
        if tp:
            times = path_timestamps(tp, em)
            print(f"    Tree path {tp}: times={times}")
            for i in range(len(times)-1):
                if times[i] > times[i+1]:
                    print(f"    DECREASING at step {i}: {times[i]} > {times[i+1]}")
        else:
            print(f"    No tree path from {a} to {b}")

        print(f"\n  Why STEEP_IN fails (a→hub→c→...→b):")
        print(f"    Need c where t(hub,c) ≥ t(a,hub)={em[(a,hub)]}")
        for c in others:
            if c == a or c == b:
                continue
            t_hub_c = em[(hub, c)]
            if t_hub_c >= em[(a, hub)]:
                tp2 = find_tree_path(ta, c, b)
                if tp2:
                    times2 = path_timestamps(tp2, em)
                    print(f"    c={c}: t(hub,c)={t_hub_c}, tree {c}→{b} path={tp2} times={times2}", end="")
                    if times2 and times2[0] < t_hub_c:
                        print(f"  FAIL: first edge {times2[0]} < {t_hub_c}")
                    elif times2 and not is_nondecreasing(times2):
                        print(f"  FAIL: not non-decreasing")
                    else:
                        print(f"  ???")
            else:
                pass  # t(hub,c) too small

        print(f"\n  Why STEEP_OUT fails (a→...→c→hub→b):")
        print(f"    Need c where t(c,hub) ≤ t(hub,b)={em[(hub,b)]}")
        for c in others:
            if c == a or c == b:
                continue
            t_c_hub = em[(c, hub)]
            if t_c_hub <= em[(hub, b)]:
                tp2 = find_tree_path(ta, a, c)
                if tp2:
                    times2 = path_timestamps(tp2, em)
                    print(f"    c={c}: t(c,hub)={t_c_hub}, tree {a}→{c} path={tp2} times={times2}", end="")
                    if times2 and not is_nondecreasing(times2):
                        print(f"  FAIL: not non-decreasing")
                    elif times2 and times2[-1] > t_c_hub:
                        print(f"  FAIL: last edge {times2[-1]} > {t_c_hub}")
                    else:
                        print(f"  ???")

        # Show actual journey
        journey = ex['journey']
        if journey:
            print(f"\n  Actual journey:")
            for (t, frm, to) in journey:
                is_star = (frm == hub or to == hub)
                label = "STAR" if is_star else "TREE"
                print(f"    {frm}→{to} @ t={t}  [{label}]")
        else:
            print(f"\n  No journey found (BUG?)")


def main():
    random.seed(42)
    for n, samples in [(5, 10000), (6, 2000)]:
        run(n, samples)


if __name__ == "__main__":
    main()
