"""
Forced edge analysis for the birthday bound.

A backward pair with coverage=1 forces that tree edge into the spanner.
Forced edges cascade: once included, they rescue other pairs, potentially
reducing other pairs' coverage to 1, forcing more edges.

Questions:
1. How many pairs have coverage=1? (= # forced edges)
2. After forcing, how many pairs remain uncovered?
3. Does the cascade resolve everything within budget?
4. Scaling with n?
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


def forced_edge_cascade(n, timestamps, hub):
    """Run forced-edge cascade for a hub. Returns cascade trace."""
    all_edges = list(timestamps.keys())
    all_timed = sorted([(t, u, v) for (u, v), t in timestamps.items()])
    target = compute_reachability(n, all_timed)

    star = {(min(hub, v), max(hub, v)) for v in range(n) if v != hub}
    non_star = [e for e in all_edges if e not in star]

    # Star reachability
    star_timed = sorted([(timestamps[e], e[0], e[1]) for e in star])
    star_reach = compute_reachability(n, star_timed)
    backward = target - star_reach

    # Build rescue map
    rescue_map = {}
    for e in non_star:
        trial = star | {e}
        trial_timed = sorted([(timestamps[ee], ee[0], ee[1]) for ee in trial])
        trial_reach = compute_reachability(n, trial_timed)
        rescue_map[e] = (trial_reach - star_reach) & backward

    # Inverse map: for each backward pair, which edges rescue it?
    pair_rescuers = {}
    for p in backward:
        pair_rescuers[p] = {e for e in non_star if p in rescue_map[e]}

    # Cascade: find pairs with exactly 1 rescuer, force that edge
    forced = set()
    covered = set()
    cascade_trace = []
    current_edges = set(star)

    iteration = 0
    while True:
        # Find pairs with coverage 1 among uncovered
        uncovered = backward - covered
        if not uncovered:
            break

        # Update coverage counts
        newly_forced = set()
        for p in uncovered:
            rescuers = pair_rescuers[p] - forced  # available rescuers not yet forced
            if len(rescuers) == 0:
                # Pair has NO available rescuer — this is a problem
                # But it might be covered by interaction of already-forced edges
                pass
            elif len(rescuers) == 1:
                e = next(iter(rescuers))
                newly_forced.add(e)

        if not newly_forced:
            break  # no more forced edges

        # Add forced edges and recompute coverage
        forced |= newly_forced
        current_edges |= newly_forced

        # Recompute what's covered with all current edges
        cur_timed = sorted([(timestamps[e], e[0], e[1]) for e in current_edges])
        cur_reach = compute_reachability(n, cur_timed)
        newly_covered = (cur_reach - star_reach) & backward
        new_this_round = newly_covered - covered
        covered = newly_covered

        iteration += 1
        cascade_trace.append({
            'iteration': iteration,
            'edges_forced': len(newly_forced),
            'total_forced': len(forced),
            'pairs_covered': len(covered),
            'pairs_remaining': len(backward) - len(covered),
        })

    return {
        'backward_count': len(backward),
        'forced_count': len(forced),
        'covered_by_cascade': len(covered),
        'remaining': len(backward) - len(covered),
        'cascade_rounds': len(cascade_trace),
        'trace': cascade_trace,
    }


def main():
    print("Forced edge cascade analysis")
    print("=" * 70)

    for n in [6, 8, 10, 12, 15, 20]:
        m = n * (n - 1) // 2
        samples = min(500, max(50, 5000 // n))
        edges_template = [(i, j) for i in range(n) for j in range(i + 1, n)]
        budget = n - 2

        forced_counts = []
        remaining_counts = []
        cascade_rounds = []
        within_budget = 0
        total_hubs = 0

        for trial in range(samples):
            ts_vals = list(range(1, m + 1))
            random.shuffle(ts_vals)
            timestamps = {e: t for e, t in zip(edges_template, ts_vals)}

            best = None
            for h in range(n):
                result = forced_edge_cascade(n, timestamps, h)
                total_hubs += 1
                if result['remaining'] == 0 and result['forced_count'] <= budget:
                    within_budget += 1
                if best is None or result['remaining'] < best['remaining']:
                    best = result
                elif (result['remaining'] == best['remaining'] and
                      result['forced_count'] < best['forced_count']):
                    best = result

            forced_counts.append(best['forced_count'])
            remaining_counts.append(best['remaining'])
            cascade_rounds.append(best['cascade_rounds'])

        avg_forced = sum(forced_counts) / len(forced_counts)
        avg_remaining = sum(remaining_counts) / len(remaining_counts)
        max_forced = max(forced_counts)
        max_remaining = max(remaining_counts)
        zero_remaining = sum(1 for r in remaining_counts if r == 0)
        avg_rounds = sum(cascade_rounds) / len(cascade_rounds)

        print(f"\nK_{n} (budget={budget}, backward=C({n-1},2)={(n-1)*(n-2)//2}), "
              f"{samples} samples, best hub per instance:")
        print(f"  Forced edges: mean={avg_forced:.1f}, max={max_forced}")
        print(f"  Remaining pairs: mean={avg_remaining:.1f}, max={max_remaining}")
        print(f"  Cascade fully covers: {zero_remaining}/{samples} "
              f"({100*zero_remaining/samples:.1f}%)")
        print(f"  Forced ≤ budget AND covers all: {within_budget}/{total_hubs} hubs "
              f"({100*within_budget/total_hubs:.1f}%)")
        print(f"  Cascade rounds: mean={avg_rounds:.1f}")

        # Distribution of forced edge counts
        dist = Counter(forced_counts)
        print(f"  Forced count distribution (best hub):")
        for k in sorted(dist):
            print(f"    {k:3d}: {dist[k]:4d} ({100*dist[k]/samples:.1f}%)")

        # Show a detailed trace for one instance
        if n <= 10:
            ts_vals = list(range(1, m + 1))
            random.shuffle(ts_vals)
            timestamps = {e: t for e, t in zip(edges_template, ts_vals)}
            result = forced_edge_cascade(n, timestamps, 0)
            print(f"\n  Example trace (hub=0):")
            for step in result['trace']:
                print(f"    Round {step['iteration']}: "
                      f"+{step['edges_forced']} edges "
                      f"(total {step['total_forced']}), "
                      f"covered {step['pairs_covered']}, "
                      f"remaining {step['pairs_remaining']}")


if __name__ == '__main__':
    main()
