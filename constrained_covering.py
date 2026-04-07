"""
Constrained covering LP on extremally matched bicliques.

Tests whether the matching/sandwiching constraints of Carnevale 2025 / Angrick ESA 2024
make the covering LP integral, compared to unconstrained random temporal cliques.

Biclique structure:
  - 2k vertices: V⁻ = {0,...,k-1}, V⁺ = {k,...,2k-1}
  - Full temporal clique (all pairs get distinct timestamps)
  - M⁻: earliest cross-edge per V⁺ vertex (random perfect matching V⁺ → V⁻)
  - M⁺: latest cross-edge per V⁻ vertex (random perfect matching V⁻ → V⁺)
  - Timestamps sandwiched: intra-V⁻ < cross < intra-V⁺
  - Condition 3: no intra-part label between adjacent matching labels
"""

import random
import numpy as np
from itertools import combinations
from scipy.optimize import linprog
from collections import defaultdict
import sys


# ---------- graph primitives ----------

def all_edges(n):
    """All undirected edges on n vertices."""
    return [(i, j) for i in range(n) for j in range(i + 1, n)]


def intra_edges(part):
    """All edges within a vertex set."""
    return [(u, v) for u, v in combinations(sorted(part), 2)]


def cross_edges(part_minus, part_plus):
    """All edges between V⁻ and V⁺ (ordered so u < v)."""
    edges = []
    for u in part_minus:
        for v in part_plus:
            edges.append((min(u, v), max(u, v)))
    return edges


# ---------- biclique generation ----------

