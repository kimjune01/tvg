"""
Is max-run the only property needed to classify?

For each max-run value:
1. Is the spanner property ALWAYS satisfied? (should be yes)
2. What's the case distribution? (flat/steep-in/steep-out)
3. Can we reach any max-run from any other via adjacent swaps?
4. Does the max-run of the HUB (not the whole instance) determine which case?

The claim: max-run of the chosen hub determines which route type
dominates, and the three cases are always exhaustive regardless of
max-run. So the proof only needs to handle each max-run bucket.
"""

import random
from itertools import combinations
from collections import defaultdict, Counter


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


def hub_max_run(n, edges, timestamps, hub):
    m = len(edges)
    ordered = sorted(range(m), key=lambda i: timestamps[i])
    involves_hub = [(edges[i][0] == hub or edges[i][1] == hub) for i in ordered]
    max_run = 0
    cur = 0
    for b in involves_hub:
        if b:
            cur += 1
            max_run = max(max_run, cur)
        else:
            cur = 0
    return max_run


def instance_max_run(n, edges, timestamps):
    """Max-run across ALL vertices."""
    return max(hub_max_run(n, edges, timestamps, v) for v in range(n))


def instance_min_max_run(n, edges, timestamps):
    """Min of per-vertex max-runs (the most interleaved vertex)."""
    return min(hub_max_run(n, edges, timestamps, v) for v in range(n))


def exhaustive_any_hub(n, edges, timestamps):
    m = len(edges)
    timed = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in range(m)])
    target = compute_reachability(n, timed)
    for hub in range(n):
        star_idx = set(i for i, (u, v) in enumerate(edges) if u == hub or v == hub)
        tree_candidates = [i for i in range(m) if i not in star_idx]
        for subset in combinations(tree_candidates, n - 2):
            used = star_idx | set(subset)
            sub = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in used])
            if compute_reachability(n, sub) == target:
                return True, hub
    return False, None


def swap_path_to_target_run(n, edges, ts, target_run):
    """Try to reach a labeling with a specific max-run via adjacent swaps.
    Returns (reached, new_ts, num_swaps)."""
    ts = ts[:]
    m = len(edges)
    for attempt in range(m * 10):
        current_run = instance_max_run(n, edges, ts)
        if current_run == target_run:
            return True, ts, attempt

        # Try all adjacent swaps, pick one that moves toward target
        best_swap = None
        best_dist = abs(current_run - target_run)

        for t_val in range(1, m):
            idx_a = ts.index(t_val)
            idx_b = ts.index(t_val + 1)
            ts[idx_a], ts[idx_b] = ts[idx_b], ts[idx_a]
            new_run = instance_max_run(n, edges, ts)
            dist = abs(new_run - target_run)
            if dist < best_dist:
                best_dist = dist
                best_swap = (idx_a, idx_b)
            ts[idx_a], ts[idx_b] = ts[idx_b], ts[idx_a]  # undo

        if best_swap is None:
            # Try random swap
            t_val = random.randint(1, m - 1)
            idx_a = ts.index(t_val)
            idx_b = ts.index(t_val + 1)
            ts[idx_a], ts[idx_b] = ts[idx_b], ts[idx_a]
        else:
            idx_a, idx_b = best_swap
            ts[idx_a], ts[idx_b] = ts[idx_b], ts[idx_a]

    return False, ts, m * 10


def run(n, num_samples):
    edges = make_edges(n)
    m = len(edges)
    print(f"\nK_{n}: {n} vertices, {m} edges, degree={n-1}")
    print("=" * 60)

    # 1. Distribution of max-runs and spanner existence per bucket
    run_buckets = defaultdict(lambda: {'count': 0, 'has_spanner': 0})
    hub_run_buckets = defaultdict(lambda: {'count': 0, 'hub_works': 0})

    for _ in range(num_samples):
        ts = list(range(1, m + 1))
        random.shuffle(ts)

        inst_run = instance_max_run(n, edges, ts)
        run_buckets[inst_run]['count'] += 1

        ok, hub = exhaustive_any_hub(n, edges, ts)
        if ok:
            run_buckets[inst_run]['has_spanner'] += 1

        # Per-hub: which max-run hubs work?
        for v in range(n):
            hr = hub_max_run(n, edges, ts, v)
            hub_run_buckets[hr]['count'] += 1
            # Check if this hub works (exhaustive)
            star_idx = set(i for i, (u, w) in enumerate(edges) if u == v or w == v)
            tree_candidates = [i for i in range(m) if i not in star_idx]
            timed = sorted([(ts[i], edges[i][0], edges[i][1]) for i in range(m)])
            target = compute_reachability(n, timed)
            hub_ok = False
            for subset in combinations(tree_candidates, n - 2):
                used = star_idx | set(subset)
                sub = sorted([(ts[i], edges[i][0], edges[i][1]) for i in used])
                if compute_reachability(n, sub) == target:
                    hub_ok = True
                    break
            if hub_ok:
                hub_run_buckets[hr]['hub_works'] += 1

    print(f"\nInstance max-run distribution (spanner always exists?):")
    for mr in sorted(run_buckets):
        b = run_buckets[mr]
        pct = b['has_spanner'] / b['count'] * 100
        print(f"  max_run={mr}: {b['count']:>5d} instances, "
              f"spanner={b['has_spanner']}/{b['count']} ({pct:.1f}%)")

    print(f"\nPer-hub max-run (does hub with this max-run work?):")
    for mr in sorted(hub_run_buckets):
        b = hub_run_buckets[mr]
        pct = b['hub_works'] / b['count'] * 100
        print(f"  hub_run={mr}: {b['count']:>5d} checks, "
              f"works={b['hub_works']}/{b['count']} ({pct:.1f}%)")

    # 2. Reachability: can we swap from identity to each max-run?
    print(f"\nReachability via adjacent swaps:")
    identity = list(range(1, m + 1))
    id_run = instance_max_run(n, edges, identity)
    print(f"  Identity max-run: {id_run}")

    all_runs = sorted(run_buckets.keys())
    for target in all_runs:
        reached, _, swaps = swap_path_to_target_run(n, edges, identity[:], target)
        status = f"reached in {swaps} swaps" if reached else "NOT reached"
        print(f"  Target run={target}: {status}")


def main():
    random.seed(42)
    for n, samples in [(5, 3000), (6, 500)]:
        run(n, samples)


if __name__ == "__main__":
    main()
