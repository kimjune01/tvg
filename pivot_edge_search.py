"""
Pivot-edge search for extremally matched temporal bicliques.

Tests the conjecture: every extremally matched temporal biclique
has a c-pivot-edge (Angrick et al. ESA 2024).

An edge e is a c-pivot-edge if |In(e) ∩ Out(e)| >= c * n,
where In(e) = vertices that can temporally reach e,
Out(e) = vertices temporally reachable from e.
"""

import random
import sys
from itertools import permutations
from collections import defaultdict

random.seed(42)


# ---------------------------------------------------------------------------
# Temporal reachability
# ---------------------------------------------------------------------------

def compute_reached_by(n, edges):
    """reached_by[v][s] = earliest arrival time of s at v via temporal path.
    Edges processed in time order; strict temporal (times strictly increase)."""
    sorted_edges = sorted(edges, key=lambda e: e[2])
    reached_by = [dict() for _ in range(n)]
    for v in range(n):
        reached_by[v][v] = -1  # present at v "before all time"

    for u, v, t in sorted_edges:
        new_v = {}
        new_u = {}
        for src, arr in reached_by[u].items():
            if arr < t:
                if src not in reached_by[v] or t < reached_by[v][src]:
                    new_v[src] = t
        for src, arr in reached_by[v].items():
            if arr < t:
                if src not in reached_by[u] or t < reached_by[u][src]:
                    new_u[src] = t
        reached_by[v].update(new_v)
        reached_by[u].update(new_u)
    return reached_by


def compute_reachable_from(n, edges):
    """reachable_from[s][v] = latest departure time from s toward v.
    Process edges in REVERSE time order for backward reachability.
    Actually easier: reachable_from[s] = set of v reachable from s.
    We compute this from reached_by."""
    reached_by = compute_reached_by(n, edges)
    reachable_from = [set() for _ in range(n)]
    for v in range(n):
        for s in reached_by[v]:
            reachable_from[s].add(v)
    return reachable_from, reached_by


def compute_pivot_scores(n, edges):
    """For each edge e=(u,w,t), compute:
    In(e) = vertices that can reach u or w with arrival < t (plus u,w themselves)
    Out(e) = vertices reachable from u or w departing at time t (via e then onward)

    Returns list of dicts with edge info and pivot scores."""

    sorted_edges = sorted(edges, key=lambda e: e[2])
    reached_by = compute_reached_by(n, edges)

    # For Out(e) at time t: propagate forward from {u,w} at time t
    # using only edges with time > t.
    # Precompute this efficiently: for each time threshold, what's reachable?
    # For small graphs, just compute per-edge.

    results = []
    for eu, ew, et in edges:
        # In(e)
        in_set = {eu, ew}
        for s in range(n):
            if s in in_set:
                continue
            if s in reached_by[eu] and reached_by[eu][s] < et:
                in_set.add(s)
            elif s in reached_by[ew] and reached_by[ew][s] < et:
                in_set.add(s)

        # Out(e): BFS forward from {eu, ew} using edges with time > et
        out_reached = {eu: et, ew: et}
        for u2, v2, t2 in sorted_edges:
            if t2 <= et:
                continue
            updated = True
            while updated:
                updated = False
                for u3, v3, t3 in sorted_edges:
                    if t3 <= et:
                        continue
                    if u3 in out_reached and out_reached[u3] < t3:
                        if v3 not in out_reached or t3 < out_reached[v3]:
                            out_reached[v3] = t3
                            updated = True
                    if v3 in out_reached and out_reached[v3] < t3:
                        if u3 not in out_reached or t3 < out_reached[u3]:
                            out_reached[u3] = t3
                            updated = True
            break  # only need one pass of the while loop after filtering

        # Actually the above is wrong - let me do it properly with a single forward pass
        out_reached = {eu: et, ew: et}
        changed = True
        while changed:
            changed = False
            for u2, v2, t2 in sorted_edges:
                if t2 <= et:
                    continue
                if u2 in out_reached and out_reached[u2] < t2:
                    if v2 not in out_reached or t2 < out_reached[v2]:
                        out_reached[v2] = t2
                        changed = True
                if v2 in out_reached and out_reached[v2] < t2:
                    if u2 not in out_reached or t2 < out_reached[u2]:
                        out_reached[u2] = t2
                        changed = True

        out_set = set(out_reached.keys())

        pivot_count = len(in_set & out_set)
        pivot_score = pivot_count / n

        results.append({
            'edge': (eu, ew, et),
            'in_size': len(in_set),
            'out_size': len(out_set),
            'pivot_count': pivot_count,
            'pivot_score': pivot_score,
        })

    return results


