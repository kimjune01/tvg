"""
Check Laman sparsity on greedy-minimal temporal spanners.

Laman condition: a graph on n vertices is minimally rigid in 2D iff
1. It has exactly 2n-3 edges
2. Every subgraph on k ≥ 2 vertices has at most 2k-3 edges

If temporal spanners satisfy this, the matroid theory explains everything.

Also check:
- Does the greedy spanner satisfy Laman sparsity?
- Which subgraphs are tight (exactly 2k-3)?
- Is the spanner a Laman graph (minimally rigid)?
- Henneberg decomposition: can the spanner be built by Henneberg moves?
"""

import random
from itertools import combinations


def make_temporal_clique(n):
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
    m = len(edges)
    ts = list(range(1, m + 1))
    random.shuffle(ts)
    return edges, ts


def make_sm_clique(k):
    n = 2 * k
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
    m = len(edges)
    eidx = {}
    for i, (u, v) in enumerate(edges):
        eidx[(u, v)] = i
        eidx[(v, u)] = i
    ts = [0] * m
    t = 1
    for i in range(k):
        for j in range(i + 1, k):
            ts[eidx[(i, j)]] = t; t += 1
    for d in range(k):
        for i in range(k):
            j = (i + d) % k
            ts[eidx[(min(i, k + j), max(i, k + j))]] = t; t += 1
    for i in range(k):
        for j in range(i + 1, k):
            ts[eidx[(k + i, k + j)]] = t; t += 1
    return edges, ts


def compute_reachability(n, edge_indices, edges, timestamps):
    timed = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in edge_indices])
    reach = [{v: 0} for v in range(n)]
    for t, u, v in timed:
        new_v = {}
        new_u = {}
        for s, arr in reach[u].items():
            if arr <= t and (s not in reach[v] or t < reach[v][s]):
                new_v[s] = t
        for s, arr in reach[v].items():
            if arr <= t and (s not in reach[u] or t < reach[u][s]):
                new_u[s] = t
        reach[v].update(new_v)
        reach[u].update(new_u)
    R = set()
    for v in range(n):
        for s in reach[v]:
            if s != v:
                R.add((s, v))
    return R


def greedy_spanner(n, edges, timestamps):
    m = len(edges)
    target = compute_reachability(n, list(range(m)), edges, timestamps)
    included = list(range(m))
    for idx in sorted(range(m), key=lambda i: -timestamps[i]):
        trial = [i for i in included if i != idx]
        if compute_reachability(n, trial, edges, timestamps) == target:
            included = trial
    return included


def check_laman_sparsity(n, spanner_edges):
    """Check if the spanner satisfies Laman sparsity:
    every subgraph on k >= 2 vertices has <= 2k-3 edges.
    Returns (is_laman, worst_violation, tight_subgraphs).
    """
    violations = []
    tight = []

    for k in range(2, n + 1):
        for subset in combinations(range(n), k):
            subset_set = set(subset)
            # Count edges within this subset
            edge_count = sum(1 for u, v in spanner_edges
                           if u in subset_set and v in subset_set)
            bound = 2 * k - 3
            if edge_count > bound:
                violations.append((subset, edge_count, bound))
            elif edge_count == bound and k >= 2:
                tight.append((subset, edge_count))

    return len(violations) == 0, violations, tight


def check_laman_exact(n, spanner_edges):
    """Check both conditions: |E| = 2n-3 AND sparsity."""
    m = len(spanner_edges)
    target = 2 * n - 3
    has_right_count = (m == target)
    is_sparse, violations, tight = check_laman_sparsity(n, spanner_edges)
    return has_right_count and is_sparse, has_right_count, is_sparse, violations, tight


def vertex_degrees(n, spanner_edges):
    deg = [0] * n
    for u, v in spanner_edges:
        deg[u] += 1
        deg[v] += 1
    return deg


def is_2_connected(n, edge_list):
    """Check if graph is 2-edge-connected (no bridge)."""
    if not edge_list:
        return False
    adj = [[] for _ in range(n)]
    for u, v in edge_list:
        adj[u].append(v)
        adj[v].append(u)

    # Check connectivity first
    visited = set()
    stack = [0]
    while stack:
        v = stack.pop()
        if v in visited:
            continue
        visited.add(v)
        for w in adj[v]:
            if w not in visited:
                stack.append(w)
    if len(visited) != n:
        return False

    # Check for bridges using DFS
    disc = [-1] * n
    low = [-1] * n
    bridges = []
    timer = [0]

    def dfs(u, parent):
        disc[u] = low[u] = timer[0]
        timer[0] += 1
        for v in adj[u]:
            if disc[v] == -1:
                dfs(v, u)
                low[u] = min(low[u], low[v])
                if low[v] > disc[u]:
                    bridges.append((u, v))
            elif v != parent:
                low[u] = min(low[u], disc[v])

    dfs(0, -1)
    return len(bridges) == 0


