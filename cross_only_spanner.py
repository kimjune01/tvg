"""
Do cross edges alone span the full temporal graph?

For SM(k), optimal spanners use zero internal edges. Does this generalize
to arbitrary extremally matched bicliques?

Questions:
1. Can cross edges alone provide A-A and B-B temporal connectivity?
2. If yes: what's the minimum cross-only spanner size?
3. If no: which bicliques need internal edges, and why?
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


def generate_sm(k):
    n = 2 * k
    edges = []
    t = 1
    for i in range(k):
        for j in range(i + 1, k):
            edges.append((i, j, t))
            t += 1
    for d in range(k):
        for i in range(k):
            j = (i + d) % k
            edges.append((i, k + j, t))
            t += 1
    for i in range(k):
        for j in range(i + 1, k):
            edges.append((k + i, k + j, t))
            t += 1
    return n, edges


def generate_biclique_constructive(k, max_attempts=1000):
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
        cross_time_by_idx = [0] * (k * k)
        base = num_vminus + 1
        for rank, node in enumerate(order):
            cross_time_by_idx[node] = base + rank
        cross_time = {}
        for i in range(k):
            for j in range(k):
                cross_time[(i, j)] = cross_time_by_idx[edge_idx[(i, j)]]
        num_vplus = k * (k - 1) // 2
        vminus_times = list(range(1, num_vminus + 1))
        random.shuffle(vminus_times)
        vplus_base = num_vminus + num_cross + 1
        vplus_times = list(range(vplus_base, vplus_base + num_vplus))
        random.shuffle(vplus_times)
        edges = []
        vi = 0
        for i in range(k):
            for j in range(i + 1, k):
                edges.append((i, j, vminus_times[vi]))
                vi += 1
        for i in range(k):
            for j in range(k):
                edges.append((i, k + j, cross_time[(i, j)]))
        pi = 0
        for i in range(k):
            for j in range(i + 1, k):
                edges.append((k + i, k + j, vplus_times[pi]))
                pi += 1
        return n, edges, m_minus, m_plus
    return None


def classify_edges(k, edges):
    """Split edges into cross, vminus internal, vplus internal."""
    cross = []
    vminus = []
    vplus = []
    for u, v, t in edges:
        if u < k and v >= k:
            cross.append((u, v, t))
        elif u < k and v < k:
            vminus.append((u, v, t))
        elif u >= k and v >= k:
            vplus.append((u, v, t))
    return cross, vminus, vplus


def find_min_cross_spanner(k, n, all_edges, cross_edges, num_trials=100):
    """Find minimum subset of cross edges that spans ALL pairs
    (including A-A and B-B) that are reachable in the full graph."""
    timed_all = [(t, u, v) for u, v, t in all_edges]
    full_pairs = compute_reachability_pairs(n, timed_all)

    timed_cross_all = [(t, u, v) for u, v, t in cross_edges]
    cross_only_pairs = compute_reachability_pairs(n, timed_cross_all)

    # How many pairs does cross-only cover?
    missing = full_pairs - cross_only_pairs
    aa_missing = sum(1 for s, t in missing if s < k and t < k)
    bb_missing = sum(1 for s, t in missing if s >= k and t >= k)
    ab_missing = sum(1 for s, t in missing if (s < k) != (t < k))

    if missing:
        return {
            'cross_spans_all': False,
            'total_pairs': len(full_pairs),
            'cross_pairs': len(cross_only_pairs),
            'missing': len(missing),
            'aa_missing': aa_missing,
            'bb_missing': bb_missing,
            'ab_missing': ab_missing,
        }

    # Cross edges span everything! Find minimum subset.
    m = len(cross_edges)
    best = list(range(m))

    for trial in range(num_trials):
        order = list(range(m))
        random.shuffle(order)
        included = list(range(m))
        for idx in order:
            if idx not in included:
                continue
            candidate = [i for i in included if i != idx]
            sub = [(cross_edges[i][2], cross_edges[i][0], cross_edges[i][1])
                   for i in candidate]
            if compute_reachability_pairs(n, sub) == full_pairs:
                included = candidate

        if len(included) < len(best):
            best = included

    return {
        'cross_spans_all': True,
        'total_pairs': len(full_pairs),
        'cross_pairs': len(cross_only_pairs),
        'missing': 0,
        'min_cross_spanner': len(best),
        'spanner_indices': best,
    }


def main():
    print("=" * 70)
    print("CROSS-ONLY SPANNER: DOES IT GENERALIZE BEYOND SM(k)?")
    print("=" * 70)

    # Part 1: SM(k) verification
    print("\n--- SM(k): cross-only spans everything ---")
    for k in range(3, 9):
        n, edges = generate_sm(k)
        cross, vminus, vplus = classify_edges(k, edges)
        result = find_min_cross_spanner(k, n, edges, cross, num_trials=50)

        print(f"\nSM({k}) (n={n}, 2n-3={2*n-3}):")
        print(f"  Cross edges: {len(cross)}, V⁻: {len(vminus)}, V⁺: {len(vplus)}")
        print(f"  Cross spans all: {result['cross_spans_all']}")
        if result['cross_spans_all']:
            print(f"  Min cross-only spanner: {result['min_cross_spanner']}")
            print(f"  Gap to 2n-3: {result['min_cross_spanner'] - (2*n-3)}")
        else:
            print(f"  Missing: {result['missing']} "
                  f"(A-A: {result['aa_missing']}, B-B: {result['bb_missing']}, "
                  f"A-B: {result['ab_missing']})")

    # Part 2: Random extremally matched bicliques
    print("\n\n--- Random bicliques: cross-only spanning ---")
    for k in range(3, 8):
        n = 2 * k
        samples = {3: 300, 4: 200, 5: 100, 6: 50, 7: 20}[k]

        cross_spans_count = 0
        cross_fails = 0
        min_sizes = []
        missing_types = defaultdict(int)

        for trial in range(samples):
            result = generate_biclique_constructive(k)
            if result is None:
                continue

            bn, bedges, bm_minus, bm_plus = result
            cross, vminus, vplus = classify_edges(k, bedges)
            r = find_min_cross_spanner(k, bn, bedges, cross,
                                       num_trials=20 if k <= 5 else 10)

            if r['cross_spans_all']:
                cross_spans_count += 1
                min_sizes.append(r['min_cross_spanner'])
            else:
                cross_fails += 1
                if r['aa_missing'] > 0:
                    missing_types['A-A'] += 1
                if r['bb_missing'] > 0:
                    missing_types['B-B'] += 1
                if r['ab_missing'] > 0:
                    missing_types['A-B'] += 1

        total = cross_spans_count + cross_fails
        print(f"\nk={k} (n={n}, 2n-3={2*n-3}), {total} samples:")
        print(f"  Cross spans all: {cross_spans_count}/{total} "
              f"({100*cross_spans_count/total:.1f}%)")
        if cross_fails:
            print(f"  Cross FAILS: {cross_fails} — missing types: {dict(missing_types)}")
        if min_sizes:
            print(f"  Min cross-only spanner: min={min(min_sizes)}, "
                  f"max={max(min_sizes)}, avg={sum(min_sizes)/len(min_sizes):.1f}")
            within = sum(1 for s in min_sizes if s <= 2*n - 3)
            print(f"  Within 2n-3: {within}/{len(min_sizes)} "
                  f"({100*within/len(min_sizes):.1f}%)")

    # Part 3: When cross-only fails, what's the failure mode?
    print("\n\n--- Failure anatomy (first few failures per k) ---")
    for k in range(3, 7):
        n = 2 * k
        failures_shown = 0

        for trial in range(500):
            result = generate_biclique_constructive(k)
            if result is None:
                continue

            bn, bedges, bm_minus, bm_plus = result
            cross, vminus, vplus = classify_edges(k, bedges)
            r = find_min_cross_spanner(k, bn, bedges, cross, num_trials=5)

            if not r['cross_spans_all'] and failures_shown < 3:
                print(f"\nk={k} failure #{failures_shown+1}: "
                      f"M⁻={bm_minus}, M⁺={bm_plus}")
                print(f"  Missing {r['missing']} pairs: "
                      f"A-A={r['aa_missing']}, B-B={r['bb_missing']}, "
                      f"A-B={r['ab_missing']}")

                # Which specific pairs are missing?
                timed_all = [(t, u, v) for u, v, t in bedges]
                full_pairs = compute_reachability_pairs(bn, timed_all)
                timed_cross = [(t, u, v) for u, v, t in cross]
                cross_pairs = compute_reachability_pairs(bn, timed_cross)
                missing_pairs = full_pairs - cross_pairs
                for s, t in sorted(missing_pairs)[:10]:
                    sl = 'a' if s < k else 'b'
                    tl = 'a' if t < k else 'b'
                    si = s if s < k else s - k
                    ti = t if t < k else t - k
                    print(f"    {sl}{si} → {tl}{ti}")
                if len(missing_pairs) > 10:
                    print(f"    ... and {len(missing_pairs)-10} more")

                failures_shown += 1


if __name__ == '__main__':
    main()
