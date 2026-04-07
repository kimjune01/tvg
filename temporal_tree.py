"""
Temporally-aware tree construction.

The greedy tree picks edges by coverage count. But coverage depends on
temporal composability — an edge (a,b) at time t only helps if there's
a valid journey through it.

New tree strategies:
1. Greedy-coverage (baseline): maximize pair coverage per edge
2. Temporal-complement: pick tree edges whose timestamps fill gaps
   in the star's timestamp range
3. Reverse-priority: prioritize edges that cover (late→early) pairs,
   since those are what the star misses
4. Composition-aware: pick edge (a,b) that maximizes the number of
   valid 3-hop compositions a→v→c→...→b through the star+tree
"""

import random
import time
from itertools import combinations


def make_edges(n):
    return [(i, j) for i in range(n) for j in range(i + 1, n)]


def compute_reachability(n, timed_edges):
    reached_by = [dict() for _ in range(n)]
    for i in range(n):
        reached_by[i][i] = 0
    for t, u, v in timed_edges:
        sources_u = {s: arr for s, arr in reached_by[u].items() if arr <= t}
        sources_v = {s: arr for s, arr in reached_by[v].items() if arr <= t}
        for s, arr in sources_u.items():
            if s not in reached_by[v] or t < reached_by[v][s]:
                reached_by[v][s] = t
        for s, arr in sources_v.items():
            if s not in reached_by[u] or t < reached_by[u][s]:
                reached_by[u][s] = t
    reach = [0] * n
    for v in range(n):
        for s in reached_by[v]:
            if s != v:
                reach[s] |= (1 << v)
    return reach


def build_tree_greedy_coverage(n, edges, timestamps, hub):
    """Baseline: greedy by coverage count."""
    m = len(edges)
    timed = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in range(m)])
    target = compute_reachability(n, timed)
    star_idx = set(i for i, (u, v) in enumerate(edges) if u == hub or v == hub)
    current = set(star_idx)
    tree_candidates = [i for i in range(m) if i not in star_idx]

    def current_reach():
        sub = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in current])
        return compute_reachability(n, sub)

    for _ in range(n - 2):
        cr = current_reach()
        if cr == target:
            break
        current_covered = sum(bin(r).count('1') for r in cr)
        best_edge = None
        best_gain = -1
        for idx in tree_candidates:
            if idx in current:
                continue
            trial = current | {idx}
            sub = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in trial])
            tr = compute_reachability(n, sub)
            gain = sum(bin(r).count('1') for r in tr) - current_covered
            if gain > best_gain:
                best_gain = gain
                best_edge = idx
        if best_edge is None or best_gain <= 0:
            break
        current.add(best_edge)

    return current_reach() == target


def build_tree_temporal_complement(n, edges, timestamps, hub):
    """Pick tree edges that fill timestamp gaps in the star."""
    m = len(edges)
    edge_map = {}
    for i, (u, v) in enumerate(edges):
        edge_map[(u, v)] = timestamps[i]
        edge_map[(v, u)] = timestamps[i]

    timed = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in range(m)])
    target = compute_reachability(n, timed)
    star_idx = set(i for i, (u, v) in enumerate(edges) if u == hub or v == hub)

    # Star timestamps
    star_times = sorted([timestamps[i] for i in star_idx])
    star_gaps = []
    for i in range(len(star_times) - 1):
        star_gaps.append((star_times[i+1] - star_times[i], star_times[i], star_times[i+1]))
    star_gaps.sort(reverse=True)  # largest gaps first

    # Non-star edges, sorted by how well they fill star gaps
    tree_candidates = [i for i in range(m) if i not in star_idx]

    def gap_fill_score(idx):
        t = timestamps[idx]
        # How far is this timestamp from the nearest star timestamp?
        min_dist = min(abs(t - st) for st in star_times)
        return min_dist  # higher = fills a bigger gap

    # Sort tree candidates: edges that fill the biggest gaps first
    tree_candidates.sort(key=lambda i: -gap_fill_score(i))

    # Greedy: add edges in gap-filling order, but only keep if they improve coverage
    current = set(star_idx)

    def current_reach():
        sub = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in current])
        return compute_reachability(n, sub)

    for idx in tree_candidates:
        if len(current) - len(star_idx) >= n - 2:
            break
        cr = current_reach()
        if cr == target:
            break
        trial = current | {idx}
        sub = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in trial])
        tr = compute_reachability(n, sub)
        if sum(bin(r).count('1') for r in tr) > sum(bin(r).count('1') for r in cr):
            current.add(idx)

    return current_reach() == target


