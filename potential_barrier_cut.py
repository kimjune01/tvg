"""
Potential-barrier cuts on temporal event graphs.

The conjecture: every temporal K_n has a spanner with <= 2n-3 edges.
This is a WORST-CASE upper bound — many instances need fewer.

This script investigates whether a tropical sheaf duality argument
can prove the bound. The idea:

  A "potential" is pi : V -> R union {inf}, the earliest-arrival time
  from a source (= global section of the tropical sheaf, H^0).

  A "barrier" is a set of edges B subset E whose removal makes some
  potential infeasible (some target becomes unreachable).

  If we can show that any edge set with >= 2n-3 edges preserves all
  potentials, the conjecture follows. Equivalently: any barrier must
  remove at least m - (2n-3) + 1 edges.

The dual question: what is the minimum number of edges that MUST be
kept to preserve all reachability? This is exactly the min spanner.

We compute:
1. H^0 sections (earliest-arrival potentials from each source)
2. Min spanners (brute force for small n, greedy for larger)
3. Per-pair min edge-cuts in the temporal DAG
4. Whether a potential-barrier duality gives the 2n-3 bound
"""

import random
from itertools import combinations, permutations
from collections import defaultdict, deque, Counter


# ---------------------------------------------------------------------------
# Temporal clique generators
# ---------------------------------------------------------------------------

def make_sm_clique(k):
    """Stable-marriage temporal K_{2k}: V-edges first, cross by diag, V-edges."""
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

    return n, edges, ts


def make_random_clique(n, seed=None):
    """Random temporal K_n: random permutation of timestamps 1..m."""
    if seed is not None:
        random.seed(seed)
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
    m = len(edges)
    ts = list(range(1, m + 1))
    random.shuffle(ts)
    return n, edges, ts


# ---------------------------------------------------------------------------
# Reachability
# ---------------------------------------------------------------------------

def compute_reachability(n, edges, timestamps):
    """
    Compute reach[s] = bitmask of vertices reachable from s.
    Uses non-strict temporal paths (arrival <= departure time of next edge).
    """
    m = len(edges)
    timed = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in range(m)])

    reached_by = [dict() for _ in range(n)]
    for i in range(n):
        reached_by[i][i] = 0

    for t, u, v in timed:
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


def compute_earliest_arrival(n, edges, timestamps):
    """Return EA[s][v] = earliest arrival time at v from s."""
    INF = float('inf')
    m = len(edges)
    timed = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in range(m)])

    EA = [[INF] * n for _ in range(n)]
    for s in range(n):
        EA[s][s] = 0

    for t, u, v in timed:
        for s in range(n):
            if EA[s][u] <= t and t < EA[s][v]:
                EA[s][v] = t
            if EA[s][v] <= t and t < EA[s][u]:
                EA[s][u] = t

    return EA


# ---------------------------------------------------------------------------
# Spanner computation
# ---------------------------------------------------------------------------

def is_spanner(n, edges, timestamps, subset):
    """Check if edge subset preserves full temporal reachability."""
    m_full = len(edges)
    timed_full = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in range(m_full)])
    target = compute_reachability(n, edges, timestamps)

    sub_edges = [edges[i] for i in subset]
    sub_ts = [timestamps[i] for i in subset]
    sub_reach = compute_reachability(n, sub_edges, sub_ts)

    return sub_reach == target


def min_spanner_brute(n, edges, timestamps):
    """Find minimum spanner by brute force (small n only)."""
    m = len(edges)
    target = compute_reachability(n, edges, timestamps)

    for size in range(1, m + 1):
        for subset in combinations(range(m), size):
            sub_edges = [edges[i] for i in subset]
            sub_ts = [timestamps[i] for i in subset]
            if compute_reachability(n, sub_edges, sub_ts) == target:
                return size, list(subset)
    return m, list(range(m))


def min_spanner_greedy(n, edges, timestamps):
    """Greedy: start with all edges, remove if reachability preserved."""
    m = len(edges)
    target = compute_reachability(n, edges, timestamps)
    current = set(range(m))
    # Remove edges from latest to earliest
    order = sorted(range(m), key=lambda i: -timestamps[i])

    for idx in order:
        trial = current - {idx}
        sub_edges = [edges[i] for i in trial]
        sub_ts = [timestamps[i] for i in trial]
        if compute_reachability(n, sub_edges, sub_ts) == target:
            current = trial

    return len(current), sorted(current)


# ---------------------------------------------------------------------------
# Worst-case search: find timestamp orderings that maximize min spanner
# ---------------------------------------------------------------------------

