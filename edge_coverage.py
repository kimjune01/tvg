"""
Edge coverage analysis for minimum temporal spanners.

For each edge in a minimum spanner:
  - What pairs (s,t) become unreachable if ONLY this edge is removed?
  - How many spanner edges are "useful" for each pair?
  - Can the spanner decompose into earliest-arrival + latest-departure arborescences?
"""

import random
from collections import defaultdict
from itertools import combinations


def make_edges(n):
    return [(i, j) for i in range(n) for j in range(i + 1, n)]


def reachable_pairs_with_journeys(n, timed_edges):
    """Return set of reachable (s, t) pairs AND the journey info.
    reached_by[v][s] = earliest arrival time at v starting from s."""
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
    return pairs, reached_by


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


def find_minimum_spanner(n, edges, ts, trials=500):
    """Randomized greedy deletion + local search to find minimum spanner."""
    m = len(edges)
    timed_all = sorted([(ts[i], edges[i][0], edges[i][1]) for i in range(m)])
    target = compute_reachability(n, timed_all)

    best = None
    best_size = m + 1

    for trial in range(trials):
        # Randomized greedy deletion
        order = list(range(m))
        if trial == 0:
            # First trial: deterministic (remove latest first)
            order.sort(key=lambda i: -ts[i])
        else:
            random.shuffle(order)

        included = set(range(m))
        for idx in order:
            if idx not in included:
                continue
            candidate = included - {idx}
            sub = sorted([(ts[i], edges[i][0], edges[i][1]) for i in candidate])
            if compute_reachability(n, sub) == target:
                included = candidate

        # Local search: try swapping an included edge for a non-included one
        improved = True
        while improved:
            improved = False
            inc_list = sorted(included)
            exc_list = [i for i in range(m) if i not in included]
            random.shuffle(exc_list)
            for rm in inc_list:
                cand = included - {rm}
                sub = sorted([(ts[i], edges[i][0], edges[i][1]) for i in cand])
                if compute_reachability(n, sub) == target:
                    included = cand
                    improved = True
                    break

        if len(included) < best_size:
            best_size = len(included)
            best = set(included)

    return best


def edge_coverage(n, edges, ts, spanner_edges):
    """For each edge in the spanner, compute coverage:
    set of pairs (s,t) that become unreachable if this edge is removed."""
    timed_spanner = sorted([(ts[i], edges[i][0], edges[i][1]) for i in spanner_edges])
    target_pairs, _ = reachable_pairs_with_journeys(n, timed_spanner)

    coverage = {}
    for idx in spanner_edges:
        remaining = spanner_edges - {idx}
        sub = sorted([(ts[i], edges[i][0], edges[i][1]) for i in remaining])
        sub_pairs, _ = reachable_pairs_with_journeys(n, sub)
        lost = target_pairs - sub_pairs
        coverage[idx] = lost

    return coverage, target_pairs


def pair_usefulness(n, edges, ts, spanner_edges):
    """For each pair (s,t), how many spanner edges are 'useful' —
    i.e., lie on SOME temporal s->t journey within the spanner?

    An edge e is useful for (s,t) if removing e changes the
    earliest arrival time from s to t (or makes it unreachable)."""
    timed_spanner = sorted([(ts[i], edges[i][0], edges[i][1]) for i in spanner_edges])
    _, base_reached = reachable_pairs_with_journeys(n, timed_spanner)

    # For each pair, track which edges affect its reachability
    pair_useful_edges = defaultdict(set)

    for idx in spanner_edges:
        remaining = spanner_edges - {idx}
        sub = sorted([(ts[i], edges[i][0], edges[i][1]) for i in remaining])
        _, sub_reached = reachable_pairs_with_journeys(n, sub)

        for v in range(n):
            for s in base_reached[v]:
                if s == v:
                    continue
                base_time = base_reached[v].get(s)
                sub_time = sub_reached[v].get(s)
                if sub_time is None or sub_time != base_time:
                    pair_useful_edges[(s, v)].add(idx)

    return pair_useful_edges


