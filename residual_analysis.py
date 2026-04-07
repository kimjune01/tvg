"""
Residual analysis after pivot-edge elimination.

Given an extremally matched biclique, find the best pivot edge,
eliminate covered vertices (In ∩ Out), and characterize the residual.

Key questions:
1. Is the residual an extremally matched biclique?
2. Does it have a good pivot edge?
3. How many recursion levels until trivial?
4. Total edge count across all levels?
"""

import random
from itertools import permutations
from collections import defaultdict

random.seed(42)


# ---------------------------------------------------------------------------
# Temporal reachability (from pivot_edge_search.py)
# ---------------------------------------------------------------------------

def compute_reached_by(n, edges):
    """reached_by[v][s] = earliest arrival time of s at v."""
    sorted_edges = sorted(edges, key=lambda e: e[2])
    reached_by = [dict() for _ in range(n)]
    for v in range(n):
        reached_by[v][v] = -1

    for u, v, t in sorted_edges:
        new_v, new_u = {}, {}
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


def compute_pivot_data(n, edges):
    """For each edge, compute In(e), Out(e), In∩Out."""
    sorted_edges = sorted(edges, key=lambda e: e[2])
    reached_by = compute_reached_by(n, edges)

    results = []
    for eu, ew, et in edges:
        # In(e): vertices that can reach eu or ew with arrival < et
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
        pivot_set = in_set & out_set

        results.append({
            'edge': (eu, ew, et),
            'in_set': in_set,
            'out_set': out_set,
            'pivot_set': pivot_set,
            'pivot_score': len(pivot_set) / n,
        })

    return results


# ---------------------------------------------------------------------------
# Biclique generation (from pivot_edge_search.py)
# ---------------------------------------------------------------------------

def generate_biclique_constructive(k, max_attempts=1000):
    """Generate extremally matched bicliques constructively."""
    n = 2 * k
    num_vminus = k * (k - 1) // 2
    num_cross = k * k

    for attempt in range(max_attempts):
        m_minus = list(range(k))
        random.shuffle(m_minus)
        m_plus = list(range(k))
        random.shuffle(m_plus)

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
            continue

        cross_time_by_idx = [0] * (k * k)
        base = num_vminus + 1
        for rank, node in enumerate(order):
            cross_time_by_idx[node] = base + rank

        cross_time = {}
        for i in range(k):
            for j in range(k):
                cross_time[(i, j)] = cross_time_by_idx[edge_idx[(i, j)]]

        num_vplus = k * (k - 1) // 2
        vminus_times = list(range(1, num_vminus + 1))
        random.shuffle(vminus_times)
        vplus_base = num_vminus + num_cross + 1
        vplus_times = list(range(vplus_base, vplus_base + num_vplus))
        random.shuffle(vplus_times)

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


def generate_sm(k):
    """SM(k) construction."""
    n = 2 * k
    edges = []
    t = 1
    for i in range(k):
        for j in range(i + 1, k):
            edges.append((i, j, t))
            t += 1
    for d in range(k):
        for i in range(k):
            j = (i + d) % k
            edges.append((i, k + j, t))
            t += 1
    for i in range(k):
        for j in range(i + 1, k):
            edges.append((k + i, k + j, t))
            t += 1
    m_minus = list(range(k))
    m_plus = [(i + k - 1) % k for i in range(k)]
    return n, edges, m_minus, m_plus


# ---------------------------------------------------------------------------
# Residual computation
# ---------------------------------------------------------------------------

def induced_subgraph(n, edges, keep_vertices):
    """Return edges restricted to keep_vertices, with relabeled vertices."""
    keep = sorted(keep_vertices)
    relabel = {v: i for i, v in enumerate(keep)}
    new_n = len(keep)
    new_edges = []
    for u, v, t in edges:
        if u in relabel and v in relabel:
            new_edges.append((relabel[u], relabel[v], t))
    return new_n, new_edges, keep


def classify_vertex(v, k):
    """Return 'left' or 'right' based on vertex index in 2k-vertex biclique."""
    return 'left' if v < k else 'right'


