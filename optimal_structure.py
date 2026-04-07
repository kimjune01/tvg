"""
Analyze the structure of optimal SM(k) spanners.

Key question: the optimal spanner uses 2n-4 cross edges (no internal).
Essential = M⁻ ∪ M⁺ (2k edges). The extra k-4 edges come from which
diagonals? What pattern do they follow?

Also: for random bicliques, are optimal spanners also all-cross?
"""

import random
from collections import defaultdict, Counter

random.seed(42)


def compute_reachability_pairs(n, timed_edges):
    """Return set of reachable (source, target) pairs."""
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


def generate_sm(k):
    n = 2 * k
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
    m = len(edges)
    eidx = {}
    for i, (u, v) in enumerate(edges):
        eidx[(u, v)] = i
        eidx[(v, u)] = i
    ts = [0] * m
    t = 1
    for i in range(k):
        for j in range(i + 1, k):
            ts[eidx[(i, j)]] = t
            t += 1
    for d in range(k):
        for i in range(k):
            j = (i + d) % k
            idx = eidx[(min(i, k + j), max(i, k + j))]
            if ts[idx] == 0:
                ts[idx] = t
                t += 1
    for i in range(k):
        for j in range(i + 1, k):
            ts[eidx[(k + i, k + j)]] = t
            t += 1
    return n, edges, ts, eidx


def find_optimal_spanner(n, edges, ts, num_trials=200):
    """Find minimum spanner via randomized greedy + local search."""
    m = len(edges)
    timed_all = sorted([(ts[i], edges[i][0], edges[i][1]) for i in range(m)])
    target = compute_reachability_pairs(n, timed_all)

    best = list(range(m))

    for trial in range(num_trials):
        order = list(range(m))
        random.shuffle(order)
        included = list(range(m))
        for idx in order:
            if idx not in included:
                continue
            candidate = [i for i in included if i != idx]
            sub = [(ts[i], edges[i][0], edges[i][1]) for i in candidate]
            if compute_reachability_pairs(n, sub) == target:
                included = candidate

        # Local search: try removing
        changed = True
        while changed:
            changed = False
            for idx in list(included):
                candidate = [i for i in included if i != idx]
                sub = [(ts[i], edges[i][0], edges[i][1]) for i in candidate]
                if compute_reachability_pairs(n, sub) == target:
                    included = candidate
                    changed = True
                    break

        if len(included) < len(best):
            best = included

    return best


def analyze_diagonal_pattern(k, spanner_indices, edges, ts, eidx):
    """Analyze which diagonals the spanner edges belong to."""
    diag_edges = defaultdict(list)

    for idx in spanner_indices:
        u, v = edges[idx]
        if (u < k) != (v < k):  # cross edge
            a = u if u < k else v
            b = (v if v >= k else u) - k
            d = (b - a) % k
            diag_edges[d].append((a, b, ts[idx]))

    return diag_edges


def compute_coverage(n, edges, ts, spanner_indices):
    """For each edge in spanner, how many source-target pairs does it uniquely cover?"""
    timed_all = [(ts[i], edges[i][0], edges[i][1]) for i in spanner_indices]
    full_pairs = compute_reachability_pairs(n, timed_all)

    coverage = {}
    for idx in spanner_indices:
        remaining = [i for i in spanner_indices if i != idx]
        sub = [(ts[i], edges[i][0], edges[i][1]) for i in remaining]
        sub_pairs = compute_reachability_pairs(n, sub)
        unique = full_pairs - sub_pairs
        coverage[idx] = len(unique)

    return coverage


def main():
    print("=" * 70)
    print("OPTIMAL SPANNER STRUCTURE ANALYSIS")
    print("=" * 70)

    for k in range(3, 9):
        n, edges, ts, eidx = generate_sm(k)
        m = len(edges)

        if k <= 7:
            trials = {3: 500, 4: 500, 5: 200, 6: 100, 7: 50, 8: 20}[k]
            optimal = find_optimal_spanner(n, edges, ts, num_trials=trials)
        else:
            optimal = find_optimal_spanner(n, edges, ts, num_trials=20)

        # Classify edges
        cross_edges = [i for i in optimal if (edges[i][0] < k) != (edges[i][1] < k)]
        vminus_edges = [i for i in optimal if edges[i][0] < k and edges[i][1] < k]
        vplus_edges = [i for i in optimal if edges[i][0] >= k and edges[i][1] >= k]

        print(f"\nSM({k}) (n={n}, 2n-3={2*n-3}):")
        print(f"  Optimal size: {len(optimal)} (gap to 2n-3: {len(optimal) - (2*n-3)})")
        print(f"  Cross: {len(cross_edges)}, V⁻ internal: {len(vminus_edges)}, "
              f"V⁺ internal: {len(vplus_edges)}")

        # Diagonal pattern
        diag = analyze_diagonal_pattern(k, optimal, edges, ts, eidx)
        print(f"  Diagonals used: {sorted(diag.keys())}")
        for d in sorted(diag.keys()):
            members = [(a, b) for a, b, t in diag[d]]
            print(f"    d={d}: {len(diag[d])} edges — {members}")

        # Which rows/columns have M⁻, M⁺, and extras?
        row_edges = defaultdict(list)
        col_edges = defaultdict(list)
        for idx in cross_edges:
            u, v = edges[idx]
            a = u if u < k else v
            b = (v if v >= k else u) - k
            d = (b - a) % k
            row_edges[a].append((b, d, ts[idx]))
            col_edges[b].append((a, d, ts[idx]))

        print(f"  Per-row edge count: {[len(row_edges[i]) for i in range(k)]}")
        print(f"  Per-col edge count: {[len(col_edges[j]) for j in range(k)]}")

        # Coverage analysis (only for small k)
        if k <= 5:
            coverage = compute_coverage(n, edges, ts, optimal)
            print(f"  Unique coverage per edge:")
            for idx in sorted(coverage, key=lambda i: -coverage[i]):
                u, v = edges[idx]
                if (u < k) != (v < k):
                    a = u if u < k else v
                    b = (v if v >= k else u) - k
                    d = (b - a) % k
                    print(f"    (a{a},b{b}) d={d} t={ts[idx]}: "
                          f"uniquely covers {coverage[idx]} pairs")
                else:
                    print(f"    ({u},{v}) t={ts[idx]}: "
                          f"uniquely covers {coverage[idx]} pairs")


if __name__ == '__main__':
    main()
