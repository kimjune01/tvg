"""
Check: is V⁻ temporally connected via its internal edges?

The claim In(e) ⊇ V⁻ requires every a_i to have a temporal path
to e's endpoint a_{i₀} using only V⁻ internal edges (all with
timestamps < t(e)).

If V⁻ internal edges don't form a temporally connected subgraph,
some a_i can't reach a_{i₀} and the pivot coverage drops below k+1.
"""

import random
from itertools import combinations


def temporal_reachability_within(k, internal_edges, internal_ts):
    """Compute temporal reachability among k vertices using only
    the given internal edges with given timestamps.
    Returns: reach[i] = set of vertices reachable from i via
    temporal paths (non-decreasing timestamps).
    """
    # Build timed edge list (undirected)
    timed = sorted(zip(internal_ts, internal_edges))

    reach = [{i} for i in range(k)]

    # Forward sweep: process edges in timestamp order
    # Each edge (u,v) at time t: merge reachability
    # Actually need proper temporal reachability (non-decreasing)
    # Use: reach_with_time[v] = {(source, arrival_time)}

    reach_t = [{(i, 0)} for i in range(k)]  # (source, arrival_time)

    for t, (u, v) in timed:
        # Anyone who reached u by time t can now reach v at time t
        new_for_v = set()
        new_for_u = set()

        for src, arr in reach_t[u]:
            if arr <= t:
                new_for_v.add((src, t))
        for src, arr in reach_t[v]:
            if arr <= t:
                new_for_u.add((src, t))

        # Add new entries (keep earliest arrival per source)
        for src, arr in new_for_v:
            existing = {a for s, a in reach_t[v] if s == src}
            if not existing or arr < min(existing):
                reach_t[v].add((src, arr))
        for src, arr in new_for_u:
            existing = {a for s, a in reach_t[u] if s == src}
            if not existing or arr < min(existing):
                reach_t[u].add((src, arr))

    # Extract reachability
    reach = [set() for _ in range(k)]
    for v in range(k):
        for src, _ in reach_t[v]:
            reach[src].add(v)

    return reach


def check_vminus_connectivity(k, vminus_edges, vminus_ts):
    """Check if V⁻ is temporally connected via its internal edges.
    Returns (is_connected, reach_matrix, num_reachable_pairs).
    """
    reach = temporal_reachability_within(k, vminus_edges, vminus_ts)

    total_pairs = k * (k - 1)
    reachable = sum(len(r) - 1 for r in reach)  # subtract self

    is_connected = all(len(r) == k for r in reach)
    return is_connected, reachable, total_pairs


def generate_sm(k):
    """Generate SM(k) and return V⁻ internal edges + timestamps."""
    # V⁻ internal edges: pairs within {0,...,k-1}
    vminus_edges = [(i, j) for i in range(k) for j in range(i+1, k)]
    t = 1
    vminus_ts = []
    for i in range(k):
        for j in range(i+1, k):
            vminus_ts.append(t)
            t += 1
    return vminus_edges, vminus_ts


def generate_random_biclique(k, seed=None):
    """Generate random extremally matched biclique.
    V⁻ internal edges get timestamps 1..k(k-1)/2.
    """
    if seed is not None:
        random.seed(seed)

    vminus_edges = [(i, j) for i in range(k) for j in range(i+1, k)]
    num_internal = len(vminus_edges)

    # Random permutation of timestamps 1..num_internal
    vminus_ts = list(range(1, num_internal + 1))
    random.shuffle(vminus_ts)

    return vminus_edges, vminus_ts


def pivot_coverage(k, vminus_edges, vminus_ts, pivot_endpoint):
    """How many V⁻ vertices can reach pivot_endpoint via V⁻ internal edges?"""
    reach = temporal_reachability_within(k, vminus_edges, vminus_ts)
    # Count vertices that can reach pivot_endpoint
    count = sum(1 for i in range(k) if pivot_endpoint in reach[i])
    return count


def main():
    random.seed(42)

    print("V⁻ TEMPORAL CONNECTIVITY CHECK")
    print("=" * 60)

    # SM(k)
    print("\n--- SM(k) ---\n")
    for k in range(3, 9):
        edges, ts = generate_sm(k)
        is_conn, reachable, total = check_vminus_connectivity(k, edges, ts)

        # Check coverage from each vertex as potential pivot endpoint
        coverages = []
        for endpoint in range(k):
            cov = pivot_coverage(k, edges, ts, endpoint)
            coverages.append(cov)

        print(f"SM({k}): k={k}, V⁻ edges={len(edges)}")
        print(f"  Temporally connected: {is_conn}")
        print(f"  Reachable pairs: {reachable}/{total} ({100*reachable/total:.0f}%)")
        print(f"  Pivot coverage per endpoint: {coverages}")
        print(f"  Min coverage: {min(coverages)}, Max: {max(coverages)}")
        print()

    # Random bicliques
    print("--- Random bicliques ---\n")
    for k in [3, 4, 5, 6, 7, 8]:
        samples = {3: 2000, 4: 1000, 5: 500, 6: 200, 7: 100, 8: 50}[k]
        connected = 0
        min_coverage_all = []
        reach_fracs = []

        for s in range(samples):
            edges, ts = generate_random_biclique(k, seed=42 + s)
            is_conn, reachable, total = check_vminus_connectivity(k, edges, ts)

            if is_conn:
                connected += 1

            reach_fracs.append(reachable / total)

            # Min coverage across all potential pivot endpoints
            min_cov = k  # start high
            for endpoint in range(k):
                cov = pivot_coverage(k, edges, ts, endpoint)
                min_cov = min(min_cov, cov)
            min_coverage_all.append(min_cov)

        avg_reach = sum(reach_fracs) / len(reach_fracs)
        avg_min_cov = sum(min_coverage_all) / len(min_coverage_all)
        worst_min_cov = min(min_coverage_all)
        all_reach_pivot = sum(1 for c in min_coverage_all if c == k)

        print(f"k={k} ({samples} samples):")
        print(f"  Fully connected: {connected}/{samples} ({100*connected/samples:.1f}%)")
        print(f"  Avg reachability: {100*avg_reach:.1f}%")
        print(f"  Avg min-pivot-coverage: {avg_min_cov:.1f} (need k={k})")
        print(f"  Worst min-pivot-coverage: {worst_min_cov}")
        print(f"  Every vertex reaches every pivot endpoint: "
              f"{all_reach_pivot}/{samples}")

        # Distribution of min coverage
        from collections import Counter
        dist = Counter(min_coverage_all)
        print(f"  Min-coverage distribution: {dict(sorted(dist.items()))}")
        print()


if __name__ == "__main__":
    main()
