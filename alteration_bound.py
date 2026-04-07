"""
Alteration bound for temporal spanners.

Key question: can we choose an initial spanning tree that minimizes broken
pairs, then greedily repair with multi-fix edges, staying within 2n-3?

Strategy:
  tree (n-1 edges) + repair edges (≤ n-2) = 2n-3 total
  This works iff the best tree has ≤ n-2 broken pairs AND each greedy
  repair edge can fix at least one pair.

Also tests: spanning forests of the temporal reachability digraph.
"""

import random
import sys
from itertools import combinations
from collections import defaultdict

random.seed(42)

# ---------------------------------------------------------------------------
# Temporal graph generators
# ---------------------------------------------------------------------------

def make_temporal_clique(n):
    """Random temporal K_n: each edge gets a unique random timestamp."""
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
    m = len(edges)
    timestamps = list(range(1, m + 1))
    random.shuffle(timestamps)
    return n, edges, timestamps


def make_sm(k):
    """Structured worst-case instance SM(k) on n=2k vertices."""
    n = 2 * k
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
    m = len(edges)
    eidx = {}
    for i, (u, v) in enumerate(edges):
        eidx[(u, v)] = i
        eidx[(v, u)] = i

    ts = [0] * m
    t = 1
    # Left clique
    for i in range(k):
        for j in range(i + 1, k):
            ts[eidx[(i, j)]] = t; t += 1
    # Cross edges (structured)
    for d in range(k):
        for i in range(k):
            j = (i + d) % k
            ts[eidx[(min(i, k + j), max(i, k + j))]] = t; t += 1
    # Right clique
    for i in range(k):
        for j in range(i + 1, k):
            ts[eidx[(k + i, k + j)]] = t; t += 1

    return n, edges, ts


# ---------------------------------------------------------------------------
# Reachability
# ---------------------------------------------------------------------------

def compute_reachability_set(n, edge_indices, edges, timestamps):
    """Return set of (s, v) pairs that are temporally reachable."""
    timed = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in edge_indices])

    # reached_by[v][s] = earliest arrival time at v starting from s
    reached_by = [dict() for _ in range(n)]
    for v in range(n):
        reached_by[v][v] = 0

    for t, u, v in timed:
        # Collect sources that can reach u by time t
        new_for_v = {}
        new_for_u = {}
        for s, arr in reached_by[u].items():
            if arr <= t:
                if s not in reached_by[v] or t < reached_by[v][s]:
                    new_for_v[s] = t
        for s, arr in reached_by[v].items():
            if arr <= t:
                if s not in reached_by[u] or t < reached_by[u][s]:
                    new_for_u[s] = t
        reached_by[v].update(new_for_v)
        reached_by[u].update(new_for_u)

    R = set()
    for v in range(n):
        for s in reached_by[v]:
            if s != v:
                R.add((s, v))
    return R


# ---------------------------------------------------------------------------
# Spanning tree enumeration (Prüfer sequences for n ≤ 8)
# ---------------------------------------------------------------------------

def prufer_to_tree(seq, n):
    """Convert Prüfer sequence to edge list."""
    degree = [1] * n
    for v in seq:
        degree[v] += 1

    tree_edges = []
    ptr = 0
    leaf = 0
    # Find smallest leaf
    for i in range(n):
        if degree[i] == 1:
            leaf = i
            break

    for v in seq:
        tree_edges.append((min(leaf, v), max(leaf, v)))
        degree[v] -= 1
        degree[leaf] -= 1
        if degree[v] == 1 and v < ptr:
            leaf = v
        else:
            ptr += 1
            while ptr < n and degree[ptr] != 1:
                ptr += 1
            leaf = ptr

    # Last edge connects the two remaining degree-1 nodes
    remaining = [i for i in range(n) if degree[i] == 1]
    if len(remaining) == 2:
        tree_edges.append((min(remaining), max(remaining)))

    return tree_edges