def find_bridging_number(n, edges, ts, spanner_edges, coverage):
    """Among non-essential edges (coverage=0), what's the minimum needed?"""
    essential = {idx for idx, lost in coverage.items() if len(lost) > 0}
    non_essential = spanner_edges - essential

    if not non_essential:
        return 0, essential

    # Check if essential edges alone preserve reachability
    timed_spanner = sorted([(ts[i], edges[i][0], edges[i][1]) for i in spanner_edges])
    target = compute_reachability(n, timed_spanner)

    timed_ess = sorted([(ts[i], edges[i][0], edges[i][1]) for i in essential])
    if compute_reachability(n, timed_ess) == target:
        return 0, essential

    # Find minimum subset of non-essential edges needed
    ne_list = sorted(non_essential)
    for size in range(1, len(ne_list) + 1):
        for subset in combinations(ne_list, size):
            combined = essential | set(subset)
            sub = sorted([(ts[i], edges[i][0], edges[i][1]) for i in combined])
            if compute_reachability(n, sub) == target:
                return size, combined
    return len(ne_list), spanner_edges


def build_earliest_arborescence(n, edges, ts, root):
    """Build earliest-arrival arborescence rooted at `root`.
    Directed tree: for each vertex v != root, find the edge that
    first connects v to the growing reachable set from root."""
    m = len(edges)
    timed = sorted([(ts[i], i) for i in range(m)])

    reached = {root: 0}  # vertex -> earliest time it was reached
    tree_edges = set()

    changed = True
    while changed:
        changed = False
        for t, idx in timed:
            u, v = edges[idx]
            # Edge at time t: can go u->v or v->u
            if u in reached and reached[u] <= t and v not in reached:
                reached[v] = t
                tree_edges.add(idx)
                changed = True
            elif v in reached and reached[v] <= t and u not in reached:
                reached[u] = t
                tree_edges.add(idx)
                changed = True

    return tree_edges, reached


def build_latest_arborescence(n, edges, ts, root):
    """Build latest-departure arborescence rooted at `root`.
    For each vertex v != root, find the edge that provides the
    latest possible departure from v toward root.
    Process edges latest-first, grow reachable-TO-root set."""
    m = len(edges)
    timed = sorted([(ts[i], i) for i in range(m)], reverse=True)

    # Vertices that can reach root, with latest departure time allowed
    can_reach = {root: float('inf')}
    tree_edges = set()

    changed = True
    while changed:
        changed = False
        for t, idx in timed:
            u, v = edges[idx]
            # Edge at time t: u-v. If v can reach root and v's entry time >= t,
            # then u can reach root by departing at time t
            if v in can_reach and can_reach[v] >= t and u not in can_reach:
                can_reach[u] = t
                tree_edges.add(idx)
                changed = True
            elif u in can_reach and can_reach[u] >= t and v not in can_reach:
                can_reach[v] = t
                tree_edges.add(idx)
                changed = True

    return tree_edges, can_reach


def analyze_arborescences(n, edges, ts, spanner_edges):
    """Build arborescences from each root, find best overlap with spanner."""
    best_overlap = 0
    best_root = -1
    best_ea = set()
    best_ld = set()
    best_union = set()

    for root in range(n):
        ea, ea_reached = build_earliest_arborescence(n, edges, ts, root)
        ld, ld_reached = build_latest_arborescence(n, edges, ts, root)

        overlap = ea & ld
        union = ea | ld
        spanner_in_union = spanner_edges & union
        union_in_spanner = union & spanner_edges

        if len(spanner_in_union) > best_overlap:
            best_overlap = len(spanner_in_union)
            best_root = root
            best_ea = ea
            best_ld = ld
            best_union = union

    return best_root, best_ea, best_ld, best_union