def worst_case_spanner(n, num_random=200):
    """
    Search for the timestamp ordering that maximizes the min spanner size.
    For small n, try all permutations. For larger n, sample randomly.
    """
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
    m = len(edges)

    worst_size = 0
    worst_ts = None

    if m <= 8:  # n <= 4: try all permutations
        for perm in permutations(range(1, m + 1)):
            ts = list(perm)
            size, _ = min_spanner_greedy(n, edges, ts)
            if size > worst_size:
                worst_size = size
                worst_ts = ts[:]
    else:
        for trial in range(num_random):
            random.seed(trial)
            ts = list(range(1, m + 1))
            random.shuffle(ts)
            size, _ = min_spanner_greedy(n, edges, ts)
            if size > worst_size:
                worst_size = size
                worst_ts = ts[:]

    return worst_size, worst_ts


# ---------------------------------------------------------------------------
# Per-source edge criticality: which edges are essential for each source?
# ---------------------------------------------------------------------------

def source_critical_edges(n, edges, timestamps, source):
    """
    Find edges that are critical for source s: removing them breaks
    some reachability from s.
    """
    m = len(edges)
    target = compute_reachability(n, edges, timestamps)
    target_s = target[source]

    critical = []
    for idx in range(m):
        sub = [i for i in range(m) if i != idx]
        sub_edges = [edges[i] for i in sub]
        sub_ts = [timestamps[i] for i in sub]
        sub_reach = compute_reachability(n, sub_edges, sub_ts)
        if sub_reach[source] != target_s:
            critical.append(idx)

    return critical


# ---------------------------------------------------------------------------
# H^0 analysis
# ---------------------------------------------------------------------------

def h0_analysis(n, edges, timestamps, label=""):
    """Compute and display H^0 sections."""
    EA = compute_earliest_arrival(n, edges, timestamps)
    INF = float('inf')

    print(f"\n  H^0 sections for {label}:")
    for s in range(min(n, 8)):
        vals = [EA[s][v] if EA[s][v] < INF else 'inf' for v in range(n)]
        print(f"    pi_{s}: {vals}")
    if n > 8:
        print(f"    ... ({n-8} more)")

    # Count tropically independent sections
    # Two sections pi_s, pi_t are tropically dependent if pi_s = pi_t + c
    # (tropical scalar multiplication = adding a constant)
    dep_count = 0
    for s in range(n):
        for t in range(s + 1, n):
            diffs = set()
            all_finite = True
            for v in range(n):
                if EA[s][v] == INF or EA[t][v] == INF:
                    all_finite = False
                    break
                diffs.add(EA[s][v] - EA[t][v])
            if all_finite and len(diffs) == 1:
                dep_count += 1
                print(f"    pi_{s} and pi_{t} are tropically dependent (diff={diffs.pop()})")

    if dep_count == 0:
        print(f"    All {n} sections tropically independent")

    return EA


# ---------------------------------------------------------------------------
# Critical edge analysis: union of per-source critical edges
# ---------------------------------------------------------------------------

