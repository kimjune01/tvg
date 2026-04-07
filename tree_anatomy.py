"""
Anatomy of winning trees.

For each instance, exhaustive search finds a tree that works.
What do these trees look like? What's the pattern?

Questions:
- Are winning tree edges early, late, or mixed?
- Do they form a path, star, or something else?
- How do tree edge timestamps relate to the hub's star timestamps?
- Is there a simple rule that always picks a winning tree?
"""

import random
from itertools import combinations
from collections import Counter


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


def exhaustive_tree(n, edges, timestamps, hub):
    """Find ALL working trees for this hub."""
    m = len(edges)
    timed = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in range(m)])
    target = compute_reachability(n, timed)
    star_idx = set(i for i, (u, v) in enumerate(edges) if u == hub or v == hub)
    tree_candidates = [i for i in range(m) if i not in star_idx]

    winners = []
    # Try subsets of size n-2
    for subset in combinations(tree_candidates, n - 2):
        used = star_idx | set(subset)
        sub = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in used])
        reach = compute_reachability(n, sub)
        if reach == target:
            winners.append(list(subset))
    return winners


def tree_structure(n, edges, timestamps, hub, tree_indices):
    """Characterize a tree's structure relative to the hub."""
    m = len(edges)
    edge_map = {}
    for i, (u, v) in enumerate(edges):
        edge_map[(u, v)] = timestamps[i]
        edge_map[(v, u)] = timestamps[i]

    others = sorted([v for v in range(n) if v != hub])
    # Hub's star timestamps
    star_times = {u: edge_map[(hub, u)] for u in others}

    # Tree edge info
    tree_info = []
    for idx in tree_indices:
        u, v = edges[idx]
        t = timestamps[idx]
        # Relative to star: is t before, between, or after the star times
        # of u and v?
        su = star_times[u]
        sv = star_times[v]
        rel_u = "before" if t < su else ("after" if t > su else "equal")
        rel_v = "before" if t < sv else ("after" if t > sv else "equal")
        tree_info.append({
            'edge': (u, v), 'time': t,
            'star_u': su, 'star_v': sv,
            'rel_u': rel_u, 'rel_v': rel_v,
            'between': min(su, sv) < t < max(su, sv),
        })

    return tree_info


