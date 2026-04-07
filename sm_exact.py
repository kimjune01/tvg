"""
Exact minimum spanner for SM(k), k=5,6,7.

The greedy gives 28 for SM(7) but 2n-3=25. Is 25 achievable?
If not, SM(7) is a counterexample to the 2n-3 conjecture.

Since we know spanners are all-cross, restrict search to cross edges only.
SM(k) has k^2 cross edges, need to find min subset that spans.

Use greedy + local search (swap one edge in, one out).
"""

import random
from itertools import combinations


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
    n = 2 * k
    edges = make_edges(n)
    m = len(edges)
    eidx = {}
    for i, (u, v) in enumerate(edges):
        eidx[(u, v)] = i; eidx[(v, u)] = i

    ts = [0] * m
    t = 1
    for i in range(k):
        for j in range(i + 1, k):
            ts[eidx[(i, j)]] = t; t += 1
    for d in range(k):
        for i in range(k):
            j = (i + d) % k
            idx = eidx[(min(i, k+j), max(i, k+j))]
            if ts[idx] == 0:
                ts[idx] = t; t += 1
    for i in range(k):
        for j in range(i + 1, k):
            ts[eidx[(k+i, k+j)]] = t; t += 1

    return n, edges, ts, eidx


def greedy_min(n, edges, ts):
    m = len(edges)
    timed_all = sorted([(ts[i], edges[i][0], edges[i][1]) for i in range(m)])
    target = compute_reachability(n, timed_all)
    included = list(range(m))
    for idx in sorted(range(m), key=lambda i: -ts[i]):
        candidate = [i for i in included if i != idx]
        sub = sorted([(ts[i], edges[i][0], edges[i][1]) for i in candidate])
        if compute_reachability(n, sub) == target:
            included = candidate
    return included


def local_search(n, edges, ts, start_set, max_rounds=1000):
    """Try swapping one edge out and one edge in to reduce size."""
    m = len(edges)
    timed_all = sorted([(ts[i], edges[i][0], edges[i][1]) for i in range(m)])
    target = compute_reachability(n, timed_all)

    current = set(start_set)
    best_size = len(current)

    for _ in range(max_rounds):
        improved = False

        # Try removing each edge
        for remove in list(current):
            trial = current - {remove}
            sub = sorted([(ts[i], edges[i][0], edges[i][1]) for i in trial])
            if compute_reachability(n, sub) == target:
                current = trial
                improved = True
                break

            # Try swapping: remove one, add another not in set
            for add in range(m):
                if add in current:
                    continue
                trial2 = (current - {remove}) | {add}
                if len(trial2) < len(current):
                    sub2 = sorted([(ts[i], edges[i][0], edges[i][1]) for i in trial2])
                    if compute_reachability(n, sub2) == target:
                        current = trial2
                        improved = True
                        break
            if improved:
                break

        if not improved:
            break

    return list(current)


def find_essential(n, edges, ts, spanner_idx):
    """Find edges that must be in every spanner."""
    m = len(edges)
    timed_all = sorted([(ts[i], edges[i][0], edges[i][1]) for i in range(m)])
    target = compute_reachability(n, timed_all)

    essential = []
    for idx in range(m):
        remaining = [i for i in range(m) if i != idx]
        sub = sorted([(ts[i], edges[i][0], edges[i][1]) for i in remaining])
        if compute_reachability(n, sub) != target:
            essential.append(idx)
    return essential


def run():
    for k in [5, 6, 7]:
        n, edges, ts, eidx = generate_sm(k)
        m = len(edges)
        print(f"\nSM({k}): n={n}, m={m}, 2n-3={2*n-3}")
        print("=" * 60)

        # Essential edges
        essential = find_essential(n, edges, ts, list(range(m)))
        print(f"  Essential edges: {len(essential)}")
        ess_cross = sum(1 for i in essential if (edges[i][0] < k) != (edges[i][1] < k))
        ess_internal = len(essential) - ess_cross
        print(f"    Cross: {ess_cross}, Internal: {ess_internal}")

        # Show essential cross edges
        for i in essential:
            u, v = edges[i]
            if (u < k) != (v < k):
                a = u if u < k else v
                b = (v if v >= k else u) - k
                d = (b - a) % k
                print(f"    (a{a}, b{b}) diag={d} @ t={ts[i]}")

        # Greedy
        greedy = greedy_min(n, edges, ts)
        print(f"\n  Greedy: {len(greedy)} edges")

        # Local search from greedy
        improved = local_search(n, edges, ts, greedy)
        print(f"  After local search: {len(improved)} edges")

        # Multiple random greedy orderings
        best = improved
        for trial in range(50):
            # Random removal order
            order = list(range(m))
            random.shuffle(order)
            timed_all = sorted([(ts[i], edges[i][0], edges[i][1]) for i in range(m)])
            target = compute_reachability(n, timed_all)
            included = list(range(m))
            for idx in order:
                if idx not in included:
                    continue
                candidate = [i for i in included if i != idx]
                sub = sorted([(ts[i], edges[i][0], edges[i][1]) for i in candidate])
                if compute_reachability(n, sub) == target:
                    included = candidate
            if len(included) < len(best):
                best = included
            ls = local_search(n, edges, ts, included)
            if len(ls) < len(best):
                best = ls

        print(f"  Best found (50 random + local): {len(best)} edges")
        print(f"  Gap to 2n-3: {len(best) - (2*n - 3)}")

        # Analyze best
        cross_best = sum(1 for i in best if (edges[i][0] < k) != (edges[i][1] < k))
        int_best = len(best) - cross_best
        print(f"    Cross: {cross_best}, Internal: {int_best}")

        # Degree distribution
        deg = [0] * n
        for i in best:
            u, v = edges[i]
            deg[u] += 1; deg[v] += 1
        print(f"    V- degs: {[deg[i] for i in range(k)]}")
        print(f"    V+ degs: {[deg[k+i] for i in range(k)]}")


if __name__ == "__main__":
    random.seed(42)
    run()
