"""
The ACTUAL open problem: temporal spanner ≤ 4k-3 for extremally matched bicliques.

Structure: k×k matrix M with:
- M⁻[j] = argmin_i M[i][j] is a permutation (column minima)
- M⁺[i] = argmax_j M[i][j] is a permutation (row maxima)

The cross-only spanning result says we only need cross edges.
The budget is 4k-3 (from the dismount reduction in K_n).

Construction: star(hub_row) + star(hub_col) + relay edges.
- star(row h): k edges, handles some B-B pairs
- star(col c): k edges, handles some A-A pairs
- overlap: edge (h,c) counted once
- base: 2k-1 edges, budget remaining: 2k-2

For A-A pair (a_i, a_{i'}) through column c: M[i][c] ≤ M[i'][c].
For B-B pair (b_j, b_{j'}) through row h: M[h][j] ≤ M[h][j'].

Star(col c) routes A-A pairs (a_i → a_{i'}) iff M[i][c] < M[i'][c].
Star(row h) routes B-B pairs (b_j → b_{j'}) iff M[h][j] < M[h][j'].

Each star handles ~k(k-1)/2 directed pairs. The other half needs relay edges.
Budget for relays: 2k-2. Need to cover ~k(k-1) missing pairs.

Each relay edge covers ~k pairs. So 2k-2 edges × k pairs ≈ 2k² coverage.
Need: k(k-1). Coverage 2k² > k² — surplus exists.
"""

import random
from itertools import combinations

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
    """Generate random extremally matched biclique."""
    for attempt in range(1000):
        m_minus = list(range(k))
        random.shuffle(m_minus)
        m_plus = list(range(k))
        random.shuffle(m_plus)

        # Build DAG for topological sort
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


def double_star_greedy(M, k, hub_row, hub_col):
    """Double star + greedy: star(row h) ∪ star(col c) ∪ greedy relay."""
    n = 2 * k
    budget = 4 * k - 3
    all_timed = sorted([(M[i][j], i, k+j) for i in range(k) for j in range(k)])
    target = compute_reachability(n, all_timed)

    # Double star
    current = set()
    for j in range(k):
        current.add((hub_row, j))
    for i in range(k):
        current.add((i, hub_col))

    # Greedy fill
    non_star = [(i, j) for i in range(k) for j in range(k)
                if (i, j) not in current]

    while len(current) < budget:
        cur_timed = sorted([(M[i][j], i, k+j) for i, j in current])
        cur_reach = compute_reachability(n, cur_timed)
        if cur_reach == target:
            break
        cur_count = len(cur_reach)
        best_e, best_g = None, 0
        for e in non_star:
            if e in current:
                continue
            trial = current | {e}
            trial_timed = sorted([(M[i][j], i, k+j) for i, j in trial])
            g = len(compute_reachability(n, trial_timed)) - cur_count
            if g > best_g:
                best_g = g
                best_e = e
        if best_e is None or best_g <= 0:
            break
        current.add(best_e)

    cur_timed = sorted([(M[i][j], i, k+j) for i, j in current])
    return len(current), compute_reachability(n, cur_timed) == target


def main():
    print("Extremally matched biclique spanner")
    print("=" * 70)

    for k in range(3, 10):
        n = 2 * k
        budget = 4 * k - 3
        samples = 300 if k <= 7 else 100

        successes = 0
        sizes = []

        for trial in range(samples):
            result = generate_extremal_biclique(k)
            if result is None:
                continue
            M, m_minus, m_plus = result

            # Try all (hub_row, hub_col) pairs
            best_size = 999
            best_ok = False
            for h in range(k):
                for c in range(k):
                    size, ok = double_star_greedy(M, k, h, c)
                    if ok and size < best_size:
                        best_size = size
                        best_ok = ok
                    if ok and size <= budget:
                        break
                if best_ok and best_size <= budget:
                    break

            if best_ok and best_size <= budget:
                successes += 1
            sizes.append(best_size)

        avg_size = sum(sizes) / len(sizes) if sizes else 0
        print(f"\nK_{{{k},{k}}} (budget={budget}, {len(sizes)} samples):")
        print(f"  ≤ budget: {successes}/{len(sizes)} ({100*successes/len(sizes):.1f}%)")
        print(f"  Best size: mean={avg_size:.1f}, min={min(sizes)}, max={max(sizes)}")


if __name__ == '__main__':
    main()
