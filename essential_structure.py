"""
Essential edge structure analysis for temporal spanners.

For SM(k) and random temporal K_n:
1. Count essential edges (removal breaks reachability)
2. Classify essential edges by type
3. Check if essentials decompose into two spanning trees
4. Test forward-tree + backward-tree hypothesis
"""

import random
from collections import defaultdict
from itertools import combinations


def make_edges(n):
    return [(i, j) for i in range(n) for j in range(i + 1, n)]


def compute_reachability(n, timed_edges):
    """Returns list of bitmasks: reach[s] = set of vertices reachable from s."""
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


def reachable_pairs(n, timed_edges):
    """Return set of reachable (s, t) pairs."""
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
    pairs = set()
    for v in range(n):
        for s in reached_by[v]:
            if s != v:
                pairs.add((s, v))
    return pairs


def generate_sm(k):
    """Generate SM(k): the hard instance for temporal spanners."""
    n = 2 * k
    edges = make_edges(n)
    m = len(edges)
    eidx = {}
    for i, (u, v) in enumerate(edges):
        eidx[(u, v)] = i
        eidx[(v, u)] = i

    ts = [0] * m
    t = 1
    # V- internal edges (earliest)
    for i in range(k):
        for j in range(i + 1, k):
            ts[eidx[(i, j)]] = t
            t += 1
    # Cross edges (middle)
    for d in range(k):
        for i in range(k):
            j = (i + d) % k
            idx = eidx[(min(i, k + j), max(i, k + j))]
            if ts[idx] == 0:
                ts[idx] = t
                t += 1
    # V+ internal edges (latest)
    for i in range(k):
        for j in range(i + 1, k):
            ts[eidx[(k + i, k + j)]] = t
            t += 1

    return n, edges, ts, eidx


def generate_random_temporal(n, seed=None):
    """Generate random temporal K_n with distinct timestamps."""
    if seed is not None:
        random.seed(seed)
    edges = make_edges(n)
    m = len(edges)
    ts = list(range(1, m + 1))
    random.shuffle(ts)
    eidx = {}
    for i, (u, v) in enumerate(edges):
        eidx[(u, v)] = i
        eidx[(v, u)] = i
    return n, edges, ts, eidx


def find_essential_edges(n, edges, ts):
    """Find all essential edges: edges whose removal breaks some reachable pair."""
    m = len(edges)
    timed_all = sorted([(ts[i], edges[i][0], edges[i][1]) for i in range(m)])
    target_pairs = reachable_pairs(n, timed_all)

    essential = []
    essential_pairs = {}  # edge_idx -> set of pairs uniquely served

    for idx in range(m):
        remaining = [i for i in range(m) if i != idx]
        sub = sorted([(ts[i], edges[i][0], edges[i][1]) for i in remaining])
        new_pairs = reachable_pairs(n, sub)
        lost = target_pairs - new_pairs
        if lost:
            essential.append(idx)
            essential_pairs[idx] = lost

    return essential, essential_pairs


def classify_edge(u, v, k):
    """Classify edge in SM(k): V- internal, cross, V+ internal."""
    if u < k and v < k:
        return "V-"
    elif u >= k and v >= k:
        return "V+"
    else:
        return "cross"


def build_forward_tree(n, edges, ts):
    """Earliest-arrival spanning tree: process edges earliest-first, add if new vertex reached."""
    m = len(edges)
    timed = sorted([(ts[i], i) for i in range(m)])

    # BFS/greedy: track which vertices are reachable from vertex 0
    # Actually: build a tree that spans all vertices by earliest edges
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra == rb:
            return False
        parent[ra] = rb
        return True

    tree_edges = []
    for t, idx in timed:
        u, v = edges[idx]
        if union(u, v):
            tree_edges.append(idx)
            if len(tree_edges) == n - 1:
                break

    return set(tree_edges)


def build_backward_tree(n, edges, ts):
    """Latest-departure spanning tree: process edges latest-first, add if new vertex reached."""
    m = len(edges)
    timed = sorted([(ts[i], i) for i in range(m)], reverse=True)

    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra == rb:
            return False
        parent[ra] = rb
        return True

    tree_edges = []
    for t, idx in timed:
        u, v = edges[idx]
        if union(u, v):
            tree_edges.append(idx)
            if len(tree_edges) == n - 1:
                break

    return set(tree_edges)


