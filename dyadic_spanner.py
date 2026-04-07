"""
Dyadic B-frame spanner construction.

Build a spanner like a hierarchical GOP:
- I-frames: M⁻ (diagonal 0) + M⁺ (diagonal k-1) — all k edges each
- B-frames: 2 edges per intermediate diagonal, chosen by dyadic recursion

For each intermediate diagonal d, pick 2 rows that maximize coverage.
Test whether this produces a valid spanner.
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


def matrix_to_edges(M, k):
    """Convert k×k matrix to temporal edge list for 2k-vertex graph."""
    edges = []
    for i in range(k):
        for j in range(k):
            edges.append((i, k + j, M[i][j]))
    return edges


def dyadic_construction(M, k):
    """Build spanner using dyadic B-frame construction.

    Returns list of (row, col) cross edges in the spanner.
    """
    spanner = set()

    # I-frames: M⁻ (diagonal 0) and M⁺ (diagonal k-1)
    # M⁻: column minimum for each column j
    for j in range(k):
        best_i = min(range(k), key=lambda i: M[i][j])
        spanner.add((best_i, j))

    # M⁺: row maximum for each row i
    for i in range(k):
        best_j = max(range(k), key=lambda j: M[i][j])
        spanner.add((i, best_j))

    # B-frames: for each intermediate diagonal, pick 2 rows
    # A diagonal d contains edges (i, (i+d)%k) for i=0,...,k-1
    for d in range(1, k - 1):
        # Pick 2 rows that maximize coverage
        # Strategy 1: dyadic bisection — pick rows at k/3 and 2k/3 positions
        # Strategy 2: greedy — pick the row that covers the most uncovered pairs

        # Let's try multiple strategies

        # Strategy: pick rows i1, i2 that maximize the number of
        # A-A and B-B pairs routable through diagonal d
        best_pair = None
        best_coverage = -1

        diag_edges = [(i, (i + d) % k) for i in range(k)]

        for idx1 in range(k):
            for idx2 in range(idx1 + 1, k):
                i1, j1 = diag_edges[idx1]
                i2, j2 = diag_edges[idx2]
                # How many A-A pairs can route through these two edges?
                # a_x → b_{j1} → a_{i1} needs M[x][j1] < M[i1][j1] (x arrives before i1)
                # or a_x → b_{j2} → a_{i2} needs M[x][j2] < M[i2][j2]
                # Plus B-B routing through rows i1, i2
                coverage = 0
                for x in range(k):
                    for xp in range(k):
                        if x == xp:
                            continue
                        # Can a_x → a_xp via (i1,j1) or (i2,j2)?
                        if M[x][j1] < M[xp][j1]:
                            coverage += 1
                        elif M[x][j2] < M[xp][j2]:
                            coverage += 1
                for y in range(k):
                    for yp in range(k):
                        if y == yp:
                            continue
                        if M[i1][y] < M[i1][yp]:
                            coverage += 1
                        elif M[i2][y] < M[i2][yp]:
                            coverage += 1
                if coverage > best_coverage:
                    best_coverage = coverage
                    best_pair = (diag_edges[idx1], diag_edges[idx2])

        if best_pair:
            spanner.add(best_pair[0])
            spanner.add(best_pair[1])

    return spanner


def dyadic_bisection_construction(M, k):
    """Build spanner using actual dyadic bisection (like hierarchical B-frames).

    Place diagonals in bisection order: mid first, then quarters, etc.
    For each diagonal, pick 2 rows.
    """
    spanner = set()

    # I-frames
    for j in range(k):
        best_i = min(range(k), key=lambda i: M[i][j])
        spanner.add((best_i, j))
    for i in range(k):
        best_j = max(range(k), key=lambda j: M[i][j])
        spanner.add((i, best_j))

    # Dyadic order of intermediate diagonals
    def bisect_order(lo, hi):
        """Generate diagonal indices in dyadic bisection order."""
        if lo > hi:
            return []
        if lo == hi:
            return [lo]
        mid = (lo + hi) // 2
        return [mid] + bisect_order(lo, mid - 1) + bisect_order(mid + 1, hi)

    diag_order = bisect_order(1, k - 2) if k > 2 else []

    for d in diag_order:
        diag_edges = [(i, (i + d) % k) for i in range(k)]

        # Pick 2 rows: one near the "top" and one near the "bottom" of the diagonal
        # Dyadic strategy: bisect the row range
        i1_idx = k // 3
        i2_idx = 2 * k // 3
        spanner.add(diag_edges[i1_idx])
        spanner.add(diag_edges[i2_idx])

    return spanner


def evenly_spaced_construction(M, k):
    """For each intermediate diagonal, pick 2 evenly-spaced rows."""
    spanner = set()

    # I-frames
    for j in range(k):
        best_i = min(range(k), key=lambda i: M[i][j])
        spanner.add((best_i, j))
    for i in range(k):
        best_j = max(range(k), key=lambda j: M[i][j])
        spanner.add((i, best_j))

    for d in range(1, k - 1):
        diag_edges = [(i, (i + d) % k) for i in range(k)]
        # Pick 2 evenly spaced
        i1 = k // 3
        i2 = 2 * k // 3
        spanner.add(diag_edges[i1])
        spanner.add(diag_edges[i2])

    return spanner


def check_spanner(k, spanner_edges, full_matrix):
    """Check if spanner preserves all-pairs reachability."""
    n = 2 * k
    full_timed = [(full_matrix[i][j], i, k + j)
                  for i in range(k) for j in range(k)]
    full_pairs = compute_reachability_pairs(n, full_timed)

    span_timed = [(full_matrix[i][j], i, k + j) for i, j in spanner_edges]
    span_pairs = compute_reachability_pairs(n, span_timed)

    missing = full_pairs - span_pairs
    # Classify missing
    aa = sum(1 for s, t in missing if s < k and t < k)
    bb = sum(1 for s, t in missing if s >= k and t >= k)
    ab = sum(1 for s, t in missing if (s < k) != (t < k))

    return {
        'valid': len(missing) == 0,
        'total_pairs': len(full_pairs),
        'span_pairs': len(span_pairs),
        'missing': len(missing),
        'aa_missing': aa,
        'bb_missing': bb,
        'ab_missing': ab,
    }


def main():
    print("=" * 70)
    print("DYADIC B-FRAME SPANNER CONSTRUCTION")
    print("=" * 70)

    # Part 1: SM(k) with greedy 2-per-diagonal
    print("\n--- SM(k): greedy 2-per-diagonal ---")
    for k in range(3, 10):
        M = generate_sm_matrix(k)
        spanner = dyadic_construction(M, k)
        result = check_spanner(k, spanner, M)

        n = 2 * k
        print(f"\nSM({k}) (n={n}, 2n-3={2*n-3}):")
        print(f"  Spanner size: {len(spanner)}")
        print(f"  Valid: {result['valid']}")
        if not result['valid']:
            print(f"  Missing: {result['missing']} "
                  f"(AA={result['aa_missing']}, BB={result['bb_missing']}, "
                  f"AB={result['ab_missing']})")

        # Show which edges were chosen
        m_minus = set()
        m_plus = set()
        intermediate = defaultdict(list)
        for i, j in spanner:
            d = (j - i) % k
            if d == 0:
                m_minus.add((i, j))
            elif d == k - 1:
                m_plus.add((i, j))
            else:
                intermediate[d].append((i, j))

        print(f"  M⁻: {len(m_minus)}, M⁺: {len(m_plus)}, "
              f"intermediate: {sum(len(v) for v in intermediate.values())}")
        for d in sorted(intermediate.keys()):
            print(f"    d={d}: {intermediate[d]}")

    # Part 2: Evenly-spaced construction
    print("\n\n--- SM(k): evenly-spaced 2-per-diagonal ---")
    for k in range(3, 10):
        M = generate_sm_matrix(k)
        spanner = evenly_spaced_construction(M, k)
        result = check_spanner(k, spanner, M)

        n = 2 * k
        print(f"SM({k}): size={len(spanner)}, valid={result['valid']}, "
              f"missing={result['missing']}")

    # Part 3: Dyadic bisection order
    print("\n\n--- SM(k): dyadic bisection ---")
    for k in range(3, 10):
        M = generate_sm_matrix(k)
        spanner = dyadic_bisection_construction(M, k)
        result = check_spanner(k, spanner, M)

        n = 2 * k
        print(f"SM({k}): size={len(spanner)}, valid={result['valid']}, "
              f"missing={result['missing']}")

    # Part 4: What's the minimum number of edges per diagonal that works?
    print("\n\n--- SM(k): how many edges per diagonal are needed? ---")
    for k in range(3, 10):
        M = generate_sm_matrix(k)
        n = 2 * k

        # For each intermediate diagonal, try 1 edge, 2 edges, ...
        # Start with M⁻ ∪ M⁺, then add diagonals one at a time
        base = set()
        for j in range(k):
            best_i = min(range(k), key=lambda i: M[i][j])
            base.add((best_i, j))
        for i in range(k):
            best_j = max(range(k), key=lambda j: M[i][j])
            base.add((i, best_j))

        # Check base alone
        result = check_spanner(k, base, M)
        print(f"\nSM({k}): M⁻∪M⁺ alone = {len(base)} edges, "
              f"valid={result['valid']}, missing={result['missing']}")

        # Try adding 1 edge per diagonal (best single edge)
        for edges_per_diag in [1, 2, 3]:
            spanner = set(base)
            for d in range(1, k - 1):
                diag_edges = [(i, (i + d) % k) for i in range(k)]
                # Try all subsets of size edges_per_diag, pick best
                from itertools import combinations
                best_sub = None
                best_missing = float('inf')
                for combo in combinations(range(k), edges_per_diag):
                    trial = set(spanner)
                    for idx in combo:
                        trial.add(diag_edges[idx])
                    r = check_spanner(k, trial, M)
                    if r['missing'] < best_missing:
                        best_missing = r['missing']
                        best_sub = combo
                if best_sub:
                    for idx in best_sub:
                        spanner.add(diag_edges[idx])

            result = check_spanner(k, spanner, M)
            print(f"  + {edges_per_diag}/diag: {len(spanner)} edges, "
                  f"valid={result['valid']}, missing={result['missing']}")


if __name__ == '__main__':
    main()
