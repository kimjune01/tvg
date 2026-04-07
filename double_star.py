"""
Double star construction: M⁻ ∪ M⁺ ∪ star(row h) ∪ star(col c)
with the constraint m⁺(h) = c.

Verify:
1. Does this always produce a valid spanner?
2. Edge count = 4k-4 = 2n-4?
3. Which pairs fail the 3-hop chain? Are they exactly the hub pairs?
4. What breaks at SM(8)?
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


def generate_sm_matrix(k):
    M = [[0] * k for _ in range(k)]
    t = 1
    for d in range(k):
        for i in range(k):
            j = (i + d) % k
            M[i][j] = t
            t += 1
    return M


def get_matchings(M, k):
    m_minus = [0] * k  # m_minus[j] = argmin_i M[i][j]
    m_plus = [0] * k   # m_plus[i] = argmax_j M[i][j]
    for j in range(k):
        m_minus[j] = min(range(k), key=lambda i: M[i][j])
    for i in range(k):
        m_plus[i] = max(range(k), key=lambda j: M[i][j])
    return m_minus, m_plus


def double_star_construction(M, k, h, c):
    """Build M⁻ ∪ M⁺ ∪ star(row h) ∪ star(col c)."""
    m_minus, m_plus = get_matchings(M, k)

    edges = set()

    # M⁻: for each column j, edge (m_minus[j], j)
    for j in range(k):
        edges.add((m_minus[j], j))

    # M⁺: for each row i, edge (i, m_plus[i])
    for i in range(k):
        edges.add((i, m_plus[i]))

    # Star(row h): all columns
    for j in range(k):
        edges.add((h, j))

    # Star(col c): all rows
    for i in range(k):
        edges.add((i, c))

    return edges


def check_spanner_detail(k, M, spanner_edges):
    """Check spanner validity and identify missing pairs."""
    n = 2 * k
    full_timed = [(M[i][j], i, k + j) for i in range(k) for j in range(k)]
    full_pairs = compute_reachability_pairs(n, full_timed)

    span_timed = [(M[i][j], i, k + j) for i, j in spanner_edges]
    span_pairs = compute_reachability_pairs(n, span_timed)

    missing = full_pairs - span_pairs
    return missing, full_pairs


def analyze_3hop_failures(M, k, h, c):
    """Which pairs fail the 3-hop chain a_i → b_c → a_h → b_j?

    Chain needs: M[i][c] < M[h][c] < M[h][j]
    Fails when:
    - M[i][c] >= M[h][c] (row i doesn't arrive at b_c before a_h)
    - M[h][j] <= M[h][c] (a_h's value in col j not greater than in col c)
    """
    first_fails = []  # rows where M[i][c] >= M[h][c]
    second_fails = []  # cols where M[h][j] <= M[h][c]

    for i in range(k):
        if i == h:
            continue
        if M[i][c] >= M[h][c]:
            first_fails.append(i)

    for j in range(k):
        if j == c:
            continue
        if M[h][j] <= M[h][c]:
            second_fails.append(j)

    return first_fails, second_fails


def analyze_reverse_3hop(M, k, h, c):
    """Reverse direction: b_j → a_i needs a path too.

    Route b_j → a_h → b_c → a_i needs:
    M[h][j] < M[h][c] < M[i][c]

    This is the REVERSE timestamp order — only works if we go
    b_j → a_h (at time M[h][j]) then a_h → b_c (at time M[h][c])
    then b_c → a_i (at time M[i][c]).
    Needs M[h][j] < M[h][c] < M[i][c].
    """
    first_fails = []  # cols where M[h][j] >= M[h][c]
    second_fails = []  # rows where M[i][c] <= M[h][c]

    for j in range(k):
        if j == c:
            continue
        if M[h][j] >= M[h][c]:
            first_fails.append(j)

    for i in range(k):
        if i == h:
            continue
        if M[i][c] <= M[h][c]:
            second_fails.append(i)

    return first_fails, second_fails


def main():
    print("=" * 70)
    print("DOUBLE STAR CONSTRUCTION: M⁻ ∪ M⁺ ∪ star(h) ∪ star(c)")
    print("=" * 70)

    for k in range(3, 12):
        M = generate_sm_matrix(k)
        m_minus, m_plus = get_matchings(M, k)
        n = 2 * k

        print(f"\n{'='*60}")
        print(f"SM({k}) (n={n}, 2n-3={2*n-3}, 2n-4={2*n-4})")
        print(f"{'='*60}")
        print(f"  M⁻: {m_minus}")
        print(f"  M⁺: {m_plus}")

        # Try all (h, c) pairs with m⁺(h) = c
        best_result = None
        all_results = []

        for h in range(k):
            c = m_plus[h]
            edges = double_star_construction(M, k, h, c)
            missing, full = check_spanner_detail(k, M, edges)

            fwd_row_fails, fwd_col_fails = analyze_3hop_failures(M, k, h, c)
            rev_col_fails, rev_row_fails = analyze_reverse_3hop(M, k, h, c)

            result = {
                'h': h, 'c': c,
                'edges': len(edges),
                'missing': len(missing),
                'missing_pairs': missing,
                'fwd_row_fails': fwd_row_fails,
                'fwd_col_fails': fwd_col_fails,
                'rev_col_fails': rev_col_fails,
                'rev_row_fails': rev_row_fails,
            }
            all_results.append(result)

            if best_result is None or len(missing) < best_result['missing']:
                best_result = result

        # Summary
        valid_count = sum(1 for r in all_results if r['missing'] == 0)
        print(f"\n  m⁺(h)=c constraint: {k} choices")
        print(f"  Valid spanners: {valid_count}/{k}")

        # Show best result
        r = best_result
        print(f"\n  Best: h={r['h']}, c={r['c']}, "
              f"edges={r['edges']}, missing={r['missing']}")
        print(f"    Forward chain fails: rows {r['fwd_row_fails']}, "
              f"cols {r['fwd_col_fails']}")
        print(f"    Reverse chain fails: cols {r['rev_col_fails']}, "
              f"rows {r['rev_row_fails']}")

        if r['missing'] > 0:
            # Show missing pairs
            missing_list = sorted(r['missing'])
            print(f"    Missing pairs ({len(missing_list)}):")
            for s, t in missing_list[:20]:
                sl = 'a' if s < k else 'b'
                tl = 'a' if t < k else 'b'
                si = s if s < k else s - k
                ti = t if t < k else t - k
                print(f"      {sl}{si} → {tl}{ti}")
            if len(missing_list) > 20:
                print(f"      ... and {len(missing_list)-20} more")

        # Also try without m⁺(h)=c constraint — any (h,c)
        print(f"\n  All (h,c) pairs:")
        best_any = None
        valid_any = 0
        for h in range(k):
            for c in range(k):
                edges = double_star_construction(M, k, h, c)
                missing, _ = check_spanner_detail(k, M, edges)
                if len(missing) == 0:
                    valid_any += 1
                if best_any is None or len(missing) < best_any[0]:
                    best_any = (len(missing), h, c, len(edges))

        print(f"    Valid: {valid_any}/{k*k}")
        print(f"    Best: h={best_any[1]}, c={best_any[2]}, "
              f"edges={best_any[3]}, missing={best_any[0]}")

        # Edge count analysis
        edges = double_star_construction(M, k, r['h'], r['c'])
        m_minus_edges = {(m_minus[j], j) for j in range(k)}
        m_plus_edges = {(i, m_plus[i]) for i in range(k)}
        star_h = {(r['h'], j) for j in range(k)}
        star_c = {(i, r['c']) for i in range(k)}

        only_mminus = m_minus_edges - m_plus_edges - star_h - star_c
        only_mplus = m_plus_edges - m_minus_edges - star_h - star_c
        only_starh = star_h - m_minus_edges - m_plus_edges - star_c
        only_starc = star_c - m_minus_edges - m_plus_edges - star_h
        overlaps = len(m_minus_edges) + len(m_plus_edges) + len(star_h) + len(star_c) - len(edges)

        print(f"\n  Edge breakdown:")
        print(f"    M⁻ only: {len(only_mminus)}")
        print(f"    M⁺ only: {len(only_mplus)}")
        print(f"    star(h) only: {len(only_starh)}")
        print(f"    star(c) only: {len(only_starc)}")
        print(f"    Overlaps saved: {overlaps}")
        print(f"    Total: {len(edges)} (target 2n-4={2*n-4})")


if __name__ == '__main__':
    main()
