"""
Covering LP analysis for temporal spanners — journey-based formulation.

For each directed reachable pair (s,t), enumerate ALL temporal s->t journeys.
A journey is a sequence of edges with strictly increasing timestamps.
The spanner must include ALL edges of at least one journey per pair.

Primal LP (set-cover-like):
  min Σ x_e
  s.t. for each pair p, for each journey j of p: Σ_{e in j} (1 - x_e) <= |j| - 1
       equivalently: Σ_{e in j} x_e >= 1 for each journey j?
       No — we need at least one journey fully included.

Actually this is a COVERING problem with an OR structure (disjunctive constraints).
The LP relaxation uses the standard technique:

  For each pair p, introduce z_{p,j} in {0,1} = "journey j is used for pair p"
  Σ_j z_{p,j} >= 1                    (pair p is covered)
  z_{p,j} <= x_e  for all e in j       (if journey j is used, all its edges must be in)
  0 <= x_e <= 1

This is equivalent to:
  min Σ x_e
  s.t. for each pair p: max_j min_{e in j} x_e >= 1
       (at least one journey has all edges selected)

The LP relaxation of the IP with z variables:
  min Σ x_e
  s.t. Σ_j z_{p,j} >= 1 for each pair p
       z_{p,j} <= x_e for each pair p, journey j, edge e in j
       0 <= x_e <= 1, 0 <= z_{p,j} <= 1

We can eliminate z: z_{p,j} = min_{e in j} x_e (optimal for LP).
So the LP becomes:
  min Σ x_e
  s.t. for each pair p: Σ_j min_{e in j} x_e >= 1
  This is NOT linear.

Alternative (standard) LP relaxation — use the BLOCKING formulation:
For each pair p, let J_p = set of all journeys for p.
The constraint is: x must HIT every "anti-journey" (complement of a journey is a cut).
Actually the right formulation: for each pair p and each MINIMAL CUT (set of edges
whose removal breaks all journeys for p), the spanner must include at least one edge
from the cut.

Equivalently, for each pair p, let T_p = set of minimal temporal s-t cuts.
For each cut C in T_p: Σ_{e in C} x_e >= 1.

This IS a covering LP. Let's compute it.

A temporal s-t cut = a set of edges whose removal eliminates all temporal s->t journeys.
A minimal such cut = no proper subset is also a cut.

For small instances we can enumerate minimal cuts by enumerating all journeys and
finding minimal hitting sets of the journey hypergraph.
"""

import random
import numpy as np
from itertools import combinations
from scipy.optimize import linprog
from collections import defaultdict


# ---------- temporal graph primitives ----------

def make_edges(n):
    return [(i, j) for i in range(n) for j in range(i + 1, n)]


def compute_reachability_set(n, timed_edges):
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


def compute_reachability_bitmask(n, timed_edges):
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


# ---------- graph generators ----------

def generate_sm(k):
    n = 2 * k
    edges = make_edges(n)
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
            idx = eidx[(min(i, k + j), max(i, k + j))]
            if ts[idx] == 0:
                ts[idx] = t; t += 1
    for i in range(k):
        for j in range(i + 1, k):
            ts[eidx[(k + i, k + j)]] = t; t += 1

    return n, edges, ts, eidx


def generate_random_temporal(n, seed=None):
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


# ---------- minimum spanner ----------

def find_minimum_spanner(n, edges, ts, trials=200):
    m = len(edges)
    timed_all = sorted([(ts[i], edges[i][0], edges[i][1]) for i in range(m)])
    target = compute_reachability_bitmask(n, timed_all)

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
            if compute_reachability_bitmask(n, sub) == target:
                included = candidate

        improved = True
        while improved:
            improved = False
            for rm in sorted(included):
                cand = included - {rm}
                sub = sorted([(ts[i], edges[i][0], edges[i][1]) for i in cand])
                if compute_reachability_bitmask(n, sub) == target:
                    included = cand
                    improved = True
                    break

        if len(included) < best_size:
            best_size = len(included)
            best = set(included)

    return best


# ---------- enumerate temporal journeys ----------