def generate_extremal_biclique(k, max_attempts=1000):
    """
    Generate a valid extremally matched biclique on 2k vertices.
    Returns (timed_edges, n) or None if condition 3 can't be satisfied.
    timed_edges: list of (timestamp, u, v) sorted by timestamp.
    """
    n = 2 * k
    v_minus = list(range(k))
    v_plus = list(range(k, 2 * k))

    intra_minus = intra_edges(v_minus)   # C(k,2) edges
    intra_plus = intra_edges(v_plus)     # C(k,2) edges
    cross = cross_edges(v_minus, v_plus) # k² edges

    n_intra_minus = len(intra_minus)
    n_cross = len(cross)
    n_intra_plus = len(intra_plus)

    for _ in range(max_attempts):
        # Random perfect matchings
        perm_minus = list(range(k))
        random.shuffle(perm_minus)
        # M⁻: V⁺[i] matched to V⁻[perm_minus[i]] — earliest cross-edge per V⁺ vertex
        m_minus = set()
        for i in range(k):
            u, v = perm_minus[i], k + i
            m_minus.add((min(u, v), max(u, v)))

        perm_plus = list(range(k))
        random.shuffle(perm_plus)
        # M⁺: V⁻[i] matched to V⁺[perm_plus[i]] — latest cross-edge per V⁻ vertex
        m_plus = set()
        for i in range(k):
            u, v = i, k + perm_plus[i]
            m_plus.add((min(u, v), max(u, v)))

        # Assign timestamps
        # Group 1: intra-V⁻ (timestamps 1..n_intra_minus)
        # Group 2: cross edges (timestamps n_intra_minus+1..n_intra_minus+n_cross)
        # Group 3: intra-V⁺ (timestamps n_intra_minus+n_cross+1..)
        base_cross = n_intra_minus
        base_plus = n_intra_minus + n_cross

        # Randomize within groups
        random.shuffle(intra_minus)
        random.shuffle(intra_plus)

        # For cross edges: M⁻ edges must be earliest per V⁺ vertex,
        # M⁺ edges must be latest per V⁻ vertex.
        # Strategy: assign M⁻ edges the k smallest cross timestamps,
        # M⁺ edges the k largest, rest in between.
        # But M⁻ and M⁺ may overlap (same edge in both matchings).

        m_both = m_minus & m_plus
        m_minus_only = m_minus - m_both
        m_plus_only = m_plus - m_both
        m_neither = [e for e in cross if e not in m_minus and e not in m_plus]

        # Cross timestamps: 1-indexed within cross group
        # M⁻-only get the earliest slots, M⁺-only get the latest slots,
        # shared edges need to be both earliest and latest for their vertices.
        # Middle edges fill the rest.

        # Number of cross timestamps needed
        n_m_minus_only = len(m_minus_only)
        n_m_plus_only = len(m_plus_only)
        n_m_both = len(m_both)
        n_middle = len(m_neither)

        # Assign: [m_both, m_minus_only, middle, m_plus_only]
        # Actually this is tricky. Let me think about ordering constraints.
        #
        # For each V⁺ vertex v: its M⁻ edge must have smallest cross-timestamp
        #   among all cross-edges incident to v.
        # For each V⁻ vertex u: its M⁺ edge must have largest cross-timestamp
        #   among all cross-edges incident to u.
        #
        # Approach: assign cross timestamps by sorting edges into layers.
        # Layer 0: edges in M⁻ (earliest)
        # Layer 2: edges in M⁺ (latest)
        # Layer 1: everything else
        # Then within each layer, random order.
        # Edges in both M⁻ and M⁺ go to layer 0 AND layer 2... conflict.
        # An edge in both must be earliest for its V⁺ endpoint AND latest for
        # its V⁻ endpoint. This means ALL other cross-edges incident to either
        # endpoint must not be in the same extremal position.

        # Simpler: greedily assign timestamps respecting constraints.
        # For each cross edge, compute constraints:
        #   - If in M⁻: must come before all other cross-edges of same V⁺ vertex
        #   - If in M⁺: must come after all other cross-edges of same V⁻ vertex
        # Topological sort with random tie-breaking.

        # Build DAG: edge a → edge b means a must come before b in timestamp
        cross_list = list(cross)
        edge_to_idx = {e: i for i, e in enumerate(cross_list)}

        # For each V⁺ vertex, find its M⁻ edge and add constraints
        predecessors = defaultdict(set)  # idx -> set of idx that must come before
        for e in m_minus:
            u, v = e
            vplus = v if v >= k else u
            for other in cross_list:
                if other != e:
                    ou, ov = other
                    if ou == vplus or ov == vplus:
                        # e must come before other
                        predecessors[edge_to_idx[other]].add(edge_to_idx[e])

        # For each V⁻ vertex, find its M⁺ edge and add constraints
        for e in m_plus:
            u, v = e
            vminus = u if u < k else v
            for other in cross_list:
                if other != e:
                    ou, ov = other
                    if ou == vminus or ov == vminus:
                        # other must come before e
                        predecessors[edge_to_idx[e]].add(edge_to_idx[other])

        # Topological sort with random tie-breaking
        in_degree = [0] * len(cross_list)
        successors = defaultdict(set)
        for idx, preds in predecessors.items():
            in_degree[idx] = len(preds)
            for p in preds:
                successors[p].add(idx)

        available = [i for i in range(len(cross_list)) if in_degree[i] == 0]
        order = []
        valid = True
        while available:
            random.shuffle(available)
            chosen = available.pop()
            order.append(chosen)
            for s in successors[chosen]:
                in_degree[s] -= 1
                if in_degree[s] == 0:
                    available.append(s)

        if len(order) != len(cross_list):
            continue  # cycle in constraints, retry

        # Assign timestamps
        timed_edges = []
        # Intra-V⁻
        for t_idx, e in enumerate(intra_minus):
            timed_edges.append((t_idx + 1, e[0], e[1]))
        # Cross edges in topological order
        for t_idx, cross_idx in enumerate(order):
            e = cross_list[cross_idx]
            timed_edges.append((base_cross + t_idx + 1, e[0], e[1]))
        # Intra-V⁺
        for t_idx, e in enumerate(intra_plus):
            timed_edges.append((base_plus + t_idx + 1, e[0], e[1]))

        timed_edges.sort()

        # Verify M⁻: for each V⁺ vertex, its M⁻ edge is the earliest cross-edge
        cross_timed = [(t, u, v) for t, u, v in timed_edges if
                       (u < k) != (v < k)]  # one in V⁻, one in V⁺
        ok = True
        for v_idx in range(k):
            vp = k + v_idx
            incident = [(t, u, w) for t, u, w in cross_timed if u == vp or w == vp]
            if not incident:
                ok = False; break
            earliest = min(incident, key=lambda x: x[0])
            e_edge = (min(earliest[1], earliest[2]), max(earliest[1], earliest[2]))
            if e_edge not in m_minus:
                ok = False; break

        if not ok:
            continue

        # Verify M⁺: for each V⁻ vertex, its M⁺ edge is the latest cross-edge
        for v_idx in range(k):
            vm = v_idx
            incident = [(t, u, w) for t, u, w in cross_timed if u == vm or w == vm]
            if not incident:
                ok = False; break
            latest = max(incident, key=lambda x: x[0])
            l_edge = (min(latest[1], latest[2]), max(latest[1], latest[2]))
            if l_edge not in m_plus:
                ok = False; break

        if not ok:
            continue

        # Check condition 3: no intra-part label between adjacent matching labels.
        # For each vertex v, let t_minus(v) = timestamp of its M⁻ edge (if in V⁺)
        # or M⁺ edge (if in V⁻). Adjacent matching labels = the M⁻ and M⁺ timestamps
        # for matching partners.
        #
        # Condition 3 (Angrick): for each edge (u,v) with u in V⁻, v in V⁺:
        #   if (u,v) in M⁻: no intra-V⁺ edge incident to v has timestamp < t(u,v)
        #   if (u,v) in M⁺: no intra-V⁻ edge incident to u has timestamp > t(u,v)
        # More precisely: for matched pair, no intra-part label of the "receiving" vertex
        # falls between the two matching timestamps.
        #
        # Since intra-V⁻ < all cross < intra-V⁺ by construction,
        # condition 3 is automatically satisfied:
        # - M⁻ edges are cross-edges, all intra-V⁺ timestamps are larger → no intra-V⁺
        #   label can be smaller than an M⁻ label.
        # - M⁺ edges are cross-edges, all intra-V⁻ timestamps are smaller → no intra-V⁻
        #   label can be larger than an M⁺ label.
        #
        # So condition 3 is guaranteed by the sandwiching. Still verify explicitly.

        edge_timestamps = {}
        for t, u, v in timed_edges:
            edge_timestamps[(min(u, v), max(u, v))] = t

        cond3_ok = True
        # For each V⁺ vertex v, M⁻ gives its earliest cross timestamp t_m.
        # No intra-V⁺ edge of v should have timestamp between t_m and...
        # Actually condition 3 says: for matching edge (u,v), no intra-part edge
        # of v (in V⁺) has a label between the M⁻(v) and M⁺(u) labels.
        # With sandwiching this is automatic. Let's just check.
        for e_m in m_minus:
            t_m = edge_timestamps[e_m]
            u, v = e_m
            vp = v if v >= k else u
            vm = u if u < k else v
            # Find M⁺ edge of vm
            m_plus_edge = None
            for e_p in m_plus:
                eu, ev = e_p
                if eu == vm or ev == vm:
                    m_plus_edge = e_p
                    break
            if m_plus_edge is None:
                cond3_ok = False; break
            t_p = edge_timestamps[m_plus_edge]
            lo, hi = min(t_m, t_p), max(t_m, t_p)
            # No intra-part edge of vp between lo and hi
            for ie in intra_edges([vp] + [x for x in v_plus if x != vp]):
                if ie in edge_timestamps:
                    t_ie = edge_timestamps[ie]
                    if lo < t_ie < hi:
                        cond3_ok = False; break
            if not cond3_ok:
                break
            # No intra-part edge of vm between lo and hi
            for ie in intra_edges([vm] + [x for x in v_minus if x != vm]):
                if ie in edge_timestamps:
                    t_ie = edge_timestamps[ie]
                    if lo < t_ie < hi:
                        cond3_ok = False; break
            if not cond3_ok:
                break

        if not cond3_ok:
            continue

        return timed_edges, n

    return None


