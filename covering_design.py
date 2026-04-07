"""
Covering design analysis for temporal spanners.

Reduces the spanner problem to a covering hypergraph:
  - Vertices = directed reachable pairs (s,t)
  - Hyperedges = COVER(e) for each edge e in the complete temporal graph
    where COVER(e) = pairs that become unreachable if e is removed from the spanner

Analyzes: size distribution, intersection patterns, sunflower structure,
packing/matching, fractional covering (LP), VC dimension, Turán density.
"""

import random
from collections import defaultdict
from itertools import combinations
from scipy.optimize import linprog
import numpy as np


# ─── Core temporal graph primitives ───────────────────────────────────────

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
    """Return set of reachable (s, t) directed pairs."""
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


# ─── Instance generators ─────────────────────────────────────────────────

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


# ─── Spanner finding ─────────────────────────────────────────────────────

def find_minimum_spanner(n, edges, ts, trials=200):
    """Randomized greedy deletion to find minimum spanner."""
    m = len(edges)
    timed_all = sorted([(ts[i], edges[i][0], edges[i][1]) for i in range(m)])
    target = compute_reachability(n, timed_all)

    best = None
    best_size = m + 1

    for trial in range(trials):
        order = list(range(m))
        if trial == 0:
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

        # Local search: try removing any remaining edge
        improved = True
        while improved:
            improved = False
            for rm in sorted(included):
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


# ─── Covering hypergraph construction ─────────────────────────────────────

def build_covering_hypergraph(n, edges, ts, spanner_edges):
    """
    For each spanner edge e, compute COVER(e) = set of directed pairs (s,t)
    that become unreachable when e is removed from the spanner.
    Returns: coverage dict, target_pairs set, pair_to_idx mapping.
    """
    timed_spanner = sorted([(ts[i], edges[i][0], edges[i][1]) for i in spanner_edges])
    target_pairs = reachable_pairs(n, timed_spanner)

    # Index pairs for matrix operations
    pair_list = sorted(target_pairs)
    pair_to_idx = {p: i for i, p in enumerate(pair_list)}

    coverage = {}
    for idx in spanner_edges:
        remaining = spanner_edges - {idx}
        sub = sorted([(ts[i], edges[i][0], edges[i][1]) for i in remaining])
        sub_pairs = reachable_pairs(n, sub)
        lost = target_pairs - sub_pairs
        coverage[idx] = lost

    return coverage, target_pairs, pair_list, pair_to_idx


# ─── Analysis functions ──────────────────────────────────────────────────

def size_distribution(coverage):
    """Distribution of |COVER(e)| across spanner edges."""
    sizes = sorted([len(v) for v in coverage.values()], reverse=True)
    dist = defaultdict(int)
    for s in sizes:
        dist[s] += 1
    return sizes, dict(sorted(dist.items()))


def intersection_analysis(coverage, spanner_edges):
    """Pairwise intersection sizes between COVER sets."""
    edge_list = sorted(spanner_edges)
    intersections = []
    for i in range(len(edge_list)):
        for j in range(i + 1, len(edge_list)):
            e1, e2 = edge_list[i], edge_list[j]
            isect = len(coverage[e1] & coverage[e2])
            intersections.append(isect)
    return intersections


def find_sunflowers(coverage, spanner_edges, min_petals=3):
    """
    Find sunflower structures: k hyperedges whose pairwise intersections
    are all the same set (the "core").
    Returns list of (core, petals) tuples.
    """
    edge_list = sorted(spanner_edges)
    # Only consider edges with non-empty coverage
    active = [e for e in edge_list if len(coverage[e]) > 0]
    sunflowers = []

    # Check all triples (and larger if found)
    for size in range(min_petals, len(active) + 1):
        found_any = False
        if size > 5:
            break  # Don't search too large
        for combo in combinations(active, size):
            # Compute pairwise intersections
            core = coverage[combo[0]]
            for e in combo[1:]:
                core = core & coverage[e]
            # Check: is every pairwise intersection == core?
            is_sunflower = True
            for i in range(len(combo)):
                for j in range(i + 1, len(combo)):
                    if coverage[combo[i]] & coverage[combo[j]] != core:
                        is_sunflower = False
                        break
                if not is_sunflower:
                    break
            if is_sunflower:
                sunflowers.append((core, combo))
                found_any = True
        if not found_any and size >= 4:
            break
    return sunflowers


def maximum_matching_hypergraph(coverage, spanner_edges, pair_list, pair_to_idx):
    """
    Maximum matching in the covering hypergraph = packing number.
    A matching = set of disjoint hyperedges.
    Greedy: pick largest uncovered hyperedge, remove its pairs.
    """
    active_edges = sorted(spanner_edges, key=lambda e: -len(coverage[e]))
    used_pairs = set()
    matching = []

    for e in active_edges:
        if len(coverage[e]) == 0:
            continue
        if not (coverage[e] & used_pairs):
            matching.append(e)
            used_pairs |= coverage[e]

    return matching