def enumerate_journeys(n, edges, ts, eidx, s, t):
    """
    Enumerate all temporal journeys from s to t.
    A journey = sequence of edge indices with strictly increasing timestamps,
    forming a walk from s to t.
    Returns list of frozensets of edge indices (we only need edge sets, not order).
    Uses DFS with pruning.
    """
    m = len(edges)
    # Build adjacency: for each vertex, edges sorted by timestamp
    adj = defaultdict(list)
    for i, (u, v) in enumerate(edges):
        adj[u].append((ts[i], v, i))
        adj[v].append((ts[i], u, i))
    for v in adj:
        adj[v].sort()

    journeys = []
    # DFS: (current_vertex, last_timestamp, edge_set_so_far)
    stack = [(s, 0, frozenset())]
    while stack:
        cur, last_t, used_edges = stack.pop()
        if cur == t and len(used_edges) > 0:
            journeys.append(used_edges)
            # Don't stop — continue to find longer journeys too
        # Extend
        for edge_t, nbr, eidx_val in adj[cur]:
            if edge_t > last_t:  # strictly increasing
                stack.append((nbr, edge_t, used_edges | {eidx_val}))

    return journeys


def enumerate_journeys_bounded(n, edges, ts, eidx, s, t, max_journeys=10000):
    """
    Enumerate temporal journeys with a cap to avoid explosion.
    Returns (journeys, truncated).
    """
    m = len(edges)
    adj = defaultdict(list)
    for i, (u, v) in enumerate(edges):
        adj[u].append((ts[i], v, i))
        adj[v].append((ts[i], u, i))
    for v in adj:
        adj[v].sort()

    journeys = []
    stack = [(s, 0, frozenset())]
    truncated = False
    while stack:
        if len(journeys) >= max_journeys:
            truncated = True
            break
        cur, last_t, used_edges = stack.pop()
        if cur == t and len(used_edges) > 0:
            journeys.append(used_edges)
        for edge_t, nbr, eidx_val in adj[cur]:
            if edge_t > last_t:
                stack.append((nbr, edge_t, used_edges | {eidx_val}))

    return journeys, truncated


# ---------- journey-based LP ----------

def build_journey_lp(n, edges, ts, eidx):
    """
    For each reachable pair, enumerate journeys.
    LP: min Σ x_e
        s.t. for each pair p, journey j: z_{p,j} <= x_e for all e in j
             for each pair p: Σ_j z_{p,j} >= 1
             0 <= x, z <= 1

    We build this as a standard LP.
    Variables: x_0..x_{m-1} (edges), then z_{p,j} for each pair/journey.
    """
    m = len(edges)
    timed_all = sorted([(ts[i], edges[i][0], edges[i][1]) for i in range(m)])
    all_pairs = sorted(compute_reachability_set(n, timed_all))

    print(f"  Enumerating journeys for {len(all_pairs)} pairs...")

    pair_journeys = {}
    total_journeys = 0
    total_truncated = 0
    for s, t in all_pairs:
        jlist, trunc = enumerate_journeys_bounded(n, edges, ts, eidx, s, t, max_journeys=5000)
        if trunc:
            total_truncated += 1
        # Deduplicate by edge set
        unique = list(set(jlist))
        pair_journeys[(s, t)] = unique
        total_journeys += len(unique)

    print(f"  Total journeys: {total_journeys}, truncated pairs: {total_truncated}")

    # Build LP
    # Variables: x_0..x_{m-1}, then z_{p,j}
    # Number z variables
    z_start = m
    z_vars = []
    z_idx = {}
    idx = z_start
    for p in all_pairs:
        for j_i, j in enumerate(pair_journeys[p]):
            z_idx[(p, j_i)] = idx
            z_vars.append((p, j_i))
            idx += 1
    total_vars = idx
    print(f"  LP variables: {m} edge + {len(z_vars)} journey = {total_vars} total")

    # Objective: min Σ x_e (z variables have 0 cost)
    c = np.zeros(total_vars)
    c[:m] = 1.0

    # Constraints (as A_ub x <= b_ub):
    # 1) z_{p,j} <= x_e  =>  z_{p,j} - x_e <= 0
    # 2) Σ_j z_{p,j} >= 1  =>  -Σ_j z_{p,j} <= -1
    rows_ub = []
    b_ub_list = []

    # Type 1: z_{p,j} - x_e <= 0
    for p in all_pairs:
        for j_i, j in enumerate(pair_journeys[p]):
            zi = z_idx[(p, j_i)]
            for e in j:
                row = np.zeros(total_vars)
                row[zi] = 1.0
                row[e] = -1.0
                rows_ub.append(row)
                b_ub_list.append(0.0)

    # Type 2: -Σ_j z_{p,j} <= -1
    for p in all_pairs:
        row = np.zeros(total_vars)
        for j_i in range(len(pair_journeys[p])):
            zi = z_idx[(p, j_i)]
            row[zi] = -1.0
        rows_ub.append(row)
        b_ub_list.append(-1.0)

    A_ub = np.array(rows_ub)
    b_ub = np.array(b_ub_list)

    print(f"  LP constraints: {A_ub.shape[0]}")

    bounds = [(0, 1) for _ in range(total_vars)]

    res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')
    if not res.success:
        print(f"  WARNING: LP failed: {res.message}")
        return None, None, None, None

    x_opt = res.x[:m]
    primal_opt = res.fun

    return primal_opt, x_opt, all_pairs, pair_journeys