def check_biclique_structure(n, edges, orig_vertices, orig_k):
    """Check if the residual has biclique structure.

    Returns dict with:
    - left_vertices, right_vertices (original labels)
    - is_biclique: do all left-right pairs have a cross edge?
    - has_extremal_matching: do M⁻/M⁺ exist?
    """
    left = [v for v in orig_vertices if v < orig_k]
    right = [v for v in orig_vertices if v >= orig_k]

    # Check cross edges
    relabel = {v: i for i, v in enumerate(sorted(orig_vertices))}
    kl, kr = len(left), len(right)

    # Build cross edge time matrix
    cross_edges = {}
    for u, v, t in edges:
        # Map back to original vertices
        orig_u = sorted(orig_vertices)[u]
        orig_v = sorted(orig_vertices)[v]
        if (orig_u < orig_k) != (orig_v < orig_k):
            # This is a cross edge
            li = orig_u if orig_u < orig_k else orig_v
            ri = orig_u if orig_u >= orig_k else orig_v
            li_idx = left.index(li)
            ri_idx = right.index(ri)
            cross_edges[(li_idx, ri_idx)] = t

    is_complete_bipartite = len(cross_edges) == kl * kr

    # Check M⁻ (column minimums) and M⁺ (row maximums)
    m_minus = {}
    m_plus = {}
    if kl > 0 and kr > 0:
        for j in range(kr):
            col_edges = [(i, t) for (i, jj), t in cross_edges.items() if jj == j]
            if col_edges:
                m_minus[j] = min(col_edges, key=lambda x: x[1])[0]

        for i in range(kl):
            row_edges = [(j, t) for (ii, j), t in cross_edges.items() if ii == i]
            if row_edges:
                m_plus[i] = max(row_edges, key=lambda x: x[1])[0]

    # Check if M⁻ is a matching (injective)
    m_minus_injective = len(set(m_minus.values())) == len(m_minus) if m_minus else False
    m_plus_injective = len(set(m_plus.values())) == len(m_plus) if m_plus else False

    # Check sandwich property
    vminus_times = []
    cross_times = []
    vplus_times = []
    for u, v, t in edges:
        orig_u = sorted(orig_vertices)[u]
        orig_v = sorted(orig_vertices)[v]
        if orig_u < orig_k and orig_v < orig_k:
            vminus_times.append(t)
        elif orig_u >= orig_k and orig_v >= orig_k:
            vplus_times.append(t)
        else:
            cross_times.append(t)

    sandwich = True
    if vminus_times and cross_times:
        if max(vminus_times) >= min(cross_times):
            sandwich = False
    if cross_times and vplus_times:
        if max(cross_times) >= min(vplus_times):
            sandwich = False

    return {
        'left': left,
        'right': right,
        'kl': kl,
        'kr': kr,
        'n_cross': len(cross_edges),
        'is_complete_bipartite': is_complete_bipartite,
        'm_minus_injective': m_minus_injective,
        'm_plus_injective': m_plus_injective,
        'sandwich': sandwich,
        'has_extremal_matching': (is_complete_bipartite and m_minus_injective
                                   and m_plus_injective and sandwich and kl == kr),
    }


def recursive_pivot(k, n, edges, depth=0, max_depth=20):
    """Recursively find pivot edges and eliminate covered vertices.

    Returns list of (depth, pivot_edge, pivot_set, residual_size, edge_count).
    """
    if n <= 2:
        return [{'depth': depth, 'n': n, 'edges_used': 1 if n == 2 else 0,
                 'pivot_score': 1.0, 'status': 'trivial'}]

    if depth >= max_depth:
        return [{'depth': depth, 'n': n, 'edges_used': 0,
                 'pivot_score': 0, 'status': 'max_depth'}]

    # Find best pivot edge
    pivot_data = compute_pivot_data(n, edges)
    if not pivot_data:
        return [{'depth': depth, 'n': n, 'edges_used': 0,
                 'pivot_score': 0, 'status': 'no_edges'}]

    best = max(pivot_data, key=lambda r: len(r['pivot_set']))
    pivot_set = best['pivot_set']
    pivot_score = best['pivot_score']

    # The pivot edge itself is kept
    # Vertices in pivot_set are "covered" — they can route through this edge
    # Residual = vertices NOT in pivot_set
    residual_vertices = set(range(n)) - pivot_set

    results = [{'depth': depth, 'n': n, 'pivot_score': pivot_score,
                'pivot_count': len(pivot_set), 'residual_size': len(residual_vertices),
                'edges_used': 1,  # the pivot edge
                'status': 'pivot'}]

    if residual_vertices:
        res_n, res_edges, res_orig = induced_subgraph(n, edges, residual_vertices)
        if res_n > 0 and res_edges:
            sub_results = recursive_pivot(k, res_n, res_edges, depth + 1, max_depth)
            results.extend(sub_results)
        else:
            results.append({'depth': depth + 1, 'n': res_n, 'edges_used': 0,
                           'pivot_score': 0, 'status': 'no_edges_residual'})

    return results


