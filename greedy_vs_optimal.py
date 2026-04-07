"""
Test whether greedy set cover on the rescue edges always finds the optimal
spanner. If greedy = optimal across all instances, the problem might be in P.
"""

import itertools
import numpy as np
from x3c_reduction import covering_hypergraph, all_reachable


def min_rescue_brute(uncovered, rescue_map):
    """Find minimum set of rescue edges that cover all uncovered pairs."""
    universe = set(uncovered)
    edges = list(rescue_map.keys())

    for size in range(1, len(edges) + 1):
        for combo in itertools.combinations(edges, size):
            covered = set()
            for e in combo:
                covered |= rescue_map[e]
            if covered >= universe:
                return set(combo), size
    return set(edges), len(edges)


def greedy_rescue(uncovered, rescue_map):
    """Greedy set cover on rescue edges."""
    remaining = set(uncovered)
    cover = []
    available = dict(rescue_map)

    while remaining and available:
        best_e = max(available, key=lambda e: len(available[e] & remaining))
        if not (available[best_e] & remaining):
            break
        cover.append(best_e)
        remaining -= available[best_e]
        del available[best_e]

    return set(cover), len(cover), len(remaining) == 0


def test_greedy_vs_optimal(k, n_instances):
    """Compare greedy vs optimal across many instances."""
    gaps = []
    greedy_fails = 0
    optimal_sizes = []
    greedy_sizes = []
    trivial = 0  # forced edges already cover everything

    for seed in range(n_instances):
        rng = np.random.default_rng(seed)
        vals = rng.permutation(k * k)
        M = vals.reshape(k, k)

        forced, uncovered, rescue_map = covering_hypergraph(M)

        if not uncovered:
            trivial += 1
            continue

        if not rescue_map:
            greedy_fails += 1
            continue

        opt_set, opt_size = min_rescue_brute(uncovered, rescue_map)
        gr_set, gr_size, gr_ok = greedy_rescue(uncovered, rescue_map)

        if not gr_ok:
            greedy_fails += 1
            continue

        optimal_sizes.append(opt_size)
        greedy_sizes.append(gr_size)
        gap = gr_size - opt_size
        gaps.append(gap)

        if gap > 0:
            print(f"  seed={seed}: greedy={gr_size}, optimal={opt_size}, GAP={gap}")
            print(f"    Uncovered pairs: {len(uncovered)}, rescue edges: {len(rescue_map)}")

    n_tested = len(gaps)
    n_gap = sum(1 for g in gaps if g > 0)
    print(f"\nk={k}: {n_tested} instances tested, {trivial} trivial, {greedy_fails} greedy fails")
    if n_tested:
        print(f"  Optimal sizes: min={min(optimal_sizes)}, max={max(optimal_sizes)}, "
              f"mean={np.mean(optimal_sizes):.2f}")
        print(f"  Greedy sizes:  min={min(greedy_sizes)}, max={max(greedy_sizes)}, "
              f"mean={np.mean(greedy_sizes):.2f}")
        print(f"  Gaps > 0: {n_gap}/{n_tested} ({100*n_gap/n_tested:.1f}%)")
        if gaps:
            print(f"  Max gap: {max(gaps)}")


def verify_spanner(M, forced, rescue_edges):
    """Verify that forced ∪ rescue_edges is actually a spanner."""
    edges = forced | rescue_edges
    return all_reachable(M, edges)


def test_with_verification(k, n_instances):
    """Same as above but verify the spanners actually work."""
    print(f"\n{'='*60}")
    print(f"k={k}, {n_instances} instances (with verification)")
    print(f"{'='*60}")

    for seed in range(n_instances):
        rng = np.random.default_rng(seed)
        vals = rng.permutation(k * k)
        M = vals.reshape(k, k)

        forced, uncovered, rescue_map = covering_hypergraph(M)

        if not uncovered:
            continue

        if not rescue_map:
            continue

        opt_set, opt_size = min_rescue_brute(uncovered, rescue_map)
        gr_set, gr_size, gr_ok = greedy_rescue(uncovered, rescue_map)

        # Verify optimal
        if not verify_spanner(M, forced, opt_set):
            print(f"  seed={seed}: OPTIMAL SPANNER BROKEN!")
            continue

        if gr_ok and not verify_spanner(M, forced, gr_set):
            print(f"  seed={seed}: GREEDY SPANNER BROKEN!")
            continue

    print("  All verified OK")


if __name__ == "__main__":
    # Quick verification first
    test_with_verification(3, 100)
    test_with_verification(4, 50)

    # Then the main comparison
    print("\n" + "="*60)
    print("GREEDY vs OPTIMAL COMPARISON")
    print("="*60)

    test_greedy_vs_optimal(3, 500)
    test_greedy_vs_optimal(4, 500)
    test_greedy_vs_optimal(5, 200)