def fractional_covering_lp(coverage, spanner_edges, pair_list, pair_to_idx):
    """
    Fractional covering number via LP relaxation.
    Minimize sum(x_e) subject to:
      for each pair p: sum(x_e : p in COVER(e)) >= 1
      x_e >= 0
    This is the LP relaxation of minimum set cover.
    """
    edge_list = sorted(spanner_edges)
    num_edges = len(edge_list)
    num_pairs = len(pair_list)

    if num_pairs == 0 or num_edges == 0:
        return 0.0, []

    # Only include pairs that are actually covered by at least one edge
    covered_pairs = set()
    for e in edge_list:
        covered_pairs |= coverage[e]

    if not covered_pairs:
        return 0.0, []

    cp_list = sorted(covered_pairs)
    cp_to_idx = {p: i for i, p in enumerate(cp_list)}
    num_cp = len(cp_list)

    # Objective: minimize sum(x_e)
    c = np.ones(num_edges)

    # Constraints: -A x <= -1 (i.e., A x >= 1)
    A_ub = np.zeros((num_cp, num_edges))
    for j, e in enumerate(edge_list):
        for p in coverage[e]:
            if p in cp_to_idx:
                A_ub[cp_to_idx[p], j] = -1.0

    b_ub = -np.ones(num_cp)

    bounds = [(0, None) for _ in range(num_edges)]

    result = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')

    if result.success:
        return result.fun, list(zip(edge_list, result.x))
    else:
        return float('inf'), []


def compute_vc_dimension(coverage, spanner_edges, pair_list):
    """
    VC dimension of the covering system.
    The ground set is pairs, the set system is {COVER(e) : e in spanner}.
    VC dim = largest d such that some d-element subset of pairs is shattered.
    """
    # Collect distinct non-empty COVER sets
    cover_sets = [frozenset(coverage[e]) for e in sorted(spanner_edges) if len(coverage[e]) > 0]

    if not cover_sets:
        return 0

    # For efficiency, only check subsets up to size 8
    max_check = min(8, len(pair_list))
    best_d = 0

    # Sample pairs that appear in covers
    active_pairs = set()
    for cs in cover_sets:
        active_pairs |= cs
    active_list = sorted(active_pairs)

    if len(active_list) > 50:
        # Sample for tractability
        random.shuffle(active_list)
        active_list = active_list[:50]

    for d in range(1, max_check + 1):
        if d > len(active_list):
            break
        shattered = False
        # Check a sample of d-subsets
        max_combos = min(500, len(list(combinations(range(min(20, len(active_list))), d))))
        subset_pairs = list(combinations(active_list[:20], d))
        random.shuffle(subset_pairs)
        for subset in subset_pairs[:500]:
            subset_set = set(subset)
            # Check if all 2^d subsets of subset are realized
            realized = set()
            for cs in cover_sets:
                intersection = frozenset(cs & subset_set)
                realized.add(intersection)
            if len(realized) == 2 ** d:
                shattered = True
                best_d = d
                break
        if not shattered:
            break

    return best_d


def turan_density(coverage, spanner_edges, pair_list, pair_to_idx):
    """
    Turán-type density: average number of hyperedges covering each pair.
    Also compute max and min multiplicity.
    """
    multiplicity = defaultdict(int)
    for e in spanner_edges:
        for p in coverage[e]:
            multiplicity[p] += 1

    if not multiplicity:
        return 0, 0, 0, {}

    vals = list(multiplicity.values())
    dist = defaultdict(int)
    for v in vals:
        dist[v] += 1

    return min(vals), max(vals), sum(vals) / len(vals), dict(sorted(dist.items()))


# ─── Main analysis ───────────────────────────────────────────────────────