def generate_random_clique(k):
    """Generate an unconstrained random temporal clique on 2k vertices."""
    n = 2 * k
    edges = all_edges(n)
    timestamps = list(range(1, len(edges) + 1))
    random.shuffle(timestamps)
    timed_edges = sorted((t, e[0], e[1]) for t, e in zip(timestamps, edges))
    return timed_edges, n


# ---------- temporal reachability / journeys ----------

def enumerate_journeys(n, timed_edges):
    """
    Enumerate all temporal journeys (strictly increasing timestamps).
    Returns dict: (s, t) -> list of frozensets of edge-indices used.
    """
    # Index edges
    edge_list = [(t, u, v) for t, u, v in timed_edges]
    # For each pair, find all journeys via DP
    # journey_to[v] = dict: frozenset(edge_indices) -> last_timestamp
    # This is exponential but ok for small k.

    journeys = defaultdict(list)  # (s,t) -> [frozenset of edge indices]

    # BFS/DP: for each source s, track partial journeys
    for s in range(n):
        # state: (current_vertex, last_time) -> set of frozensets of edge indices
        # Use BFS over edges in timestamp order
        # partial[v] = list of (edge_set, last_time)
        partial = defaultdict(list)
        partial[s].append((frozenset(), 0))

        for eidx, (t, u, v) in enumerate(edge_list):
            # Try extending journeys at u and v
            new_at_u = []
            new_at_v = []
            for eset, last_t in partial[u]:
                if t > last_t:
                    new_set = eset | {eidx}
                    new_at_v.append((new_set, t))
            for eset, last_t in partial[v]:
                if t > last_t:
                    new_set = eset | {eidx}
                    new_at_u.append((new_set, t))

            partial[v].extend(new_at_v)
            partial[u].extend(new_at_u)

        for t_vertex in range(n):
            if t_vertex == s:
                continue
            for eset, _ in partial[t_vertex]:
                journeys[(s, t_vertex)].append(eset)

    return journeys