def build_tree_reverse_priority(n, edges, timestamps, hub):
    """Prioritize tree edges that cover reverse (late→early) pairs."""
    m = len(edges)
    edge_map = {}
    for i, (u, v) in enumerate(edges):
        edge_map[(u, v)] = timestamps[i]
        edge_map[(v, u)] = timestamps[i]

    timed = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in range(m)])
    target = compute_reachability(n, timed)
    star_idx = set(i for i, (u, v) in enumerate(edges) if u == hub or v == hub)
    current = set(star_idx)
    tree_candidates = [i for i in range(m) if i not in star_idx]

    # Identify reverse pairs: (a,b) where t(a,hub) > t(hub,b)
    others = [v for v in range(n) if v != hub]
    reverse_pairs = set()
    for a in others:
        for b in others:
            if a != b and edge_map[(a, hub)] > edge_map[(hub, b)]:
                reverse_pairs.add((a, b))

    def current_reach():
        sub = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in current])
        return compute_reachability(n, sub)

    def reverse_coverage_gain(idx):
        """How many reverse pairs does adding this edge newly cover?"""
        trial = current | {idx}
        sub_old = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in current])
        sub_new = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in trial])
        reach_old = compute_reachability(n, sub_old)
        reach_new = compute_reachability(n, sub_new)
        gain = 0
        for (a, b) in reverse_pairs:
            old_ok = (reach_old[a] >> b) & 1
            new_ok = (reach_new[a] >> b) & 1
            if new_ok and not old_ok:
                gain += 1
        return gain

    for _ in range(n - 2):
        cr = current_reach()
        if cr == target:
            break
        best_edge = None
        best_gain = -1
        for idx in tree_candidates:
            if idx in current:
                continue
            gain = reverse_coverage_gain(idx)
            if gain > best_gain:
                best_gain = gain
                best_edge = idx
        if best_edge is None or best_gain <= 0:
            # Fall back to regular coverage
            current_covered = sum(bin(r).count('1') for r in cr)
            for idx in tree_candidates:
                if idx in current:
                    continue
                trial = current | {idx}
                sub = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in trial])
                tr = compute_reachability(n, sub)
                gain = sum(bin(r).count('1') for r in tr) - current_covered
                if gain > best_gain:
                    best_gain = gain
                    best_edge = idx
            if best_edge is None or best_gain <= 0:
                break
        current.add(best_edge)

    return current_reach() == target


def build_tree_earliest_bridge(n, edges, timestamps, hub):
    """Pick tree edges ordered by timestamp (earliest first).
    Intuition: early tree edges create early arrival times,
    which compose with more star edges."""
    m = len(edges)
    timed = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in range(m)])
    target = compute_reachability(n, timed)
    star_idx = set(i for i, (u, v) in enumerate(edges) if u == hub or v == hub)
    current = set(star_idx)

    # Non-star edges sorted by timestamp (earliest first)
    tree_candidates = sorted(
        [i for i in range(m) if i not in star_idx],
        key=lambda i: timestamps[i]
    )

    def current_reach():
        sub = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in current])
        return compute_reachability(n, sub)

    for idx in tree_candidates:
        if len(current) - len(star_idx) >= n - 2:
            break
        cr = current_reach()
        if cr == target:
            break
        trial = current | {idx}
        sub = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in trial])
        tr = compute_reachability(n, sub)
        if sum(bin(r).count('1') for r in tr) > sum(bin(r).count('1') for r in cr):
            current.add(idx)

    return current_reach() == target


