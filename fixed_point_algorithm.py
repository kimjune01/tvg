"""
Can fixed points of σ = m⁺ ∘ (m⁻)⁻¹ serve as an O(n) hub finder?

Algorithm:
1. Compute M⁻, M⁺, σ. O(k²)
2. Find fixed points of σ. O(k)
3. Try each fixed point as hub. O(k × k²) = O(k³) verification.
4. If no fixed points (derangement), fall back to ???

Questions:
- What fraction of bicliques have σ with fixed points?
- When fixed points exist, do they always contain a valid hub?
- When σ is a derangement, what predicts the hub?
- For the 2-hub construction, can the second hub be found from σ too?
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
    m_minus = [min(range(k), key=lambda i: M[i][j]) for j in range(k)]
    m_plus = [max(range(k), key=lambda j: M[i][j]) for i in range(k)]
    for j in range(k):
        edges.add((m_minus[j], j))
    for i in range(k):
        edges.add((i, m_plus[i]))
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


def get_sigma(m_minus, m_plus, k):
    """σ = m⁺ ∘ (m⁻)⁻¹: column → column."""
    m_minus_inv = [0] * k  # m_minus_inv[i] = j where m_minus[j] = i
    for j in range(k):
        m_minus_inv[m_minus[j]] = j
    # σ(c) = m⁺(m⁻⁻¹(c))... wait, let me be precise.
    # m⁻: col → row (m_minus[j] = row with min in col j)
    # m⁺: row → col (m_plus[i] = col with max in row i)
    # σ = m⁺ ∘ m⁻: col → row → col
    # σ(j) = m⁺(m⁻(j)) = m_plus[m_minus[j]]
    sigma = [m_plus[m_minus[j]] for j in range(k)]
    return sigma


def get_cycle_structure(sigma, k):
    visited = [False] * k
    cycles = []
    for start in range(k):
        if visited[start]:
            continue
        cycle = []
        j = start
        while not visited[j]:
            visited[j] = True
            cycle.append(j)
            j = sigma[j]
        cycles.append(cycle)
    return cycles


def main():
    print("=" * 70)
    print("FIXED-POINT ALGORITHM FOR HUB SELECTION")
    print("=" * 70)

    for k in range(3, 11):
        n = 2 * k
        samples = {3: 1000, 4: 500, 5: 300, 6: 200, 7: 100, 8: 50, 9: 30, 10: 20}[k]

        # Counters
        has_fp = 0           # σ has at least one fixed point
        no_fp = 0            # σ is a derangement
        fp_hub_works = 0     # some fixed point is a valid single hub
        fp_hub_fails = 0     # fixed points exist but none is a valid hub
        no_fp_any_hub = 0    # derangement, but some hub works anyway
        no_fp_no_hub = 0     # derangement, no single hub works

        # 2-hub analysis for derangements
        no_fp_2hub_fp2 = 0   # derangement: σ² fixed point works as 2nd hub
        no_fp_2hub_other = 0 # derangement: 2 hubs work but not via σ²
        no_fp_2hub_fail = 0  # derangement: even 2 hubs fail

        # Track which σ-derived properties predict 2nd hub
        derangement_details = []

        for trial in range(samples):
            result = generate_random_biclique(k)
            if result is None:
                continue

            M, m_minus, m_plus = result
            sigma = get_sigma(m_minus, m_plus, k)
            cycles = get_cycle_structure(sigma, k)
            fixed_points = [j for j in range(k) if sigma[j] == j]

            if fixed_points:
                has_fp += 1
                # Try each fixed point as hub
                found = False
                for c in fixed_points:
                    h = m_minus[c]  # row that is min in column c
                    edges = build_spanner(M, k, [h], [c])
                    missing = check(k, M, edges)
                    if not missing:
                        found = True
                        break
                if found:
                    fp_hub_works += 1
                else:
                    fp_hub_fails += 1
            else:
                no_fp += 1
                # Derangement — try all single hubs
                any_single = False
                for h in range(k):
                    c = m_plus[h]
                    edges = build_spanner(M, k, [h], [c])
                    missing = check(k, M, edges)
                    if not missing:
                        any_single = True
                        break
                if any_single:
                    no_fp_any_hub += 1
                else:
                    no_fp_no_hub += 1

                # For derangements: try 2-hub construction
                # First hub: try all rows. Second hub: check σ² fixed points
                sigma2 = [sigma[sigma[j]] for j in range(k)]
                fp2 = [j for j in range(k) if sigma2[j] == j and sigma[j] != j]
                # fp2 = fixed points of σ² that aren't fixed points of σ
                # These are elements in 2-cycles of σ

                found_2hub = False
                # Try: first hub from any row, second from σ² fixed points
                if fp2:
                    for h1 in range(k):
                        c1 = m_plus[h1]
                        for c2_candidate in fp2:
                            h2 = m_minus[c2_candidate]
                            edges = build_spanner(M, k, [h1, h2], [c1, c2_candidate])
                            missing = check(k, M, edges)
                            if not missing:
                                found_2hub = True
                                no_fp_2hub_fp2 += 1
                                break
                        if found_2hub:
                            break

                if not found_2hub:
                    # Try all 2-hub pairs
                    for h1 in range(k):
                        for h2 in range(h1 + 1, k):
                            c1 = m_plus[h1]
                            c2 = m_plus[h2]
                            edges = build_spanner(M, k, [h1, h2], [c1, c2])
                            missing = check(k, M, edges)
                            if not missing:
                                found_2hub = True
                                no_fp_2hub_other += 1
                                break
                        if found_2hub:
                            break

                if not found_2hub:
                    # Exhaustive: any 2 rows × any 2 cols
                    for hs in combinations(range(k), 2):
                        for cs in combinations(range(k), 2):
                            edges = build_spanner(M, k, list(hs), list(cs))
                            missing = check(k, M, edges)
                            if not missing:
                                found_2hub = True
                                no_fp_2hub_other += 1
                                break
                        if found_2hub:
                            break

                if not found_2hub:
                    no_fp_2hub_fail += 1

        total = has_fp + no_fp
        print(f"\nk={k} (n={n}), {total} samples:")
        print(f"  σ has fixed points: {has_fp}/{total} ({100*has_fp/total:.1f}%)")
        print(f"  σ is derangement:   {no_fp}/{total} ({100*no_fp/total:.1f}%)")
        if has_fp > 0:
            print(f"  Fixed-point hub works: {fp_hub_works}/{has_fp} "
                  f"({100*fp_hub_works/has_fp:.1f}%)")
            if fp_hub_fails > 0:
                print(f"  Fixed-point hub FAILS: {fp_hub_fails}/{has_fp}")
        if no_fp > 0:
            print(f"  Derangement, single hub exists: {no_fp_any_hub}/{no_fp} "
                  f"({100*no_fp_any_hub/no_fp:.1f}%)")
            print(f"  Derangement, no single hub:     {no_fp_no_hub}/{no_fp} "
                  f"({100*no_fp_no_hub/no_fp:.1f}%)")
            print(f"  Derangement 2-hub via σ² fp:    {no_fp_2hub_fp2}")
            print(f"  Derangement 2-hub other:        {no_fp_2hub_other}")
            print(f"  Derangement 2-hub FAIL:         {no_fp_2hub_fail}")


if __name__ == '__main__':
    main()
