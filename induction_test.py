"""
Induction test: can a new row+column be added with 4 edges?

Given a valid (4k-3)-spanner for a k×k extremally matched biclique,
extend to (k+1)×(k+1) by adding one row and one column with 4 new edges.

Budget: 4(k+1)-3 = 4k+1. Previous: 4k-3. Increase: 4.

The new row a_{k+1} connects to columns b_1,...,b_{k+1}.
The new column b_{k+1} connects to rows a_1,...,a_{k+1}.

Pairs to cover involving new vertices:
- a_{k+1} → everything (n new A-B, A-A pairs)
- everything → a_{k+1}
- b_{k+1} → everything
- everything → b_{k+1}

With 4 new edges: which 4 from the new row/column suffice?

Test: for random (k+1)×(k+1) bicliques, find the optimal k×k sub-biclique,
build its spanner, then check how many edges are needed for the new vertices.
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
    """Find best greedy spanner for k×k biclique."""
    n = 2 * k
    budget = 4 * k - 3
    all_timed = sorted([(M[i][j], i, k+j) for i in range(k) for j in range(k)])
    target = compute_reachability(n, all_timed)

    # Try all hub pairs
    best_edges = None
    best_size = k * k

    for h in range(min(k, 5)):
        for c in range(min(k, 5)):
            current = set()
            for j in range(k):
                current.add((h, j))
            for i in range(k):
                current.add((i, c))

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
                    t_timed = sorted([(M[ii][jj], ii, k+jj) for ii, jj in trial])
                    g = len(compute_reachability(n, t_timed)) - cur_count
                    if g > best_g:
                        best_g = g
                        best_e = e
                if best_e is None or best_g <= 0:
                    break
                current.add(best_e)

            cur_timed = sorted([(M[i][j], i, k+j) for i, j in current])
            if compute_reachability(n, cur_timed) == target and len(current) < best_size:
                best_size = len(current)
                best_edges = set(current)

    return best_edges, best_size


def test_induction(k_big):
    """Generate (k_big)×(k_big) biclique. For each way to remove one
    row and one column (giving k×k sub-biclique), find the sub-spanner,
    then count how many new edges are needed."""
    k = k_big
    result = generate_extremal_biclique(k)
    if result is None:
        return None
    M, m_minus, m_plus = result

    n = 2 * k
    all_timed = sorted([(M[i][j], i, k+j) for i in range(k) for j in range(k)])
    target = compute_reachability(n, all_timed)

    best_extra = k * k

    # Try removing row r and column c
    for r in range(k):
        for c in range(k):
            # Sub-biclique: rows {0..k-1}\{r}, cols {0..k-1}\{c}
            sub_rows = [i for i in range(k) if i != r]
            sub_cols = [j for j in range(k) if j != c]
            k_sub = k - 1

            # Build sub-matrix
            M_sub = [[M[sub_rows[i]][sub_cols[j]]
                       for j in range(k_sub)] for i in range(k_sub)]

            # Find spanner for sub-biclique
            sub_edges_raw, sub_size = greedy_spanner(M_sub, k_sub)
            if sub_edges_raw is None:
                continue

            # Map sub-edges back to original indices
            base_edges = set()
            for (si, sj) in sub_edges_raw:
                base_edges.add((sub_rows[si], sub_cols[sj]))

            # Now: base_edges is a valid spanner for the sub-biclique.
            # Add edges involving row r and column c.
            # Available new edges: (r, j) for j in 0..k-1 and (i, c) for i in 0..k-1
            new_candidates = [(r, j) for j in range(k)] + \
                             [(i, c) for i in range(k) if i != r]

            # Greedy: add new edges one at a time until full spanner
            current = set(base_edges)
            extra = 0

            while True:
                cur_timed = sorted([(M[i][j], i, k+j) for i, j in current])
                cur_reach = compute_reachability(n, cur_timed)
                if cur_reach == target:
                    break

                cur_count = len(cur_reach)
                best_e, best_g = None, 0
                for e in new_candidates:
                    if e in current:
                        continue
                    trial = current | {e}
                    t_timed = sorted([(M[i][j], i, k+j) for i, j in trial])
                    g = len(compute_reachability(n, t_timed)) - cur_count
                    if g > best_g:
                        best_g = g
                        best_e = e

                if best_e is None or best_g <= 0:
                    # Can't fix with new edges alone — try ANY edge
                    all_remaining = [(i, j) for i in range(k) for j in range(k)
                                     if (i, j) not in current]
                    for e in all_remaining:
                        trial = current | {e}
                        t_timed = sorted([(M[i][j], i, k+j) for i, j in trial])
                        g = len(compute_reachability(n, t_timed)) - cur_count
                        if g > best_g:
                            best_g = g
                            best_e = e
                    if best_e is None or best_g <= 0:
                        extra = k * k  # failed
                        break

                current.add(best_e)
                extra += 1

            best_extra = min(best_extra, extra)
            if extra <= 4:
                return extra, r, c, sub_size

    return best_extra, -1, -1, -1


def main():
    print("Induction test: edges needed for new row+column")
    print("=" * 60)
    print(f"{'k':>3} {'budget':>6} {'sub_bgt':>7} {'extra':>6} {'≤4':>5}")
    print("-" * 35)

    for k in range(4, 10):
        budget = 4 * k - 3
        sub_budget = 4 * (k - 1) - 3
        samples = 100 if k <= 7 else 30

        extras = []
        within_4 = 0

        for trial in range(samples):
            result = test_induction(k)
            if result is None:
                continue
            extra, r, c, sub_size = result
            extras.append(extra)
            if extra <= 4:
                within_4 += 1

        if extras:
            avg = sum(extras) / len(extras)
            mx = max(extras)
            print(f"{k:3d} {budget:6d} {sub_budget:7d} {avg:5.1f}({mx:d}) "
                  f"{100*within_4/len(extras):4.0f}%")


if __name__ == '__main__':
    main()
