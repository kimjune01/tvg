"""
Double star on general extremally matched bicliques.

The construction: M⁻ ∪ M⁺ ∪ star(row h) ∪ star(col c), with m⁺(h) = c.

Key question: does m⁺(h) = c guarantee that M[h][c] is BOTH
the row max (by definition of m⁺) AND the column max (needed for
zero forward chain failures)?

For SM(k) this holds because of the circulant structure. For general
bicliques it might not — and that's where failures would appear.
"""

import random
from collections import defaultdict

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
    n = 2 * k
    num_vminus = k * (k - 1) // 2
    num_cross = k * k
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


def double_star(M, k, h, c):
    m_minus = [min(range(k), key=lambda i: M[i][j]) for j in range(k)]
    m_plus = [max(range(k), key=lambda j: M[i][j]) for i in range(k)]
    edges = set()
    for j in range(k):
        edges.add((m_minus[j], j))
    for i in range(k):
        edges.add((i, m_plus[i]))
    for j in range(k):
        edges.add((h, j))
    for i in range(k):
        edges.add((i, c))
    return edges


def check_spanner(k, M, edges):
    n = 2 * k
    full_timed = [(M[i][j], i, k + j) for i in range(k) for j in range(k)]
    full_pairs = compute_reachability_pairs(n, full_timed)
    span_timed = [(M[i][j], i, k + j) for i, j in edges]
    span_pairs = compute_reachability_pairs(n, span_timed)
    return full_pairs - span_pairs


def main():
    print("=" * 70)
    print("DOUBLE STAR ON GENERAL EXTREMALLY MATCHED BICLIQUES")
    print("=" * 70)

    for k in range(3, 9):
        n = 2 * k
        samples = {3: 500, 4: 300, 5: 200, 6: 100, 7: 50, 8: 20}[k]

        # Track results for m⁺(h)=c construction
        valid_mplus = 0
        fail_mplus = 0
        fail_details = []

        # Track results for best (h,c) over all choices
        valid_any = 0
        fail_any = 0

        # Track: is M[h][c] also column max?
        col_max_count = 0
        not_col_max_count = 0

        for trial in range(samples):
            result = generate_random_biclique(k)
            if result is None:
                continue

            M, m_minus, m_plus = result

            # Try all h with m⁺(h)=c
            best_missing_mplus = None
            for h in range(k):
                c = m_plus[h]
                edges = double_star(M, k, h, c)
                missing = check_spanner(k, M, edges)

                # Is M[h][c] the column max?
                col_vals = [M[i][c] for i in range(k)]
                is_col_max = M[h][c] == max(col_vals)

                if best_missing_mplus is None or len(missing) < len(best_missing_mplus):
                    best_missing_mplus = missing
                    best_h, best_c = h, c
                    best_is_col_max = is_col_max

                if len(missing) == 0 and is_col_max:
                    col_max_count += 1
                    break
                elif len(missing) == 0 and not is_col_max:
                    not_col_max_count += 1
                    break

            if len(best_missing_mplus) == 0:
                valid_mplus += 1
            else:
                fail_mplus += 1
                if len(fail_details) < 5:
                    fail_details.append({
                        'k': k, 'h': best_h, 'c': best_c,
                        'missing': len(best_missing_mplus),
                        'is_col_max': best_is_col_max,
                        'M': [row[:] for row in M],
                        'm_minus': m_minus[:],
                        'm_plus': m_plus[:],
                    })

            # Try all (h, c) pairs
            found_any = False
            for h in range(k):
                for c in range(k):
                    edges = double_star(M, k, h, c)
                    missing = check_spanner(k, M, edges)
                    if len(missing) == 0:
                        found_any = True
                        break
                if found_any:
                    break

            if found_any:
                valid_any += 1
            else:
                fail_any += 1

        total = valid_mplus + fail_mplus
        print(f"\nk={k} (n={n}, 2n-3={2*n-3}), {total} samples:")
        print(f"  m⁺(h)=c valid: {valid_mplus}/{total} "
              f"({100*valid_mplus/total:.1f}%)")
        print(f"  Any (h,c) valid: {valid_any}/{total} "
              f"({100*valid_any/total:.1f}%)")
        if col_max_count + not_col_max_count > 0:
            print(f"  When valid: col_max={col_max_count}, "
                  f"not_col_max={not_col_max_count}")

        if fail_details:
            print(f"\n  Failure examples:")
            for fd in fail_details[:3]:
                print(f"    h={fd['h']}, c={fd['c']}, "
                      f"missing={fd['missing']}, "
                      f"col_max={fd['is_col_max']}")
                print(f"    M⁻={fd['m_minus']}, M⁺={fd['m_plus']}")
                if k <= 5:
                    for i, row in enumerate(fd['M']):
                        print(f"      row {i}: {row}")

    # Part 2: When double star fails, what's the minimum with one extra edge?
    print("\n\n" + "=" * 70)
    print("FAILURES: CAN ONE EXTRA EDGE FIX THEM?")
    print("=" * 70)

    random.seed(42)
    for k in range(3, 8):
        n = 2 * k
        fix_count = 0
        total_fails = 0

        for trial in range(500 if k <= 5 else 100):
            result = generate_random_biclique(k)
            if result is None:
                continue

            M, m_minus, m_plus = result

            # Find best m⁺(h)=c
            best_missing = None
            for h in range(k):
                c = m_plus[h]
                edges = double_star(M, k, h, c)
                missing = check_spanner(k, M, edges)
                if best_missing is None or len(missing) < len(best_missing):
                    best_missing = missing
                    best_edges = edges
                    best_h, best_c = h, c

            if len(best_missing) == 0:
                continue

            total_fails += 1

            # Try adding one extra cross edge
            fixed = False
            for i in range(k):
                for j in range(k):
                    if (i, j) in best_edges:
                        continue
                    trial_edges = best_edges | {(i, j)}
                    missing = check_spanner(k, M, trial_edges)
                    if len(missing) == 0:
                        fixed = True
                        fix_count += 1
                        if total_fails <= 3:
                            print(f"\n  k={k} fix: add ({i},{j}), "
                                  f"h={best_h}, c={best_c}, "
                                  f"total={len(trial_edges)}={2*n-4}+1={2*n-3}")
                        break
                if fixed:
                    break

        if total_fails > 0:
            print(f"\n  k={k}: {total_fails} failures, "
                  f"{fix_count} fixed with +1 edge "
                  f"({100*fix_count/total_fails:.0f}%)")


if __name__ == '__main__':
    main()
