"""
Build a spanner using the pivot-edge recursion.

At each level:
1. Find the best pivot edge e = (a_{i0}, b_{j0}, t)
2. In(e) = vertices that can reach e; Out(e) = vertices reachable from e
3. Route covered vertices (In∩Out) through e:
   - Left vertices a_i: use V⁻ internal edge (a_i, a_{i0}) to reach e,
     then cross edge (a_i, b_{j0}) for exit from e
   - Right vertex b_{j0}: already at e
4. Recurse on residual (vertices not in In∩Out)

Count: routing edges + pivot edge = total spanner edges at this level.
Compare to 2n-3.
"""

import random
from collections import defaultdict

random.seed(42)


def compute_reached_by(n, edges):
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
    sorted_edges = sorted(edges, key=lambda e: e[2])
    reached_by = compute_reached_by(n, edges)
    results = []
    for eu, ew, et in edges:
        in_set = {eu, ew}
        for s in range(n):
            if s in in_set:
                continue
            if s in reached_by[eu] and reached_by[eu][s] < et:
                in_set.add(s)
            elif s in reached_by[ew] and reached_by[ew][s] < et:
                in_set.add(s)
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


def generate_sm(k):
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
    return n, edges


def generate_biclique_constructive(k, max_attempts=1000):
    n = 2 * k
    num_vminus = k * (k - 1) // 2
    num_cross = k * k
    for attempt in range(max_attempts):
        m_minus = list(range(k))
        random.shuffle(m_minus)
        m_plus = list(range(k))
        random.shuffle(m_plus)
        edge_idx = {(i, j): i * k + j for i in range(k) for j in range(k)}
        adj = [[] for _ in range(k * k)]
        in_degree = [0] * (k * k)
        for j in range(k):
            src = edge_idx[(m_minus[j], j)]
            for i in range(k):
                if i != m_minus[j]:
                    adj[src].append(edge_idx[(i, j)])
                    in_degree[edge_idx[(i, j)]] += 1
        for i in range(k):
            dst = edge_idx[(i, m_plus[i])]
            for jj in range(k):
                if jj != m_plus[i]:
                    adj[edge_idx[(i, jj)]].append(dst)
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
        return n, edges
    return None


def identify_routing_edges(n, edges, pivot_edge, pivot_set):
    """Identify which edges from the original graph are needed to route
    covered vertices through the pivot edge.

    For each vertex v in pivot_set:
    - Need a temporal path from v to one endpoint of pivot_edge arriving before t
    - Need a temporal path from one endpoint of pivot_edge to v departing after t

    Returns set of edge indices used for routing.
    """
    eu, ew, et = pivot_edge
    sorted_edges = sorted(edges, key=lambda e: e[2])

    # For IN routing: find shortest (fewest edges) temporal path
    # from each v to {eu, ew} arriving before et.
    # For OUT routing: find shortest temporal path from {eu, ew} to each v
    # departing after et.

    # Actually, in the PivotEdge.lean proof, the routing is single-hop:
    # - Left vertex a_i reaches a_{i0} via ONE V⁻ internal edge
    # - From pivot, a_i is reached via ONE cross edge (a_i, b_{j0})
    # - b_{j0} is at the pivot

    # Let's compute which single-hop edges are used.
    # But we need to be more general for non-SM bicliques.

    # For each vertex in pivot_set:
    # IN: find an edge (v, x, t') with x ∈ {eu, ew} and t' < et
    #     OR an edge (x, v, t') with x ∈ {eu, ew} and t' < et
    # OUT: find an edge (x, v, t') with x ∈ {eu, ew} and t' > et
    #      OR edge from eu/ew forward to v

    # More accurately: compute the actual temporal paths using BFS
    routing_edges = set()

    # Add the pivot edge itself
    for idx, (u, v, t) in enumerate(edges):
        if u == eu and v == ew and t == et:
            routing_edges.add(idx)
            break
        if u == ew and v == eu and t == et:
            routing_edges.add(idx)
            break

    # For each vertex in pivot_set, find IN and OUT single-hop edges
    for v in pivot_set:
        if v == eu or v == ew:
            continue

        # IN: find edge to eu or ew with timestamp < et
        best_in = None
        for idx, (u1, v1, t1) in enumerate(edges):
            if t1 >= et:
                continue
            if (u1 == v and v1 in {eu, ew}) or (v1 == v and u1 in {eu, ew}):
                if best_in is None or t1 > best_in[1]:  # latest arrival before et
                    best_in = (idx, t1)
        if best_in:
            routing_edges.add(best_in[0])

        # OUT: find edge from eu or ew with timestamp > et
        best_out = None
        for idx, (u1, v1, t1) in enumerate(edges):
            if t1 <= et:
                continue
            if (u1 in {eu, ew} and v1 == v) or (v1 in {eu, ew} and u1 == v):
                if best_out is None or t1 < best_out[1]:  # earliest departure after et
                    best_out = (idx, t1)
        if best_out:
            routing_edges.add(best_out[0])

    return routing_edges


def check_spanner(n, spanner_edges, all_edges):
    """Check if spanner_edges preserve temporal reachability of all_edges."""
    full_reach = compute_reached_by(n, all_edges)
    span_reach = compute_reached_by(n, spanner_edges)

    full_pairs = set()
    span_pairs = set()
    for v in range(n):
        for s in full_reach[v]:
            if s != v:
                full_pairs.add((s, v))
    for v in range(n):
        for s in span_reach[v]:
            if s != v:
                span_pairs.add((s, v))

    missing = full_pairs - span_pairs
    return len(missing) == 0, len(missing), len(full_pairs)