def analyze_residual_structure(k, n, edges, orig_k):
    """After one pivot elimination, analyze the residual's structure."""
    pivot_data = compute_pivot_data(n, edges)
    if not pivot_data:
        return None

    best = max(pivot_data, key=lambda r: len(r['pivot_set']))
    pivot_set = best['pivot_set']
    residual_vertices = set(range(n)) - pivot_set

    if not residual_vertices:
        return {'status': 'fully_covered', 'pivot_score': best['pivot_score']}

    res_n, res_edges, res_orig_map = induced_subgraph(n, edges, residual_vertices)

    # Map back to original vertex labels
    all_verts = sorted(range(n))
    orig_residual = [all_verts[v] for v in residual_vertices]

    structure = check_biclique_structure(res_n, res_edges, orig_residual, orig_k)
    structure['status'] = 'residual'
    structure['pivot_score'] = best['pivot_score']
    structure['pivot_count'] = len(pivot_set)
    structure['residual_n'] = res_n

    # Check if residual has a good pivot
    if res_n > 2 and res_edges:
        res_pivot = compute_pivot_data(res_n, res_edges)
        if res_pivot:
            res_best = max(res_pivot, key=lambda r: len(r['pivot_set']))
            structure['residual_pivot_score'] = res_best['pivot_score']
            structure['residual_pivot_count'] = len(res_best['pivot_set'])

    return structure


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("RESIDUAL ANALYSIS AFTER PIVOT-EDGE ELIMINATION")
    print("=" * 70)

    # Part 1: SM(k) recursion
    print("\n--- SM(k) recursive pivot ---")
    for k in range(3, 9):
        n, edges, m_minus, m_plus = generate_sm(k)
        results = recursive_pivot(k, n, edges)
        total_edges = sum(r.get('edges_used', 0) for r in results)
        max_depth = max(r['depth'] for r in results)

        print(f"\nSM({k}) (n={n}, 2n-3={2*n-3}):")
        print(f"  Recursion depth: {max_depth}")
        print(f"  Total pivot edges used: {total_edges}")
        for r in results:
            status = r['status']
            if status == 'pivot':
                print(f"    depth={r['depth']}: n={r['n']}, "
                      f"pivot covers {r['pivot_count']} ({r['pivot_score']:.3f}), "
                      f"residual={r['residual_size']}")
            else:
                print(f"    depth={r['depth']}: n={r['n']}, status={status}")

    # Part 2: SM(k) residual structure
    print("\n\n--- SM(k) residual structure ---")
    for k in range(3, 8):
        n, edges, m_minus, m_plus = generate_sm(k)
        structure = analyze_residual_structure(k, n, edges, k)

        print(f"\nSM({k}) (n={n}):")
        if structure:
            print(f"  Pivot covers: {structure.get('pivot_count', '?')} "
                  f"(score={structure.get('pivot_score', 0):.3f})")
            print(f"  Residual n: {structure.get('residual_n', '?')}")
            print(f"  Left: {structure.get('left', [])}, Right: {structure.get('right', [])}")
            print(f"  Complete bipartite: {structure.get('is_complete_bipartite', '?')}")
            print(f"  Sandwich: {structure.get('sandwich', '?')}")
            print(f"  M⁻ injective: {structure.get('m_minus_injective', '?')}")
            print(f"  M⁺ injective: {structure.get('m_plus_injective', '?')}")
            print(f"  Extremally matched: {structure.get('has_extremal_matching', '?')}")
            if 'residual_pivot_score' in structure:
                print(f"  Residual pivot: score={structure['residual_pivot_score']:.3f}, "
                      f"covers={structure['residual_pivot_count']}")

    # Part 3: Random bicliques — recursion statistics
    print("\n\n--- Random bicliques: recursion statistics ---")
    for k in range(3, 8):
        n = 2 * k
        samples = {3: 300, 4: 200, 5: 100, 6: 50, 7: 20}[k]

        depths = []
        total_edges_list = []
        residual_extremal = []

        for trial in range(samples):
            result = generate_biclique_constructive(k)
            if result is None:
                continue

            bn, bedges, bm_minus, bm_plus = result
            rec = recursive_pivot(k, bn, bedges)
            total_edges = sum(r.get('edges_used', 0) for r in rec)
            max_depth = max(r['depth'] for r in rec)
            depths.append(max_depth)
            total_edges_list.append(total_edges)

            # Check first residual structure
            structure = analyze_residual_structure(k, bn, bedges, k)
            if structure and structure.get('has_extremal_matching'):
                residual_extremal.append(True)
            else:
                residual_extremal.append(False)

        if not depths:
            print(f"\nk={k}: no valid bicliques")
            continue

        print(f"\nk={k} (n={n}, 2n-3={2*n-3}), {len(depths)} samples:")
        print(f"  Recursion depth: min={min(depths)}, max={max(depths)}, "
              f"avg={sum(depths)/len(depths):.1f}")
        print(f"  Total pivot edges: min={min(total_edges_list)}, "
              f"max={max(total_edges_list)}, "
              f"avg={sum(total_edges_list)/len(total_edges_list):.1f}")
        print(f"  Budget ratio (edges/n): "
              f"min={min(total_edges_list)/n:.2f}, "
              f"max={max(total_edges_list)/n:.2f}, "
              f"avg={sum(total_edges_list)/len(total_edges_list)/n:.2f}")
        ext_count = sum(residual_extremal)
        print(f"  First residual is extremally matched: "
              f"{ext_count}/{len(residual_extremal)} "
              f"({100*ext_count/len(residual_extremal):.1f}%)")

    # Part 4: What kind of structure does the residual have?
    print("\n\n--- Detailed residual anatomy (SM(k)) ---")
    for k in range(3, 7):
        n, edges, m_minus, m_plus = generate_sm(k)

        print(f"\nSM({k}) step-by-step:")
        current_n = n
        current_edges = edges
        depth = 0
        all_verts = list(range(n))

        while current_n > 2 and depth < 10:
            pivot_data = compute_pivot_data(current_n, current_edges)
            if not pivot_data:
                print(f"  depth {depth}: no edges, done")
                break

            best = max(pivot_data, key=lambda r: len(r['pivot_set']))
            pivot_set = best['pivot_set']
            residual_verts = set(range(current_n)) - pivot_set

            # Map to original labels
            orig_pivot = sorted([all_verts[v] for v in pivot_set])
            orig_residual = sorted([all_verts[v] for v in residual_verts])

            left_pivot = [v for v in orig_pivot if v < k]
            right_pivot = [v for v in orig_pivot if v >= k]
            left_res = [v for v in orig_residual if v < k]
            right_res = [v for v in orig_residual if v >= k]

            print(f"  depth {depth}: n={current_n}, "
                  f"pivot edge={best['edge']}, "
                  f"|In∩Out|={len(pivot_set)} (score={best['pivot_score']:.3f})")
            print(f"    Covered: {len(left_pivot)}L + {len(right_pivot)}R = "
                  f"{orig_pivot}")
            print(f"    Residual: {len(left_res)}L + {len(right_res)}R = "
                  f"{orig_residual}")

            if not residual_verts:
                print(f"    Fully covered!")
                break

            # Compute induced subgraph
            res_n, res_edges, res_map = induced_subgraph(
                current_n, current_edges, residual_verts)

            current_n = res_n
            current_edges = res_edges
            all_verts = [all_verts[v] for v in sorted(residual_verts)]
            depth += 1

        print(f"  Total recursion depth: {depth}")


if __name__ == '__main__':
    main()