def build_journey_lp_sparse(n, edges, ts, eidx):
    """
    Same LP but using sparse matrices for larger instances.
    """
    from scipy.sparse import lil_matrix

    m = len(edges)
    timed_all = sorted([(ts[i], edges[i][0], edges[i][1]) for i in range(m)])
    all_pairs = sorted(compute_reachability_set(n, timed_all))

    print(f"  Enumerating journeys for {len(all_pairs)} pairs...")

    pair_journeys = {}
    total_journeys = 0
    total_truncated = 0
    for s, t in all_pairs:
        jlist, trunc = enumerate_journeys_bounded(n, edges, ts, eidx, s, t, max_journeys=2000)
        if trunc:
            total_truncated += 1
        unique = list(set(jlist))
        pair_journeys[(s, t)] = unique
        total_journeys += len(unique)

    print(f"  Total journeys: {total_journeys}, truncated pairs: {total_truncated}")

    z_start = m
    z_vars = []
    z_idx = {}
    idx = z_start
    for p in all_pairs:
        for j_i, j in enumerate(pair_journeys[p]):
            z_idx[(p, j_i)] = idx
            z_vars.append((p, j_i))
            idx += 1
    total_vars = idx

    # Count constraints
    n_type1 = sum(len(e_set) for p in all_pairs for e_set in pair_journeys[p])
    n_type2 = len(all_pairs)
    n_constraints = n_type1 + n_type2

    print(f"  LP: {total_vars} vars, {n_constraints} constraints (sparse)")

    c = np.zeros(total_vars)
    c[:m] = 1.0

    A_ub = lil_matrix((n_constraints, total_vars))
    b_ub = np.zeros(n_constraints)

    row = 0
    # Type 1
    for p in all_pairs:
        for j_i, j in enumerate(pair_journeys[p]):
            zi = z_idx[(p, j_i)]
            for e in j:
                A_ub[row, zi] = 1.0
                A_ub[row, e] = -1.0
                b_ub[row] = 0.0
                row += 1

    # Type 2
    for p in all_pairs:
        for j_i in range(len(pair_journeys[p])):
            zi = z_idx[(p, j_i)]
            A_ub[row, zi] = -1.0
        b_ub[row] = -1.0
        row += 1

    A_ub = A_ub.tocsc()

    bounds = [(0, 1) for _ in range(total_vars)]
    res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')

    if not res.success:
        print(f"  WARNING: LP failed: {res.message}")
        return None, None, None, None

    x_opt = res.x[:m]
    primal_opt = res.fun

    return primal_opt, x_opt, all_pairs, pair_journeys


# ---------- dual analysis ----------

def solve_dual_journey_lp(n, edges, ts, eidx, all_pairs, pair_journeys):
    """
    The dual of the journey LP:
    Primal: min Σ x_e
      s.t.  z_{p,j} <= x_e  (for e in j)
            Σ_j z_{p,j} >= 1
            0 <= x,z <= 1

    Dual variables:
      α_{p,j,e} >= 0  for z_{p,j} <= x_e constraints
      β_p >= 0         for Σ_j z_{p,j} >= 1 constraints
      μ_e >= 0         for x_e <= 1 upper bounds
      (lower bounds are free)

    Dual:  max Σ_p β_p - Σ_e μ_e
      s.t. for each e: Σ_{(p,j): e in j} α_{p,j,e} + μ_e >= 1  (dual of x_e)
           for each (p,j): β_p <= Σ_{e in j} α_{p,j,e}          (dual of z_{p,j})
           (plus dual of z_{p,j} <= 1 but that doesn't bind usually)

    This is complex. Instead, just solve the dual via strong duality and linprog's dual.
    Actually, let's just extract the dual from the primal solution.

    Simpler: we already know the LP optimum. Let's focus on the PACKING dual,
    which is what matters for the 2n-4 lower bound.

    Actually, the cleaner approach: use linprog's built-in dual.
    Or: solve the dual directly as a max LP.

    Let's just report the primal result and compare to IP.
    """
    pass


