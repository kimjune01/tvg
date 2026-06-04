"""
O(Cn) spanner: star + K earliest + K latest non-star edges per vertex.

Find the minimum K such that the construction ALWAYS spans.
This gives a Cn spanner where C = 1 + 2K.
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


def k_early_late(n, timestamps, hub, K):
    """Star + K earliest + K latest non-star edges per non-hub vertex."""
    star = {(min(hub, v), max(hub, v)) for v in range(n) if v != hub}
    non_star = {e: t for e, t in timestamps.items() if e not in star}

    edges = set(star)
    for v in range(n):
        if v == hub:
            continue
        v_edges = sorted([(t, e) for e, t in non_star.items() if v in e])
        # K earliest
        for _, e in v_edges[:K]:
            edges.add(e)
        # K latest
        for _, e in v_edges[-K:]:
            edges.add(e)
    return edges


def main():
    print("Cn spanner: star + K early + K late per vertex")
    print("=" * 70)

    for n in [10, 15, 20, 25, 30]:
        m = n * (n - 1) // 2
        all_edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
        samples = 500 if n <= 15 else 100

        print(f"\nn={n}:")
        print(f"  {'K':>3} {'size':>6} {'ratio':>6} {'success':>8}")

        for K in range(1, min(n, 10)):
            successes = 0
            sizes = []

            for trial in range(samples):
                ts_vals = list(range(1, m + 1))
                random.shuffle(ts_vals)
                timestamps = {e: t for e, t in zip(all_edges, ts_vals)}

                all_timed = sorted([(t, u, v) for (u, v), t in timestamps.items()])
                target = compute_reachability(n, all_timed)

                best_ok = False
                best_size = n * n
                for hub in range(min(n, 5)):  # try first 5 hubs
                    edges = k_early_late(n, timestamps, hub, K)
                    sub = sorted([(timestamps[e], e[0], e[1]) for e in edges])
                    if compute_reachability(n, sub) == target:
                        best_ok = True
                        best_size = min(best_size, len(edges))
                        break

                if best_ok:
                    successes += 1
                    sizes.append(best_size)

            if sizes:
                avg_size = sum(sizes) / len(sizes)
                ratio = avg_size / n
            else:
                avg_size = 0
                ratio = 0
            pct = 100 * successes / samples
            print(f"  {K:3d} {avg_size:6.1f} {ratio:5.2f}n {pct:7.1f}%")

            if pct >= 99.5:
                print(f"  → K={K} sufficient (C ≈ {ratio:.1f})")
                break


if __name__ == '__main__':
    main()