def analyze_instance(name, n, edges, ts):
    """Full coverage analysis of one temporal graph instance."""
    print(f"\n{'='*70}")
    print(f"  {name}  (n={n}, n(n-1)={n*(n-1)}, 2n-3={2*n-3})")
    print(f"{'='*70}")

    m = len(edges)

    # Find minimum spanner
    # For small n, use more trials
    trial_count = 500 if n <= 10 else 200
    spanner = find_minimum_spanner(n, edges, ts, trials=trial_count)
    sp_size = len(spanner)
    print(f"\nMinimum spanner found: {sp_size} edges (2n-3={2*n-3})")

    # 1. Coverage per edge
    coverage, target_pairs = edge_coverage(n, edges, ts, spanner)
    total_pairs = len(target_pairs)

    essential = {idx for idx, lost in coverage.items() if len(lost) > 0}
    non_essential = spanner - essential
    cov_sizes = sorted([len(lost) for lost in coverage.values()], reverse=True)

    print(f"\n--- COVERAGE PER EDGE ---")
    print(f"Essential edges (coverage > 0): {len(essential)}")
    print(f"Non-essential edges (coverage = 0): {len(non_essential)}")
    print(f"Coverage distribution: {cov_sizes}")

    if essential:
        ess_cov = [len(coverage[idx]) for idx in essential]
        print(f"  Essential: min={min(ess_cov)}, max={max(ess_cov)}, "
              f"mean={sum(ess_cov)/len(ess_cov):.1f}")

    # Singly-covered pairs
    singly_covered = set()
    for idx in essential:
        singly_covered |= coverage[idx]
    print(f"\nSingly-covered pairs: {len(singly_covered)} / {total_pairs} "
          f"({100*len(singly_covered)/total_pairs:.1f}%)")

    # 2. Bridging number
    if non_essential:
        bridge_num, min_set = find_bridging_number(n, edges, ts, spanner, coverage)
        print(f"\n--- BRIDGING ---")
        print(f"Bridging number (min non-essential edges needed): {bridge_num}")
        print(f"Spanner = {len(essential)} essential + {bridge_num} bridging "
              f"= {len(essential) + bridge_num}")
        if sp_size > len(essential) + bridge_num:
            print(f"  (Our spanner has {sp_size - len(essential) - bridge_num} "
                  f"redundant non-essential edges)")
    else:
        print(f"\n--- BRIDGING ---")
        print(f"All edges essential. Bridging number = 0.")

    # 3. Pair usefulness (how many edges each pair depends on)
    print(f"\n--- PAIR USEFULNESS ---")
    pair_useful = pair_usefulness(n, edges, ts, spanner)

    useful_counts = [len(pair_useful.get(p, set())) for p in target_pairs]
    if useful_counts:
        min_u = min(useful_counts)
        max_u = max(useful_counts)
        mean_u = sum(useful_counts) / len(useful_counts)
        # Distribution
        dist = defaultdict(int)
        for c in useful_counts:
            dist[c] += 1
        print(f"Useful edges per pair: min={min_u}, max={max_u}, mean={mean_u:.1f}")
        print(f"Distribution: {dict(sorted(dist.items()))}")
        if min_u == 1:
            single_pairs = [p for p in target_pairs if len(pair_useful.get(p, set())) == 1]
            print(f"Pairs with exactly 1 useful edge: {len(single_pairs)}")
        if min_u >= 2:
            print(f"Every pair has >= 2 useful edges (redundancy exists)")

    # 4. Arborescence decomposition
    print(f"\n--- ARBORESCENCE DECOMPOSITION ---")
    best_root, ea, ld, arb_union = analyze_arborescences(n, edges, ts, spanner)

    ea_in_sp = ea & spanner
    ld_in_sp = ld & spanner
    union_in_sp = arb_union & spanner
    sp_in_union = spanner & arb_union

    print(f"Best root: {best_root}")
    print(f"Earliest-arrival arb: {len(ea)} edges ({len(ea_in_sp)} in spanner)")
    print(f"Latest-departure arb: {len(ld)} edges ({len(ld_in_sp)} in spanner)")
    print(f"Arb overlap (EA & LD): {len(ea & ld)} edges")
    print(f"Arb union (EA | LD): {len(arb_union)} edges")
    print(f"Spanner edges in arb union: {len(sp_in_union)} / {sp_size}")
    print(f"Arb union edges in spanner: {len(union_in_sp)} / {len(arb_union)}")

    # Check if arb union is itself a spanner
    timed_all = sorted([(ts[i], edges[i][0], edges[i][1]) for i in range(m)])
    target_reach = compute_reachability(n, timed_all)
    timed_arb = sorted([(ts[i], edges[i][0], edges[i][1]) for i in arb_union])
    arb_reach = compute_reachability(n, timed_arb)
    arb_is_spanner = arb_reach == target_reach
    print(f"Arb union is spanner: {arb_is_spanner}")

    # Also try: use ALL roots and take union of all arborescences
    all_ea = set()
    all_ld = set()
    for root in range(n):
        ea_r, _ = build_earliest_arborescence(n, edges, ts, root)
        ld_r, _ = build_latest_arborescence(n, edges, ts, root)
        all_ea |= ea_r
        all_ld |= ld_r

    print(f"\nAll-roots EA edges: {len(all_ea)} ({len(all_ea & spanner)} in spanner)")
    print(f"All-roots LD edges: {len(all_ld)} ({len(all_ld & spanner)} in spanner)")
    print(f"All-roots union: {len(all_ea | all_ld)} "
          f"({len((all_ea | all_ld) & spanner)} in spanner)")
    print(f"Spanner edges NOT in any arborescence: "
          f"{len(spanner - (all_ea | all_ld))} / {sp_size}")

    # Per-edge detail for small instances
    if n <= 8:
        print(f"\n--- EDGE DETAIL ---")
        print(f"{'edge':<10} {'ts':>4} {'cov':>4} {'useful_for':>10} {'in_EA':>5} {'in_LD':>5}")
        for idx in sorted(spanner, key=lambda i: ts[i]):
            u, v = edges[idx]
            cov = len(coverage[idx])
            # Count how many pairs this edge is useful for
            useful_count = sum(1 for p in target_pairs if idx in pair_useful.get(p, set()))
            in_ea = "Y" if idx in all_ea else ""
            in_ld = "Y" if idx in all_ld else ""
            print(f"({u},{v}){'':<5} {ts[idx]:>4} {cov:>4} {useful_count:>10} {in_ea:>5} {in_ld:>5}")

    return {
        'n': n,
        'spanner_size': sp_size,
        'essential': len(essential),
        'non_essential': len(non_essential),
        'singly_covered': len(singly_covered),
        'total_pairs': total_pairs,
        'arb_union_is_spanner': arb_is_spanner,
        'spanner_in_arb': len(sp_in_union),
    }


