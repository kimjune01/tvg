"""
True hub-less rate for K_n.

For each n, measure:
1. Greedy hub-less rate (fast, approximate)
2. True hub-less rate (exhaustive tree search, exact but slow)

The gap between (1) and (2) quantifies greedy suboptimality.
For large n where exhaustive is infeasible, estimate the true rate.
"""

import random
from itertools import combinations
from math import comb

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


def check_spanner(n, timestamps, edge_set):
    all_timed = sorted([(t, u, v) for (u, v), t in timestamps.items()])
    target = compute_reachability(n, all_timed)
    sub_timed = sorted([(timestamps[e], e[0], e[1]) for e in edge_set])
    return compute_reachability(n, sub_timed) == target


def greedy_star_tree(n, timestamps, hub):
    """Greedy star+tree. Returns (ok, edge_count)."""
    all_timed = sorted([(t, u, v) for (u, v), t in timestamps.items()])
    target = compute_reachability(n, all_timed)

    star = {(min(hub, v), max(hub, v)) for v in range(n) if v != hub}
    non_star = [e for e in timestamps if e not in star]
    current = set(star)

    for _ in range(n - 2):
        sub = sorted([(timestamps[e], e[0], e[1]) for e in current])
        cur_reach = compute_reachability(n, sub)
        if cur_reach == target:
            break
        cur_count = len(cur_reach)
        best_e, best_g = None, -1
        for e in non_star:
            if e in current:
                continue
            trial = current | {e}
            sub = sorted([(timestamps[ee], ee[0], ee[1]) for ee in trial])
            g = len(compute_reachability(n, sub)) - cur_count
            if g > best_g:
                best_g = g
                best_e = e
        if best_e is None or best_g <= 0:
            break
        current.add(best_e)

    if len(current) > 2 * n - 3:
        return False
    sub = sorted([(timestamps[e], e[0], e[1]) for e in current])
    return compute_reachability(n, sub) == target


def exhaustive_star_tree(n, timestamps, hub):
    """Exhaustive: try all C(non_star, n-2) tree subsets."""
    star = {(min(hub, v), max(hub, v)) for v in range(n) if v != hub}
    non_star = [e for e in timestamps if e not in star]
    for tree_edges in combinations(non_star, n - 2):
        if check_spanner(n, timestamps, star | set(tree_edges)):
            return True
    return False


def main():
    print("Hub-less rate for K_n")
    print("=" * 60)
    print(f"{'n':>3} {'m':>4} {'tree_choices':>12} {'samples':>8} "
          f"{'greedy_hl':>10} {'true_hl':>10} {'greedy_%':>8} {'true_%':>8}")
    print("-" * 80)

    for n in range(5, 13):
        m = n * (n - 1) // 2
        non_star_count = m - (n - 1)  # non-star edges per hub
        tree_choices = comb(non_star_count, n - 2)

        # Decide whether exhaustive is feasible
        # C(non_star, n-2) per hub, n hubs
        total_exhaustive = n * tree_choices
        exhaustive_feasible = total_exhaustive < 500000

        if n <= 7:
            samples = 50000
        elif n <= 9:
            samples = 10000
        else:
            samples = 5000

        greedy_hubless = 0
        true_hubless = 0

        for trial in range(samples):
            edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
            ts_vals = list(range(1, m + 1))
            random.shuffle(ts_vals)
            timestamps = {e: t for e, t in zip(edges, ts_vals)}

            # Greedy check
            has_greedy_hub = any(greedy_star_tree(n, timestamps, h) for h in range(n))

            if not has_greedy_hub:
                greedy_hubless += 1

                if exhaustive_feasible:
                    has_true_hub = any(exhaustive_star_tree(n, timestamps, h)
                                       for h in range(n))
                    if not has_true_hub:
                        true_hubless += 1
                else:
                    true_hubless += 1  # upper bound (can't verify)

        greedy_pct = 100 * greedy_hubless / samples
        true_pct = 100 * true_hubless / samples
        exact = "exact" if exhaustive_feasible else "upper"

        print(f"{n:3d} {m:4d} {tree_choices:12d} {samples:8d} "
              f"{greedy_hubless:10d} {true_hubless:10d} "
              f"{greedy_pct:7.3f}% {true_pct:7.3f}% ({exact})")


if __name__ == '__main__':
    main()
