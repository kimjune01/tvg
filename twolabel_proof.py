"""
2-label temporal K_n: prove minimum spanner is small.

Question: what's the tight bound?
- n - 1 (just spanning tree) — probably insufficient
- n (close to lower bound)
- n + 1 (one fix-up edge)
- n + 2

Verify empirically what the tight bound is, then attempt proof.

Spanner = subset of EDGES (each selected edge contributes both labels).
"""

import random
from itertools import combinations

random.seed(42)


def compute_reachability_2label(n, edge_labels):
    """edge_labels: dict {(u,v): [t1, t2]}.
    Each edge contributes 2 time events."""
    expanded = []
    for (u, v), labels in edge_labels.items():
        for t in labels:
            expanded.append((t, u, v))

    reached_by = [dict() for _ in range(n)]
    for i in range(n):
        reached_by[i][i] = 0
    for t, u, v in sorted(expanded):
        sources_u = {s: arr for s, arr in reached_by[u].items() if arr <= t}
        sources_v = {s: arr for s, arr in reached_by[v].items() if arr <= t}
        for s, arr in sources_u.items():
            if s not in reached_by[v] or t < reached_by[v][s]:
                reached_by[v][s] = t
        for s, arr in sources_v.items():
            if s not in reached_by[u] or t < reached_by[u][s]:
                reached_by[u][s] = t
    pairs = set()
    for v in range(n):
        for s in reached_by[v]:
            if s != v:
                pairs.add((s, v))
    return pairs


def min_spanner_2label(n, edge_labels):
    """Find minimum spanner size by exhaustive search (small n only)."""
    full_reach = compute_reachability_2label(n, edge_labels)
    edges = list(edge_labels.keys())
    m = len(edges)

    for size in range(n - 1, m + 1):
        for subset in combinations(range(m), size):
            sub_labels = {edges[i]: edge_labels[edges[i]] for i in subset}
            if compute_reachability_2label(n, sub_labels) == full_reach:
                return size, subset
    return m, list(range(m))


def greedy_spanner_2label(n, edge_labels, hub=None):
    """Greedy: start with star (or empty), add edges one at a time."""
    full_reach = compute_reachability_2label(n, edge_labels)

    if hub is None:
        # Try all hubs
        best_size = n * n
        best_edges = None
        for h in range(n):
            size, edges = greedy_spanner_2label(n, edge_labels, hub=h)
            if size < best_size:
                best_size = size
                best_edges = edges
        return best_size, best_edges

    star = {(min(hub, v), max(hub, v)) for v in range(n) if v != hub}
    current = set(star)
    non_star = [e for e in edge_labels if e not in star]

    while True:
        sub_labels = {e: edge_labels[e] for e in current}
        cur_reach = compute_reachability_2label(n, sub_labels)
        if cur_reach == full_reach:
            break
        cur_count = len(cur_reach)
        best_e, best_g = None, 0
        for e in non_star:
            if e in current:
                continue
            trial_labels = {ee: edge_labels[ee] for ee in current | {e}}
            tr = compute_reachability_2label(n, trial_labels)
            g = len(tr) - cur_count
            if g > best_g:
                best_g = g
                best_e = e
        if best_e is None or best_g <= 0:
            break
        current.add(best_e)

    sub_labels = {e: edge_labels[e] for e in current}
    final = compute_reachability_2label(n, sub_labels)
    if final == full_reach:
        return len(current), current
    return n * n, current


def main():
    print("2-label K_n: minimum spanner size")
    print("=" * 60)
    print(f"{'n':>3} {'samples':>8} {'mean':>6} {'min':>4} {'max':>4} "
          f"{'all=n-1':>9} {'all=n':>7} {'all≤n+1':>8}")
    print("-" * 60)

    for n in range(4, 10):
        m_pairs = n * (n - 1) // 2
        total_labels = 2 * m_pairs
        samples = 100 if n <= 6 else 30

        # Use exact for small n (≤5), greedy for larger
        sizes = []
        spanning_tree_works = 0
        size_n_works = 0
        size_n1_works = 0

        for trial in range(samples):
            all_ts = list(range(1, total_labels + 1))
            random.shuffle(all_ts)
            edge_labels = {}
            idx = 0
            for i in range(n):
                for j in range(i + 1, n):
                    edge_labels[(i, j)] = sorted([all_ts[idx], all_ts[idx + 1]])
                    idx += 2

            if n <= 5:
                size, _ = min_spanner_2label(n, edge_labels)
            else:
                size, _ = greedy_spanner_2label(n, edge_labels)

            sizes.append(size)
            if size <= n - 1:
                spanning_tree_works += 1
            if size <= n:
                size_n_works += 1
            if size <= n + 1:
                size_n1_works += 1

        avg = sum(sizes) / len(sizes)
        mn = min(sizes)
        mx = max(sizes)
        print(f"{n:3d} {samples:8d} {avg:6.2f} {mn:4d} {mx:4d} "
              f"{100*spanning_tree_works/samples:8.0f}% "
              f"{100*size_n_works/samples:6.0f}% "
              f"{100*size_n1_works/samples:7.0f}%")


if __name__ == '__main__':
    main()
