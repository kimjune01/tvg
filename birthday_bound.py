"""
Birthday bound formalization for hub existence.

Setup: K_n, distinct timestamps on all C(n,2) edges.
Hub h is valid if ∃ (n-2) non-star edges such that star(h) ∪ tree is a spanner.

Star(h) covers forward pairs: (a,b) where t(a,h) < t(h,b).
Tree edges must rescue all backward pairs: (a,b) where t(a,h) > t(h,b).

For hub h, define:
- B(h) = set of backward pairs (ordered, so |B(h)| = C(n-1,2))
- For each non-star edge e, R(h,e) = set of backward pairs rescued by adding e
- Hub h is valid iff ∃ S ⊆ non-star, |S|=n-2, ∪_{e∈S} R(h,e) ⊇ B(h)

This is a SET COVER instance. If each edge rescues many pairs and pairs
are easy to cover, hub h is valid.

Key quantities to measure:
1. |R(h,e)| distribution — how many pairs does each tree edge rescue?
2. Coverage overlap — are rescue sets concentrated or spread out?
3. Minimum cover size — how many tree edges actually needed?
4. How do these scale with n?
"""

import random
from itertools import combinations
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


def analyze_hub(n, timestamps, hub):
    """Analyze the set-cover structure for a given hub."""
    all_edges = list(timestamps.keys())
    all_timed = sorted([(t, u, v) for (u, v), t in timestamps.items()])
    target = compute_reachability(n, all_timed)

    star = {(min(hub, v), max(hub, v)) for v in range(n) if v != hub}
    non_star = [e for e in all_edges if e not in star]

    # What does star alone cover?
    star_timed = sorted([(timestamps[e], e[0], e[1]) for e in star])
    star_reach = compute_reachability(n, star_timed)
    backward = target - star_reach  # pairs star misses

    # For each non-star edge, what backward pairs does it rescue?
    rescue_map = {}
    for e in non_star:
        trial = star | {e}
        trial_timed = sorted([(timestamps[ee], ee[0], ee[1]) for ee in trial])
        trial_reach = compute_reachability(n, trial_timed)
        rescued = trial_reach - star_reach
        rescue_map[e] = rescued & backward  # only count backward rescues

    # Greedy cover: repeatedly pick edge that rescues most uncovered
    uncovered = set(backward)
    greedy_cover = []
    while uncovered:
        best_e = max(non_star, key=lambda e: len(rescue_map[e] & uncovered))
        gain = rescue_map[best_e] & uncovered
        if not gain:
            break
        greedy_cover.append((best_e, len(gain)))
        uncovered -= gain

    # Pair coverage: how many edges rescue each backward pair?
    pair_coverage = Counter()
    for e, rescued in rescue_map.items():
        for p in rescued:
            pair_coverage[p] += 1

    return {
        'backward_count': len(backward),
        'rescue_sizes': sorted([len(v) for v in rescue_map.values()], reverse=True),
        'non_star_count': len(non_star),
        'greedy_cover_size': len(greedy_cover),
        'greedy_cover': greedy_cover,
        'uncovered': len(uncovered),
        'min_pair_coverage': min(pair_coverage.values()) if pair_coverage else 0,
        'max_pair_coverage': max(pair_coverage.values()) if pair_coverage else 0,
        'mean_pair_coverage': (sum(pair_coverage.values()) / len(pair_coverage)
                               if pair_coverage else 0),
    }


def main():
    print("Birthday bound: hub set-cover analysis")
    print("=" * 70)

    for n in [6, 8, 10, 12, 15, 20]:
        m = n * (n - 1) // 2
        samples = min(500, max(50, 5000 // n))
        edges_template = [(i, j) for i in range(n) for j in range(i + 1, n)]

        backward_counts = []
        greedy_sizes = []
        min_coverages = []
        mean_coverages = []
        max_rescue_sizes = []
        mean_rescue_sizes = []
        hub_valid_count = 0
        total_hubs = 0

        for trial in range(samples):
            ts_vals = list(range(1, m + 1))
            random.shuffle(ts_vals)
            timestamps = {e: t for e, t in zip(edges_template, ts_vals)}

            # Analyze best hub (lowest greedy cover size)
            best = None
            for h in range(n):
                info = analyze_hub(n, timestamps, h)
                total_hubs += 1
                if info['uncovered'] == 0 and info['greedy_cover_size'] <= n - 2:
                    hub_valid_count += 1
                if best is None or info['greedy_cover_size'] < best['greedy_cover_size']:
                    best = info

            backward_counts.append(best['backward_count'])
            greedy_sizes.append(best['greedy_cover_size'])
            min_coverages.append(best['min_pair_coverage'])
            mean_coverages.append(best['mean_pair_coverage'])
            if best['rescue_sizes']:
                max_rescue_sizes.append(best['rescue_sizes'][0])
                mean_rescue_sizes.append(
                    sum(best['rescue_sizes']) / len(best['rescue_sizes']))

        budget = n - 2
        non_star = m - (n - 1)

        print(f"\nK_{n} (m={m}, budget={budget}, non-star={non_star}), "
              f"{samples} samples:")
        print(f"  Backward pairs: {backward_counts[0]} "
              f"(= C({n-1},2) = {(n-1)*(n-2)//2})")
        print(f"  Greedy cover (best hub): "
              f"mean={sum(greedy_sizes)/len(greedy_sizes):.1f}, "
              f"max={max(greedy_sizes)}, "
              f"budget={budget}")
        print(f"  Greedy valid hubs: {hub_valid_count}/{total_hubs} "
              f"({100*hub_valid_count/total_hubs:.1f}%)")
        print(f"  Max rescue per edge: "
              f"mean={sum(max_rescue_sizes)/len(max_rescue_sizes):.1f}")
        print(f"  Mean rescue per edge: "
              f"mean={sum(mean_rescue_sizes)/len(mean_rescue_sizes):.1f}")
        print(f"  Min coverage of a pair: "
              f"mean={sum(min_coverages)/len(min_coverages):.1f}")
        print(f"  Mean coverage of a pair: "
              f"mean={sum(mean_coverages)/len(mean_coverages):.1f}")

        # Key ratio: backward_pairs / budget = pairs each tree edge must cover on avg
        avg_load = backward_counts[0] / budget
        print(f"  Average load per tree edge: {avg_load:.1f} backward pairs")
        print(f"  Ratio mean_rescue / load: "
              f"{sum(mean_rescue_sizes)/len(mean_rescue_sizes) / avg_load:.2f}")


if __name__ == '__main__':
    main()
