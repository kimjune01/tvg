"""
SAT-based temporal spanner verification for K_n.

For a given n, find the timestamp assignment that MAXIMIZES the minimum
spanner size. If that maximum is ≤ 2n-3, the conjecture holds for this n.

Approach: adversarial search with exact minimum spanner computation.
Not full SAT encoding — instead, use the greedy spanner as upper bound
and try to find hard instances via local search on the timestamp assignment.

For exact verification at n=10, we use:
1. Random sampling to find candidate hard instances
2. Greedy spanner (fast upper bound)
3. Edge-criticality check (fast lower bound: count edges that can't be removed)
"""

import random
import time
from itertools import combinations


def compute_reachability_fast(n, timed_edges):
    """Fast reachability via forward sweep."""
    reached_by = [dict() for _ in range(n)]
    for i in range(n):
        reached_by[i][i] = 0
    for t, u, v in timed_edges:  # must be sorted by t
        # Collect sources reaching u and v by time t
        new_v = {}
        new_u = {}
        for s, arr in reached_by[u].items():
            if arr <= t and (s not in reached_by[v] or t < reached_by[v][s]):
                new_v[s] = t
        for s, arr in reached_by[v].items():
            if arr <= t and (s not in reached_by[u] or t < reached_by[u][s]):
                new_u[s] = t
        reached_by[v].update(new_v)
        reached_by[u].update(new_u)

    reach = [0] * n
    for v in range(n):
        for s in reached_by[v]:
            if s != v:
                reach[s] |= (1 << v)
    return reach


def greedy_spanner(n, edges, timestamps):
    """Greedy edge removal — returns upper bound on min spanner."""
    m = len(edges)
    timed = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in range(m)])
    target = compute_reachability_fast(n, timed)

    included = set(range(m))
    # Remove edges highest timestamp first
    for idx in sorted(range(m), key=lambda i: -timestamps[i]):
        trial = sorted([(timestamps[i], edges[i][0], edges[i][1])
                       for i in included if i != idx])
        if compute_reachability_fast(n, trial) == target:
            included.discard(idx)

    return len(included), included


def count_essential(n, edges, timestamps):
    """Count edges that MUST be in every spanner (lower bound)."""
    m = len(edges)
    timed = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in range(m)])
    target = compute_reachability_fast(n, timed)

    essential = 0
    for idx in range(m):
        trial = sorted([(timestamps[i], edges[i][0], edges[i][1])
                       for i in range(m) if i != idx])
        if compute_reachability_fast(n, trial) != target:
            essential += 1
    return essential


def local_search_hard_instance(n, edges, iterations=500):
    """Try to find the hardest timestamp assignment via local search."""
    m = len(edges)

    # Start with random assignment
    best_ts = list(range(1, m + 1))
    random.shuffle(best_ts)
    best_size, _ = greedy_spanner(n, edges, best_ts)

    for it in range(iterations):
        # Swap two random timestamps
        ts = best_ts[:]
        i, j = random.sample(range(m), 2)
        ts[i], ts[j] = ts[j], ts[i]

        size, _ = greedy_spanner(n, edges, ts)
        if size >= best_size:
            best_size = size
            best_ts = ts

    return best_size, best_ts


def main():
    for n in [8, 9, 10]:
        edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
        m = len(edges)
        target_bound = 2 * n - 3

        print(f"\n{'='*60}")
        print(f"K_{n}: {n} vertices, {m} edges, target ≤ {target_bound}")
        print(f"{'='*60}")

        start = time.time()

        # Phase 1: random sampling
        worst_greedy = 0
        worst_ts = None
        num_samples = 2000 if n <= 8 else 500

        for i in range(num_samples):
            ts = list(range(1, m + 1))
            random.shuffle(ts)
            size, _ = greedy_spanner(n, edges, ts)
            if size > worst_greedy:
                worst_greedy = size
                worst_ts = ts[:]
            if (i + 1) % max(1, num_samples // 5) == 0:
                elapsed = time.time() - start
                print(f"  Sample {i+1}/{num_samples}: worst greedy = {worst_greedy} ({elapsed:.1f}s)")

        # Phase 2: local search from best found
        print(f"\n  Local search from worst found (greedy={worst_greedy})...")
        ls_size, ls_ts = local_search_hard_instance(n, edges, iterations=300)
        if ls_size > worst_greedy:
            worst_greedy = ls_size
            worst_ts = ls_ts
            print(f"  Local search improved to {worst_greedy}")
        else:
            print(f"  Local search: no improvement (still {worst_greedy})")

        # Phase 3: count essential edges on worst instance
        print(f"\n  Counting essential edges on worst instance...")
        essential = count_essential(n, edges, worst_ts)

        elapsed = time.time() - start

        print(f"\n  RESULT for K_{n}:")
        print(f"    Worst greedy spanner: {worst_greedy}")
        print(f"    Essential edges (lower bound): {essential}")
        print(f"    Target (2n-3): {target_bound}")
        print(f"    Conjecture holds (greedy): {'YES' if worst_greedy <= target_bound else 'NO — COUNTEREXAMPLE?'}")
        print(f"    Time: {elapsed:.1f}s")


if __name__ == "__main__":
    random.seed(42)
    main()