def analyze_tree_timestamps(n, edges, timestamps, hub, tree_indices):
    """Where do tree timestamps sit relative to the star?"""
    m = len(edges)
    star_idx = [i for i, (u, v) in enumerate(edges) if u == hub or v == hub]
    star_times = sorted([timestamps[i] for i in star_idx])
    tree_times = sorted([timestamps[i] for i in tree_indices])

    star_min, star_max = star_times[0], star_times[-1]
    star_median = star_times[len(star_times) // 2]

    # Tree times relative to star range
    below = sum(1 for t in tree_times if t < star_min)
    above = sum(1 for t in tree_times if t > star_max)
    inside = sum(1 for t in tree_times if star_min <= t <= star_max)

    # Tree times relative to star median
    early = sum(1 for t in tree_times if t < star_median)
    late = sum(1 for t in tree_times if t > star_median)

    return {
        'below_star': below,
        'inside_star': inside,
        'above_star': above,
        'early': early,
        'late': late,
        'tree_times': tree_times,
        'star_range': (star_min, star_max),
    }


def is_spanning_tree(n, hub, edges, tree_indices):
    """Check if tree_indices form a spanning tree on V \ {hub}."""
    others = set(v for v in range(n) if v != hub)
    tree_edges = [edges[i] for i in tree_indices]

    # Check connectivity
    adj = {v: set() for v in others}
    for u, v in tree_edges:
        if u in others and v in others:
            adj[u].add(v)
            adj[v].add(u)

    if not adj:
        return False

    start = next(iter(others))
    visited = set()
    stack = [start]
    while stack:
        v = stack.pop()
        if v in visited:
            continue
        visited.add(v)
        for w in adj[v]:
            if w not in visited:
                stack.append(w)

    return visited == others


def run(n, num_samples):
    edges = make_edges(n)
    m = len(edges)
    print(f"\nK_{n}: {n} vertices, {m} edges")
    print("=" * 70)

    # Aggregate stats
    position_counts = Counter()  # below/inside/above
    tree_is_spanning = 0
    tree_not_spanning = 0
    total_trees_found = 0

    # Degree distribution in winning trees
    degree_in_tree = Counter()

    # Timestamp ordering pattern
    timestamp_patterns = Counter()

    for trial in range(num_samples):
        ts = list(range(1, m + 1))
        random.shuffle(ts)

        # Find best hub (most winning trees)
        best_hub = None
        best_trees = []
        for v in range(n):
            trees = exhaustive_tree(n, edges, ts, v)
            if len(trees) > len(best_trees):
                best_trees = trees
                best_hub = v

        if not best_trees:
            continue

        # Analyze the first winning tree
        tree = best_trees[0]
        total_trees_found += 1

        # Is it a spanning tree?
        if is_spanning_tree(n, best_hub, edges, tree):
            tree_is_spanning += 1
        else:
            tree_not_spanning += 1

        # Timestamp positions
        pos = analyze_tree_timestamps(n, edges, ts, best_hub, tree)
        position_counts['below'] += pos['below_star']
        position_counts['inside'] += pos['inside_star']
        position_counts['above'] += pos['above_star']

        # Degree distribution
        others = [v for v in range(n) if v != best_hub]
        deg = Counter()
        for idx in tree:
            u, v = edges[idx]
            deg[u] += 1
            deg[v] += 1
        max_deg = max(deg.values()) if deg else 0
        degree_in_tree[max_deg] += 1

        # Timestamp pattern: sort tree edges by time, record which
        # endpoint has the earlier star time
        tree_info = tree_structure(n, edges, ts, best_hub, tree)
        pattern = []
        for info in sorted(tree_info, key=lambda x: x['time']):
            u, v = info['edge']
            if info['star_u'] < info['star_v']:
                pattern.append('early-late')
            elif info['star_u'] > info['star_v']:
                pattern.append('late-early')
            else:
                pattern.append('same')
        timestamp_patterns[tuple(pattern)] += 1

    print(f"\nAnalyzed {total_trees_found} winning trees")

    total_edges = position_counts['below'] + position_counts['inside'] + position_counts['above']
    if total_edges > 0:
        print(f"\nTree edge timestamps relative to star range:")
        for pos in ['below', 'inside', 'above']:
            c = position_counts[pos]
            print(f"  {pos:>8s}: {c:>6d} ({c/total_edges*100:.1f}%)")

    print(f"\nTree is spanning tree of K_{{n-1}}\\hub:")
    print(f"  Yes: {tree_is_spanning}  No: {tree_not_spanning}")

    print(f"\nMax degree in tree:")
    for d in sorted(degree_in_tree):
        print(f"  deg={d}: {degree_in_tree[d]}")

    print(f"\nTop 10 timestamp patterns (tree edges by time, endpoint star-time order):")
    for pattern, count in timestamp_patterns.most_common(10):
        print(f"  {count:>5d}  {pattern}")

    # Detailed examples
    print(f"\nDetailed examples:")
    random.seed(42)
    for ex in range(3):
        ts = list(range(1, m + 1))
        random.shuffle(ts)

        edge_map = {}
        for i, (u, v) in enumerate(edges):
            edge_map[(u, v)] = ts[i]
            edge_map[(v, u)] = ts[i]

        for hub in range(n):
            trees = exhaustive_tree(n, edges, ts, hub)
            if trees:
                tree = trees[0]
                others = sorted([v for v in range(n) if v != hub])
                print(f"\n  Example {ex+1}, hub={hub}:")
                print(f"    Star edges: ", end="")
                for u in others:
                    print(f"({hub},{u})@{edge_map[(hub,u)]}  ", end="")
                print()
                print(f"    Tree edges: ", end="")
                for idx in tree:
                    u, v = edges[idx]
                    print(f"({u},{v})@{ts[idx]}  ", end="")
                print()

                # Show which pairs the star covers vs tree covers
                star_covers = []
                tree_covers = []
                for a in others:
                    for b in others:
                        if a != b:
                            if edge_map[(a, hub)] <= edge_map[(hub, b)]:
                                star_covers.append((a, b))
                            else:
                                tree_covers.append((a, b))
                print(f"    Star covers {len(star_covers)} forward pairs")
                print(f"    Tree must cover {len(tree_covers)} reverse pairs")
                break


def main():
    random.seed(42)
    for n, samples in [(5, 3000), (6, 500)]:
        run(n, samples)


if __name__ == "__main__":
    main()