# ---------------------------------------------------------------------------
# SM(k) construction
# ---------------------------------------------------------------------------

def generate_sm(k):
    """SM(k): V⁻={0..k-1}, V⁺={k..2k-1}.
    Internal V⁻ edges first, then cross by diagonal, then internal V⁺.
    M⁻ = identity, M⁺ = identity (diagonal d=0 is first cross edge per row,
    but that makes M⁻ = identity; M⁺ = last cross edge per row).

    Actually SM(k) orders cross edges by diagonal offset d=0,1,...,k-1.
    For row a_i, cross edges appear at times for d=0 (a_i,b_i), d=1 (a_i,b_{i+1}), ...
    So the earliest cross neighbor of a_i is b_i (d=0), and the latest is b_{i+k-1 mod k} (d=k-1).
    For column b_j, the earliest is a_j (d=0), latest is a_{j-k+1 mod k} (d=k-1).
    So M⁻(b_j) = a_j (earliest), M⁺(a_i) = b_{(i+k-1)%k} (latest).
    """
    n = 2 * k
    edges = []
    t = 1

    # V⁻ internal
    for i in range(k):
        for j in range(i + 1, k):
            edges.append((i, j, t))
            t += 1

    # Cross edges by diagonal offset
    for d in range(k):
        for i in range(k):
            j = (i + d) % k
            edges.append((i, k + j, t))
            t += 1

    # V⁺ internal
    for i in range(k):
        for j in range(i + 1, k):
            edges.append((k + i, k + j, t))
            t += 1

    m_minus = list(range(k))  # M⁻(b_j) = a_j
    m_plus = [(i + k - 1) % k for i in range(k)]  # M⁺(a_i) = b_{(i+k-1)%k}

    return n, edges, m_minus, m_plus


def check_sm_extremal(k):
    """Verify SM(k) is extremally matched."""
    n, edges, m_minus, m_plus = generate_sm(k)

    # Build cross edge time lookup
    cross_time = {}
    for u, v, t in edges:
        if u < k and v >= k:
            cross_time[(u, v - k)] = t

    # Check M⁻: for each b_j, M⁻(b_j)=a_j should have earliest time
    m_minus_ok = True
    for j in range(k):
        i_star = m_minus[j]
        t_star = cross_time[(i_star, j)]
        for i in range(k):
            if cross_time[(i, j)] < t_star:
                m_minus_ok = False
                print(f"  M⁻ fail: b_{j} has earlier neighbor a_{i} "
                      f"(t={cross_time[(i,j)]}) than a_{i_star} (t={t_star})")
                break

    # Check M⁺: for each a_i, M⁺(a_i) should have latest time
    m_plus_ok = True
    for i in range(k):
        j_star = m_plus[i]
        t_star = cross_time[(i, j_star)]
        for j in range(k):
            if cross_time[(i, j)] > t_star:
                m_plus_ok = False
                print(f"  M⁺ fail: a_{i} has later neighbor b_{j} "
                      f"(t={cross_time[(i,j)]}) than b_{j_star} (t={t_star})")
                break

    # Check condition 3
    cond3_ok = True
    for u, v, t in edges:
        if u < k and v < k:
            i, ip = u, v
            t1 = cross_time[(i, m_plus[i])]
            t2 = cross_time[(ip, m_plus[ip])]
            lo, hi = min(t1, t2), max(t1, t2)
            if lo < t < hi:
                cond3_ok = False
                print(f"  Cond3 V⁻ fail: edge ({u},{v},t={t}) "
                      f"between M⁺ labels {t1},{t2}")
                break
        elif u >= k and v >= k:
            j, jp = u - k, v - k
            t1 = cross_time[(m_minus[j], j)]
            t2 = cross_time[(m_minus[jp], jp)]
            lo, hi = min(t1, t2), max(t1, t2)
            if lo < t < hi:
                cond3_ok = False
                print(f"  Cond3 V⁺ fail: edge ({u},{v},t={t}) "
                      f"between M⁻ labels {t1},{t2}")
                break

    return n, edges, m_minus, m_plus, m_minus_ok, m_plus_ok, cond3_ok


# ---------------------------------------------------------------------------
# Constructive generation of extremally matched bicliques
# ---------------------------------------------------------------------------

