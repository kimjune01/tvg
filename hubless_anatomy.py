"""
Find and characterize truly hub-less K_n instances.

For each, check: does ANY 2n-3 edge subset form a valid spanner?
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


def check_spanner(n, timestamps, edge_set):
    all_timed = sorted([(t, u, v) for (u, v), t in timestamps.items()])
    target = compute_reachability(n, all_timed)
    sub_timed = sorted([(timestamps[e], e[0], e[1]) for e in edge_set])
    span_reach = compute_reachability(n, sub_timed)
    return span_reach == target


def star_exhaustive_check(n, timestamps, hub):
    star = {(min(hub, v), max(hub, v)) for v in range(n) if v != hub}
    non_star = [e for e in timestamps if e not in star]
    need = n - 2
    for tree_edges in combinations(non_star, need):
        edges = star | set(tree_edges)
        if check_spanner(n, timestamps, edges):
            return True
    return False


def find_min_spanner(n, timestamps):
    """Find minimum spanner size by trying all subsets from small to large."""
    all_edges = list(timestamps.keys())
    m = len(all_edges)
    # Start from 2n-4 and go up
    for size in range(2 * n - 4, m + 1):
        if size > 2 * n - 1:  # don't go too far
            return None, None
        for subset in combinations(all_edges, size):
            if check_spanner(n, timestamps, set(subset)):
                return size, set(subset)
    return None, None


def analyze_instance(n, timestamps):
    """Full analysis of a hub-less instance."""
    all_edges = list(timestamps.keys())
    m = len(all_edges)

    print(f"\n  Timestamp matrix:")
    # Show as adjacency matrix
    for i in range(n):
        row = []
        for j in range(n):
            if i == j:
                row.append("  .")
            else:
                e = (min(i, j), max(i, j))
                row.append(f"{timestamps[e]:3d}")
        print(f"    {' '.join(row)}")

    # Per-vertex stats
    print(f"\n  Per-vertex analysis:")
    for v in range(n):
        neighbors = [(timestamps[(min(v, u), max(v, u))], u)
                      for u in range(n) if u != v]
        neighbors.sort()
        ts = [t for t, u in neighbors]
        # Forward pairs: how many (a,b) with t(a,v) <= t(v,b)?
        forward = 0
        total_pairs = 0
        for a in range(n):
            if a == v:
                continue
            for b in range(n):
                if b == v or b == a:
                    continue
                ta = timestamps[(min(a, v), max(a, v))]
                tb = timestamps[(min(v, b), max(v, b))]
                total_pairs += 1
                if ta <= tb:
                    forward += 1
        print(f"    v={v}: times={ts}, forward={forward}/{total_pairs} "
              f"({100*forward/total_pairs:.0f}%)")

    # Find minimum spanner
    print(f"\n  Searching for minimum spanner...")
    min_size, min_spanner = find_min_spanner(n, timestamps)
    if min_size is not None:
        print(f"  Minimum spanner size: {min_size} (2n-3={2*n-3})")
        if min_size <= 2 * n - 3:
            print(f"  ✓ Conjecture holds (non-star spanner exists)")
            # Analyze structure of min spanner
            degrees = [0] * n
            for u, v in min_spanner:
                degrees[u] += 1
                degrees[v] += 1
            print(f"  Degrees: {degrees}")
            max_deg = max(degrees)
            hubs = [v for v in range(n) if degrees[v] == max_deg]
            print(f"  Max degree: {max_deg} at vertices {hubs}")
            print(f"  Edges: {sorted(min_spanner)}")
        else:
            print(f"  ✗ CONJECTURE FAILS!")
    else:
        print(f"  Could not find spanner ≤ {2*n-1}")


def main():
    print("Finding and characterizing truly hub-less K_n instances")
    print("=" * 60)

    for n in [5, 6, 7]:
        m = n * (n - 1) // 2
        samples = {5: 100000, 6: 50000, 7: 10000}[n]
        truly_hubless = []

        print(f"\nK_{n}: scanning {samples} instances...")

        for trial in range(samples):
            edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
            ts_vals = list(range(1, m + 1))
            random.shuffle(ts_vals)
            timestamps = {e: t for e, t in zip(edges, ts_vals)}

            # Exhaustive hub check
            has_hub = False
            for h in range(n):
                if star_exhaustive_check(n, timestamps, h):
                    has_hub = True
                    break

            if not has_hub:
                truly_hubless.append(dict(timestamps))
                if len(truly_hubless) >= 5:
                    break  # enough examples

        print(f"  Found {len(truly_hubless)} truly hub-less instances")

        for idx, ts in enumerate(truly_hubless[:3]):
            print(f"\n  === Instance {idx+1} ===")
            analyze_instance(n, ts)


if __name__ == '__main__':
    main()
