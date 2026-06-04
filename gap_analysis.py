"""
Gap analysis: for each hub, each non-star edge has a "dead zone"
(T_a, T_b) where it fails both Route A and Route B.

Key questions:
1. What fraction of non-star timestamps land in dead zones?
2. How does this depend on edge rank distance?
3. Can the adversary concentrate timestamps in dead zones?
4. For the BEST hub: what's the tightest bottleneck pair?

Also: verify that backward pairs route through PURE tree paths
(no star edges) or use star bounces.
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


def gap_analysis(n, timestamps, hub):
    """For each non-star edge, compute its dead zone and which zone its
    timestamp falls in."""
    non_hub = [v for v in range(n) if v != hub]
    star_times = {v: timestamps[(min(hub, v), max(hub, v))] for v in non_hub}
    ordered = sorted(non_hub, key=lambda v: star_times[v])
    rank = {v: i for i, v in enumerate(ordered)}
    T = [star_times[v] for v in ordered]  # T[rank] = star timestamp

    results = {'route_a': 0, 'dead': 0, 'route_b': 0, 'by_dist': {}}

    for a_idx in range(len(ordered)):
        for b_idx in range(a_idx + 1, len(ordered)):
            va, vb = ordered[a_idx], ordered[b_idx]
            e = (min(va, vb), max(va, vb))
            tau = timestamps[e]
            dist = b_idx - a_idx

            Ta, Tb = T[a_idx], T[b_idx]

            if tau <= Ta:
                zone = 'route_a'
            elif tau >= Tb:
                zone = 'route_b'
            else:
                zone = 'dead'

            results[zone] += 1
            if dist not in results['by_dist']:
                results['by_dist'][dist] = {'route_a': 0, 'dead': 0, 'route_b': 0, 'total': 0}
            results['by_dist'][dist][zone] += 1
            results['by_dist'][dist]['total'] += 1

    return results


def main():
    print("Dead zone analysis")
    print("=" * 70)

    for n in [8, 12, 20, 30]:
        m = n * (n - 1) // 2
        edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
        samples = min(2000, max(200, 10000 // n))

        all_dead_fracs = []
        dead_by_dist = {}

        for trial in range(samples):
            ts_vals = list(range(1, m + 1))
            random.shuffle(ts_vals)
            timestamps = {e: t for e, t in zip(edges, ts_vals)}

            # Use hub 0 for simplicity
            result = gap_analysis(n, timestamps, 0)
            total = result['route_a'] + result['dead'] + result['route_b']
            dead_frac = result['dead'] / total
            all_dead_fracs.append(dead_frac)

            for dist, counts in result['by_dist'].items():
                if dist not in dead_by_dist:
                    dead_by_dist[dist] = []
                dead_by_dist[dist].append(counts['dead'] / counts['total'])

        avg_dead = sum(all_dead_fracs) / len(all_dead_fracs)
        print(f"\nK_{n} ({samples} samples, hub 0):")
        print(f"  Overall dead zone fraction: {avg_dead:.4f}")
        print(f"  Dead zone by rank distance:")
        print(f"  {'dist':>4} {'dead_frac':>10} {'predicted':>10}  {'edges':>6}")
        for dist in sorted(dead_by_dist):
            avg = sum(dead_by_dist[dist]) / len(dead_by_dist[dist])
            predicted = dist / (n - 1)  # gap width ≈ dist/(n-1)
            edge_count = n - 1 - dist
            print(f"  {dist:4d} {avg:10.4f} {predicted:10.4f}  {edge_count:6d}")

    # Part 2: Adversarial — can the adversary concentrate dead zones
    # on critical relay edges?
    print(f"\n\n{'='*70}")
    print("Adversarial: for scale-1 pairs, what fraction of relays are dead?")
    print("=" * 70)

    for n in [8, 12, 20]:
        m = n * (n - 1) // 2
        edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
        samples = 2000

        # For each scale-1 pair, count dead vs live relays
        pair_dead_fracs = []

        for trial in range(samples):
            ts_vals = list(range(1, m + 1))
            random.shuffle(ts_vals)
            timestamps = {e: t for e, t in zip(edges, ts_vals)}

            for hub in range(n):
                non_hub = [v for v in range(n) if v != hub]
                star_times = {v: timestamps[(min(hub, v), max(hub, v))]
                              for v in non_hub}
                ordered = sorted(non_hub, key=lambda v: star_times[v])
                T = [star_times[v] for v in ordered]

                for j in range(len(ordered) - 1):
                    src = ordered[j + 1]  # rank j+1 (higher star time)
                    tgt = ordered[j]      # rank j (lower star time)

                    live = 0
                    dead = 0

                    # Route A relays: rank a < j (strict, to avoid edge reuse)
                    for a in range(j):
                        va = ordered[a]
                        e = (min(src, va), max(src, va))
                        tau = timestamps[e]
                        if tau <= T[a]:
                            live += 1
                        else:
                            dead += 1

                    # Route B relays: rank a > j+1 (strict)
                    for a in range(j + 2, len(ordered)):
                        va = ordered[a]
                        e = (min(va, tgt), max(va, tgt))
                        tau = timestamps[e]
                        if tau >= T[a]:
                            live += 1
                        else:
                            dead += 1

                    total_relays = live + dead
                    if total_relays > 0:
                        pair_dead_fracs.append((j, dead / total_relays,
                                                live, total_relays))

        # Summarize by position
        by_pos = {}
        for j, frac, live, total in pair_dead_fracs:
            if j not in by_pos:
                by_pos[j] = {'dead_fracs': [], 'zero_live': 0, 'total': 0}
            by_pos[j]['dead_fracs'].append(frac)
            by_pos[j]['total'] += 1
            if live == 0:
                by_pos[j]['zero_live'] += 1

        print(f"\nK_{n}: scale-1 pair relay analysis")
        print(f"  {'rank j':>6} {'mean dead%':>10} {'P(0 live)':>10} {'total_relays':>12}")
        for j in sorted(by_pos):
            avg_dead = sum(by_pos[j]['dead_fracs']) / len(by_pos[j]['dead_fracs'])
            p_zero = by_pos[j]['zero_live'] / by_pos[j]['total']
            # Average total relays = (j-1) + (n-2-j-1) = n-4 for middle,
            # less at extremes
            avg_relays = max(0, j - 1) + max(0, n - 3 - j)
            print(f"  {j:6d} {100*avg_dead:9.1f}% {p_zero:10.4f} {avg_relays:12d}")


if __name__ == '__main__':
    main()
