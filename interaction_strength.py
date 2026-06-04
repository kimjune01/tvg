"""
Edge interaction strength: are rescue sets subadditive or superadditive?

If adding edges e1 and e2 together rescues MORE pairs than |R(e1)| + |R(e2)|,
interactions are superadditive (synergy). This would mean the forced-edge
analysis overcounts the required edges.

Measure: for random pairs of non-star edges,
  synergy(e1,e2) = |R({e1,e2})| - |R(e1) ∪ R(e2)|
  (positive = superadditive = journey chaining helps)
"""

import random
from itertools import combinations

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


def measure_interactions(n, timestamps, hub, num_pairs=200):
    all_edges = list(timestamps.keys())
    all_timed = sorted([(t, u, v) for (u, v), t in timestamps.items()])
    target = compute_reachability(n, all_timed)

    star = {(min(hub, v), max(hub, v)) for v in range(n) if v != hub}
    non_star = [e for e in all_edges if e not in star]
    star_timed = sorted([(timestamps[e], e[0], e[1]) for e in star])
    star_reach = compute_reachability(n, star_timed)
    backward = target - star_reach

    # Individual rescue maps
    rescue_map = {}
    for e in non_star:
        trial = star | {e}
        trial_timed = sorted([(timestamps[ee], ee[0], ee[1]) for ee in trial])
        rescue_map[e] = (compute_reachability(n, trial_timed) - star_reach) & backward

    # Sample pairs of non-star edges
    if len(non_star) < 2:
        return None

    edge_pairs = list(combinations(non_star, 2))
    if len(edge_pairs) > num_pairs:
        edge_pairs = random.sample(edge_pairs, num_pairs)

    synergies = []
    for e1, e2 in edge_pairs:
        # Joint rescue
        trial = star | {e1, e2}
        trial_timed = sorted([(timestamps[ee], ee[0], ee[1]) for ee in trial])
        joint = (compute_reachability(n, trial_timed) - star_reach) & backward

        # Individual union
        union = rescue_map[e1] | rescue_map[e2]

        synergy = len(joint) - len(union)
        synergies.append(synergy)

    # Also measure synergy for triples
    triple_synergies = []
    if len(non_star) >= 3:
        edge_triples = list(combinations(non_star, 3))
        if len(edge_triples) > num_pairs:
            edge_triples = random.sample(edge_triples, num_pairs)

        for e1, e2, e3 in edge_triples:
            trial = star | {e1, e2, e3}
            trial_timed = sorted([(timestamps[ee], ee[0], ee[1]) for ee in trial])
            joint = (compute_reachability(n, trial_timed) - star_reach) & backward
            union = rescue_map[e1] | rescue_map[e2] | rescue_map[e3]
            synergy = len(joint) - len(union)
            triple_synergies.append(synergy)

    return {
        'pair_synergies': synergies,
        'triple_synergies': triple_synergies,
        'backward_count': len(backward),
    }


def main():
    print("Edge interaction / synergy analysis")
    print("=" * 70)

    for n in [6, 8, 10, 12, 15]:
        m = n * (n - 1) // 2
        samples = min(100, max(20, 2000 // n))
        edges_template = [(i, j) for i in range(n) for j in range(i + 1, n)]

        all_pair_syn = []
        all_triple_syn = []
        positive_pair_frac = []
        positive_triple_frac = []

        for trial in range(samples):
            ts_vals = list(range(1, m + 1))
            random.shuffle(ts_vals)
            timestamps = {e: t for e, t in zip(edges_template, ts_vals)}

            # Use hub 0
            result = measure_interactions(n, timestamps, 0, num_pairs=100)
            if result is None:
                continue

            all_pair_syn.extend(result['pair_synergies'])
            if result['pair_synergies']:
                pos = sum(1 for s in result['pair_synergies'] if s > 0)
                positive_pair_frac.append(pos / len(result['pair_synergies']))

            all_triple_syn.extend(result['triple_synergies'])
            if result['triple_synergies']:
                pos = sum(1 for s in result['triple_synergies'] if s > 0)
                positive_triple_frac.append(pos / len(result['triple_synergies']))

        backward = (n - 1) * (n - 2) // 2
        print(f"\nK_{n} (backward={backward}), {samples} samples:")

        if all_pair_syn:
            mean_s = sum(all_pair_syn) / len(all_pair_syn)
            max_s = max(all_pair_syn)
            pos_frac = sum(1 for s in all_pair_syn if s > 0) / len(all_pair_syn)
            mean_pos = (sum(s for s in all_pair_syn if s > 0) /
                        max(1, sum(1 for s in all_pair_syn if s > 0)))
            print(f"  Pair synergy: mean={mean_s:.2f}, max={max_s}, "
                  f"positive={100*pos_frac:.1f}%")
            if pos_frac > 0:
                print(f"    Mean when positive: {mean_pos:.2f}")

        if all_triple_syn:
            mean_s = sum(all_triple_syn) / len(all_triple_syn)
            max_s = max(all_triple_syn)
            pos_frac = sum(1 for s in all_triple_syn if s > 0) / len(all_triple_syn)
            mean_pos = (sum(s for s in all_triple_syn if s > 0) /
                        max(1, sum(1 for s in all_triple_syn if s > 0)))
            print(f"  Triple synergy: mean={mean_s:.2f}, max={max_s}, "
                  f"positive={100*pos_frac:.1f}%")
            if pos_frac > 0:
                print(f"    Mean when positive: {mean_pos:.2f}")

        # Interactive greedy: add edges sequentially, recomputing reachability
        print(f"\n  Interactive greedy cover size (hub 0):")
        interactive_sizes = []

        for trial in range(min(samples, 50)):
            ts_vals = list(range(1, m + 1))
            random.shuffle(ts_vals)
            timestamps = {e: t for e, t in zip(edges_template, ts_vals)}

            all_timed = sorted([(t, u, v) for (u, v), t in timestamps.items()])
            target = compute_reachability(n, all_timed)
            star = {(min(0, v), max(0, v)) for v in range(n) if v != 0}
            non_star = [e for e in timestamps if e not in star]
            star_timed = sorted([(timestamps[e], e[0], e[1]) for e in star])
            star_reach = compute_reachability(n, star_timed)

            current = set(star)
            count = 0
            while True:
                sub = sorted([(timestamps[e], e[0], e[1]) for e in current])
                cur_reach = compute_reachability(n, sub)
                if cur_reach == target:
                    break
                cur_count = len(cur_reach)
                best_e, best_g = None, 0
                for e in non_star:
                    if e in current:
                        continue
                    trial_set = current | {e}
                    sub2 = sorted([(timestamps[ee], ee[0], ee[1]) for ee in trial_set])
                    g = len(compute_reachability(n, sub2)) - cur_count
                    if g > best_g:
                        best_g = g
                        best_e = e
                if best_e is None or best_g <= 0:
                    break
                current.add(best_e)
                count += 1

            interactive_sizes.append(count)

        if interactive_sizes:
            avg_s = sum(interactive_sizes) / len(interactive_sizes)
            print(f"    mean={avg_s:.1f}, max={max(interactive_sizes)}, budget={n-2}")

if __name__ == '__main__':
    main()
