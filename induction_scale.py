"""
Quick scaling test: does the 4-edge induction hold at larger k?
Simplified: generate (k+1)×(k+1), find optimal k×k sub-spanner,
count minimum extra edges over all row/column removals.
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


def generate_random_biclique(k):
    """Simple random k×k biclique (not necessarily extremally matched)."""
    M = [[0]*k for _ in range(k)]
    vals = list(range(1, k*k+1))
    random.shuffle(vals)
    idx = 0
    for i in range(k):
        for j in range(k):
            M[i][j] = vals[idx]
            idx += 1
    return M


def greedy_spanner_fast(M, k, budget):
    """Fast greedy: try 3 hub pairs, return best."""
    n = 2 * k
    all_timed = sorted([(M[i][j], i, k+j) for i in range(k) for j in range(k)])
    target = compute_reachability(n, all_timed)

    best_edges = None
    best_size = k * k

    for h in range(min(k, 3)):
        c = (h + k // 2) % k
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


def test_one(k):
    """Generate k×k, find spanner, then for each possible new row+col
    extension to (k+1)×(k+1), count extra edges needed."""
    # Generate (k+1)×(k+1) biclique
    k1 = k + 1
    M_big = generate_random_biclique(k1)
    n_big = 2 * k1

    all_timed_big = sorted([(M_big[i][j], i, k1+j)
                            for i in range(k1) for j in range(k1)])
    target_big = compute_reachability(n_big, all_timed_big)

    best_extra = k1 * k1

    # Try removing each row r and column c
    for r in range(k1):
        for c_rem in range(k1):
            sub_rows = [i for i in range(k1) if i != r]
            sub_cols = [j for j in range(k1) if j != c_rem]

            M_sub = [[M_big[sub_rows[i]][sub_cols[j]]
                       for j in range(k)] for i in range(k)]

            sub_edges, sub_size = greedy_spanner_fast(M_sub, k, 4*k-3)
            if sub_edges is None:
                continue

            # Map back to big indices
            current = set()
            for (si, sj) in sub_edges:
                current.add((sub_rows[si], sub_cols[sj]))

            # Greedily add edges involving row r or column c_rem
            extra = 0
            new_cands = ([(r, j) for j in range(k1)] +
                         [(i, c_rem) for i in range(k1) if i != r])

            while True:
                cur_timed = sorted([(M_big[i][j], i, k1+j) for i, j in current])
                cur_reach = compute_reachability(n_big, cur_timed)
                if cur_reach == target_big:
                    break

                cur_count = len(cur_reach)
                best_e, best_g = None, 0
                for e in new_cands:
                    if e in current:
                        continue
                    trial = current | {e}
                    t_timed = sorted([(M_big[i][j], i, k1+j) for i, j in trial])
                    g = len(compute_reachability(n_big, t_timed)) - cur_count
                    if g > best_g:
                        best_g = g
                        best_e = e

                if best_e is None or best_g <= 0:
                    extra = k1 * k1
                    break

                current.add(best_e)
                extra += 1

            best_extra = min(best_extra, extra)
            if best_extra <= 4:
                return best_extra

    return best_extra


def main():
    print("Induction scaling test")
    print("=" * 50)

    for k in [4, 5, 6, 7, 8, 10, 12, 15]:
        samples = 50 if k <= 8 else 20
        extras = []
        within_4 = 0

        for trial in range(samples):
            extra = test_one(k)
            extras.append(extra)
            if extra <= 4:
                within_4 += 1

        avg = sum(extras) / len(extras)
        mx = max(extras)
        print(f"  k={k:2d} → k+1={k+1:2d}: "
              f"avg_extra={avg:.1f}, max={mx}, "
              f"≤4: {100*within_4/samples:.0f}%")


if __name__ == '__main__':
    main()
