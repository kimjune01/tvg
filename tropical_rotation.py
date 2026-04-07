"""
Tropical rotation: can node potentials + vertex permutation
reduce any timestamp matrix to "caterpillar form" where the
essential edges are obvious?

The transformation: M'[i][j] = M[i][j] + c_i + c_j
preserves which edges are essential for the spanner.

We test: after optimizing potentials c, do the essential edges
form a caterpillar (or near-caterpillar)?
"""

import random
import math
from itertools import permutations as perms


def compute_reachability(n, timed_edges):
    reached_by = [dict() for _ in range(n)]
    for i in range(n):
        reached_by[i][i] = 0
    for t, u, v in sorted(timed_edges):
        su = {s: a for s, a in reached_by[u].items() if a <= t}
        sv = {s: a for s, a in reached_by[v].items() if a <= t}
        for s, a in su.items():
            if s not in reached_by[v] or t < reached_by[v][s]:
                reached_by[v][s] = t
        for s, a in sv.items():
            if s not in reached_by[u] or t < reached_by[u][s]:
                reached_by[u][s] = t
    reach = [0] * n
    for v in range(n):
        for s in reached_by[v]:
            if s != v:
                reach[s] |= (1 << v)
    return reach


def find_essential_edges(n, edges, timestamps):
    """Edges that MUST be in every spanner."""
    m = len(edges)
    timed = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in range(m)])
    target = compute_reachability(n, timed)
    essential = []
    for idx in range(m):
        remaining = [(timestamps[i], edges[i][0], edges[i][1])
                     for i in range(m) if i != idx]
        if compute_reachability(n, sorted(remaining)) != target:
            essential.append(idx)
    return essential


def apply_potentials(n, edges, timestamps, potentials):
    """Apply node potentials: t'[i][j] = t[i][j] + c_i + c_j.
    Return the new timestamps (preserving which are essential)."""
    new_ts = []
    for idx, (u, v) in enumerate(edges):
        new_ts.append(timestamps[idx] + potentials[u] + potentials[v])
    return new_ts


def is_caterpillar(n, edge_indices, edges):
    """Check if the given edges form a caterpillar graph."""
    if len(edge_indices) < n - 1:
        return False, "too few edges"

    adj = [[] for _ in range(n)]
    deg = [0] * n
    for idx in edge_indices:
        u, v = edges[idx]
        adj[u].append(v)
        adj[v].append(u)
        deg[u] += 1
        deg[v] += 1

    # Check connected
    visited = set()
    stack = [edge_indices[0] if edge_indices else 0]
    start = edges[edge_indices[0]][0] if edge_indices else 0
    stack = [start]
    while stack:
        v = stack.pop()
        if v in visited:
            continue
        visited.add(v)
        for w in adj[v]:
            if w not in visited:
                stack.append(w)

    verts_in_edges = set()
    for idx in edge_indices:
        verts_in_edges.add(edges[idx][0])
        verts_in_edges.add(edges[idx][1])

    if not verts_in_edges.issubset(visited):
        return False, "disconnected"

    # Not a tree if too many edges
    if len(edge_indices) > len(verts_in_edges) - 1:
        return False, f"has cycles ({len(edge_indices)} edges, {len(verts_in_edges)} vertices)"

    # Remove leaves, check if remainder is a path
    inner = [v for v in verts_in_edges if deg[v] >= 2]
    if len(inner) <= 2:
        return True, f"caterpillar (spine={len(inner)})"

    # Check inner vertices form a path
    inner_set = set(inner)
    inner_deg = {v: sum(1 for w in adj[v] if w in inner_set) for v in inner}
    endpoints = sum(1 for v in inner if inner_deg[v] <= 1)
    branches = sum(1 for v in inner if inner_deg[v] > 2)
    if endpoints <= 2 and branches == 0:
        return True, f"caterpillar (spine={len(inner)})"
    return False, f"not caterpillar (inner degs: {sorted(inner_deg.values(), reverse=True)})"


def analyze_essential_structure(n, edges, timestamps):
    """Analyze the structure of essential edges."""
    essential = find_essential_edges(n, edges, timestamps)
    ess_edges = [edges[i] for i in essential]
    deg = [0] * n
    for u, v in ess_edges:
        deg[u] += 1
        deg[v] += 1

    cat, reason = is_caterpillar(n, essential, edges)
    return {
        'essential': essential,
        'count': len(essential),
        'caterpillar': cat,
        'reason': reason,
        'degrees': deg,
        'max_deg': max(deg) if deg else 0,
    }


def try_potentials_to_caterpillar(n, edges, timestamps, attempts=200):
    """Try random potentials and check if essential edges become a caterpillar.
    Since potentials PRESERVE which edges are essential, we're really
    checking whether the essential edges already form a caterpillar.

    But wait — potentials don't change which edges are essential!
    They change the timestamps but preserve essentiality.

    The potentials change the ORDER of non-essential edges, which
    might reveal structure. But the essential set is FIXED.

    So the question is simpler: are the essential edges already
    a caterpillar (or close to one)?
    """
    # Essential edges don't change with potentials
    info = analyze_essential_structure(n, edges, timestamps)
    return info


def greedy_spanner(n, edges, timestamps):
    m = len(edges)
    timed = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in range(m)])
    target = compute_reachability(n, timed)
    included = set(range(m))
    for idx in sorted(range(m), key=lambda i: -timestamps[i]):
        trial = sorted([(timestamps[i], edges[i][0], edges[i][1])
                       for i in included if i != idx])
        if compute_reachability(n, trial) == target:
            included.discard(idx)
    return included


def main():
    random.seed(42)

    for n in [4, 5, 6, 7]:
        edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
        m = len(edges)
        samples = 500 if n <= 5 else 200

        print(f"\n{'='*60}")
        print(f"K_{n}: {n} vertices, {m} edges, 2n-3={2*n-3}")
        print(f"{'='*60}")

        cat_count = 0
        tree_count = 0
        ess_sizes = {}
        structures = {}

        for _ in range(samples):
            ts = list(range(1, m + 1))
            random.shuffle(ts)

            info = analyze_essential_structure(n, edges, ts)
            ess_count = info['count']
            ess_sizes[ess_count] = ess_sizes.get(ess_count, 0) + 1

            if info['caterpillar']:
                cat_count += 1

            # Also check greedy spanner structure
            greedy = greedy_spanner(n, edges, ts)
            greedy_cat, greedy_reason = is_caterpillar(n, list(greedy), edges)

            key = (ess_count, info['caterpillar'], len(greedy), greedy_cat)
            structures[key] = structures.get(key, 0) + 1

        print(f"\nEssential edge counts:")
        for sz, cnt in sorted(ess_sizes.items()):
            print(f"  {sz} essential: {cnt} ({100*cnt/samples:.1f}%)")

        print(f"\nEssential edges are caterpillar: {cat_count}/{samples} ({100*cat_count/samples:.1f}%)")

        print(f"\nDetailed structures (essential_count, ess_cat, greedy_count, greedy_cat):")
        for (ec, ecat, gc, gcat), cnt in sorted(structures.items(), key=lambda x: -x[1])[:10]:
            print(f"  ess={ec}{'(cat)' if ecat else ''}, greedy={gc}{'(cat)' if gcat else ''}: {cnt}")


if __name__ == "__main__":
    main()
