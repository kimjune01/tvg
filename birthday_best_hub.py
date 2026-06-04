"""
Birthday bound: interactive greedy cover for the BEST hub.

For each instance, try all n hubs with interactive greedy.
Report the minimum cover size across all hubs.
The conjecture holds if min_hub cover ≤ n-2 always.
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


def interactive_greedy_cover(n, timestamps, hub, target):
    """Interactive greedy: add tree edges one at a time to star(hub).
    Returns (cover_size, success) where success = all pairs covered."""
    star = {(min(hub, v), max(hub, v)) for v in range(n) if v != hub}
    non_star = [e for e in timestamps if e not in star]
    current = set(star)
    count = 0

    while count < len(non_star):  # don't exceed available edges
        sub = sorted([(timestamps[e], e[0], e[1]) for e in current])
        cur_reach = compute_reachability(n, sub)
        if cur_reach == target:
            return count, True
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
            return count, False
        current.add(best_e)
        count += 1

    sub = sorted([(timestamps[e], e[0], e[1]) for e in current])
    return count, compute_reachability(n, sub) == target


def main():
    print("Birthday bound: best hub interactive greedy")
    print("=" * 70)

    for n in [6, 8, 10, 12, 15, 20]:
        m = n * (n - 1) // 2
        budget = n - 2
        edges_template = [(i, j) for i in range(n) for j in range(i + 1, n)]

        if n <= 10:
            samples = 2000
        elif n <= 15:
            samples = 500
        else:
            samples = 200

        best_hub_sizes = []
        within_budget = 0
        all_hub_sizes = []  # for distribution
        per_hub_within = [0] * n

        for trial in range(samples):
            ts_vals = list(range(1, m + 1))
            random.shuffle(ts_vals)
            timestamps = {e: t for e, t in zip(edges_template, ts_vals)}
            all_timed = sorted([(t, u, v) for (u, v), t in timestamps.items()])
            target = compute_reachability(n, all_timed)

            best_size = None
            for h in range(n):
                size, ok = interactive_greedy_cover(n, timestamps, h, target)
                if ok:
                    all_hub_sizes.append(size)
                    if size <= budget:
                        per_hub_within[h] += 1
                    if best_size is None or size < best_size:
                        best_size = size

            if best_size is not None:
                best_hub_sizes.append(best_size)
                if best_size <= budget:
                    within_budget += 1

        avg_best = sum(best_hub_sizes) / len(best_hub_sizes) if best_hub_sizes else 0
        max_best = max(best_hub_sizes) if best_hub_sizes else 0
        min_best = min(best_hub_sizes) if best_hub_sizes else 0

        # P(random hub within budget)
        p_random = sum(per_hub_within) / (samples * n) if samples > 0 else 0

        print(f"\nK_{n} (budget={budget}), {samples} samples:")
        print(f"  Best hub cover: mean={avg_best:.2f}, min={min_best}, "
              f"max={max_best}")
        print(f"  Best hub ≤ budget: {within_budget}/{samples} "
              f"({100*within_budget/samples:.1f}%)")
        print(f"  P(random hub ≤ budget): {100*p_random:.2f}%")

        # Birthday: P(no hub within budget) ≈ (1-p)^n
        if p_random > 0:
            p_fail = (1 - p_random) ** n
            print(f"  Birthday P(no hub): (1-{p_random:.4f})^{n} "
                  f"= {p_fail:.6f}")
        else:
            print(f"  Birthday P(no hub): p_random=0, can't compute")

        # Distribution of best hub sizes
        from collections import Counter
        dist = Counter(best_hub_sizes)
        print(f"  Best hub size distribution:")
        for k in sorted(dist):
            marker = " <==" if k <= budget else ""
            print(f"    {k:3d}: {dist[k]:4d} ({100*dist[k]/samples:.1f}%){marker}")


if __name__ == '__main__':
    main()