def compute_reachable_pairs(n, timed_edges):
    """Compute all reachable directed pairs using DP."""
    # reached_by[v] = {s: earliest_arrival}
    reached_by = [dict() for _ in range(n)]
    for i in range(n):
        reached_by[i][i] = 0

    for t, u, v in timed_edges:
        # Extend from u to v
        new_v = {}
        for s, arr in reached_by[u].items():
            if arr <= t:
                if s not in reached_by[v] or t < reached_by[v][s]:
                    new_v[s] = t
        # Extend from v to u
        new_u = {}
        for s, arr in reached_by[v].items():
            if arr <= t:
                if s not in reached_by[u] or t < reached_by[u][s]:
                    new_u[s] = t
        for s, arr in new_v.items():
            reached_by[v][s] = min(reached_by[v].get(s, float('inf')), arr)
        for s, arr in new_u.items():
            reached_by[u][s] = min(reached_by[u].get(s, float('inf')), arr)

    pairs = set()
    for v in range(n):
        for s in reached_by[v]:
            if s != v:
                pairs.add((s, v))
    return pairs


# ---------- covering sets ----------

def compute_cover_sets(n, timed_edges):
    """
    COVER(e) = set of directed pairs (s,t) that lose reachability when e is removed.
    Returns dict: edge_index -> set of (s,t) pairs.
    """
    full_pairs = compute_reachable_pairs(n, timed_edges)
    covers = {}
    for eidx in range(len(timed_edges)):
        reduced = timed_edges[:eidx] + timed_edges[eidx + 1:]
        reduced_pairs = compute_reachable_pairs(n, reduced)
        broken = full_pairs - reduced_pairs
        covers[eidx] = broken
    return covers


# ---------- VC dimension ----------

def vc_dimension(covers, pairs):
    """
    Compute VC dimension of the set system {COVER(e) : e in edges} over universe = pairs.
    """
    pair_list = list(pairs)
    pair_to_idx = {p: i for i, p in enumerate(pair_list)}

    # Convert covers to bitmasks
    edge_masks = []
    for eidx in sorted(covers.keys()):
        mask = 0
        for p in covers[eidx]:
            if p in pair_to_idx:
                mask |= (1 << pair_to_idx[p])
        edge_masks.append(mask)

    max_vc = 0
    n_pairs = len(pair_list)

    for size in range(1, n_pairs + 1):
        if size > 20:  # cap for tractability
            break
        found = False
        for subset in combinations(range(n_pairs), size):
            subset_mask = 0
            for idx in subset:
                subset_mask |= (1 << idx)
            # Check if all 2^size subsets are realized
            realized = set()
            for emask in edge_masks:
                realized.add(emask & subset_mask)
            if len(realized) == (1 << size):
                found = True
                max_vc = size
                break
        if not found:
            break

    return max_vc


# ---------- minimum spanner ----------

def greedy_spanner(n, timed_edges, n_trials=50):
    """Find minimum spanner via randomized greedy (n_trials attempts)."""
    full_pairs = compute_reachable_pairs(n, timed_edges)
    m = len(timed_edges)
    best_size = m

    for _ in range(n_trials):
        # Try removing edges in random order
        perm = list(range(m))
        random.shuffle(perm)
        included = [True] * m
        for eidx in perm:
            included[eidx] = False
            remaining = [timed_edges[i] for i in range(m) if included[i]]
            if compute_reachable_pairs(n, remaining) == full_pairs:
                pass  # can remove
            else:
                included[eidx] = True
        size = sum(included)
        best_size = min(best_size, size)

    return best_size


# ---------- covering LP ----------

