"""
Primal-dual spanner construction via alternating prune/traverse.

Round 1 (traverse): build earliest-arrival spanning tree (n-1 edges)
Round 2 (traverse): find broken pairs in the tree
Round 3 (un-prune): add one repair edge per broken pair
Round 4 (prune): remove newly-redundant edges from the augmented set
Repeat until stable.

Questions:
1. How many rounds to convergence?
2. Does the fixed point always have ≤ 2n-3 edges?
3. Do repairs cascade (fixing one pair breaks another)?
"""

import random
from itertools import combinations


def make_temporal_clique(n):
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
    m = len(edges)
    timestamps = list(range(1, m + 1))
    random.shuffle(timestamps)
    return edges, timestamps


def make_sm_clique(k):
    n = 2 * k
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
    m = len(edges)
    eidx = {}
    for i, (u, v) in enumerate(edges):
        eidx[(u, v)] = i
        eidx[(v, u)] = i

    ts = [0] * m
    t = 1
    for i in range(k):
        for j in range(i + 1, k):
            ts[eidx[(i, j)]] = t; t += 1
    for d in range(k):
        for i in range(k):
            j = (i + d) % k
            ts[eidx[(min(i, k + j), max(i, k + j))]] = t; t += 1
    for i in range(k):
        for j in range(i + 1, k):
            ts[eidx[(k + i, k + j)]] = t; t += 1

    return edges, ts


def compute_reachability(n, edge_indices, edges, timestamps):
    """Compute temporal reachability for a subset of edges."""
    timed = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in edge_indices])

    reach = [{v: 0} for v in range(n)]
    for t, u, v in timed:
        new_v = {}
        new_u = {}
        for s, arr in reach[u].items():
            if arr <= t and (s not in reach[v] or t < reach[v][s]):
                new_v[s] = t
        for s, arr in reach[v].items():
            if arr <= t and (s not in reach[u] or t < reach[u][s]):
                new_u[s] = t
        reach[v].update(new_v)
        reach[u].update(new_u)

    R = set()
    for v in range(n):
        for s in reach[v]:
            if s != v:
                R.add((s, v))
    return R


def build_earliest_tree(n, edges, timestamps):
    """Build spanning tree by processing edges earliest-first,
    adding edge if it connects a new vertex."""
    timed = sorted(enumerate(range(len(edges))), key=lambda x: timestamps[x[1]])

    parent = list(range(n))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    tree_indices = []
    for _, idx in timed:
        u, v = edges[idx]
        ru, rv = find(u), find(v)
        if ru != rv:
            parent[ru] = rv
            tree_indices.append(idx)
            if len(tree_indices) == n - 1:
                break

    return tree_indices


def build_latest_tree(n, edges, timestamps):
    """Build spanning tree by processing edges latest-first."""
    timed = sorted(enumerate(range(len(edges))), key=lambda x: -timestamps[x[1]])

    parent = list(range(n))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    tree_indices = []
    for _, idx in timed:
        u, v = edges[idx]
        ru, rv = find(u), find(v)
        if ru != rv:
            parent[ru] = rv
            tree_indices.append(idx)
            if len(tree_indices) == n - 1:
                break

    return tree_indices


def find_broken_pairs(n, edge_indices, edges, timestamps, target_reach):
    """Find pairs that are in target_reach but not reachable with given edges."""
    current_reach = compute_reachability(n, edge_indices, edges, timestamps)
    broken = target_reach - current_reach
    return broken


def find_repair_edge(n, current_indices, edges, timestamps, broken_pair, all_indices):
    """Find the best edge to add that fixes this broken pair.
    Try each edge not in current set; pick the one that fixes the pair
    with minimum timestamp (earliest repair)."""
    s, t = broken_pair
    candidates = set(all_indices) - set(current_indices)

    for idx in sorted(candidates, key=lambda i: timestamps[i]):
        trial = current_indices + [idx]
        reach = compute_reachability(n, trial, edges, timestamps)
        if (s, t) in reach:
            return idx
    return None


def find_repair_edge_fast(n, current_indices, edges, timestamps, broken_pairs, all_indices):
    """Find the single edge that repairs the most broken pairs."""
    candidates = set(all_indices) - set(current_indices)
    current_set = set(current_indices)

    best_idx = None
    best_fixed = 0

    for idx in sorted(candidates, key=lambda i: timestamps[i]):
        trial = sorted(current_indices + [idx])
        reach = compute_reachability(n, trial, edges, timestamps)
        fixed = len(broken_pairs & reach)
        if fixed > best_fixed:
            best_fixed = fixed
            best_idx = idx
        if fixed == len(broken_pairs):
            break  # fixes everything

    return best_idx, best_fixed


