"""
Compute the distribution of |G| = number of valid hubs for random σ.

If E[|G|] and Var(|G|) scale right, the second moment method gives:
  P(|G| ≥ 1) ≥ E[|G|]² / E[|G|²]

For this to → 1: need E[|G|] → ∞ AND E[|G|²] ≤ E[|G|]² × (1 + o(1)).

Equivalently: Var(|G|) / E[|G|]² → 0.

Also: is there ever an instance where |G| = 0? If not, the claim is
actually deterministic (no need for probability).
"""

import random
from collections import Counter

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


def greedy_hub_works(n, timestamps, hub):
    """Does greedy star+tree with this hub fit in 2n-3?"""
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
    print("Distribution of |G| = number of good hubs")
    print("=" * 70)
    print(f"{'n':>3} {'samples':>8} {'E[|G|]':>8} {'SD(|G|)':>8} "
          f"{'Var/E²':>8} {'min|G|':>7} {'P(|G|=0)':>10}")
    print("-" * 60)

    for n in range(5, 20):
        m = n * (n - 1) // 2
        edges = [(i, j) for i in range(n) for j in range(i + 1, n)]

        if n <= 10:
            samples = 2000
        elif n <= 15:
            samples = 500
        else:
            samples = 200

        counts = []
        for trial in range(samples):
            ts_vals = list(range(1, m + 1))
            random.shuffle(ts_vals)
            timestamps = {e: t for e, t in zip(edges, ts_vals)}

            good = sum(1 for h in range(n)
                        if greedy_hub_works(n, timestamps, h))
            counts.append(good)

        mean = sum(counts) / len(counts)
        var = sum((c - mean) ** 2 for c in counts) / len(counts)
        sd = var ** 0.5
        min_g = min(counts)
        p_zero = sum(1 for c in counts if c == 0) / len(counts)
        var_over_mean_sq = var / (mean ** 2) if mean > 0 else 0

        print(f"{n:3d} {samples:8d} {mean:8.2f} {sd:8.2f} {var_over_mean_sq:8.3f} "
              f"{min_g:7d} {p_zero:10.4f}")


if __name__ == '__main__':
    main()
