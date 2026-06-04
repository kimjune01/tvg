"""
Analyzable O(n) construction: star + early-exit + late-entry.

For hub h and each non-hub vertex v:
- early(v) = non-star edge from v with smallest timestamp
- late(v) = non-star edge from v with largest timestamp

Total: (n-1) star + (n-1) early + (n-1) late = 3(n-1) edges (with overlaps).

Question: does this span all pairs?
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


def star_early_late(n, timestamps, hub):
    """Star + early + late construction."""
    star = {(min(hub, v), max(hub, v)) for v in range(n) if v != hub}
    non_star = {e: t for e, t in timestamps.items() if e not in star}

    edges = set(star)

    for v in range(n):
        if v == hub:
            continue
        # Non-star edges from v
        v_edges = [(t, e) for e, t in non_star.items()
                   if v in e]
        if not v_edges:
            continue
        # Early: smallest timestamp
        _, e_early = min(v_edges)
        edges.add(e_early)
        # Late: largest timestamp
        _, e_late = max(v_edges)
        edges.add(e_late)

    return edges


def test_construction(n, timestamps, hub):
    edges = star_early_late(n, timestamps, hub)
    all_timed = sorted([(t, u, v) for (u, v), t in timestamps.items()])
    target = compute_reachability(n, all_timed)
    sub_timed = sorted([(timestamps[e], e[0], e[1]) for e in edges])
    reach = compute_reachability(n, sub_timed)
    missing = target - reach
    return len(edges), len(missing), missing


def main():
    print("Star + early + late: O(n) construction test")
    print("=" * 70)

    for n in range(5, 25):
        m = n * (n - 1) // 2
        all_edges = [(i, j) for i in range(n) for j in range(i + 1, n)]

        if n <= 15:
            samples = 1000
        else:
            samples = 200

        successes = 0
        sizes = []
        missing_counts = []

        for trial in range(samples):
            ts_vals = list(range(1, m + 1))
            random.shuffle(ts_vals)
            timestamps = {e: t for e, t in zip(all_edges, ts_vals)}

            # Try all hubs
            best_missing = n * n
            best_size = 0
            for hub in range(n):
                size, nmiss, _ = test_construction(n, timestamps, hub)
                if nmiss < best_missing:
                    best_missing = nmiss
                    best_size = size

            sizes.append(best_size)
            missing_counts.append(best_missing)
            if best_missing == 0:
                successes += 1

        avg_size = sum(sizes) / len(sizes)
        avg_miss = sum(missing_counts) / len(missing_counts)
        pct = 100 * successes / samples

        print(f"  n={n:2d}: size={avg_size:.1f} ({avg_size/n:.2f}n), "
              f"success={pct:.1f}%, "
              f"avg_missing={avg_miss:.1f}")


if __name__ == '__main__':
    main()
