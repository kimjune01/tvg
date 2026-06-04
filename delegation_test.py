"""
Test: is the log factor in CPS structural or removable?

Build the bipartite residual (k emitters, k collectors).
Try two constructions:
1. Root delegation: pick one root emitter, include all its edges.
   Each other emitter delegates to root. Count missed collectors.
2. Chained delegation: chain emitters. Each delegates to previous.
   Track temporal constraints and count total edges.

If total edges = O(k), the log is removable.
If total edges = Θ(k log k), the log is structural.
"""

import random
from math import log2

random.seed(42)


def compute_reachability(n, timed_edges):
    reached_by = [dict() for _ in range(n)]
    for i in range(n):
        reached_by[i][i] = 0
    for t, u, v in sorted(timed_edges):
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


def generate_extremal_biclique(k):
    for attempt in range(1000):
        m_minus = list(range(k))
        random.shuffle(m_minus)
        m_plus = list(range(k))
        random.shuffle(m_plus)
        edge_idx = {(i, j): i * k + j for i in range(k) for j in range(k)}
        adj = [[] for _ in range(k * k)]
        in_deg = [0] * (k * k)
        for j in range(k):
            src = edge_idx[(m_minus[j], j)]
            for i in range(k):
                if i != m_minus[j]:
                    adj[src].append(edge_idx[(i, j)])
                    in_deg[edge_idx[(i, j)]] += 1
        for i in range(k):
            dst = edge_idx[(i, m_plus[i])]
            for jj in range(k):
                if jj != m_plus[i]:
                    adj[edge_idx[(i, jj)]].append(dst)
                    in_deg[dst] += 1
        queue = [x for x in range(k * k) if in_deg[x] == 0]
        order = []
        while queue:
            random.shuffle(queue)
            node = queue.pop()
            order.append(node)
            for nb in adj[node]:
                in_deg[nb] -= 1
                if in_deg[nb] == 0:
                    queue.append(nb)
        if len(order) != k * k:
            continue
        M = [[0] * k for _ in range(k)]
        for rank, node in enumerate(order):
            i, j = node // k, node % k
            M[i][j] = rank + 1
        return M, m_minus, m_plus
    return None


def root_delegation(M, k, root):
    """Root emitter gets all k edges. Others delegate to root.
    Count total edges including missed collectors."""
    n = 2 * k
    edges = set()

    # Root star: all k edges
    for j in range(k):
        edges.add((root, j))

    # Sort root's edges by timestamp
    root_order = sorted(range(k), key=lambda j: M[root][j])

    total_missed = 0

    for i in range(k):
        if i == root:
            continue

        # Find best delegation collector: minimize arrival rank at root
        # Delegation: emitter i → collector c → root
        # Need M[i][c] ≤ M[root][c]
        best_c = None
        best_root_rank = k

        for c in range(k):
            if M[i][c] <= M[root][c]:
                # Root's rank for this collector
                rr = root_order.index(c)
                if rr < best_root_rank:
                    best_root_rank = rr
                    best_c = c

        if best_c is None:
            # Can't delegate to root — add all edges from i
            for j in range(k):
                edges.add((i, j))
            total_missed += k
            continue

        # Add delegation edges
        edges.add((i, best_c))
        # Missed: collectors with root timestamp < M[root][best_c]
        arrival_at_root = M[root][best_c]
        missed = [j for j in range(k) if M[root][j] < arrival_at_root]
        total_missed += len(missed)

        # Add direct edges to missed collectors
        for j in missed:
            edges.add((i, j))

    return len(edges), total_missed


def main():
    print("Delegation test: is the log factor structural?")
    print("=" * 70)
    print(f"{'k':>4} {'n':>4} {'root_edges':>11} {'root/k':>7} "
          f"{'klogk':>6} {'missed/k':>8}")
    print("-" * 55)

    for k in [4, 6, 8, 10, 15, 20, 30, 50]:
        samples = 200 if k <= 20 else 50

        root_sizes = []
        missed_counts = []

        for trial in range(samples):
            result = generate_extremal_biclique(k)
            if result is None:
                continue
            M, _, _ = result

            # Try all roots, pick best
            best_size = k * k
            best_missed = k * k
            for root in range(k):
                size, missed = root_delegation(M, k, root)
                if size < best_size:
                    best_size = size
                    best_missed = missed

            root_sizes.append(best_size)
            missed_counts.append(best_missed)

        if root_sizes:
            avg_size = sum(root_sizes) / len(root_sizes)
            avg_missed = sum(missed_counts) / len(missed_counts)
            klogk = k * log2(k) if k > 1 else k
            print(f"{k:4d} {2*k:4d} {avg_size:11.1f} {avg_size/k:7.2f} "
                  f"{klogk:6.1f} {avg_missed/k:8.2f}")


if __name__ == '__main__':
    main()