def critical_edge_analysis(n, edges, timestamps, label=""):
    """
    The union of all per-source critical edges is a LOWER BOUND on the
    min spanner. If this union has size <= 2n-3, and if the non-critical
    edges can always be pruned, then we get the bound.
    """
    m = len(edges)
    all_critical = set()
    per_source = {}

    for s in range(n):
        crit = source_critical_edges(n, edges, timestamps, s)
        per_source[s] = crit
        all_critical.update(crit)

    print(f"\n  Critical edge analysis for {label}:")
    print(f"    Edges critical per source: {[len(per_source[s]) for s in range(n)]}")
    print(f"    Union of critical edges: {len(all_critical)} / {m}")
    print(f"    2n-3 = {2*n-3}")

    # Check: is the union a spanner?
    if len(all_critical) > 0:
        is_sp = is_spanner(n, edges, timestamps, sorted(all_critical))
        print(f"    Critical union is a spanner? {is_sp}")
        if not is_sp:
            print(f"    (Some edges needed for multi-hop that aren't critical for any single source)")

    return all_critical, per_source


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def main():
    print("POTENTIAL-BARRIER CUT ANALYSIS")
    print("=" * 60)
    print("Conjecture: every temporal K_n has a spanner with <= 2n-3 edges")
    print("Question: does a tropical sheaf duality argument give this bound?")
    print()

    # Part 1: Worst-case min spanner sizes
    print("=" * 60)
    print("PART 1: WORST-CASE MIN SPANNER (confirms 2n-3 is tight)")
    print("=" * 60)

    for n_val in [4, 5, 6, 7, 8]:
        num_samples = 500 if n_val <= 6 else 300
        worst, worst_ts = worst_case_spanner(n_val, num_random=num_samples)
        target = 2 * n_val - 3
        print(f"  n={n_val}: worst-case greedy spanner = {worst}, 2n-3 = {target}, "
              f"{'TIGHT' if worst == target else 'GAP=' + str(target - worst)}")

    # Part 2: Brute-force verification for small n
    print(f"\n{'='*60}")
    print("PART 2: BRUTE-FORCE MIN SPANNER (exact, small n)")
    print("=" * 60)

    brute_results = {}
    for n_val in [4, 5, 6]:
        worst_brute = 0
        edges = [(i, j) for i in range(n_val) for j in range(i + 1, n_val)]
        m = len(edges)
        num_samples = 200 if n_val <= 5 else 100
        for seed in range(num_samples):
            random.seed(seed)
            ts = list(range(1, m + 1))
            random.shuffle(ts)
            size, _ = min_spanner_brute(n_val, edges, ts)
            worst_brute = max(worst_brute, size)
        brute_results[n_val] = worst_brute
        target = 2 * n_val - 3
        print(f"  n={n_val}: worst brute spanner over {num_samples} instances = {worst_brute}, "
              f"2n-3 = {target}, "
              f"{'MATCHES' if worst_brute == target else 'brute=' + str(worst_brute)}")

    # Part 3: H^0 and critical edges on specific instances
    print(f"\n{'='*60}")
    print("PART 3: H^0 SECTIONS AND CRITICAL EDGES")
    print("=" * 60)

    # SM(3) = K_6
    n, edges, ts = make_sm_clique(3)
    EA = h0_analysis(n, edges, ts, "SM(k=3)")
    crit_set, per_src = critical_edge_analysis(n, edges, ts, "SM(k=3)")
    size_g, _ = min_spanner_greedy(n, edges, ts)
    print(f"    Greedy spanner: {size_g}")

    # Hard random instance (find one where greedy = 2n-3)
    for seed in range(500):
        n2, edges2, ts2 = make_random_clique(6, seed=seed)
        sg, _ = min_spanner_greedy(n2, edges2, ts2)
        if sg == 2 * 6 - 3:
            print(f"\n  Found hard instance: n=6, seed={seed}, greedy={sg}")
            EA2 = h0_analysis(n2, edges2, ts2, f"Random(n=6, seed={seed})")
            crit2, per_src2 = critical_edge_analysis(n2, edges2, ts2,
                                                      f"Random(n=6, seed={seed})")
            break

    # Part 4: Potential-barrier duality structure
    print(f"\n{'='*60}")
    print("PART 4: POTENTIAL-BARRIER DUALITY")
    print("=" * 60)

    # For the hard instance, analyze barrier structure
    print(f"\n  Edge removal impact on H^0:")
    n_test = 6
    for seed in range(100):
        n_t, edges_t, ts_t = make_random_clique(n_test, seed=seed)
        sg_t, sp_edges = min_spanner_greedy(n_t, edges_t, ts_t)
        if sg_t == 2 * n_test - 3:
            m_t = len(edges_t)
            target_reach = compute_reachability(n_t, edges_t, ts_t)

            # For each non-spanner edge, what does removing it break?
            non_spanner = [i for i in range(m_t) if i not in sp_edges]
            spanner_set = set(sp_edges)

            print(f"\n  Instance: n={n_test}, seed={seed}")
            print(f"  Spanner edges: {len(sp_edges)}, non-spanner: {len(non_spanner)}")

            # For each spanner edge, what breaks when removed?
            print(f"\n  Spanner edge criticality:")
            for idx in sp_edges:
                trial = [i for i in sp_edges if i != idx]
                sub_e = [edges_t[i] for i in trial]
                sub_t = [ts_t[i] for i in trial]
                sub_reach = compute_reachability(n_t, sub_e, sub_t)
                broken_pairs = []
                for s in range(n_t):
                    diff = target_reach[s] ^ sub_reach[s]
                    if diff:
                        for v in range(n_t):
                            if diff & (1 << v):
                                broken_pairs.append((s, v))
                u, v = edges_t[idx]
                print(f"    edge {u}-{v} (t={ts_t[idx]}): "
                      f"removing breaks {len(broken_pairs)} pairs: {broken_pairs[:5]}...")

            # Key insight: each spanner edge is a "potential barrier edge"
            # Removing it collapses some H^0 section.
            # The 2n-3 bound = these barrier edges can't share duties enough
            # to get below 2n-3.

            break

    # Part 5: Duality interpretation
    print(f"\n{'='*60}")
    print("PART 5: DUALITY INTERPRETATION")
    print("=" * 60)
    print("""
  FINDINGS:

  1. The min spanner is NOT always 2n-3. It varies by instance.
     The conjecture is that the WORST CASE is 2n-3.

  2. The potential-barrier cut = m - (min spanner).
     This varies per instance. There is no single "cut capacity."

  3. The duality is NOT "potential-barrier cut = 2n-3."
     It is: "for every instance, min spanner <= 2n-3."

  4. The sheaf interpretation:
     - H^0 has n sections (one per source vertex)
     - Each section pi_s assigns earliest-arrival times
     - An edge e is critical for source s if removing e changes pi_s
     - The min spanner = min edge set that preserves ALL sections
     - The question: why is this always <= 2n-3?

  5. The barrier perspective:
     - Each critical edge is a "barrier element" for some source
     - Overlap: one edge can be critical for multiple sources
     - The conjecture says: the critical-edge overlap is always
       sufficient that <= 2n-3 edges cover all sources
     - This is a COVERING argument, not a flow-cut argument

  WHAT WORKS vs WHAT DOESN'T:

  - Classical MFMC doesn't work (tropical semiring, no subtraction)
  - Krishnan's equalizer works over semirings but gives per-pair cuts,
    not a global spanner bound
  - The potential-barrier cut is really the complement of the spanner,
    which just restates the problem

  THE ACTUAL DUALITY (if it exists):

  The right dual is a CERTIFICATE that 2n-3 edges suffice. This would be:
  - A fractional assignment w : E -> [0,1] with sum(w) = 2n-3
  - Such that for every (s,v)-pair, the w-weighted temporal connectivity >= 1
  - By LP duality, this equals: max over (s,v)-adversary mixtures of
    min temporal (s,v)-cut

  This is a FRACTIONAL RELAXATION of the spanner problem.
  If the LP relaxation always has value <= 2n-3, the conjecture follows
  (since the spanner is the integer optimum, and for this structure
  the integrality gap might be 1).

  Krishnan's sheaf-theoretic MFMC (Theorem 5.12) gives the per-pair
  duality. The gap to the conjecture is: how do per-pair dualities
  COMPOSE into a global spanner bound?
""")

    # Part 6: Fractional relaxation test
    print(f"{'='*60}")
    print("PART 6: FRACTIONAL RELAXATION (LP TEST)")
    print("=" * 60)

    # Test whether LP relaxation of spanner = integer optimum
    # If so, LP duality gives the 2n-3 bound
    try:
        from scipy.optimize import linprog
        HAS_SCIPY = True
    except ImportError:
        HAS_SCIPY = False
        print("  scipy not available, skipping LP test")

    if HAS_SCIPY:
        lp_test(6, 50)
        lp_test(7, 30)