def build_tree_latest_bridge(n, edges, timestamps, hub):
    """Pick tree edges ordered by timestamp (latest first)."""
    m = len(edges)
    timed = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in range(m)])
    target = compute_reachability(n, timed)
    star_idx = set(i for i, (u, v) in enumerate(edges) if u == hub or v == hub)
    current = set(star_idx)

    tree_candidates = sorted(
        [i for i in range(m) if i not in star_idx],
        key=lambda i: -timestamps[i]
    )

    def current_reach():
        sub = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in current])
        return compute_reachability(n, sub)

    for idx in tree_candidates:
        if len(current) - len(star_idx) >= n - 2:
            break
        cr = current_reach()
        if cr == target:
            break
        trial = current | {idx}
        sub = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in trial])
        tr = compute_reachability(n, sub)
        if sum(bin(r).count('1') for r in tr) > sum(bin(r).count('1') for r in cr):
            current.add(idx)

    return current_reach() == target


def run(n, num_samples):
    edges = make_edges(n)
    m = len(edges)
    print(f"\nK_{n}: {n} vertices, {m} edges")
    print("=" * 70)

    strategies = {
        'greedy_coverage': build_tree_greedy_coverage,
        'temporal_complement': build_tree_temporal_complement,
        'reverse_priority': build_tree_reverse_priority,
        'earliest_bridge': build_tree_earliest_bridge,
        'latest_bridge': build_tree_latest_bridge,
    }

    # Per strategy: how many instances have ≥1 working hub?
    any_hub = {s: 0 for s in strategies}
    # Per strategy: total vertex successes
    vertex_ok = {s: 0 for s in strategies}
    total_vertices = 0
    # Union of all strategies
    union_any = 0

    start = time.time()
    for trial in range(num_samples):
        ts = list(range(1, m + 1))
        random.shuffle(ts)

        per_strategy_any = {s: False for s in strategies}
        for v in range(n):
            total_vertices += 1
            for sname, builder in strategies.items():
                ok = builder(n, edges, ts, v)
                if ok:
                    vertex_ok[sname] += 1
                    per_strategy_any[sname] = True

        for sname in strategies:
            if per_strategy_any[sname]:
                any_hub[sname] += 1

        if any(per_strategy_any.values()):
            union_any += 1

        if (trial + 1) % max(1, num_samples // 5) == 0:
            elapsed = time.time() - start
            print(f"  {trial+1}/{num_samples} ({elapsed:.1f}s)")

    total = num_samples
    print(f"\nResults (instances with ≥1 working hub):")
    print(f"{'strategy':>25s}  {'any_hub%':>8s}  {'vertex_ok%':>10s}")
    print("-" * 50)
    for sname in strategies:
        print(f"{sname:>25s}  {any_hub[sname]/total*100:>8.2f}  "
              f"{vertex_ok[sname]/total_vertices*100:>10.2f}")
    print(f"{'UNION (any strategy)':>25s}  {union_any/total*100:>8.2f}")

    # Per-hub comparison: for each vertex in each instance,
    # which strategies succeed where greedy fails?
    print(f"\nRecovery rates (when greedy_coverage fails on a hub):")
    greedy_fail_count = 0
    recovery = {s: 0 for s in strategies if s != 'greedy_coverage'}

    for _ in range(min(num_samples, 2000)):
        ts = list(range(1, m + 1))
        random.shuffle(ts)
        for v in range(n):
            greedy_ok = build_tree_greedy_coverage(n, edges, ts, v)
            if not greedy_ok:
                greedy_fail_count += 1
                for sname, builder in strategies.items():
                    if sname == 'greedy_coverage':
                        continue
                    if builder(n, edges, ts, v):
                        recovery[sname] += 1

    if greedy_fail_count > 0:
        print(f"  Greedy failures: {greedy_fail_count}")
        for sname, count in recovery.items():
            print(f"  {sname:>25s}: recovers {count}/{greedy_fail_count} "
                  f"({count/greedy_fail_count*100:.1f}%)")


def main():
    random.seed(42)
    for n, samples in [(5, 5000), (6, 1500), (7, 400)]:
        run(n, samples)


if __name__ == "__main__":
    main()
