"""
O(n) spanner via 2 hub pairs.

Construction: M⁻ ∪ M⁺ ∪ star(h1) ∪ star(c1) ∪ star(h2) ∪ star(c2)

Prove: for any extremally matched biclique, 2 hub pairs suffice.
Total ≤ 6k = 3n = O(n).
"""

import random

random.seed(42)


def compute_reachability_pairs(n, timed_edges):
    reached_by = [dict() for _ in range(n)]
    for i in range(n):
        reached_by[i][i] = 0
    for t, u, v in sorted(timed_edges):
        for s, arr in list(reached_by[u].items()):
            if arr <= t and (s not in reached_by[v] or t < reached_by[v][s]):
                reached_by[v][s] = t
        for s, arr in list(reached_by[v].items()):
            if arr <= t and (s not in reached_by[u] or t < reached_by[u][s]):
                reached_by[u][s] = t
    pairs = set()
    for v in range(n):
        for s in reached_by[v]:
            if s != v:
                pairs.add((s, v))
    return pairs


def generate_random_biclique(k, max_attempts=1000):
    num_vminus = k * (k - 1) // 2
    for attempt in range(max_attempts):
        m_minus = list(range(k))
        random.shuffle(m_minus)
        m_plus = list(range(k))
        random.shuffle(m_plus)
        edge_idx = {(i, j): i * k + j for i in range(k) for j in range(k)}
        adj = [[] for _ in range(k * k)]
        in_degree = [0] * (k * k)
        for j in range(k):
            src = edge_idx[(m_minus[j], j)]
            for i in range(k):
                if i != m_minus[j]:
                    adj[src].append(edge_idx[(i, j)])
                    in_degree[edge_idx[(i, j)]] += 1
        for i in range(k):
            dst = edge_idx[(i, m_plus[i])]
            for jj in range(k):
                if jj != m_plus[i]:
                    adj[edge_idx[(i, jj)]].append(dst)
                    in_degree[dst] += 1
        queue = [i for i in range(k * k) if in_degree[i] == 0]
        order = []
        while queue:
            random.shuffle(queue)
            node = queue.pop()
            order.append(node)
            for nb in adj[node]:
                in_degree[nb] -= 1
                if in_degree[nb] == 0:
                    queue.append(nb)
        if len(order) != k * k:
            continue
        M = [[0] * k for _ in range(k)]
        for rank, node in enumerate(order):
            i, j = node // k, node % k
            M[i][j] = rank + 1
        return M, m_minus, m_plus
    return None


def build_spanner(M, k, hub_rows, hub_cols):
    """M⁻ ∪ M⁺ ∪ stars for given hub rows and columns."""
    edges = set()
    for j in range(k):
        best_i = min(range(k), key=lambda i: M[i][j])
        edges.add((best_i, j))
    for i in range(k):
        best_j = max(range(k), key=lambda j: M[i][j])
        edges.add((i, best_j))
    for h in hub_rows:
        for j in range(k):
            edges.add((h, j))
    for c in hub_cols:
        for i in range(k):
            edges.add((i, c))
    return edges


def check(k, M, edges):
    n = 2 * k
    full_timed = [(M[i][j], i, k + j) for i in range(k) for j in range(k)]
    full_pairs = compute_reachability_pairs(n, full_timed)
    span_timed = [(M[i][j], i, k + j) for i, j in edges]
    span_pairs = compute_reachability_pairs(n, span_timed)
    return full_pairs - span_pairs


def main():
    print("=" * 70)
    print("O(n) SPANNER: HOW MANY HUB PAIRS SUFFICE?")
    print("=" * 70)

    for k in range(3, 13):
        n = 2 * k
        samples = min(500, max(20, 2000 // k))

        results = {0: 0, 1: 0, 2: 0, 3: 0}
        total = 0
        max_edges_used = 0

        for trial in range(samples):
            result = generate_random_biclique(k)
            if result is None:
                continue
            M, m_minus, m_plus = result
            total += 1

            # 0 hubs: just M⁻ ∪ M⁺
            edges = build_spanner(M, k, [], [])
            if not check(k, M, edges):
                results[0] += 1
                max_edges_used = max(max_edges_used, len(edges))
                continue

            # 1 hub pair: try all (h, c)
            found = False
            for h in range(k):
                for c in range(k):
                    edges = build_spanner(M, k, [h], [c])
                    if not check(k, M, edges):
                        found = True
                        max_edges_used = max(max_edges_used, len(edges))
                        break
                if found:
                    break
            if found:
                results[1] += 1
                continue

            # 2 hub pairs: try some combinations
            found = False
            # Try all pairs of rows × pairs of cols (or sample)
            if k <= 8:
                for h1 in range(k):
                    for h2 in range(h1 + 1, k):
                        for c1 in range(k):
                            for c2 in range(c1 + 1, k):
                                edges = build_spanner(M, k, [h1, h2], [c1, c2])
                                if not check(k, M, edges):
                                    found = True
                                    max_edges_used = max(max_edges_used, len(edges))
                                    break
                            if found:
                                break
                        if found:
                            break
                    if found:
                        break
            else:
                # Sample random pairs
                for _ in range(200):
                    h1, h2 = random.sample(range(k), 2)
                    c1, c2 = random.sample(range(k), 2)
                    edges = build_spanner(M, k, [h1, h2], [c1, c2])
                    if not check(k, M, edges):
                        found = True
                        max_edges_used = max(max_edges_used, len(edges))
                        break

            if found:
                results[2] += 1
                continue

            # 3 hub pairs
            found = False
            for _ in range(500):
                hs = random.sample(range(k), 3)
                cs = random.sample(range(k), 3)
                edges = build_spanner(M, k, hs, cs)
                if not check(k, M, edges):
                    found = True
                    max_edges_used = max(max_edges_used, len(edges))
                    break
            if found:
                results[3] += 1
            else:
                results[3] -= 1  # flag as needing >3

        print(f"\nk={k} (n={n}), {total} samples:")
        print(f"  0 hubs (M⁻∪M⁺ only):  {results[0]}")
        print(f"  1 hub pair:             {results[1]}")
        print(f"  2 hub pairs:            {results[2]}")
        print(f"  3+ hub pairs:           {results.get(3, 0)}")
        cum = results[0]
        for h in [1, 2, 3]:
            cum += results[h]
            pct = 100 * cum / total if total > 0 else 0
            bound = 2 * k + 2 * h * k  # rough upper bound on edges
            print(f"    ≤{h} hub pairs: {cum}/{total} ({pct:.1f}%), "
                  f"≤{bound} edges = {bound/n:.1f}n")


if __name__ == '__main__':
    main()