def analyze_instance(name, n, edges, ts):
    """Full covering design analysis of one temporal graph instance."""
    print(f"\n{'='*72}")
    print(f"  {name}  (n={n}, n(n-1)={n*(n-1)}, 2n-3={2*n-3}, 2n-4={2*n-4})")
    print(f"{'='*72}")

    m = len(edges)

    # Find minimum spanner
    spanner = find_minimum_spanner(n, edges, ts, trials=200)
    sp_size = len(spanner)
    print(f"\nMinimum spanner: {sp_size} edges  (2n-3={2*n-3}, 2n-4={2*n-4})")

    # Build covering hypergraph
    coverage, target_pairs, pair_list, pair_to_idx = build_covering_hypergraph(
        n, edges, ts, spanner)
    num_pairs = len(target_pairs)
    print(f"Reachable pairs: {num_pairs} / {n*(n-1)}")

    # ── 1. Size distribution ──
    sizes, dist = size_distribution(coverage)
    essential = sum(1 for s in sizes if s > 0)
    print(f"\n--- COVER SIZE DISTRIBUTION ---")
    print(f"  |COVER(e)| values: {sizes}")
    print(f"  Distribution: {dist}")
    print(f"  Essential edges: {essential}/{sp_size}")
    if sizes:
        nonzero = [s for s in sizes if s > 0]
        if nonzero:
            print(f"  Non-zero: min={min(nonzero)}, max={max(nonzero)}, "
                  f"mean={sum(nonzero)/len(nonzero):.1f}, sum={sum(nonzero)}")
            print(f"  Sum / |pairs|: {sum(nonzero)/num_pairs:.2f}  "
                  f"(>1 means overlap, <1 impossible if all covered)")

    # ── 2. Intersection pattern ──
    isects = intersection_analysis(coverage, spanner)
    print(f"\n--- PAIRWISE INTERSECTIONS ---")
    if isects:
        nonzero_isects = [x for x in isects if x > 0]
        print(f"  Total pairs of edges: {len(isects)}")
        print(f"  Non-zero intersections: {len(nonzero_isects)} / {len(isects)} "
              f"({100*len(nonzero_isects)/len(isects):.1f}%)")
        if nonzero_isects:
            print(f"  Non-zero: min={min(nonzero_isects)}, max={max(nonzero_isects)}, "
                  f"mean={sum(nonzero_isects)/len(nonzero_isects):.1f}")
        idist = defaultdict(int)
        for x in isects:
            idist[x] += 1
        print(f"  Intersection size distribution: {dict(sorted(idist.items()))}")

        # Classify: almost disjoint vs highly overlapping
        if len(nonzero_isects) == 0:
            print(f"  --> DISJOINT: all COVER sets are pairwise disjoint")
        elif len(nonzero_isects) / len(isects) < 0.3:
            print(f"  --> ALMOST DISJOINT: most COVER sets don't overlap")
        else:
            print(f"  --> OVERLAPPING: significant intersection structure")

    # ── 3. Sunflower structure ──
    print(f"\n--- SUNFLOWER ANALYSIS ---")
    sunflowers = find_sunflowers(coverage, spanner, min_petals=3)
    if sunflowers:
        # Group by core size
        by_core = defaultdict(list)
        for core, petals in sunflowers:
            by_core[len(core)].append((core, petals))
        print(f"  Found {len(sunflowers)} sunflowers:")
        for core_size in sorted(by_core.keys()):
            items = by_core[core_size]
            petal_counts = [len(p) for _, p in items]
            print(f"    Core size {core_size}: {len(items)} sunflowers, "
                  f"petals: {min(petal_counts)}-{max(petal_counts)}")
        # Show largest
        largest = max(sunflowers, key=lambda x: len(x[1]))
        print(f"  Largest sunflower: {len(largest[1])} petals, "
              f"core size {len(largest[0])}")
        if len(largest[0]) <= 5:
            print(f"    Core pairs: {sorted(largest[0])}")
    else:
        print(f"  No sunflowers found (min 3 petals)")

    # ── 4. Packing number (greedy matching) ──
    print(f"\n--- PACKING (MATCHING) ---")
    matching = maximum_matching_hypergraph(coverage, spanner, pair_list, pair_to_idx)
    print(f"  Greedy matching size: {len(matching)}")
    matching_pairs = set()
    for e in matching:
        matching_pairs |= coverage[e]
    print(f"  Pairs covered by matching: {len(matching_pairs)} / {num_pairs}")

    # ── 5. Fractional covering LP ──
    print(f"\n--- FRACTIONAL COVERING (LP) ---")
    frac_val, frac_sol = fractional_covering_lp(coverage, spanner, pair_list, pair_to_idx)
    print(f"  Fractional covering number: {frac_val:.3f}")
    if frac_sol:
        nonzero_frac = [(e, x) for e, x in frac_sol if x > 1e-6]
        print(f"  Non-zero variables: {len(nonzero_frac)} / {sp_size}")
        if nonzero_frac:
            xvals = [x for _, x in nonzero_frac]
            print(f"  x values: min={min(xvals):.3f}, max={max(xvals):.3f}")
            # How many are integral (0 or 1)?
            integral = sum(1 for x in xvals if abs(x - round(x)) < 1e-6)
            print(f"  Integral: {integral}/{len(nonzero_frac)}")

    # ── 6. VC dimension ──
    print(f"\n--- VC DIMENSION ---")
    vc = compute_vc_dimension(coverage, spanner, pair_list)
    print(f"  VC dimension: {vc}")
    print(f"  Sauer-Shelah bound: {sp_size} edges can shatter at most "
          f"O(n^{vc}) subsets")

    # ── 7. Turán density (pair multiplicity) ──
    print(f"\n--- PAIR MULTIPLICITY (Turán density) ---")
    t_min, t_max, t_mean, t_dist = turan_density(
        coverage, spanner, pair_list, pair_to_idx)
    print(f"  Pairs covered by k edges:")
    uncovered = num_pairs - sum(t_dist.get(k, 0) for k in t_dist)
    if uncovered > 0:
        print(f"    k=0: {uncovered} pairs (not exclusively covered by any single edge)")
    for k in sorted(t_dist.keys()):
        print(f"    k={k}: {t_dist[k]} pairs")
    if t_mean > 0:
        print(f"  min={t_min}, max={t_max}, mean={t_mean:.2f}")

    # ── 8. KEY structural question ──
    print(f"\n--- STRUCTURAL SUMMARY ---")
    total_cover = sum(len(coverage[e]) for e in spanner)
    if num_pairs > 0:
        avg_cover_per_pair = total_cover / num_pairs
        print(f"  Average edges covering each pair: {avg_cover_per_pair:.2f}")
    print(f"  Total cover sum: {total_cover}")
    print(f"  |spanner| * avg |COVER|: {sp_size} * {total_cover/sp_size:.1f} = {total_cover}")

    # Ratio analysis
    if essential > 0:
        avg_ess_cover = sum(len(coverage[e]) for e in spanner if len(coverage[e]) > 0) / essential
        print(f"  Avg essential cover: {avg_ess_cover:.1f}")
        print(f"  If covers were disjoint: need >= ceil({num_pairs}/{avg_ess_cover:.1f}) "
              f"= {int(np.ceil(num_pairs / avg_ess_cover))} edges")

    return {
        'n': n, 'sp_size': sp_size, 'num_pairs': num_pairs,
        'essential': essential, 'vc_dim': vc,
        'frac_cover': frac_val, 'matching': len(matching),
        'max_isect': max(isects) if isects else 0,
        'sunflowers': len(sunflowers),
        'total_cover': total_cover,
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
        for seed in range(2):
            actual_seed = seed * 100 + n
            nn, edges, ts, eidx = generate_random_temporal(n, seed=actual_seed)
            r = analyze_instance(f"Random K_{n} (seed={actual_seed})", nn, edges, ts)
            results.append((f"Rand_{n}_{seed}", r))

    # ── Summary table ──
    print(f"\n{'='*72}")
    print(f"  SUMMARY TABLE")
    print(f"{'='*72}")
    hdr = (f"{'Instance':<18} {'n':>3} {'|S|':>4} {'2n-4':>4} {'ess':>4} "
           f"{'pairs':>5} {'match':>5} {'frac':>6} {'VC':>3} "
           f"{'max∩':>5} {'sun':>4} {'Σcov':>5}")
    print(hdr)
    print("-" * len(hdr))
    for name, r in results:
        print(f"{name:<18} {r['n']:>3} {r['sp_size']:>4} {2*r['n']-4:>4} "
              f"{r['essential']:>4} {r['num_pairs']:>5} {r['matching']:>5} "
              f"{r['frac_cover']:>6.1f} {r['vc_dim']:>3} "
              f"{r['max_isect']:>5} {r['sunflowers']:>4} {r['total_cover']:>5}")

    # ── Key findings ──
    print(f"\n{'='*72}")
    print(f"  KEY FINDINGS")
    print(f"{'='*72}")
    print("""
The covering hypergraph structure should reveal WHY 2n-3 suffices:

1. If covers are "almost disjoint" => each edge covers ~n pairs independently
   => need ~n(n-1)/n = n-1 edges. But we need 2n-4, so covers overlap ~2x.

2. If fractional covering number ~ 2n-4 => LP relaxation is tight,
   and the integer gap is at most 1 (giving 2n-3).

3. Sunflower structure constrains how edges can share covered pairs.
   Sunflower lemma: if |COVER(e)| <= s for all e, and there are more than
   (p-1)^s * s! hyperedges, then a p-petal sunflower exists.

4. VC dimension d => at most O(n^d) distinct cover patterns.
   Low VC dim means the covering system is "simple" and LP rounding works.
""")

    # Check the LP gap pattern
    print("LP integrality gap analysis:")
    for name, r in results:
        gap = r['sp_size'] - r['frac_cover']
        print(f"  {name:<18}: |S|={r['sp_size']}, frac={r['frac_cover']:.2f}, "
              f"gap={gap:.2f}")


if __name__ == "__main__":
    main()
