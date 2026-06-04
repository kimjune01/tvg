"""
Prove: star + 3 earliest + 3 latest per vertex spans all pairs.

The 4-hop route for backward pair (v_i, v_j):
  v_i → w (early edge) → hub (star) → w' (star) → v_j (late edge)

Conditions:
  1. σ({v_i, w}) ≤ T_w (early edge time ≤ relay's star time)
  2. T_w ≤ T_{w'} (relay below w' in star ordering)
  3. T_{w'} ≤ σ({w', v_j}) (star time ≤ late edge time)

For the construction to work:
  - v_i must have ≥1 early edge to a vertex w satisfying condition 1
  - v_j must have ≥1 late edge from a vertex w' satisfying condition 3
  - The w and w' must have T_w ≤ T_{w'} (condition 2)

Measure: for each vertex, how many early/late edges satisfy conditions 1/3?
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


def analyze_4hop(n, timestamps, hub, K=3):
    """For each non-hub vertex, count valid early/late relays."""
    star = {(min(hub, v), max(hub, v)) for v in range(n) if v != hub}
    non_hub = [v for v in range(n) if v != hub]
    T = {v: timestamps[(min(hub, v), max(hub, v))] for v in non_hub}

    # For each vertex: find K earliest and K latest non-star edges
    early_relays = {}  # v -> [(w, τ) where τ ≤ T_w]
    late_relays = {}   # v -> [(w, τ) where τ ≥ T_w]

    for v in non_hub:
        v_non_star = []
        for w in non_hub:
            if w == v:
                continue
            e = (min(v, w), max(v, w))
            t = timestamps[e]
            v_non_star.append((t, w))
        v_non_star.sort()

        # K earliest
        early = v_non_star[:K]
        valid_early = [(w, t) for t, w in early if t <= T[w]]
        early_relays[v] = valid_early

        # K latest
        late = v_non_star[-K:]
        valid_late = [(w, t) for t, w in late if t >= T[w]]
        late_relays[v] = valid_late

    # For each backward pair: can the 4-hop route work?
    ordered = sorted(non_hub, key=lambda v: T[v])
    backward_ok = 0
    backward_fail = 0

    for i_idx in range(len(ordered)):
        for j_idx in range(i_idx):
            vi = ordered[i_idx]  # higher star time (source)
            vj = ordered[j_idx]  # lower star time (target)

            # Need: early relay from vi with T_w ≤ T_{w'} for some
            # late relay to vj
            if not early_relays[vi] or not late_relays[vj]:
                backward_fail += 1
                continue

            # Find max T_w among early relays from vi
            max_early_T = max(T[w] for w, _ in early_relays[vi])
            # Find min T_{w'} among late relays to vj
            min_late_T = min(T[w] for w, _ in late_relays[vj])

            if max_early_T <= min_late_T:
                # Can always pair: pick early with highest T, late with lowest T
                backward_ok += 1
            else:
                # Check if any pairing works
                found = False
                for w, _ in early_relays[vi]:
                    for wp, _ in late_relays[vj]:
                        if T[w] <= T[wp]:
                            found = True
                            break
                    if found:
                        break
                if found:
                    backward_ok += 1
                else:
                    backward_fail += 1

    return {
        'backward_ok': backward_ok,
        'backward_fail': backward_fail,
        'early_counts': {v: len(early_relays[v]) for v in non_hub},
        'late_counts': {v: len(late_relays[v]) for v in non_hub},
    }


def main():
    print("4-hop route analysis for K=3 early+late construction")
    print("=" * 70)

    for n in [10, 15, 20, 25]:
        m = n * (n - 1) // 2
        edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
        samples = 500 if n <= 15 else 100

        for K in [2, 3]:
            all_fail = 0
            all_total = 0
            min_early_counts = []
            min_late_counts = []
            full_4hop_success = 0

            for trial in range(samples):
                ts_vals = list(range(1, m + 1))
                random.shuffle(ts_vals)
                timestamps = {e: t for e, t in zip(edges, ts_vals)}

                best_fail = n * n
                best_result = None
                for hub in range(min(n, 5)):
                    result = analyze_4hop(n, timestamps, hub, K)
                    if result['backward_fail'] < best_fail:
                        best_fail = result['backward_fail']
                        best_result = result

                all_fail += best_result['backward_fail']
                all_total += best_result['backward_ok'] + best_result['backward_fail']
                min_early_counts.append(min(best_result['early_counts'].values()))
                min_late_counts.append(min(best_result['late_counts'].values()))
                if best_result['backward_fail'] == 0:
                    full_4hop_success += 1

            avg_fail = all_fail / samples
            pct_4hop = 100 * full_4hop_success / samples
            avg_min_early = sum(min_early_counts) / len(min_early_counts)
            avg_min_late = sum(min_late_counts) / len(min_late_counts)

            print(f"\nn={n}, K={K}:")
            print(f"  4-hop covers all backward: {pct_4hop:.1f}%")
            print(f"  Avg backward failures: {avg_fail:.1f}")
            print(f"  Min valid early relays per vertex: mean={avg_min_early:.1f}")
            print(f"  Min valid late relays per vertex: mean={avg_min_late:.1f}")


if __name__ == '__main__':
    main()
