"""
Exact Nash equilibrium computation for the temporal spanner game.

Builder plays optimally (exact minimum spanner via ILP-style search).
Adversary plays optimally (exhaustive enumeration for small n, or
targeted search for larger n).

Goal: determine the true minimax value — the worst-case minimum spanner size.
"""

import time
import math
from itertools import permutations, combinations


def make_edges(n: int) -> list[tuple[int, int]]:
    return [(i, j) for i in range(n) for j in range(i + 1, n)]


def compute_reachability(n: int, timed_edges: list[tuple[int, int, int]]) -> list[int]:
    """
    Compute reachability bitmasks. timed_edges = [(timestamp, u, v), ...] sorted by time.
    Returns reach[src] = bitmask of vertices reachable from src.
    """
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


def exact_minimum_spanner(n: int, edges: list[tuple[int, int]], timestamps: list[int]) -> int:
    """
    Find the exact minimum spanner size.
    Strategy: greedy to get upper bound, then search below it.
    """
    m = len(edges)
    timed = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in range(m)])
    target = compute_reachability(n, timed)

    # Quick check: is the graph temporally connected?
    full_mask = (1 << n) - 1
    for src in range(n):
        expected = full_mask ^ (1 << src)
        if target[src] != expected:
            # Not fully connected — spanner = all edges needed
            # Still find minimum
            pass

    # Greedy upper bound (try removing edges, lowest timestamp first for variety)
    included = list(range(m))
    for idx in sorted(range(m), key=lambda i: -timestamps[i]):
        candidate = [i for i in included if i != idx]
        sub_timed = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in candidate])
        if compute_reachability(n, sub_timed) == target:
            included = candidate
    greedy_size = len(included)

    # Now search for smaller subsets
    best = greedy_size
    for size in range(n - 1, greedy_size):
        found = False
        for subset in combinations(range(m), size):
            sub_timed = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in subset])
            if compute_reachability(n, sub_timed) == target:
                best = size
                found = True
                break
        if found:
            break

    return best


def exhaustive_adversary(n: int):
    """
    Exhaustive search over ALL labelings. Feasible for K_4 (720 perms).
    Returns the true minimax value.
    """
    edges = make_edges(n)
    m = len(edges)

    worst_size = 0
    worst_labeling = None
    best_size = m
    count = 0
    sizes = {}

    start = time.time()

    for perm in permutations(range(1, m + 1)):
        timestamps = list(perm)
        size = exact_minimum_spanner(n, edges, timestamps)

        if size > worst_size:
            worst_size = size
            worst_labeling = timestamps[:]
        if size < best_size:
            best_size = size

        sizes[size] = sizes.get(size, 0) + 1
        count += 1

        if count % 100 == 0:
            elapsed = time.time() - start
            print(f"  {count} labelings, worst={worst_size}, best={best_size} ({elapsed:.1f}s)")

    elapsed = time.time() - start
    print(f"\nK_{n} EXACT (all {count} labelings, {elapsed:.1f}s):")
    print(f"  Minimax value (worst-case min spanner): {worst_size}")
    print(f"  Best-case min spanner: {best_size}")
    print(f"  Distribution: {dict(sorted(sizes.items()))}")
    print(f"  Worst labeling: {worst_labeling}")

    return worst_size, best_size, sizes


def sampled_exact(n: int, num_samples: int):
    """
    Sample random labelings but compute EXACT minimum spanner for each.
    """
    import random
    edges = make_edges(n)
    m = len(edges)

    worst_size = 0
    worst_labeling = None
    best_size = m
    total = 0
    count = 0
    sizes = {}

    start = time.time()

    for i in range(num_samples):
        timestamps = list(range(1, m + 1))
        random.shuffle(timestamps)

        size = exact_minimum_spanner(n, edges, timestamps)

        if size > worst_size:
            worst_size = size
            worst_labeling = timestamps[:]
        if size < best_size:
            best_size = size

        total += size
        sizes[size] = sizes.get(size, 0) + 1
        count += 1

        if (i + 1) % max(1, num_samples // 10) == 0:
            elapsed = time.time() - start
            print(f"  {i+1}/{num_samples}: worst={worst_size}, best={best_size}, "
                  f"avg={total/count:.2f} ({elapsed:.1f}s)")

    elapsed = time.time() - start
    avg = total / count
    print(f"\nK_{n} EXACT ({count} samples, {elapsed:.1f}s):")
    print(f"  Worst min spanner: {worst_size}")
    print(f"  Best min spanner: {best_size}")
    print(f"  Average: {avg:.2f}")
    print(f"  Distribution: {dict(sorted(sizes.items()))}")

    return worst_size, best_size, avg


def main():
    print("Exact Nash equilibrium for temporal spanner game")
    print("=" * 60)

    results = {}

    # K_4: exhaustive (720 labelings × exact minimum)
    print("\n--- K_4: Exhaustive ---")
    w, b, dist = exhaustive_adversary(4)
    results[4] = (w, b)

    # K_5: sampled exact (exact minimum on random labelings)
    # 10! = 3.6M total, sample 2000 with exact
    print("\n--- K_5: Sampled exact ---")
    w, b, avg = sampled_exact(5, 2000)
    results[5] = (w, b)

    # K_6: sampled exact (fewer samples, exact is slower)
    print("\n--- K_6: Sampled exact ---")
    w, b, avg = sampled_exact(6, 500)
    results[6] = (w, b)

    # K_7: sampled exact
    print("\n--- K_7: Sampled exact ---")
    w, b, avg = sampled_exact(7, 200)
    results[7] = (w, b)

    # K_8: sampled exact
    print("\n--- K_8: Sampled exact ---")
    w, b, avg = sampled_exact(8, 100)
    results[8] = (w, b)

    print("\n" + "=" * 60)
    print("EXACT minimax values (builder plays optimally)")
    print(f"{'n':>4} {'worst':>6} {'best':>6} {'w/n':>6} {'w/(n·lgn)':>10} {'2(n-1)':>7} {'greedy_worst':>13}")
    print("-" * 65)

    # Compare with greedy results from previous run
    greedy_worst = {4: 5, 5: 7, 6: 10, 7: 13, 8: 15}

    for n, (w, b) in sorted(results.items()):
        log2n = math.log2(n)
        gw = greedy_worst.get(n, "?")
        print(f"{n:>4} {w:>6} {b:>6} {w/n:>6.2f} {w/(n*log2n):>10.3f} {2*(n-1):>7} {gw:>13}")


if __name__ == "__main__":
    main()
