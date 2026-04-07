"""
Exhaustive check: do 2 hub pairs ALWAYS suffice?

The previous script sampled at k>8. This does exhaustive search
on the specific failure cases.
"""

import random
from itertools import combinations

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
    for k in range(3, 16):
        n = 2 * k
        samples = min(300, max(10, 1000 // k))
        need_3 = 0
        total = 0

        for trial in range(samples):
            result = generate_random_biclique(k)
            if result is None:
                continue
            M, m_minus, m_plus = result
            total += 1

            # Exhaustive: try ALL pairs of hub rows × pairs of hub cols
            # Plus single rows/cols
            found = False

            # Try all (h1,h2) × (c1,c2) — including h1=h2 (1 hub row) etc.
            row_sets = [(h,) for h in range(k)]
            row_sets += list(combinations(range(k), 2))
            col_sets = [(c,) for c in range(k)]
            col_sets += list(combinations(range(k), 2))

            for hs in row_sets:
                for cs in col_sets:
                    edges = build_spanner(M, k, list(hs), list(cs))
                    if not check(k, M, edges):
                        found = True
                        break
                if found:
                    break

            if not found:
                need_3 += 1
                # Show the failure
                if need_3 <= 2:
                    print(f"  k={k} FAILURE: m⁻={m_minus}, m⁺={m_plus}")

        pct = 100 * (total - need_3) / total if total > 0 else 0
        status = "✓" if need_3 == 0 else f"✗ ({need_3} failures)"
        print(f"k={k:2d} (n={n:2d}): {total:3d} samples, "
              f"2 hubs suffice: {total-need_3}/{total} ({pct:.1f}%) {status}")


if __name__ == '__main__':
    main()
