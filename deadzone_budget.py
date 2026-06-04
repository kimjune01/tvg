"""
Can the adversary block a scale-1 pair using only dead-zone assignments?

For pair (j+1, j) to have zero live relays:
- Route A relay a (a < j): need τ_{j+1,a} > T_a
- Route B relay b (b > j+1): need τ_{b,j} < T_b

Each relay edge needs its timestamp in the "non-helpful" zone.
How many timestamp values are available in each non-helpful zone?

For Route A relay a: non-helpful means τ > T_a.
  Available timestamps > T_a: all m - T_a timestamps.
  Of non-star timestamps: (m - T_a) - (n-1 - a) = m - T_a - n + 1 + a

For Route B relay b: non-helpful means τ < T_b.
  Available timestamps < T_b: T_b - 1 timestamps.
  Of non-star timestamps: (T_b - 1) - (b - 1) = T_b - b

The adversary needs to match relay edges to non-helpful timestamps.
This is a bipartite matching problem.

Key question: does a valid matching always exist?
"""

import random
from itertools import combinations

random.seed(42)


def analyze_blocking_feasibility(n, sigma, hub, target_j):
    """For a specific hub and scale-1 pair at position j,
    can the adversary block all relays using a consistent assignment?

    This checks: given the star timestamps, is there a matching of
    non-star edges to non-star timestamps such that all relays of
    pair (j+1, j) are non-helpful?
    """
    edges = [(i, k) for i in range(n) for k in range(i + 1, n)]
    timestamps = {e: t for e, t in zip(edges, sigma)}

    non_hub = [v for v in range(n) if v != hub]
    star_times = {v: timestamps[(min(hub, v), max(hub, v))] for v in non_hub}
    ordered = sorted(non_hub, key=lambda v: star_times[v])
    T = [star_times[v] for v in ordered]

    j = target_j
    if j >= len(ordered) - 1:
        return None

    src = ordered[j + 1]
    tgt = ordered[j]

    # Route A relays: rank a < j
    route_a_relays = []
    for a in range(j):
        va = ordered[a]
        e = (min(src, va), max(src, va))
        # Non-helpful: τ > T[a]
        route_a_relays.append({
            'edge': e,
            'condition': 'tau > T_a',
            'threshold': T[a],
            'non_helpful_count': sum(1 for t in range(T[a] + 1, max(T) + 2)
                                     if t not in set(T))
        })

    # Route B relays: rank b > j+1
    route_b_relays = []
    for b in range(j + 2, len(ordered)):
        vb = ordered[b]
        e = (min(vb, tgt), max(vb, tgt))
        # Non-helpful: τ < T[b]
        route_b_relays.append({
            'edge': e,
            'condition': 'tau < T_b',
            'threshold': T[b],
            'non_helpful_count': sum(1 for t in range(1, T[b])
                                     if t not in set(T))
        })

    return {
        'route_a': route_a_relays,
        'route_b': route_b_relays,
        'star_timestamps': T,
    }


def main():
    print("Dead-zone budget analysis")
    print("=" * 70)

    for n in [8, 12, 15, 20]:
        m = n * (n - 1) // 2
        edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
        samples = 500

        print(f"\nK_{n} (m={m}):")

        # For each instance, analyze the middle pair for hub 0
        for trial in range(min(3, samples)):
            ts_vals = list(range(1, m + 1))
            random.shuffle(ts_vals)

            hub = 0
            non_hub = [v for v in range(n) if v != hub]
            star_times = {v: ts_vals[edges.index((min(hub, v), max(hub, v)))]
                          for v in non_hub}
            ordered = sorted(non_hub, key=lambda v: star_times[v])
            T = [star_times[v] for v in ordered]

            j_mid = (n - 2) // 2  # middle pair

            result = analyze_blocking_feasibility(n, ts_vals, hub, j_mid)
            if result is None:
                continue

            n_route_a = len(result['route_a'])
            n_route_b = len(result['route_b'])

            # For each relay, what fraction of non-star timestamps are non-helpful?
            all_non_star_ts = sorted(set(range(1, m + 1)) - set(T))
            total_non_star = len(all_non_star_ts)

            print(f"\n  Trial {trial+1}, hub=0, pair at j={j_mid}:")
            print(f"    Star timestamps: {T}")
            print(f"    Route A relays: {n_route_a}, Route B relays: {n_route_b}")

            # For Route A relays: fraction of non-star ts that are > T_a
            for r in result['route_a'][:3]:
                above = sum(1 for t in all_non_star_ts if t > r['threshold'])
                print(f"    Route A relay: T_a={r['threshold']}, "
                      f"non-helpful ts: {above}/{total_non_star} "
                      f"({100*above/total_non_star:.0f}%)")

            # For Route B relays: fraction of non-star ts that are < T_b
            for r in result['route_b'][:3]:
                below = sum(1 for t in all_non_star_ts if t < r['threshold'])
                print(f"    Route B relay: T_b={r['threshold']}, "
                      f"non-helpful ts: {below}/{total_non_star} "
                      f"({100*below/total_non_star:.0f}%)")

            # The crux: can ALL relays be simultaneously non-helpful?
            # Route A needs τ > T_a for each relay. These use DIFFERENT edges.
            # Route B needs τ < T_b for each relay. These use DIFFERENT edges.
            # All edges are distinct. The constraint is:
            # Can we assign non-star timestamps to relay edges such that
            # Route A edges get large timestamps, Route B edges get small ones?

            # This is a bipartite matching: relay edges → non-star timestamps
            # Route A edge a → any non-star timestamp > T[a]
            # Route B edge b → any non-star timestamp < T[b]

            # Count: do we have enough large timestamps for Route A
            # AND enough small timestamps for Route B?

            # Route A needs: j-1 timestamps, each > T[a] for its relay
            # Sort Route A by threshold (ascending): T[0], T[1], ..., T[j-2]
            # Greedy: assign the SMALLEST available > T[a] timestamp to each
            route_a_thresholds = sorted([r['threshold'] for r in result['route_a']])
            route_b_thresholds = sorted([r['threshold'] for r in result['route_b']],
                                         reverse=True)

            # Available non-star timestamps
            available = list(all_non_star_ts)

            # Try greedy assignment: Route A gets large ts, Route B gets small
            route_a_ok = True
            used = set()
            for threshold in route_a_thresholds:
                # Find smallest available > threshold
                found = False
                for t in available:
                    if t > threshold and t not in used:
                        used.add(t)
                        found = True
                        break
                if not found:
                    route_a_ok = False
                    break

            route_b_ok = True
            for threshold in route_b_thresholds:
                # Find largest available < threshold
                found = False
                for t in reversed(available):
                    if t < threshold and t not in used:
                        used.add(t)
                        found = True
                        break
                if not found:
                    route_b_ok = False
                    break

            both_ok = route_a_ok and route_b_ok
            print(f"    Greedy blocking feasible: Route A={route_a_ok}, "
                  f"Route B={route_b_ok}, Both={both_ok}")

            # But we also need the OTHER non-star edges to get timestamps
            # that don't create live relays. This is a STRONGER constraint.
            remaining = total_non_star - len(used)
            other_edges = total_non_star - n_route_a - n_route_b
            print(f"    Used {len(used)}/{total_non_star} timestamps, "
                  f"remaining {remaining} for {other_edges} other edges")


if __name__ == '__main__':
    main()
