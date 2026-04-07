"""
Label the M⁻ + M⁺ + two trees construction, then find which edge is redundant.

Construction:
- V⁻ spanning tree (k-1 edges): earliest-timestamp spanning tree on V⁻ internals
- M⁻ matching (k edges): earliest cross edge per column
- M⁺ matching (k edges): latest cross edge per row
- V⁺ spanning tree (k-1 edges): earliest-timestamp spanning tree on V⁺ internals
Total: 4k-2 edges

For each edge, check: is the full temporal reachability preserved without it?
The redundant edges are the ones we can drop. We need to find at least 1.

Then: characterize which edge is redundant and why.
"""

import random


def make_biclique(k, seed=None):
    """Full temporal clique on 2k vertices.
    V⁻ = {0..k-1}, V⁺ = {k..2k-1}.
    Returns: edges list, timestamps list.
    """
    if seed is not None:
        random.seed(seed)
    n = 2 * k
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
    m = len(edges)

    # Sandwich: V⁻ internal first, cross middle, V⁺ internal last
    vminus = [(i, j) for i, j in edges if i < k and j < k]
    cross = [(i, j) for i, j in edges if (i < k) != (j < k)]
    vplus = [(i, j) for i, j in edges if i >= k and j >= k]

    t = 1
    ts_map = {}

    random.shuffle(vminus)
    for e in vminus:
        ts_map[e] = t
        t += 1

    random.shuffle(cross)
    for e in cross:
        ts_map[e] = t
        t += 1

    random.shuffle(vplus)
    for e in vplus:
        ts_map[e] = t
        t += 1

    timestamps = [ts_map[e] for e in edges]
    return edges, timestamps, n


def compute_reachability(n, edge_subset, edges, timestamps):
    timed = sorted([(timestamps[idx], edges[idx][0], edges[idx][1])
                    for idx in edge_subset])
    reach = [{v: 0} for v in range(n)]
    for t, u, v in timed:
        nv, nu = {}, {}
        for s, a in reach[u].items():
            if a <= t and (s not in reach[v] or t < reach[v][s]):
                nv[s] = t
        for s, a in reach[v].items():
            if a <= t and (s not in reach[u] or t < reach[u][s]):
                nu[s] = t
        reach[v].update(nv)
        reach[u].update(nu)
    return set((s, v) for v in range(n) for s in reach[v] if s != v)


