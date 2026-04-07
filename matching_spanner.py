"""
Matching-based spanner for bi-cliques.

Hypothesis: the minimum spanner of SM(k) is a union of 3 perfect matchings.
Specifically diagonals 0, 1, and k-1 (first, second, last).

Test:
1. Does {diagonal 0, diagonal 1, diagonal k-1} always span SM(k)?
2. Does any pair of diagonals suffice? (probably not)
3. For random bi-cliques: what's the minimum number of matchings needed?
4. Which 3 matchings work? Is it always first + second + last?
"""

import random
from itertools import combinations
from collections import defaultdict


def make_edges(n):
    return [(i, j) for i in range(n) for j in range(i + 1, n)]


def compute_reachability(n, timed_edges):
    reached_by = [dict() for _ in range(n)]
    for i in range(n):
        reached_by[i][i] = 0
    for t, u, v in timed_edges:
        sources_u = {s: arr for s, arr in reached_by[u].items() if arr <= t}
        sources_v = {s: arr for s, arr in reached_by[v].items() if arr <= t}
        for s, arr in sources_u.items():
            if s not in reached_by[v] or t < reached_by[v][s]:
                reached_by[v][s] = t
        for s, arr in sources_v.items():
            if s not in reached_by[u] or t < reached_by[u][s]:
                reached_by[u][s] = t
    reach = [0] * n
    for v in range(n):
        for s in reached_by[v]:
            if s != v:
                reach[s] |= (1 << v)
    return reach


def generate_sm(k):
    """SM(k) with proper timestamp assignment."""
    n = 2 * k
    edges = make_edges(n)
    m = len(edges)
    edge_to_idx = {}
    for i, (u, v) in enumerate(edges):
        edge_to_idx[(u, v)] = i
        edge_to_idx[(v, u)] = i

    timestamps = [0] * m
    t = 1

    # V- internal
    for i in range(k):
        for j in range(i + 1, k):
            timestamps[edge_to_idx[(i, j)]] = t; t += 1

    # Cross edges by diagonal
    for d in range(k):
        for i in range(k):
            j = (i + d) % k
            idx = edge_to_idx[(min(i, k+j), max(i, k+j))]
            if timestamps[idx] == 0:
                timestamps[idx] = t; t += 1

    # V+ internal
    for i in range(k):
        for j in range(i + 1, k):
            timestamps[edge_to_idx[(k+i, k+j)]] = t; t += 1

    return n, edges, timestamps, edge_to_idx


def diagonal_edges(k, d, edge_to_idx):
    """Return edge indices for diagonal d of SM(k)."""
    idx = []
    for i in range(k):
        j = (i + d) % k
        idx.append(edge_to_idx[(min(i, k+j), max(i, k+j))])
    return idx


def test_subset_spans(n, edges, timestamps, subset_idx):
    """Does this subset of edges span (preserve all-pairs reachability)?"""
    m = len(edges)
    timed_all = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in range(m)])
    target = compute_reachability(n, timed_all)
    sub = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in subset_idx])
    reach = compute_reachability(n, sub)
    return reach == target