def build_pivot_spanner(n, edges, orig_k=None):
    """Build a spanner using recursive pivot construction.

    Returns: list of edge indices in the spanner, recursion log.
    """
    if orig_k is None:
        orig_k = n // 2

    # Map edges to indices
    edge_to_idx = {}
    for idx, (u, v, t) in enumerate(edges):
        edge_to_idx[(u, v, t)] = idx

    spanner_indices = set()
    log = []

    def recurse(active_verts, depth):
        active = sorted(active_verts)
        na = len(active)
        if na <= 1:
            return

        # Get edges within active vertices
        relabel = {v: i for i, v in enumerate(active)}
        sub_edges = []
        sub_to_orig = {}
        for idx, (u, v, t) in enumerate(edges):
            if u in relabel and v in relabel:
                sub_e = (relabel[u], relabel[v], t)
                sub_edges.append(sub_e)
                sub_to_orig[(relabel[u], relabel[v], t)] = idx

        if not sub_edges:
            return

        if na == 2:
            # Just need one edge
            best = min(sub_edges, key=lambda e: e[2])
            spanner_indices.add(sub_to_orig[best])
            log.append({'depth': depth, 'n': na, 'edges_added': 1, 'status': 'base'})
            return

        # Find best pivot
        pivot_data = compute_pivot_data(na, sub_edges)
        if not pivot_data:
            return

        best = max(pivot_data, key=lambda r: len(r['pivot_set']))
        pivot_set = best['pivot_set']
        pivot_edge_sub = best['edge']

        # Add routing edges (in original indices)
        routing = identify_routing_edges(na, sub_edges, pivot_edge_sub, pivot_set)
        for sub_idx in routing:
            sub_e = sub_edges[sub_idx]
            if sub_e in sub_to_orig:
                spanner_indices.add(sub_to_orig[sub_e])

        orig_pivot = [active[v] for v in pivot_set]
        orig_residual = [v for v in active if relabel[v] not in pivot_set]

        log.append({
            'depth': depth,
            'n': na,
            'pivot_count': len(pivot_set),
            'pivot_score': best['pivot_score'],
            'routing_edges': len(routing),
            'residual_size': len(orig_residual),
            'status': 'pivot',
        })

        # Recurse on residual
        if orig_residual:
            recurse(set(orig_residual), depth + 1)

    recurse(set(range(n)), 0)
    return spanner_indices, log


def main():
    print("=" * 70)
    print("PIVOT-EDGE SPANNER CONSTRUCTION")
    print("=" * 70)

    # Part 1: SM(k)
    print("\n--- SM(k): pivot spanner ---")
    for k in range(3, 9):
        n, edges = generate_sm(k)
        spanner_idx, log = build_pivot_spanner(n, edges, k)

        spanner_edges = [edges[i] for i in spanner_idx]
        is_spanner, missing, total_pairs = check_spanner(n, spanner_edges, edges)

        print(f"\nSM({k}) (n={n}, 2n-3={2*n-3}):")
        print(f"  Spanner edges: {len(spanner_idx)}")
        print(f"  Is valid spanner: {is_spanner} (missing {missing}/{total_pairs})")
        for entry in log:
            if entry['status'] == 'pivot':
                print(f"    depth={entry['depth']}: n={entry['n']}, "
                      f"pivot covers {entry['pivot_count']} ({entry['pivot_score']:.3f}), "
                      f"routing edges={entry['routing_edges']}, "
                      f"residual={entry['residual_size']}")
            else:
                print(f"    depth={entry['depth']}: n={entry['n']}, "
                      f"edges_added={entry['edges_added']}, status={entry['status']}")

    # Part 2: Random bicliques
    print("\n\n--- Random bicliques: pivot spanner ---")
    for k in range(3, 8):
        n = 2 * k
        samples = {3: 200, 4: 100, 5: 50, 6: 30, 7: 15}[k]

        sizes = []
        valid_count = 0
        invalid_count = 0

        for trial in range(samples):
            result = generate_biclique_constructive(k)
            if result is None:
                continue

            bn, bedges = result
            spanner_idx, log = build_pivot_spanner(bn, bedges, k)
            spanner_edges = [bedges[i] for i in spanner_idx]
            is_spanner, missing, total = check_spanner(bn, spanner_edges, bedges)

            sizes.append(len(spanner_idx))
            if is_spanner:
                valid_count += 1
            else:
                invalid_count += 1

        if not sizes:
            print(f"\nk={k}: no valid bicliques")
            continue

        print(f"\nk={k} (n={n}, 2n-3={2*n-3}), {len(sizes)} samples:")
        print(f"  Spanner size: min={min(sizes)}, max={max(sizes)}, "
              f"avg={sum(sizes)/len(sizes):.1f}")
        print(f"  Valid spanners: {valid_count}/{len(sizes)} "
              f"({100*valid_count/len(sizes):.1f}%)")
        if invalid_count > 0:
            print(f"  INVALID: {invalid_count}")
        within_bound = sum(1 for s in sizes if s <= 2*n - 3)
        print(f"  Within 2n-3: {within_bound}/{len(sizes)} "
              f"({100*within_bound/len(sizes):.1f}%)")


if __name__ == '__main__':
    main()