def enumerate_all_trees(n):
    """Enumerate all labeled spanning trees via Prüfer sequences."""
    if n <= 2:
        return [[(0, 1)]]

    trees = []
    # n^(n-2) Prüfer sequences
    count = n ** (n - 2)
    for code in range(count):
        seq = []
        c = code
        for _ in range(n - 2):
            seq.append(c % n)
            c //= n
        tree_edges = prufer_to_tree(seq, n)
        trees.append(tree_edges)
    return trees


def tree_edges_to_indices(tree_edges, edges):
    """Map tree edge list to indices in the master edge list."""
    eidx = {}
    for i, (u, v) in enumerate(edges):
        eidx[(u, v)] = i
        eidx[(v, u)] = i
    return [eidx[e] for e in tree_edges]


# ---------------------------------------------------------------------------
# Random spanning tree (for n > 8)
# ---------------------------------------------------------------------------

def random_spanning_tree(n, edges, timestamps):
    """Random spanning tree via random-weight Kruskal."""
    order = list(range(len(edges)))
    random.shuffle(order)

    parent = list(range(n))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    tree_idx = []
    for idx in order:
        u, v = edges[idx]
        ru, rv = find(u), find(v)
        if ru != rv:
            parent[ru] = rv
            tree_idx.append(idx)
            if len(tree_idx) == n - 1:
                break
    return tree_idx


# ---------------------------------------------------------------------------
# Greedy multi-fix repair
# ---------------------------------------------------------------------------

def greedy_repair(n, tree_indices, edges, timestamps, target_reach):
    """Greedily add edges that fix the most broken pairs."""
    current = list(tree_indices)
    current_set = set(current)
    all_indices = set(range(len(edges)))

    current_reach = compute_reachability_set(n, current, edges, timestamps)
    broken = target_reach - current_reach

    repair_log = []

    while broken:
        candidates = all_indices - current_set
        best_idx = None
        best_fixed = set()

        for idx in candidates:
            trial = current + [idx]
            trial_reach = compute_reachability_set(n, trial, edges, timestamps)
            fixed = broken & trial_reach
            if len(fixed) > len(best_fixed):
                best_fixed = fixed
                best_idx = idx

        if best_idx is None or len(best_fixed) == 0:
            print(f"    WARNING: {len(broken)} pairs unfixable!")
            break

        current.append(best_idx)
        current_set.add(best_idx)
        # Recompute reachability with ALL current edges (not just +1)
        current_reach = compute_reachability_set(n, current, edges, timestamps)
        new_broken = target_reach - current_reach
        actually_fixed = broken - new_broken
        repair_log.append((best_idx, len(actually_fixed)))
        broken = new_broken

    return current, repair_log


# ---------------------------------------------------------------------------
# Analyze what makes the best tree special
# ---------------------------------------------------------------------------

def tree_properties(n, tree_indices, edges, timestamps):
    """Compute structural properties of a tree."""
    tree_edges = [edges[i] for i in tree_indices]
    tree_ts = [timestamps[i] for i in tree_indices]

    # Degree distribution
    deg = [0] * n
    for u, v in tree_edges:
        deg[u] += 1
        deg[v] += 1
    max_deg = max(deg)

    # Timestamp span
    ts_sorted = sorted(tree_ts)
    ts_range = ts_sorted[-1] - ts_sorted[0] if ts_sorted else 0

    # Average timestamp gap
    gaps = [ts_sorted[i+1] - ts_sorted[i] for i in range(len(ts_sorted)-1)]
    avg_gap = sum(gaps) / len(gaps) if gaps else 0

    return {
        'max_degree': max_deg,
        'degree_seq': sorted(deg, reverse=True),
        'ts_range': ts_range,
        'avg_gap': avg_gap,
        'min_ts': ts_sorted[0] if ts_sorted else 0,
        'max_ts': ts_sorted[-1] if ts_sorted else 0,
    }


# ---------------------------------------------------------------------------
# Forest experiment: temporal reachability forest
# ---------------------------------------------------------------------------