def run_sm_tests():
    print("SHIFTED MATCHING: diagonal-based spanners")
    print("=" * 70)

    for k in range(3, 9):
        n, edges, ts, eidx = generate_sm(k)
        m = len(edges)
        print(f"\nSM({k}): n={n}, m={m}, 2n-3={2*n-3}, 3k={3*k}")

        # Test: diagonals 0, 1, k-1
        d0 = diagonal_edges(k, 0, eidx)
        d1 = diagonal_edges(k, 1, eidx)
        dk = diagonal_edges(k, k-1, eidx)

        three_diags = d0 + d1 + dk
        spans_3 = test_subset_spans(n, edges, ts, three_diags)
        print(f"  Diags {{0,1,{k-1}}}: {len(three_diags)} edges, spans={spans_3}")

        # Test all pairs of diagonals
        pair_works = []
        for da in range(k):
            for db in range(da + 1, k):
                sub = diagonal_edges(k, da, eidx) + diagonal_edges(k, db, eidx)
                if test_subset_spans(n, edges, ts, sub):
                    pair_works.append((da, db))
        print(f"  Any pair of diags that spans: {pair_works[:5]}{'...' if len(pair_works) > 5 else ''} ({len(pair_works)} total)")

        # Test all triples of diagonals
        triple_works = []
        for da in range(k):
            for db in range(da + 1, k):
                for dc in range(db + 1, k):
                    sub = diagonal_edges(k, da, eidx) + diagonal_edges(k, db, eidx) + diagonal_edges(k, dc, eidx)
                    if test_subset_spans(n, edges, ts, sub):
                        triple_works.append((da, db, dc))
        print(f"  Triples of diags that span: {triple_works[:10]}{'...' if len(triple_works) > 10 else ''} ({len(triple_works)} total)")

        # What's the minimum number of diagonals needed?
        for num_diags in range(1, k + 1):
            found = False
            for combo in combinations(range(k), num_diags):
                sub = []
                for d in combo:
                    sub.extend(diagonal_edges(k, d, eidx))
                if test_subset_spans(n, edges, ts, sub):
                    print(f"  Min diagonals needed: {num_diags}, e.g. {combo}")
                    found = True
                    break
            if found:
                break

        # Can we do better with mixed (some cross + some internal)?
        # Find greedy minimum
        included = list(range(m))
        for idx in sorted(range(m), key=lambda i: -ts[i]):
            candidate = [i for i in included if i != idx]
            sub = sorted([(ts[i], edges[i][0], edges[i][1]) for i in candidate])
            timed_all = sorted([(ts[i], edges[i][0], edges[i][1]) for i in range(m)])
            if compute_reachability(n, sub) == compute_reachability(n, timed_all):
                included = candidate
        print(f"  Greedy minimum: {len(included)} edges")

        # How many are cross vs internal?
        cross_count = sum(1 for i in included
                         if (edges[i][0] < k) != (edges[i][1] < k))
        internal_count = len(included) - cross_count
        print(f"    Cross: {cross_count}, Internal: {internal_count}")


def run_random_biclique_tests():
    print(f"\n{'='*70}")
    print("RANDOM BI-CLIQUES: matching structure")
    print("=" * 70)

    random.seed(42)
    for k in [3, 4, 5]:
        n = 2 * k
        print(f"\nRandom bi-clique k={k} (n={n}):")

        min_sizes = []
        all_cross = 0
        total = 0

        samples = 500 if k <= 4 else 100
        for _ in range(samples):
            edges = make_edges(n)
            m = len(edges)
            eidx = {}
            for i, (u, v) in enumerate(edges):
                eidx[(u, v)] = i; eidx[(v, u)] = i

            ts = [0] * m
            t = 1
            internal_m = [(u, v) for (u, v) in edges if u < k and v < k]
            random.shuffle(internal_m)
            for (u, v) in internal_m:
                ts[eidx[(u, v)]] = t; t += 1
            cross = [(u, v) for (u, v) in edges if (u < k) != (v < k)]
            random.shuffle(cross)
            for (u, v) in cross:
                ts[eidx[(u, v)]] = t; t += 1
            internal_p = [(u, v) for (u, v) in edges if u >= k and v >= k]
            random.shuffle(internal_p)
            for (u, v) in internal_p:
                ts[eidx[(u, v)]] = t; t += 1

            # Greedy minimum
            included = list(range(m))
            timed_all = sorted([(ts[i], edges[i][0], edges[i][1]) for i in range(m)])
            target = compute_reachability(n, timed_all)
            for idx in sorted(range(m), key=lambda i: -ts[i]):
                candidate = [i for i in included if i != idx]
                sub = sorted([(ts[i], edges[i][0], edges[i][1]) for i in candidate])
                if compute_reachability(n, sub) == target:
                    included = candidate

            min_sizes.append(len(included))
            total += 1
            cross_in_spanner = sum(1 for i in included
                                   if (edges[i][0] < k) != (edges[i][1] < k))
            if cross_in_spanner == len(included):
                all_cross += 1

        avg = sum(min_sizes) / len(min_sizes)
        print(f"  Greedy min: min={min(min_sizes)} avg={avg:.1f} max={max(min_sizes)} "
              f"(2n-3={2*n-3})")
        print(f"  All-cross spanners: {all_cross}/{total} ({all_cross/total*100:.0f}%)")


if __name__ == "__main__":
    run_sm_tests()
    run_random_biclique_tests()
