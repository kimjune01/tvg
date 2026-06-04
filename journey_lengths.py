"""
What journey lengths does the greedy spanner actually use?
For each rescued pair, find the shortest journey in the spanner.
"""

import random
from collections import defaultdict

random.seed(42)


def compute_reachability_with_hops(n, timed_edges):
    """Track minimum hop count for each reachable pair."""
    reached_by = [dict() for _ in range(n)]  # v -> {source: (arrival_time, hops)}
    for i in range(n):
        reached_by[i][i] = (0, 0)
    for t, u, v in sorted(timed_edges):
        for s, (arr, hops) in list(reached_by[u].items()):
            if arr <= t:
                if s not in reached_by[v] or t < reached_by[v][s][0]:
                    reached_by[v][s] = (t, hops + 1)
        for s, (arr, hops) in list(reached_by[v].items()):
            if arr <= t:
                if s not in reached_by[u] or t < reached_by[u][s][0]:
                    reached_by[u][s] = (t, hops + 1)
    hop_counts = {}
    for v in range(n):
        for s, (arr, hops) in reached_by[v].items():
            if s != v:
                hop_counts[(s, v)] = hops
    return hop_counts


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


def greedy_spanner(M, k):
    """Best double-star + greedy over all (h,c) pairs."""
    n = 2 * k
    budget = 4 * k - 3
    all_timed = sorted([(M[i][j], i, k+j) for i in range(k) for j in range(k)])

    # Compute reachability with hops for full graph
    full_hops = compute_reachability_with_hops(n, all_timed)

    best_edges = None
    best_size = 999

    for h in range(k):
        for c in range(k):
            current = set()
            for j in range(k):
                current.add((h, j))
            for i in range(k):
                current.add((i, c))

            non_star = [(i, j) for i in range(k) for j in range(k)
                        if (i, j) not in current]

            while len(current) < budget:
                cur_timed = sorted([(M[i][j], i, k+j) for i, j in current])
                cur_hops = compute_reachability_with_hops(n, cur_timed)
                if len(cur_hops) == len(full_hops):
                    break
                cur_count = len(cur_hops)
                best_e, best_g = None, 0
                for e in non_star:
                    if e in current:
                        continue
                    trial = current | {e}
                    t_timed = sorted([(M[ii][jj], ii, k+jj) for ii, jj in trial])
                    t_hops = compute_reachability_with_hops(n, t_timed)
                    g = len(t_hops) - cur_count
                    if g > best_g:
                        best_g = g
                        best_e = e
                if best_e is None or best_g <= 0:
                    break
                current.add(best_e)

            if len(current) <= budget:
                cur_timed = sorted([(M[i][j], i, k+j) for i, j in current])
                cur_hops = compute_reachability_with_hops(n, cur_timed)
                if len(cur_hops) == len(full_hops) and len(current) < best_size:
                    best_size = len(current)
                    best_edges = set(current)

    return best_edges, best_size


def main():
    print("Journey lengths in greedy biclique spanners")
    print("=" * 70)

    for k in range(3, 9):
        n = 2 * k
        budget = 4 * k - 3
        samples = 50 if k <= 6 else 20

        all_max_hops = []
        hop_distributions = defaultdict(int)

        for trial in range(samples):
            result = generate_extremal_biclique(k)
            if result is None:
                continue
            M, _, _ = result

            edges, size = greedy_spanner(M, k)
            if edges is None:
                continue

            # Compute hop counts in the spanner
            timed = sorted([(M[i][j], i, k+j) for i, j in edges])
            hops = compute_reachability_with_hops(n, timed)

            max_hop = max(hops.values()) if hops else 0
            all_max_hops.append(max_hop)

            for (s, t), h in hops.items():
                hop_distributions[h] += 1

        if all_max_hops:
            avg_max = sum(all_max_hops) / len(all_max_hops)
            print(f"\nK_{{{k},{k}}} (budget={budget}, {len(all_max_hops)} samples):")
            print(f"  Max journey hops: mean={avg_max:.1f}, "
                  f"min={min(all_max_hops)}, max={max(all_max_hops)}")
            total_pairs = sum(hop_distributions.values())
            print(f"  Hop distribution:")
            for h in sorted(hop_distributions):
                pct = 100 * hop_distributions[h] / total_pairs
                print(f"    {h}-hop: {hop_distributions[h]:6d} ({pct:.1f}%)")


if __name__ == '__main__':
    main()
