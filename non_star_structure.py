"""
Structure of non-star optimal spanners in truly hub-less K_n instances.

Questions:
1. Is the [3,3,3,3,2,2] degree pattern at K_6 universal?
2. What graph structure do these spanners have? (trees, cycles, etc.)
3. Does the 50% forward ratio characterize hub-less instances?
4. For K_6: enumerate ALL truly hub-less instances in a large sample,
   find ALL minimal spanners for each, characterize.
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


def check_spanner(n, timestamps, edge_set):
    all_timed = sorted([(t, u, v) for (u, v), t in timestamps.items()])
    target = compute_reachability(n, all_timed)
    sub_timed = sorted([(timestamps[e], e[0], e[1]) for e in edge_set])
    span_reach = compute_reachability(n, sub_timed)
    return span_reach == target


def is_truly_hubless(n, timestamps):
    """Exhaustive check: no hub has a valid star+tree of size 2n-3."""
    all_edges = list(timestamps.keys())
    for hub in range(n):
        star = {(min(hub, v), max(hub, v)) for v in range(n) if v != hub}
        non_star = [e for e in all_edges if e not in star]
        need = n - 2
        for tree_edges in combinations(non_star, need):
            if check_spanner(n, timestamps, star | set(tree_edges)):
                return False
    return True


def find_all_min_spanners(n, timestamps, max_results=20):
    """Find all minimum-size spanners."""
    all_edges = list(timestamps.keys())
    for size in range(n - 1, len(all_edges) + 1):
        results = []
        for subset in combinations(all_edges, size):
            if check_spanner(n, timestamps, set(subset)):
                results.append(set(subset))
                if len(results) >= max_results:
                    return size, results
        if results:
            return size, results
    return None, []


def graph_properties(n, edge_set):
    """Compute graph properties of edge set."""
    degrees = [0] * n
    for u, v in edge_set:
        degrees[u] += 1
        degrees[v] += 1

    # Check connectivity
    adj = [[] for _ in range(n)]
    for u, v in edge_set:
        adj[u].append(v)
        adj[v].append(u)

    visited = set()
    stack = [0]
    while stack:
        v = stack.pop()
        if v in visited:
            continue
        visited.add(v)
        for u in adj[v]:
            if u not in visited:
                stack.append(u)

    # Cycle count: edges - vertices + components
    components = 1 if len(visited) == n else "disconnected"
    cycle_rank = len(edge_set) - n + 1 if len(visited) == n else "N/A"

    return {
        'degrees': sorted(degrees),
        'max_deg': max(degrees),
        'min_deg': min(degrees),
        'connected': len(visited) == n,
        'cycle_rank': cycle_rank,
        'size': len(edge_set),
    }


def forward_ratio(n, timestamps, v):
    """Fraction of pairs (a,b) where t(a,v) <= t(v,b)."""
    forward = 0
    total = 0
    for a in range(n):
        if a == v:
            continue
        for b in range(n):
            if b == v or b == a:
                continue
            ta = timestamps[(min(a, v), max(a, v))]
            tb = timestamps[(min(v, b), max(v, b))]
            total += 1
            if ta <= tb:
                forward += 1
    return forward / total if total > 0 else 0.5


def main():
    print("Non-star spanner structure in hub-less K_n instances")
    print("=" * 60)

    n = 6
    m = n * (n - 1) // 2
    samples = 100000
    hubless_instances = []

    print(f"\nK_{n}: scanning {samples} instances for truly hub-less...")

    for trial in range(samples):
        edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
        ts_vals = list(range(1, m + 1))
        random.shuffle(ts_vals)
        timestamps = {e: t for e, t in zip(edges, ts_vals)}

        if is_truly_hubless(n, timestamps):
            hubless_instances.append(dict(timestamps))
            if len(hubless_instances) >= 20:
                break

        if (trial + 1) % 10000 == 0:
            print(f"  ...{trial+1} checked, {len(hubless_instances)} hub-less found")

    print(f"\nFound {len(hubless_instances)} truly hub-less instances")

    # Analyze each
    degree_patterns = Counter()
    all_forward_ratios = []
    min_sizes = Counter()

    for idx, ts in enumerate(hubless_instances):
        # Forward ratios
        ratios = [forward_ratio(n, ts, v) for v in range(n)]
        all_forward_ratios.append(ratios)

        # Find minimum spanners
        min_size, spanners = find_all_min_spanners(n, ts, max_results=50)
        min_sizes[min_size] += 1

        if idx < 5:
            print(f"\n  Instance {idx+1}:")
            print(f"    Forward ratios: {[f'{r:.2f}' for r in ratios]}")
            print(f"    Min spanner size: {min_size} (2n-3={2*n-3})")
            print(f"    Number of min spanners: {len(spanners)}")

        # Degree patterns of all min spanners
        for sp in spanners:
            props = graph_properties(n, sp)
            degree_patterns[tuple(props['degrees'])] += 1

            if idx < 3:
                print(f"      degrees={props['degrees']}, "
                      f"cycle_rank={props['cycle_rank']}, "
                      f"connected={props['connected']}")

    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY ({len(hubless_instances)} hub-less instances)")
    print(f"{'='*60}")

    print(f"\nMinimum spanner sizes: {dict(min_sizes)}")

    print(f"\nDegree patterns of min spanners:")
    for pattern, count in degree_patterns.most_common(10):
        print(f"  {list(pattern)}: {count}")

    print(f"\nForward ratios:")
    if all_forward_ratios:
        all_flat = [r for ratios in all_forward_ratios for r in ratios]
        print(f"  Mean: {sum(all_flat)/len(all_flat):.4f}")
        print(f"  Min: {min(all_flat):.4f}")
        print(f"  Max: {max(all_flat):.4f}")
        # Are they all exactly 0.5?
        exact_half = sum(1 for r in all_flat if r == 0.5)
        print(f"  Exactly 0.5: {exact_half}/{len(all_flat)}")


if __name__ == '__main__':
    main()