def build_construction(k, edges, timestamps):
    """Build the M⁻ + M⁺ + two trees construction.
    Returns: set of edge indices, labeled by role.
    """
    n = 2 * k
    edge_idx = {e: i for i, e in enumerate(edges)}

    # Cross edge matrix
    M = [[0] * k for _ in range(k)]
    cross_idx = {}
    for i in range(k):
        for j in range(k):
            e = (min(i, k + j), max(i, k + j))
            idx = edge_idx[e]
            M[i][j] = timestamps[idx]
            cross_idx[(i, j)] = idx

    # M⁻: earliest cross edge per column (min_i M[i][j])
    m_minus = {}
    for j in range(k):
        best_i = min(range(k), key=lambda i: M[i][j])
        m_minus[j] = (best_i, j, cross_idx[(best_i, j)])

    # M⁺: latest cross edge per row (max_j M[i][j])
    m_plus = {}
    for i in range(k):
        best_j = max(range(k), key=lambda j: M[i][j])
        m_plus[i] = (i, best_j, cross_idx[(i, best_j)])

    # V⁻ spanning tree (earliest-timestamp Kruskal on V⁻ internal edges)
    vminus_edges = [(i, j) for i in range(k) for j in range(i + 1, k)]
    vminus_sorted = sorted(vminus_edges, key=lambda e: timestamps[edge_idx[e]])

    parent = list(range(k))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    vminus_tree = []
    for e in vminus_sorted:
        u, v = e
        ru, rv = find(u), find(v)
        if ru != rv:
            parent[ru] = rv
            vminus_tree.append(edge_idx[e])
            if len(vminus_tree) == k - 1:
                break

    # V⁺ spanning tree (earliest-timestamp Kruskal on V⁺ internal edges)
    vplus_edges = [(i, j) for i in range(k, n) for j in range(i + 1, n)]
    vplus_sorted = sorted(vplus_edges, key=lambda e: timestamps[edge_idx[e]])

    parent = list(range(n))
    def find2(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    vplus_tree = []
    for e in vplus_sorted:
        u, v = e
        ru, rv = find2(u), find2(v)
        if ru != rv:
            parent[ru] = rv
            vplus_tree.append(edge_idx[e])
            if len(vplus_tree) == k - 1:
                break

    # Label each edge
    labeled = {}
    for idx in vminus_tree:
        labeled[idx] = 'V⁻ tree'
    for j, (i, _, idx) in m_minus.items():
        labeled[idx] = labeled.get(idx, '') + 'M⁻'
    for i, (_, j, idx) in m_plus.items():
        if idx in labeled:
            labeled[idx] += '+M⁺'
        else:
            labeled[idx] = 'M⁺'
    for idx in vplus_tree:
        labeled[idx] = labeled.get(idx, '') + 'V⁺ tree'

    return labeled, set(labeled.keys())


def find_redundant(n, construction_indices, edges, timestamps):
    """Find edges in the construction that can be removed
    without breaking temporal reachability."""
    full_reach = compute_reachability(n, list(construction_indices),
                                      edges, timestamps)
    redundant = []
    for idx in construction_indices:
        remaining = construction_indices - {idx}
        if compute_reachability(n, list(remaining), edges, timestamps) == full_reach:
            redundant.append(idx)
    return redundant


def main():
    random.seed(42)

    print("REDUNDANT EDGE FINDER")
    print("=" * 65)

    for k in range(3, 8):
        samples = {3: 500, 4: 200, 5: 100, 6: 50, 7: 20}[k]
        n = 2 * k

        redundant_counts = []
        redundant_labels = {}
        construction_preserves = 0

        for s in range(samples):
            edges, ts, n = make_biclique(k, seed=42 + s)
            labeled, construction = build_construction(k, edges, ts)

            # Check if construction preserves full reachability
            full_reach = compute_reachability(n, list(range(len(edges))),
                                              edges, ts)
            constr_reach = compute_reachability(n, list(construction),
                                                edges, ts)
            if constr_reach == full_reach:
                construction_preserves += 1

            # Find redundant edges
            redundant = find_redundant(n, construction, edges, ts)
            redundant_counts.append(len(redundant))

            for idx in redundant:
                label = labeled.get(idx, '?')
                redundant_labels[label] = redundant_labels.get(label, 0) + 1

            if s < 3 and redundant:
                print(f"\n  k={k} sample {s}: {len(redundant)} redundant")
                for idx in redundant:
                    u, v = edges[idx]
                    print(f"    edge ({u},{v}) t={ts[idx]} label={labeled.get(idx, '?')}")

            if (s + 1) % max(1, samples // 5) == 0:
                print(f"  k={k}: {s+1}/{samples}...", flush=True)

        avg_red = sum(redundant_counts) / len(redundant_counts)
        min_red = min(redundant_counts)
        always_has = sum(1 for c in redundant_counts if c > 0)

        print(f"\nk={k} (n={n}, 2n-3={2*n-3}, construction=4k-2={4*k-2}):")
        print(f"  Construction preserves reachability: "
              f"{construction_preserves}/{samples}")
        print(f"  Redundant edges: min={min_red}, avg={avg_red:.1f}, "
              f"max={max(redundant_counts)}")
        print(f"  Has ≥1 redundant: {always_has}/{samples} "
              f"({100*always_has/samples:.1f}%)")
        print(f"  Redundant by label: {dict(sorted(redundant_labels.items()))}")
        print()


if __name__ == "__main__":
    main()