def generate_biclique_constructive(k, max_attempts=1000):
    """Generate extremally matched bicliques constructively.

    Strategy: pick random M⁻, M⁺ (permutations). Then assign cross-edge
    timestamps so that M⁻(b_j) is the min-time edge into b_j, and M⁺(a_i)
    is the max-time edge from a_i.

    Cross edge timestamp assignment:
    - For each column j: edge (M⁻(b_j), j) must have the smallest time
    - For each row i: edge (i, M⁺(a_i)) must have the largest time
    - These are ordering constraints; assign times consistent with them.

    Then assign intra-part times satisfying the sandwich property and cond 3.
    """
    n = 2 * k
    num_vminus = k * (k - 1) // 2
    num_cross = k * k
    num_vplus = k * (k - 1) // 2

    for attempt in range(max_attempts):
        # Random matchings
        m_minus = list(range(k))
        random.shuffle(m_minus)
        m_plus = list(range(k))
        random.shuffle(m_plus)

        # Assign cross-edge times respecting row-max and column-min constraints.
        # Build a partial order on cross edges:
        # For column j: (m_minus[j], j) < all other (i, j)
        # For row i: (i, m_plus[i]) > all other (i, j')
        # Edges: list of (i, j) for i in range(k), j in range(k)

        # Check consistency: an edge (i,j) where m_minus[j]=i AND m_plus[i]=j
        # must be both min-in-column and max-in-row. Only possible if k=1 or
        # it's the sole edge (which it isn't). So if m_minus[j]=i and m_plus[i]=j
        # for some i,j, the edge must be both smallest in column and largest in row.
        # This is fine if k=1. For k>1, this edge must be < other edges in column j
        # AND > other edges in row i. This constrains but doesn't necessarily conflict.

        # Use topological sort. Create a DAG:
        # For each column j: (m_minus[j], j) -> (i, j) for i != m_minus[j]
        #   meaning (m_minus[j], j) must come before (i, j)
        # For each row i: (i, j') -> (i, m_plus[i]) for j' != m_plus[i]
        #   meaning (i, j') must come before (i, m_plus[i])

        # Check for cycles
        edge_list = [(i, j) for i in range(k) for j in range(k)]
        edge_idx = {(i, j): i * k + j for i in range(k) for j in range(k)}
        adj = [[] for _ in range(k * k)]
        in_degree = [0] * (k * k)

        for j in range(k):
            src = edge_idx[(m_minus[j], j)]
            for i in range(k):
                if i != m_minus[j]:
                    dst = edge_idx[(i, j)]
                    adj[src].append(dst)
                    in_degree[dst] += 1

        for i in range(k):
            dst = edge_idx[(i, m_plus[i])]
            for jj in range(k):
                if jj != m_plus[i]:
                    src = edge_idx[(i, jj)]
                    adj[src].append(dst)
                    in_degree[dst] += 1

        # Topological sort (Kahn's algorithm) with randomization
        queue = [i for i in range(k * k) if in_degree[i] == 0]
        order = []
        while queue:
            random.shuffle(queue)
            node = queue.pop()
            order.append(node)
            for nb in adj[node]:
                in_degree[nb] -= 1
                if in_degree[nb] == 0:
                    queue.append(nb)

        if len(order) != k * k:
            # Cycle in constraints - matchings incompatible
            continue

        # Assign cross times based on topological order
        cross_time_by_idx = [0] * (k * k)
        base = num_vminus + 1
        for rank, node in enumerate(order):
            cross_time_by_idx[node] = base + rank

        cross_time = {}
        for i in range(k):
            for j in range(k):
                cross_time[(i, j)] = cross_time_by_idx[edge_idx[(i, j)]]

        # Build V⁻ internal edges and check condition 3
        # For V⁻ edge {a_i, a_ip}: label must not be between
        # cross_time[(i, m_plus[i])] and cross_time[(ip, m_plus[ip])]
        # V⁻ labels are 1..num_vminus

        # Get M⁺ labels for each a_i
        mplus_labels = [cross_time[(i, m_plus[i])] for i in range(k)]
        # Get M⁻ labels for each b_j
        mminus_labels = [cross_time[(m_minus[j], j)] for j in range(k)]

        # V⁻ internal edges
        vminus_pairs = [(i, j) for i in range(k) for j in range(i + 1, k)]
        # For each pair, the forbidden interval is (min(mplus[i],mplus[j]), max(...))
        # But V⁻ labels are all < base, so they're all below any cross label.
        # Therefore condition 3 is automatically satisfied for V⁻ edges!
        # (V⁻ edge label < all cross labels, so it can't be between two cross labels)

        # Similarly V⁺ labels are all > max cross label, so condition 3
        # is automatically satisfied for V⁺ edges!

        # Wait - condition 3 says the V⁻ edge label should not fall between
        # the M⁺ labels of its endpoints. M⁺ labels are cross-edge labels
        # (in the cross range). V⁻ edge labels are in range [1, num_vminus].
        # Cross edge labels are in range [num_vminus+1, ...].
        # So V⁻ edge label < any cross label. Since both M⁺ labels > V⁻ label,
        # the V⁻ label is below both, not between them. Condition 3 is auto-satisfied!

        # Same logic for V⁺ edges and M⁻ labels.
        # So condition 3 is ALWAYS satisfied with the sandwich property!

        # Assign V⁻ and V⁺ times randomly within their ranges
        vminus_times = list(range(1, num_vminus + 1))
        random.shuffle(vminus_times)

        vplus_base = num_vminus + num_cross + 1
        vplus_times = list(range(vplus_base, vplus_base + num_vplus))
        random.shuffle(vplus_times)

        # Build edge list
        edges = []
        vi = 0
        for i in range(k):
            for j in range(i + 1, k):
                edges.append((i, j, vminus_times[vi]))
                vi += 1

        for i in range(k):
            for j in range(k):
                edges.append((i, k + j, cross_time[(i, j)]))

        pi = 0
        for i in range(k):
            for j in range(i + 1, k):
                edges.append((k + i, k + j, vplus_times[pi]))
                pi += 1

        return n, edges, m_minus, m_plus

    return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def analyze_biclique(k, n, edges):
    results = compute_pivot_scores(n, edges)
    best = max(results, key=lambda r: r['pivot_score'])
    return results, best