def greedy_forest(n, edges, timestamps, target_reach):
    """Build a forest greedily: add edges that maximize reachability gain,
    stop when adding an edge would create a cycle in the underlying graph."""
    parent = list(range(n))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    forest = []
    forest_set = set()
    current_reach = set()  # initially no edges

    all_by_coverage = []

    for iteration in range(n - 1):  # forest has at most n-1 edges
        best_idx = None
        best_gain = -1

        candidates = [i for i in range(len(edges)) if i not in forest_set]
        for idx in candidates:
            u, v = edges[idx]
            if find(u) == find(v):
                continue  # would create cycle
            trial = forest + [idx]
            trial_reach = compute_reachability_set(n, trial, edges, timestamps)
            gain = len(trial_reach) - len(current_reach)
            if gain > best_gain:
                best_gain = gain
                best_idx = idx

        if best_idx is None or best_gain <= 0:
            break

        u, v = edges[best_idx]
        parent[find(u)] = find(v)
        forest.append(best_idx)
        forest_set.add(best_idx)
        current_reach = compute_reachability_set(n, forest, edges, timestamps)

    return forest


# ---------------------------------------------------------------------------
# Main experiment
# ---------------------------------------------------------------------------

def run_experiment(name, n, edges, timestamps):
    m = len(edges)
    all_indices = list(range(m))
    target_reach = compute_reachability_set(n, all_indices, edges, timestamps)
    total_pairs = n * (n - 1)  # ordered pairs
    reachable_pairs = len(target_reach)

    print(f"\n{'='*60}")
    print(f"  {name}   n={n}, m={m}")
    print(f"  Reachable pairs: {reachable_pairs}/{total_pairs}")
    print(f"  Target: 2n-3 = {2*n - 3} edges")
    print(f"{'='*60}")

    # --- Phase 1: Find best tree ---
    EXHAUSTIVE_LIMIT = 8
    if n <= EXHAUSTIVE_LIMIT:
        print(f"\n  Enumerating all {n**(n-2)} spanning trees...")
        all_trees = enumerate_all_trees(n)
        results = []
        for tree_edges in all_trees:
            tidx = tree_edges_to_indices(tree_edges, edges)
            tree_reach = compute_reachability_set(n, tidx, edges, timestamps)
            broken = len(target_reach - tree_reach)
            results.append((broken, tidx))

        results.sort(key=lambda x: x[0])
        min_broken = results[0][0]
        max_broken = results[-1][0]
        avg_broken = sum(r[0] for r in results) / len(results)
        best_tree = results[0][1]

        print(f"  Tree broken pairs: min={min_broken}, avg={avg_broken:.1f}, max={max_broken}")
    else:
        NUM_SAMPLES = 10000
        print(f"\n  Sampling {NUM_SAMPLES} random spanning trees...")
        results = []
        for _ in range(NUM_SAMPLES):
            tidx = random_spanning_tree(n, edges, timestamps)
            tree_reach = compute_reachability_set(n, tidx, edges, timestamps)
            broken = len(target_reach - tree_reach)
            results.append((broken, tidx))

        results.sort(key=lambda x: x[0])
        min_broken = results[0][0]
        max_broken = results[-1][0]
        avg_broken = sum(r[0] for r in results) / len(results)
        best_tree = results[0][1]

        print(f"  Tree broken pairs (sampled): min={min_broken}, avg={avg_broken:.1f}, max={max_broken}")

    print(f"  n-2 = {n-2}")
    print(f"  min_broken ≤ n-2? {'YES' if min_broken <= n-2 else 'NO'} ({min_broken} vs {n-2})")

    # Best tree properties
    props = tree_properties(n, best_tree, edges, timestamps)
    print(f"\n  Best tree properties:")
    print(f"    Degree sequence: {props['degree_seq']}")
    print(f"    Max degree: {props['max_degree']}")
    print(f"    Timestamp range: [{props['min_ts']}, {props['max_ts']}]")
    print(f"    Avg timestamp gap: {props['avg_gap']:.1f}")

    # --- Phase 2: Greedy repair ---
    print(f"\n  Greedy repair from best tree...")
    augmented, repair_log = greedy_repair(n, best_tree, edges, timestamps, target_reach)
    total_edges = len(augmented)
    repair_count = total_edges - len(best_tree)

    print(f"  Repair edges needed: {repair_count}")
    for i, (idx, fixed) in enumerate(repair_log):
        u, v = edges[idx]
        print(f"    Repair {i+1}: edge ({u},{v}) t={timestamps[idx]}, fixed {fixed} pairs")
    print(f"  Total edges: {total_edges}")
    print(f"  2n-3 = {2*n-3}")
    print(f"  Within bound? {'YES' if total_edges <= 2*n-3 else 'NO'} ({total_edges} vs {2*n-3})")

    # --- Phase 3: Greedy forest alternative ---
    if n <= 10:  # forest is expensive
        print(f"\n  Building greedy reachability forest...")
        forest = greedy_forest(n, edges, timestamps, target_reach)
        forest_reach = compute_reachability_set(n, forest, edges, timestamps)
        forest_broken = len(target_reach - forest_reach)
        print(f"  Forest edges: {len(forest)}")
        print(f"  Forest broken pairs: {forest_broken}")

        # Repair from forest
        print(f"  Greedy repair from forest...")
        aug_forest, repair_log_f = greedy_repair(n, forest, edges, timestamps, target_reach)
        total_forest = len(aug_forest)
        print(f"  Forest + repairs: {total_forest} edges")
        print(f"  Within 2n-3? {'YES' if total_forest <= 2*n-3 else 'NO'} ({total_forest} vs {2*n-3})")

    # --- Summary ---
    print(f"\n  SUMMARY for {name}:")
    print(f"    Best tree broken:  {min_broken}")
    print(f"    n-2:               {n-2}")
    print(f"    Repair edges:      {repair_count}")
    print(f"    Total edges:       {total_edges}")
    print(f"    Budget (2n-3):     {2*n-3}")
    print(f"    Tight?             {'YES' if total_edges <= 2*n-3 else 'NO'}")
    ratio = repair_count / max(min_broken, 1)
    print(f"    Repair efficiency: {ratio:.2f} edges per broken pair")

    return {
        'name': name,
        'n': n,
        'min_broken': min_broken,
        'avg_broken': avg_broken,
        'n_minus_2': n - 2,
        'repair_count': repair_count,
        'total_edges': total_edges,
        'budget': 2 * n - 3,
        'within_bound': total_edges <= 2 * n - 3,
    }