def main():
    random.seed(42)

    print("LAMAN SPARSITY CHECK ON TEMPORAL SPANNERS")
    print("=" * 70)

    # SM(k)
    print("\n--- SM(k) greedy spanners ---\n")
    for k in range(3, 8):
        n = 2 * k
        edges, ts = make_sm_clique(k)

        if n <= 14:
            spanner_idx = greedy_spanner(n, edges, ts)
        else:
            continue

        spanner_edges = [edges[i] for i in spanner_idx]
        is_laman, has_count, is_sparse, violations, tight = \
            check_laman_exact(n, spanner_edges)

        degs = vertex_degrees(n, spanner_edges)
        two_conn = is_2_connected(n, spanner_edges)

        print(f"SM({k}): n={n}, |E|={len(spanner_idx)}, 2n-3={2*n-3}")
        print(f"  Laman count (|E|=2n-3): {has_count}")
        print(f"  Laman sparse: {is_sparse}")
        print(f"  IS LAMAN: {is_laman}")
        print(f"  2-edge-connected: {two_conn}")
        print(f"  Degrees: {degs}")
        if violations:
            print(f"  VIOLATIONS ({len(violations)}):")
            for subset, ec, bound in violations[:5]:
                print(f"    vertices {subset}: {ec} edges > {bound} bound")
        if tight:
            print(f"  Tight subgraphs ({len(tight)}):")
            for subset, ec in tight[:10]:
                print(f"    vertices {subset}: {ec} edges = 2*{len(subset)}-3={ec}")
        print()

    # Random temporal cliques
    print("\n--- Random temporal cliques ---\n")
    for n in [6, 8, 10, 12]:
        samples = {6: 500, 8: 200, 10: 50, 12: 20}[n]
        laman_count = 0
        sparse_count = 0
        right_size_count = 0
        violation_sizes = []
        max_violation = 0

        for s in range(samples):
            edges, ts = make_temporal_clique(n)
            spanner_idx = greedy_spanner(n, edges, ts)
            spanner_edges = [edges[i] for i in spanner_idx]

            is_laman, has_count, is_sparse, violations, tight = \
                check_laman_exact(n, spanner_edges)

            if has_count:
                right_size_count += 1
            if is_sparse:
                sparse_count += 1
            if is_laman:
                laman_count += 1
            if violations:
                worst = max(ec - bound for _, ec, bound in violations)
                violation_sizes.append(worst)
                max_violation = max(max_violation, worst)

            if (s + 1) % max(1, samples // 5) == 0:
                print(f"  n={n}: {s+1}/{samples}...", flush=True)

        print(f"\nn={n} ({samples} samples):")
        print(f"  |E| = 2n-3 = {2*n-3}: {right_size_count}/{samples} "
              f"({100*right_size_count/samples:.1f}%)")
        print(f"  Laman sparse: {sparse_count}/{samples} "
              f"({100*sparse_count/samples:.1f}%)")
        print(f"  Full Laman: {laman_count}/{samples} "
              f"({100*laman_count/samples:.1f}%)")
        if violation_sizes:
            print(f"  Violations: {len(violation_sizes)} spanners, "
                  f"max excess={max_violation}")
        print()

    # Deep dive: one specific spanner
    print("\n--- Deep dive: SM(4) spanner structure ---\n")
    k = 4
    n = 2 * k
    edges, ts = make_sm_clique(k)
    spanner_idx = greedy_spanner(n, edges, ts)
    spanner_edges = [edges[i] for i in spanner_idx]

    print(f"Spanner edges ({len(spanner_edges)}):")
    for idx in spanner_idx:
        u, v = edges[idx]
        t = ts[idx]
        etype = "V-" if u < k and v < k else ("V+" if u >= k and v >= k else "cross")
        print(f"  ({u},{v}) t={t} [{etype}]")

    _, _, _, _, tight = check_laman_exact(n, spanner_edges)
    print(f"\nTight subgraphs (|E|=2k-3 for k vertices):")
    for subset, ec in sorted(tight, key=lambda x: len(x[0])):
        print(f"  k={len(subset)}: vertices {subset}, {ec} edges")


if __name__ == "__main__":
    main()