def prune_pass(n, edge_indices, edges, timestamps, target_reach):
    """Remove redundant edges (latest first)."""
    current = list(edge_indices)
    for idx in sorted(current, key=lambda i: -timestamps[i]):
        trial = [i for i in current if i != idx]
        if compute_reachability(n, trial, edges, timestamps) == target_reach:
            current = trial
    return current


def primal_dual_construction(n, edges, timestamps):
    """Alternating prune/traverse spanner construction."""
    m = len(edges)
    all_indices = list(range(m))
    target = compute_reachability(n, all_indices, edges, timestamps)

    rounds = []

    # Round 1: earliest spanning tree
    tree = build_earliest_tree(n, edges, timestamps)
    current = list(tree)
    broken = find_broken_pairs(n, current, edges, timestamps, target)
    rounds.append({
        'phase': 'tree',
        'edges': len(current),
        'broken': len(broken),
    })

    # Iterative repair + prune
    for iteration in range(20):
        if not broken:
            break

        # Repair: add edges to fix broken pairs
        added = 0
        broken_list = sorted(broken)
        for pair in broken_list:
            if pair not in find_broken_pairs(n, current, edges, timestamps, target):
                continue  # already fixed by a previous repair
            repair_idx = find_repair_edge(n, current, edges, timestamps, pair, all_indices)
            if repair_idx is not None:
                current.append(repair_idx)
                added += 1

        # Check for new breakages (cascade)
        broken_after_repair = find_broken_pairs(n, current, edges, timestamps, target)
        cascade = len(broken_after_repair)  # should be 0 since we only ADD edges

        rounds.append({
            'phase': f'repair-{iteration+1}',
            'edges': len(current),
            'added': added,
            'cascade': cascade,
            'broken_remaining': len(broken_after_repair),
        })

        # Prune: remove newly-redundant edges
        pruned = prune_pass(n, current, edges, timestamps, target)
        removed = len(current) - len(pruned)
        current = pruned

        broken = find_broken_pairs(n, current, edges, timestamps, target)

        rounds.append({
            'phase': f'prune-{iteration+1}',
            'edges': len(current),
            'removed': removed,
            'broken_after_prune': len(broken),
        })

        if len(broken) == 0:
            break

    return current, rounds


def main():
    random.seed(42)

    print("PRIMAL-DUAL SPANNER CONSTRUCTION")
    print("=" * 70)

    # SM(k)
    print("\n--- SM(k) ---\n")
    for k in range(3, 8):
        n = 2 * k
        edges, ts = make_sm_clique(k)
        spanner, rounds = primal_dual_construction(n, edges, ts)

        print(f"SM({k}): n={n}, 2n-3={2*n-3}, final={len(spanner)}, "
              f"rounds={len(rounds)}")
        for r in rounds:
            phase = r['phase']
            if phase == 'tree':
                print(f"  {phase}: {r['edges']} edges, {r['broken']} broken pairs")
            elif phase.startswith('repair'):
                print(f"  {phase}: {r['edges']} edges (+{r['added']}), "
                      f"cascade={r['cascade']}")
            elif phase.startswith('prune'):
                print(f"  {phase}: {r['edges']} edges (-{r['removed']}), "
                      f"broken={r['broken_after_prune']}")

    # Random temporal cliques
    print("\n--- Random temporal cliques ---\n")
    for n in [6, 8, 10]:
        samples = {6: 500, 8: 200, 10: 50}[n]
        sizes = []
        round_counts = []
        tree_broken = []
        repair_cascade = []

        for _ in range(samples):
            edges, ts = make_temporal_clique(n)
            spanner, rounds = primal_dual_construction(n, edges, ts)
            sizes.append(len(spanner))
            round_counts.append(len(rounds))

            # Extract stats
            for r in rounds:
                if r['phase'] == 'tree':
                    tree_broken.append(r['broken'])
                if r['phase'].startswith('repair') and 'cascade' in r:
                    repair_cascade.append(r['cascade'])

        print(f"n={n} ({samples} samples):")
        print(f"  2n-3 = {2*n-3}")
        print(f"  Spanner size: avg={sum(sizes)/len(sizes):.1f}, "
              f"max={max(sizes)}, min={min(sizes)}")
        print(f"  Rounds: avg={sum(round_counts)/len(round_counts):.1f}, "
              f"max={max(round_counts)}")
        print(f"  Broken after tree: avg={sum(tree_broken)/len(tree_broken):.1f}, "
              f"max={max(tree_broken)}")
        if repair_cascade:
            print(f"  Cascade events: {sum(1 for c in repair_cascade if c > 0)}"
                  f"/{len(repair_cascade)}")
        print(f"  Hit 2n-3: {sum(1 for s in sizes if s <= 2*n-3)}/{samples} "
              f"({100*sum(1 for s in sizes if s <= 2*n-3)/samples:.1f}%)")
        print()


if __name__ == "__main__":
    main()