def solve_covering_lp(n, timed_edges):
    """
    Covering LP: min Σx_e s.t. for each reachable pair p,
    Σ_{e : p in COVER(e)} x_e >= 1; 0 <= x_e <= 1.

    Returns (lp_value, ip_value).
    IP value = greedy spanner size (heuristic upper bound).
    """
    m = len(timed_edges)
    full_pairs = compute_reachable_pairs(n, timed_edges)
    covers = compute_cover_sets(n, timed_edges)

    # Build pair -> list of edge indices that cover it
    pair_to_edges = defaultdict(list)
    for eidx, broken in covers.items():
        for p in broken:
            pair_to_edges[p].append(eidx)

    # LP: min c^T x, A_ub x <= b_ub (use -A for >= constraints)
    c = np.ones(m)
    pairs_with_cover = [p for p in full_pairs if pair_to_edges[p]]

    if not pairs_with_cover:
        return 0.0, 0, covers, full_pairs

    A_ub = np.zeros((len(pairs_with_cover), m))
    b_ub = -np.ones(len(pairs_with_cover))

    for row, p in enumerate(pairs_with_cover):
        for eidx in pair_to_edges[p]:
            A_ub[row, eidx] = -1.0

    bounds = [(0, 1) for _ in range(m)]

    result = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')

    lp_val = result.fun if result.success else float('inf')

    # IP: greedy spanner
    ip_val = greedy_spanner(n, timed_edges, n_trials=50)

    return lp_val, ip_val, covers, full_pairs


# ---------- main experiment ----------

def run_experiment(k, n_samples, mode="constrained"):
    """Run experiment for given k."""
    n = 2 * k
    target = 2 * n - 3

    lp_vals = []
    ip_vals = []
    vc_dims = []
    gaps = []
    generated = 0
    attempts = 0

    while generated < n_samples:
        attempts += 1
        if mode == "constrained":
            result = generate_extremal_biclique(k)
            if result is None:
                continue
            timed_edges, n_v = result
        else:
            timed_edges, n_v = generate_random_clique(k)

        lp_val, ip_val, covers, pairs = solve_covering_lp(n_v, timed_edges)

        vc_d = vc_dimension(covers, pairs)

        gap = ip_val - lp_val if lp_val < float('inf') else float('inf')

        lp_vals.append(lp_val)
        ip_vals.append(ip_val)
        vc_dims.append(vc_d)
        gaps.append(gap)
        generated += 1

        if generated % 50 == 0:
            print(f"  [{mode}] k={k}: {generated}/{n_samples} done "
                  f"(attempts={attempts})", flush=True)

    return {
        'lp_vals': lp_vals,
        'ip_vals': ip_vals,
        'vc_dims': vc_dims,
        'gaps': gaps,
        'target': target,
        'attempts': attempts,
    }


def report(k, constrained, unconstrained):
    n = 2 * k
    target = 2 * n - 3
    print(f"\n{'='*60}")
    print(f"k = {k}, n = {n}, target = 2n-3 = {target}")
    print(f"{'='*60}")

    for label, data in [("CONSTRAINED (extremal biclique)", constrained),
                        ("UNCONSTRAINED (random clique)", unconstrained)]:
        print(f"\n  --- {label} ---")
        print(f"  Samples: {len(data['lp_vals'])} "
              f"(generation attempts: {data['attempts']})")

        lp = np.array(data['lp_vals'])
        ip = np.array(data['ip_vals'])
        vc = np.array(data['vc_dims'])
        gaps = np.array(data['gaps'])

        print(f"  Min spanner size: min={ip.min()}, max={ip.max()}, "
              f"mean={ip.mean():.2f}, vs target={target}")
        print(f"  LP value: min={lp.min():.3f}, max={lp.max():.3f}, "
              f"mean={lp.mean():.3f}")
        print(f"  VC dimension: min={vc.min()}, max={vc.max()}, "
              f"mean={vc.mean():.2f}")
        print(f"  Integrality gap (IP - LP): min={gaps.min():.3f}, "
              f"max={gaps.max():.3f}, mean={gaps.mean():.3f}")

        # Check if LP is always integral
        fractional = np.sum(np.abs(lp - np.round(lp)) > 1e-6)
        print(f"  Fractional LP solutions: {fractional}/{len(lp)}")

        # Check LP + gap <= target
        lp_plus_gap = lp + gaps  # = ip
        violations = np.sum(lp_plus_gap > target + 0.001)
        print(f"  IP > 2n-3 violations: {violations}/{len(ip)}")

        # Gap distribution
        unique_gaps = sorted(set(np.round(gaps, 3)))
        if len(unique_gaps) <= 10:
            for g in unique_gaps:
                count = np.sum(np.abs(gaps - g) < 0.01)
                print(f"    gap={g:.3f}: {count}")


def main():
    random.seed(42)
    np.random.seed(42)

    for k in [3, 4, 5]:
        n_samples = 500 if k <= 4 else 200  # k=5 is slower
        print(f"\n>>> Starting k={k} ({n_samples} samples each) <<<", flush=True)

        constrained = run_experiment(k, n_samples, mode="constrained")
        unconstrained = run_experiment(k, n_samples, mode="unconstrained")

        report(k, constrained, unconstrained)

    print("\nDone.")


if __name__ == "__main__":
    main()
