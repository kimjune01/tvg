"""
Compute p_n = P(greedy star+tree from hub 0 works) exactly for small n.

For n = 4, 5 (maybe 6): enumerate all permutations, count good ones.

If p_n has a closed form or stabilizes, we have a handle on Lemma A.
"""

from itertools import permutations


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


def greedy_hub_works(n, timestamps, hub):
    all_timed = sorted([(t, u, v) for (u, v), t in timestamps.items()])
    target = compute_reachability(n, all_timed)

    star = {(min(hub, v), max(hub, v)) for v in range(n) if v != hub}
    non_star = [e for e in timestamps if e not in star]
    current = set(star)
    budget = 2 * n - 3

    while len(current) < budget:
        sub = sorted([(timestamps[e], e[0], e[1]) for e in current])
        cur_reach = compute_reachability(n, sub)
        if cur_reach == target:
            return True
        cur_count = len(cur_reach)
        best_e, best_g = None, 0
        for e in non_star:
            if e in current:
                continue
            trial = current | {e}
            sub2 = sorted([(timestamps[ee], ee[0], ee[1]) for ee in trial])
            g = len(compute_reachability(n, sub2)) - cur_count
            if g > best_g:
                best_g = g
                best_e = e
        if best_e is None or best_g <= 0:
            return False
        current.add(best_e)

    sub = sorted([(timestamps[e], e[0], e[1]) for e in current])
    return compute_reachability(n, sub) == target


def main():
    print("Exact p_n for small n")
    print("=" * 50)
    print(f"{'n':>3} {'m':>3} {'permutations':>15} {'good':>8} "
          f"{'p_n':>8} {'1-p_n':>8}")
    print("-" * 55)

    from math import factorial
    for n in [4, 5, 6]:
        m = n * (n - 1) // 2
        edges = [(i, j) for i in range(n) for j in range(i + 1, n)]

        good = 0
        total = 0

        # For efficiency, only check hub 0
        for perm in permutations(range(1, m + 1)):
            timestamps = {e: t for e, t in zip(edges, perm)}
            total += 1
            if greedy_hub_works(n, timestamps, 0):
                good += 1

        p_n = good / total
        print(f"{n:3d} {m:3d} {total:15d} {good:8d} {p_n:8.4f} {1-p_n:8.4f}")


if __name__ == '__main__':
    main()