def main():
    random.seed(42)
    results = []

    # SM instances
    for k in range(3, 7):
        n, edges, ts, eidx = generate_sm(k)
        r = analyze_instance(f"SM({k})", n, edges, ts)
        results.append((f"SM({k})", r))

    # Random instances
    for n in [6, 8, 10]:
        for seed in range(3):
            actual_seed = seed * 100 + n
            nn, edges, ts, eidx = generate_random_temporal(n, seed=actual_seed)
            r = analyze_instance(f"Random K_{n} (seed={actual_seed})", nn, edges, ts)
            results.append((f"Rand_{n}_{seed}", r))

    # Summary table
    print(f"\n{'='*70}")
    print(f"  SUMMARY")
    print(f"{'='*70}")
    print(f"{'Instance':<25} {'n':>3} {'|S|':>4} {'ess':>4} {'non':>4} "
          f"{'singly':>6} {'pairs':>6} {'%sing':>6} {'arb?':>5}")
    print("-" * 75)
    for name, r in results:
        pct = 100 * r['singly_covered'] / r['total_pairs'] if r['total_pairs'] > 0 else 0
        print(f"{name:<25} {r['n']:>3} {r['spanner_size']:>4} {r['essential']:>4} "
              f"{r['non_essential']:>4} {r['singly_covered']:>6} {r['total_pairs']:>6} "
              f"{pct:>5.1f}% {'Y' if r['arb_union_is_spanner'] else 'N':>4}")


if __name__ == "__main__":
    main()
