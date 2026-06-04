"""
Test: when hub row dominates all others (column-min in every column),
does the greedy still find a 4k-3 spanner?

Also: count early/late edges per non-hub row for random and adversarial M.
"""

import random

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


def greedy_biclique_spanner(M, k, hub_row):
    """Greedy star+tree for biclique with given hub row."""
    n = 2 * k
    all_timed = sorted([(M[i][j], i, k+j) for i in range(k) for j in range(k)])
    target = compute_reachability(n, all_timed)

    star = {(hub_row, j) for j in range(k)}
    current = set(star)
    budget = 4 * k - 3

    while len(current) < budget:
        cur_timed = sorted([(M[i][j], i, k+j) for i, j in current])
        cur_reach = compute_reachability(n, cur_timed)
        if cur_reach == target:
            break
        cur_count = len(cur_reach)
        best_e, best_g = None, 0
        for i in range(k):
            for j in range(k):
                if (i, j) in current:
                    continue
                trial = current | {(i, j)}
                trial_timed = sorted([(M[ii][jj], ii, k+jj) for ii, jj in trial])
                g = len(compute_reachability(n, trial_timed)) - cur_count
                if g > best_g:
                    best_g = g
                    best_e = (i, j)
        if best_e is None or best_g <= 0:
            break
        current.add(best_e)

    cur_timed = sorted([(M[i][j], i, k+j) for i, j in current])
    return len(current), compute_reachability(n, cur_timed) == target


def make_dominated_matrix(k, hub=0):
    """Hub row has column minima everywhere. Other rows have larger values."""
    M = [[0]*k for _ in range(k)]
    # Hub row: values 1..k
    for j in range(k):
        M[hub][j] = j + 1
    # Other rows: values k+1..k² in random order
    remaining = list(range(k+1, k*k+1))
    random.shuffle(remaining)
    idx = 0
    for i in range(k):
        if i == hub:
            continue
        for j in range(k):
            M[i][j] = remaining[idx]
            idx += 1
    return M


def early_late_analysis(M, k, hub):
    """Count early/late edges per non-hub row."""
    results = []
    for i in range(k):
        if i == hub:
            continue
        early = sum(1 for j in range(k) if M[i][j] <= M[hub][j])
        late = sum(1 for j in range(k) if M[i][j] >= M[hub][j])
        results.append((i, early, late))
    return results


def main():
    print("Biclique dominated hub analysis")
    print("=" * 70)

    for k in range(3, 10):
        n = 2 * k
        budget = 4 * k - 3

        # Test 1: Dominated hub (adversarial)
        hub = 0
        M = make_dominated_matrix(k, hub)
        size, ok = greedy_biclique_spanner(M, k, hub)

        el = early_late_analysis(M, k, hub)
        min_early = min(e for _, e, _ in el)
        min_late = min(l for _, _, l in el)

        print(f"\nK_{{{k},{k}}} (budget={budget}):")
        print(f"  Dominated hub: size={size}, ok={ok}, "
              f"min_early={min_early}, min_late={min_late}")

        # Also try other hubs on the dominated matrix
        best_other = 999
        for h in range(k):
            if h == hub:
                continue
            s, o = greedy_biclique_spanner(M, k, h)
            if o and s < best_other:
                best_other = s
        print(f"  Best non-dominated hub: size={best_other}")

        # Test 2: Random bicliques — early/late stats
        samples = 200
        zero_early = 0
        all_success = 0
        for trial in range(samples):
            vals = list(range(1, k*k+1))
            random.shuffle(vals)
            M2 = [[vals[i*k+j] for j in range(k)] for i in range(k)]

            best_size = 999
            for h in range(k):
                s, o = greedy_biclique_spanner(M2, k, h)
                if o and s < best_size:
                    best_size = s

            if best_size <= budget:
                all_success += 1

            # Check if any hub has a row with zero early edges
            for h in range(k):
                el2 = early_late_analysis(M2, k, h)
                if any(e == 0 for _, e, _ in el2):
                    zero_early += 1
                    break

        print(f"  Random: best hub ≤ budget: {all_success}/{samples} "
              f"({100*all_success/samples:.0f}%)")
        print(f"  Random instances with zero-early row: {zero_early}/{samples}")

        # Test 3: proof sketch — include star + 1 early + 1 late per row
        # Does this always span all pairs?
        proof_successes = 0
        for trial in range(samples):
            vals = list(range(1, k*k+1))
            random.shuffle(vals)
            M3 = [[vals[i*k+j] for j in range(k)] for i in range(k)]

            for h in range(k):
                edges = {(h, j) for j in range(k)}  # star

                for i in range(k):
                    if i == h:
                        continue
                    # Pick one early edge (smallest M[i][j] where M[i][j] <= M[h][j])
                    early_cols = [j for j in range(k) if M3[i][j] < M3[h][j]]
                    if early_cols:
                        j_e = min(early_cols, key=lambda j: M3[i][j])
                        edges.add((i, j_e))

                    # Pick one late edge (largest M[i][j] where M[i][j] > M[h][j])
                    late_cols = [j for j in range(k) if M3[i][j] > M3[h][j]]
                    if late_cols:
                        j_l = max(late_cols, key=lambda j: M3[i][j])
                        edges.add((i, j_l))

                if len(edges) <= budget:
                    timed = sorted([(M3[i][j], i, k+j) for i, j in edges])
                    reach = compute_reachability(n, timed)
                    target = compute_reachability(n, sorted(
                        [(M3[i][j], i, k+j) for i in range(k) for j in range(k)]))
                    if reach == target:
                        proof_successes += 1
                        break

        print(f"  Proof sketch (star+early+late): {proof_successes}/{samples}")


if __name__ == '__main__':
    main()