def main():
    print("=" * 70)
    print("PART 1: SM(k) analysis — is it extremally matched?")
    print("=" * 70)

    for k in range(3, 8):
        print(f"\n--- SM({k}) ---")
        n, edges, m_minus, m_plus, m_minus_ok, m_plus_ok, cond3_ok = check_sm_extremal(k)
        extremal = m_minus_ok and m_plus_ok and cond3_ok
        print(f"  M⁻ ok={m_minus_ok}, M⁺ ok={m_plus_ok}, Cond3={cond3_ok}, "
              f"Extremally matched={extremal}")
        print(f"  M⁻={m_minus}, M⁺={m_plus}")

        # Analyze pivot scores regardless
        results, best = analyze_biclique(k, n, edges)
        print(f"  Best pivot: score={best['pivot_score']:.4f} "
              f"(edge {best['edge']}, |In|={best['in_size']}, "
              f"|Out|={best['out_size']}, |In∩Out|={best['pivot_count']})")
        scores = sorted([r['pivot_score'] for r in results], reverse=True)
        print(f"  Top 5 scores: {[f'{s:.4f}' for s in scores[:5]]}")

    print("\n" + "=" * 70)
    print("PART 2: Random extremally matched bicliques (constructive)")
    print("=" * 70)

    for k in range(3, 9):
        n = 2 * k
        num_target = 500 if k <= 5 else (200 if k <= 6 else (100 if k <= 7 else 30))
        print(f"\nk={k} (n={n}), generating {num_target} bicliques...")

        valid_count = 0
        best_pivots = []
        worst_case = None

        for trial in range(num_target):
            result = generate_biclique_constructive(k)
            if result is None:
                continue

            bn, bedges, bm_minus, bm_plus = result
            valid_count += 1

            results, best = analyze_biclique(k, bn, bedges)
            bp = best['pivot_score']
            best_pivots.append(bp)

            if worst_case is None or bp < worst_case[0]:
                worst_case = (bp, best['edge'], bm_minus, bm_plus)

        if valid_count == 0:
            print("  No valid bicliques generated!")
            continue

        best_pivots.sort()
        avg_pivot = sum(best_pivots) / len(best_pivots)
        print(f"  Generated: {valid_count}/{num_target}")
        print(f"  Pivot scores: min={best_pivots[0]:.4f}, "
              f"max={best_pivots[-1]:.4f}, avg={avg_pivot:.4f}, "
              f"median={best_pivots[len(best_pivots)//2]:.4f}")
        print(f"  Worst case: score={worst_case[0]:.4f}, "
              f"edge={worst_case[1]}, M⁻={worst_case[2]}, M⁺={worst_case[3]}")

        all_01 = all(p >= 0.1 for p in best_pivots)
        all_025 = all(p >= 0.25 for p in best_pivots)
        print(f"  All have 0.1-pivot: {all_01}")
        print(f"  All have 0.25-pivot: {all_025}")

        # Histogram
        buckets = defaultdict(int)
        for p in best_pivots:
            bucket = int(p * 20) / 20  # 0.05 bins
            buckets[bucket] += 1
        print(f"  Distribution (0.05 bins):")
        for b in sorted(buckets.keys()):
            bar = '#' * buckets[b]
            print(f"    [{b:.2f}, {b+0.05:.2f}): {buckets[b]:4d} {bar}")


if __name__ == '__main__':
    main()