def check_nash_williams(n, edge_set, edges, k_trees):
    """
    Check Nash-Williams condition: graph has k edge-disjoint spanning trees
    iff for every partition into r parts, cross-partition edges >= k(r-1).

    We check all partitions for small n (only feasible for small n).
    For larger n, check random partitions + the obvious ones.
    """
    adj = set()
    for idx in edge_set:
        u, v = edges[idx]
        adj.add((min(u, v), max(u, v)))

    # For small n, check all partitions (Bell number grows fast)
    # Use Stirling partitions for r=2..n
    def cross_edges(partition):
        """Count edges crossing partition boundaries."""
        count = 0
        for (u, v) in adj:
            if partition[u] != partition[v]:
                count += 1
        return count

    # Check partition into 2 parts (all 2^(n-1) - 1 ways)
    min_ratio = float('inf')
    worst_partition = None

    for mask in range(1, 1 << (n - 1)):
        partition = [0] * n
        r = 1
        parts = {0}
        for i in range(1, n):
            if mask & (1 << (i - 1)):
                partition[i] = 1
                parts.add(1)
        if len(parts) < 2:
            continue
        ce = cross_edges(partition)
        needed = k_trees * (len(parts) - 1)
        ratio = ce / needed if needed > 0 else float('inf')
        if ratio < min_ratio:
            min_ratio = ratio
            worst_partition = partition[:]

    # Also check partitions into 3..min(n,5) parts using random sampling
    for r in range(3, min(n, 6)):
        for _ in range(200):
            partition = [random.randint(0, r - 1) for _ in range(n)]
            actual_parts = len(set(partition))
            if actual_parts < 2:
                continue
            ce = cross_edges(partition)
            needed = k_trees * (actual_parts - 1)
            ratio = ce / needed if needed > 0 else float('inf')
            if ratio < min_ratio:
                min_ratio = ratio

    return min_ratio >= 1.0, min_ratio


def is_connected(n, edge_set, edges):
    """Check if the edge set forms a connected graph."""
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra == rb:
            return
        parent[ra] = rb

    for idx in edge_set:
        u, v = edges[idx]
        union(u, v)

    roots = set(find(i) for i in range(n))
    return len(roots) == 1


def analyze_instance(name, n, edges, ts, eidx, k=None):
    """Full analysis of one temporal K_n instance."""
    print(f"\n{'='*60}")
    print(f"  {name}  (n={n}, 2n-3={2*n-3})")
    print(f"{'='*60}")

    m = len(edges)
    essential, essential_pairs = find_essential_edges(n, edges, ts)
    e_count = len(essential)

    print(f"\nEssential edges: {e_count}  (2n-3 = {2*n-3})")
    print(f"Gap (2n-3 - essential): {2*n-3 - e_count}")

    if e_count > 2 * n - 3:
        print(f"*** ESSENTIAL > 2n-3! Conjecture in danger! ***")

    # Classification (for SM instances)
    if k is not None:
        types = defaultdict(int)
        for idx in essential:
            u, v = edges[idx]
            types[classify_edge(u, v, k)] += 1
        print(f"\nEssential by type:  V-={types['V-']}  cross={types['cross']}  V+={types['V+']}")

    # Pairs uniquely served
    service_counts = [len(essential_pairs[idx]) for idx in essential]
    if service_counts:
        print(f"\nPairs uniquely served per essential edge:")
        print(f"  min={min(service_counts)}  max={max(service_counts)}  "
              f"mean={sum(service_counts)/len(service_counts):.1f}  "
              f"total_unique_pairs={len(set().union(*essential_pairs.values()))}")

    # Connectivity of essential subgraph
    if essential:
        conn = is_connected(n, essential, edges)
        print(f"\nEssential subgraph connected: {conn}")

    # Degree distribution
    if essential:
        deg = defaultdict(int)
        for idx in essential:
            u, v = edges[idx]
            deg[u] += 1
            deg[v] += 1
        degs = sorted(deg.values(), reverse=True)
        print(f"Essential subgraph degrees: {degs}")

    # Nash-Williams: can essentials support 2 edge-disjoint spanning trees?
    if e_count >= 2 * (n - 1):
        nw_ok, nw_ratio = check_nash_williams(n, essential, edges, 2)
        print(f"\nNash-Williams (2 trees): {'YES' if nw_ok else 'NO'}  (min ratio={nw_ratio:.2f})")
    else:
        print(f"\nNash-Williams (2 trees): NOT POSSIBLE ({e_count} < {2*(n-1)} = 2(n-1))")
        # Check for 1 tree + forest
        if e_count >= n - 1:
            print(f"  But enough for 1 spanning tree + forest")

    # Forward and backward trees
    fwd = build_forward_tree(n, edges, ts)
    bwd = build_backward_tree(n, edges, ts)
    shared = fwd & bwd
    union_size = len(fwd | bwd)

    print(f"\nForward tree (earliest-arrival):  {len(fwd)} edges")
    print(f"Backward tree (latest-departure): {len(bwd)} edges")
    print(f"Shared edges: {len(shared)}")
    print(f"Union size: {union_size}  (2(n-1)-shared = {2*(n-1)-len(shared)})")

    # Does the union form a spanner?
    union_edges = fwd | bwd
    timed_union = sorted([(ts[i], edges[i][0], edges[i][1]) for i in union_edges])
    timed_all = sorted([(ts[i], edges[i][0], edges[i][1]) for i in range(m)])
    target = reachable_pairs(n, timed_all)
    union_reach = reachable_pairs(n, timed_union)
    union_is_spanner = union_reach == target

    print(f"Union is spanner: {union_is_spanner}")
    if not union_is_spanner:
        lost = len(target - union_reach)
        print(f"  Lost {lost} pairs out of {len(target)}")

    # How many essential edges are in each tree?
    ess_set = set(essential)
    ess_in_fwd = len(ess_set & fwd)
    ess_in_bwd = len(ess_set & bwd)
    ess_in_either = len(ess_set & (fwd | bwd))
    print(f"\nEssential edges in forward tree:  {ess_in_fwd}/{e_count}")
    print(f"Essential edges in backward tree: {ess_in_bwd}/{e_count}")
    print(f"Essential edges in either tree:   {ess_in_either}/{e_count}")

    # Greedy deletion spanner
    included = list(range(m))
    for idx in sorted(range(m), key=lambda i: -ts[i]):
        candidate = [i for i in included if i != idx]
        sub = sorted([(ts[i], edges[i][0], edges[i][1]) for i in candidate])
        if compute_reachability(n, sub) == compute_reachability(n, timed_all):
            included = candidate
    greedy_size = len(included)
    print(f"\nGreedy deletion spanner: {greedy_size} edges")

    return {
        'n': n,
        'essential': e_count,
        'bound': 2 * n - 3,
        'shared': len(shared),
        'union_size': union_size,
        'union_is_spanner': union_is_spanner,
        'greedy': greedy_size,
    }


