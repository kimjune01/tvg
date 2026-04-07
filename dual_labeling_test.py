"""
Test: does the minimum spanner have a spanning tree where each edge
serves dual temporal roles (in-tree + out-tree)?

The Mertzios labeling: 2n-3 labels on n-1 tree edges.
The spanner: 2n-4 underlying edges selected from K_n.

Questions:
1. Does the min spanner contain a spanning tree?
2. If so, how many spanner edges are tree edges vs non-tree?
3. For each tree edge, does it participate in both "early" and "late" journeys?
4. Can we identify a pivot edge (single role) vs dual-role edges?
"""

import random
from itertools import combinations


def make_temporal_clique(n, seed=None):
    if seed is not None:
        random.seed(seed)
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
    m = len(edges)
    ts = list(range(1, m + 1))
    random.shuffle(ts)
    return edges, ts


def compute_reachability(n, edge_indices, edges, timestamps):
    timed = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in edge_indices])
    reach = [{v: 0} for v in range(n)]
    for t, u, v in timed:
        new_v, new_u = {}, {}
        for s, arr in reach[u].items():
            if arr <= t and (s not in reach[v] or t < reach[v][s]):
                new_v[s] = t
        for s, arr in reach[v].items():
            if arr <= t and (s not in reach[u] or t < reach[u][s]):
                new_u[s] = t
        reach[v].update(new_v)
        reach[u].update(new_u)
    return set((s, v) for v in range(n) for s in reach[v] if s != v)


def find_min_spanner(n, edges, timestamps, trials=200):
    m = len(edges)
    target = compute_reachability(n, list(range(m)), edges, timestamps)
    best = list(range(m))
    for _ in range(trials):
        order = list(range(m))
        random.shuffle(order)
        included = list(range(m))
        for idx in order:
            trial = [i for i in included if i != idx]
            if compute_reachability(n, trial, edges, timestamps) == target:
                included = trial
        if len(included) < len(best):
            best = included
    return best


def contains_spanning_tree(n, spanner_edges):
    """Check if spanner edges contain a spanning tree. Return all spanning trees."""
    # Find ANY spanning tree via BFS/Kruskal on the spanner
    adj = [[] for _ in range(n)]
    for u, v in spanner_edges:
        adj[u].append((v, (u, v)))
        adj[v].append((u, (u, v)))

    # BFS tree
    visited = {0}
    queue = [0]
    tree_edges = []
    while queue:
        node = queue.pop(0)
        for neighbor, edge in adj[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
                tree_edges.append(edge)

    if len(visited) < n:
        return False, []
    return True, tree_edges


def count_journey_roles(n, edges, timestamps, spanner_idx, edge_idx):
    """For a specific spanner edge, count how many (source, dest) pairs
    use this edge in their EARLIEST journey vs LATEST journey."""
    m_spanner = len(spanner_idx)
    target = compute_reachability(n, spanner_idx, edges, timestamps)

    e_u, e_v = edges[edge_idx]
    e_t = timestamps[edge_idx]

    # Count pairs where this edge is on some temporal journey
    # and classify by direction: source→e (early role) vs e→dest (late role)
    early_role = 0  # pairs where source reaches e_u or e_v, then crosses e
    late_role = 0   # pairs where e leads to dest via e_u or e_v after crossing e

    # Simpler: for each source s, does the earliest arrival at any vertex
    # USE this edge? Count sources that route through this edge.

    # Even simpler: remove this edge, see which pairs break.
    # Those pairs DEPEND on this edge.
    remaining = [i for i in spanner_idx if i != edge_idx]
    reduced = compute_reachability(n, remaining, edges, timestamps)
    dependent_pairs = target - reduced

    # For each dependent pair, classify:
    # - source is in {e_u, e_v} → "outbound" (late role)
    # - dest is in {e_u, e_v} → "inbound" (early role)
    # - neither → "through" (both roles)
    inbound = sum(1 for s, t in dependent_pairs if t in (e_u, e_v))
    outbound = sum(1 for s, t in dependent_pairs if s in (e_u, e_v))
    through = sum(1 for s, t in dependent_pairs
                  if s not in (e_u, e_v) and t not in (e_u, e_v))

    return len(dependent_pairs), inbound, outbound, through


def main():
    random.seed(42)

    print("DUAL LABELING TEST")
    print("=" * 65)

    for n in [6, 8, 10]:
        samples = {6: 100, 8: 50, 10: 20}[n]

        tree_contained = 0
        tree_edges_in_spanner = []
        non_tree_edges = []
        pivot_found = 0

        for s in range(samples):
            edges, ts = make_temporal_clique(n, seed=42 + s)
            spanner_idx = find_min_spanner(n, edges, ts, trials=100)
            spanner_edges = [edges[i] for i in spanner_idx]

            has_tree, tree = contains_spanning_tree(n, spanner_edges)
            if has_tree:
                tree_contained += 1
                tree_set = set(tree)
                spanner_set = set(spanner_edges)
                n_tree = sum(1 for e in spanner_edges if e in tree_set)
                n_nontree = len(spanner_edges) - n_tree
                tree_edges_in_spanner.append(n_tree)
                non_tree_edges.append(n_nontree)

                # For each spanner edge, check its role
                single_role = 0
                dual_role = 0
                for idx in spanner_idx:
                    dep, inb, outb, thru = count_journey_roles(
                        n, edges, ts, spanner_idx, idx)
                    if dep > 0:
                        if thru > 0:
                            dual_role += 1
                        elif inb > 0 and outb > 0:
                            dual_role += 1
                        else:
                            single_role += 1

                if single_role == 1:
                    pivot_found += 1

            if (s + 1) % max(1, samples // 5) == 0:
                print(f"  n={n}: {s+1}/{samples}...", flush=True)

        print(f"\nn={n} ({samples} samples):")
        print(f"  Spanner size: 2n-3={2*n-3}, 2n-4={2*n-4}")
        print(f"  Contains spanning tree: {tree_contained}/{samples}")
        if tree_edges_in_spanner:
            avg_tree = sum(tree_edges_in_spanner) / len(tree_edges_in_spanner)
            avg_nontree = sum(non_tree_edges) / len(non_tree_edges)
            print(f"  Avg tree edges in spanner: {avg_tree:.1f}")
            print(f"  Avg non-tree edges: {avg_nontree:.1f}")
            print(f"  (spanning tree = {n-1} edges)")
        print(f"  Exactly 1 single-role edge (pivot): {pivot_found}/{samples}")
        print()


if __name__ == "__main__":
    main()
