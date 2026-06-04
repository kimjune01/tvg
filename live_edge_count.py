"""
For each non-hub vertex v (rank r), count LIVE edges:
- Route A live: edges from v to lower ranks with τ ≤ T_v's_lower_endpoint
- Route B live: edges from v to any other vertex with τ ≥ T_max(ranks)

More precisely, for edge {v_a, v_b} with a < b:
- Route A live: τ ≤ T_a (helps pair (b, b-1))
- Route B live: τ ≥ T_b (helps pair (a+1, a))

For vertex v at rank r, its edges to rank s:
- If s < r: edge has ranks (s, r). Route A live: τ ≤ T_s. Route B live: τ ≥ T_r.
- If s > r: edge has ranks (r, s). Route A live: τ ≤ T_r. Route B live: τ ≥ T_s.

Count of Route B live edges FROM vertex v (rank r):
- To lower ranks s < r: need τ ≥ T_r
- To higher ranks s > r: need τ ≥ T_s > T_r

The adversary controls timestamps. Can they minimize the max LIVE degree?
"""

import random
from collections import Counter

random.seed(42)


def count_live_edges_per_vertex(n, timestamps, hub):
    non_hub = [v for v in range(n) if v != hub]
    star = {(min(hub, v), max(hub, v)): timestamps[(min(hub, v), max(hub, v))]
            for v in non_hub}
    ordered = sorted(non_hub, key=lambda v: star[(min(hub, v), max(hub, v))])
    rank = {v: i for i, v in enumerate(ordered)}
    T = [star[(min(hub, v), max(hub, v))] for v in ordered]

    live_counts = {v: 0 for v in non_hub}
    for v in non_hub:
        r = rank[v]
        for w in non_hub:
            if w == v:
                continue
            s = rank[w]
            e = (min(v, w), max(v, w))
            tau = timestamps[e]
            lo, hi = min(r, s), max(r, s)
            # Route A live: τ ≤ T[lo]
            # Route B live: τ ≥ T[hi]
            if tau <= T[lo] or tau >= T[hi]:
                live_counts[v] += 1

    return {v: (live_counts[v], rank[v]) for v in non_hub}


def main():
    print("Live edge counts per non-hub vertex")
    print("=" * 70)

    for n in [8, 12, 15, 20]:
        m = n * (n - 1) // 2
        edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
        samples = 2000 if n <= 12 else 500

        # Track: for each instance, what's the max LIVE degree?
        max_live_degrees = []
        # Also: what's the MINIMUM over hubs of max LIVE degree?
        min_max_live = []

        for trial in range(samples):
            ts_vals = list(range(1, m + 1))
            random.shuffle(ts_vals)
            timestamps = {e: t for e, t in zip(edges, ts_vals)}

            best_max_live = 0
            for hub in range(n):
                live = count_live_edges_per_vertex(n, timestamps, hub)
                max_live = max(count for count, rank in live.values())
                if max_live > best_max_live:
                    best_max_live = max_live

            min_max_live.append(best_max_live)

        budget = n - 2
        avg = sum(min_max_live) / len(min_max_live)
        mn = min(min_max_live)
        mx = max(min_max_live)

        print(f"\nK_{n} (budget={budget}):")
        print(f"  Max LIVE degree (best hub): mean={avg:.1f}, min={mn}, max={mx}")
        print(f"  Budget needs: {budget}")
        print(f"  Min surplus: {mn - budget}")

        # Distribution
        dist = Counter(min_max_live)
        print(f"  Distribution:")
        for k in sorted(dist):
            marker = " <==" if k == budget else ""
            print(f"    {k:3d}: {dist[k]:4d} ({100*dist[k]/samples:.1f}%){marker}")

    # Part 2: adversarial — minimize max LIVE degree
    print(f"\n\n{'='*70}")
    print("Adversarial: minimize max LIVE degree for best hub")
    print("=" * 70)

    for n in [8, 10, 12]:
        m = n * (n - 1) // 2
        edges = [(i, j) for i in range(n) for j in range(i + 1, n)]

        def eval_perm(perm):
            timestamps = {e: t for e, t in zip(edges, perm)}
            best = 0
            for hub in range(n):
                live = count_live_edges_per_vertex(n, timestamps, hub)
                mx = max(c for c, r in live.values())
                best = max(best, mx)
            return best

        # Hill-climb to minimize
        perm = list(range(1, m + 1))
        random.shuffle(perm)
        best_score = eval_perm(perm)
        best_perm = list(perm)

        for step in range(10000):
            i, j = random.sample(range(m), 2)
            candidate = list(perm)
            candidate[i], candidate[j] = candidate[j], candidate[i]
            score = eval_perm(candidate)
            if score <= best_score:
                perm = candidate
                if score < best_score:
                    best_score = score
                    best_perm = list(perm)

        print(f"\nK_{n}: adversarial min max_LIVE = {best_score}, budget={n-2}")
        if best_score >= n - 2:
            print(f"  ✓ Always enough LIVE edges for budget")
        else:
            print(f"  ✗ Not enough LIVE edges!")


if __name__ == '__main__':
    main()