def main():
    results = []

    # SM instances
    for k in [3, 4, 5, 6]:
        n, edges, ts, eidx = generate_sm(k)
        r = analyze_instance(f"SM({k})", n, edges, ts, eidx, k=k)
        results.append((f"SM({k})", r))

    # Random instances
    for n in [6, 8, 10, 12]:
        for seed in range(3):
            nn, edges, ts, eidx = generate_random_temporal(n, seed=seed * 100 + n)
            r = analyze_instance(f"Random K_{n} (seed={seed*100+n})", nn, edges, ts, eidx)
            results.append((f"Rand_{n}_{seed}", r))

    # Summary
    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")
    print(f"{'Instance':<25} {'n':>3} {'ess':>5} {'2n-3':>5} {'gap':>5} "
          f"{'shared':>6} {'union':>6} {'spanner?':>8} {'greedy':>7}")
    print("-" * 90)
    for name, r in results:
        print(f"{name:<25} {r['n']:>3} {r['essential']:>5} {r['bound']:>5} "
              f"{r['bound']-r['essential']:>5} {r['shared']:>6} "
              f"{r['union_size']:>6} {'YES' if r['union_is_spanner'] else 'NO':>8} "
              f"{r['greedy']:>7}")

    # Check hypothesis: shared >= 1 always?
    print(f"\n--- Hypothesis: forward & backward trees share >= 1 edge ---")
    all_share = all(r['shared'] >= 1 for _, r in results)
    print(f"All instances share >= 1 edge: {all_share}")
    min_shared = min(r['shared'] for _, r in results)
    print(f"Minimum shared edges across all instances: {min_shared}")

    # Check: essential always <= 2n-3?
    print(f"\n--- Essential <= 2n-3? ---")
    all_bounded = all(r['essential'] <= r['bound'] for _, r in results)
    print(f"All instances: essential <= 2n-3: {all_bounded}")
    if not all_bounded:
        violations = [(name, r) for name, r in results if r['essential'] > r['bound']]
        for name, r in violations:
            print(f"  VIOLATION: {name}: essential={r['essential']} > 2n-3={r['bound']}")

    # Check: union always a spanner?
    print(f"\n--- Forward+Backward union is spanner? ---")
    all_span = all(r['union_is_spanner'] for _, r in results)
    print(f"All instances: union is spanner: {all_span}")


if __name__ == "__main__":
    main()