def main():
    results = []

    # Random K_n
    for n in [6, 8, 10, 12]:
        nn, edges, ts = make_temporal_clique(n)
        r = run_experiment(f"Random K_{n}", nn, edges, ts)
        results.append(r)

    # SM(k)
    for k in range(3, 8):
        n, edges, ts = make_sm(k)
        r = run_experiment(f"SM({k})", n, edges, ts)
        results.append(r)

    # --- Final table ---
    print(f"\n\n{'='*70}")
    print(f"  FINAL SUMMARY")
    print(f"{'='*70}")
    print(f"  {'Instance':<15} {'n':>3} {'min_brk':>8} {'n-2':>5} {'brk≤n-2':>8} "
          f"{'repairs':>8} {'total':>6} {'2n-3':>5} {'ok?':>5}")
    print(f"  {'-'*65}")
    for r in results:
        ok = 'YES' if r['within_bound'] else 'NO'
        brk_ok = 'YES' if r['min_broken'] <= r['n_minus_2'] else 'NO'
        print(f"  {r['name']:<15} {r['n']:>3} {r['min_broken']:>8} {r['n_minus_2']:>5} "
              f"{brk_ok:>8} {r['repair_count']:>8} {r['total_edges']:>6} "
              f"{r['budget']:>5} {ok:>5}")

    print(f"\n  Key insight: if min_broken ≤ n-2 AND greedy repairs are efficient,")
    print(f"  then alteration gives (n-1) + repairs ≤ 2n-3.")


if __name__ == '__main__':
    main()