# ---------- analysis ----------

def analyze_instance(label, n, edges, ts, eidx):
    print(f"\n{'='*60}")
    print(f"Instance: {label}  (n={n}, m={len(edges)})")
    print(f"{'='*60}")

    m = len(edges)

    # Use sparse for larger instances
    if m > 20:
        primal_opt, x_opt, all_pairs, pair_journeys = build_journey_lp_sparse(
            n, edges, ts, eidx)
    else:
        primal_opt, x_opt, all_pairs, pair_journeys = build_journey_lp(
            n, edges, ts, eidx)

    if primal_opt is None:
        return None

    print(f"\n  LP optimum: {primal_opt:.4f}")

    # Fractional edge analysis
    eps = 1e-6
    integral = np.sum((x_opt < eps) | (x_opt > 1 - eps))
    fractional = m - integral
    print(f"  Integral edges: {integral}/{m}, fractional: {fractional}")
    selected = np.sum(x_opt > 1 - eps)
    print(f"  Edges selected (x=1): {int(selected)}")

    if fractional > 0:
        frac_vals = x_opt[(x_opt > eps) & (x_opt < 1 - eps)]
        print(f"  Fractional values: {sorted(frac_vals)[:15]}{'...' if len(frac_vals) > 15 else ''}")

    # Integer optimum via min spanner
    spanner = find_minimum_spanner(n, edges, ts)
    int_opt = len(spanner)
    print(f"\n  Integer optimum (min spanner): {int_opt}")
    print(f"  2n-4 = {2*n - 4},  2n-3 = {2*n - 3}")

    gap = int_opt / primal_opt if primal_opt > eps else float('inf')
    print(f"\n  Integrality gap: {int_opt} / {primal_opt:.4f} = {gap:.4f}")

    if abs(gap - 1.0) < 0.01:
        print("  => LP relaxation is integral!")
    elif gap < 1.1:
        print("  => Very small gap")
    else:
        print(f"  => Gap of {gap:.4f}")

    # Which edges are fractional?
    if fractional > 0:
        print("\n  Fractional edges (edge_idx: (u,v) ts x_val):")
        for e in range(m):
            if x_opt[e] > eps and x_opt[e] < 1 - eps:
                u, v = edges[e]
                print(f"    edge {e}: ({u},{v}) t={ts[e]} x={x_opt[e]:.4f}")

    return {
        'label': label, 'n': n, 'lp': primal_opt, 'ip': int_opt,
        'gap': gap, 'fractional': fractional,
    }


# ---------- main ----------

def main():
    results = []

    # SM(k) instances
    for k in [3, 4, 5]:
        n, edges, ts, eidx = generate_sm(k)
        r = analyze_instance(f"SM({k})", n, edges, ts, eidx)
        if r:
            results.append(r)

    # Random temporal K_n
    for n_val in [6, 8]:
        for seed in [42, 137, 271]:
            n, edges, ts, eidx = generate_random_temporal(n_val, seed=seed)
            r = analyze_instance(f"Random K_{n_val} seed={seed}", n, edges, ts, eidx)
            if r:
                results.append(r)

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"{'Instance':<30} {'n':>3} {'LP':>8} {'IP':>4} {'Gap':>7} {'Frac':>5}")
    print("-" * 60)
    for r in results:
        print(f"{r['label']:<30} {r['n']:>3} {r['lp']:>8.4f} {r['ip']:>4} "
              f"{r['gap']:>7.4f} {r['fractional']:>5}")

    if results:
        max_gap = max(r['gap'] for r in results)
        print(f"\nMax integrality gap observed: {max_gap:.4f}")
        if max_gap <= 1.01:
            print("=> LP relaxation appears integral for all tested instances.")
        elif max_gap <= 1.5:
            print("=> Moderate gap — LP gives a reasonable bound but not tight.")
        else:
            print("=> Large gap — LP relaxation is weak for this structure.")

        # Check if LP >= 2n-4 for all
        print("\nLP vs 2n-4 check:")
        for r in results:
            lb = 2 * r['n'] - 4
            status = "LP >= 2n-4" if r['lp'] >= lb - 0.01 else f"LP < 2n-4 (LP={r['lp']:.2f} < {lb})"
            print(f"  {r['label']}: {status}")


if __name__ == "__main__":
    main()