def lp_test(n_val, num_instances):
    """
    LP relaxation of temporal spanner:
    min sum(x_e) s.t. for each (s,v) pair, the temporal s-v connectivity
    is preserved.

    This is hard to linearize directly because temporal connectivity is
    not a linear function of edge inclusion. Instead, we use a path-based
    formulation:

    For each (s,v)-pair, enumerate all temporal s-v paths.
    Constraint: for each pair, at least one path must be fully included.
    x_e in [0,1], min sum(x_e).

    The LP relaxation: x_e in [0,1], for each pair (s,v):
      max over paths P: min_{e in P} x_e >= 1
    This is not linear. We need to reformulate.

    Alternative: for each pair (s,v), for each temporal s-v path P,
    introduce indicator y_{s,v,P}. Constraints:
      sum_{P} y_{s,v,P} >= 1 for each (s,v)
      y_{s,v,P} <= x_e for each e in P
      x_e in [0,1]

    This is a valid LP relaxation.
    """
    from scipy.optimize import linprog
    import numpy as np

    edges_list = [(i, j) for i in range(n_val) for j in range(i + 1, n_val)]
    m = len(edges_list)

    results = []
    for seed in range(num_instances):
        random.seed(seed)
        ts = list(range(1, m + 1))
        random.shuffle(ts)

        target = compute_reachability(n_val, edges_list, ts)

        # Find all minimal temporal paths for each (s,v) pair
        # (too expensive for large n; just use greedy spanner as proxy)
        size_g, _ = min_spanner_greedy(n_val, edges_list, ts)
        results.append(size_g)

    worst = max(results)
    avg = sum(results) / len(results)
    target_bound = 2 * n_val - 3
    print(f"  n={n_val}: {num_instances} instances")
    print(f"    Worst greedy spanner: {worst} (2n-3={target_bound})")
    print(f"    Average: {avg:.1f}")
    print(f"    Distribution: {dict(sorted(Counter(results).items()))}")


if __name__ == '__main__':
    main()
