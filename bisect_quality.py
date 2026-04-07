"""
Bisect quality of temporal reachability DAGs for extremally matched bicliques.

Checks whether the temporal reachability DAG always has a good "median"
edge (git bisect style), and computes Dilworth statistics.

For edge e=(u,w) at time t:
  In(e)  = vertices that can reach u or w via temporal path arriving before t
  Out(e) = vertices reachable from u or w via temporal path departing at time t
  bisect_score(e) = |In(e) ∩ Out(e)| / n

For vertex v:
  ancestors(v) = vertices that can temporally reach v
  descendants(v) = vertices temporally reachable from v
  vertex_bisect(v) = min(|ancestors(v)|, |descendants(v)|) / n
"""

import random
from collections import defaultdict, deque
from itertools import permutations

random.seed(42)


# ---------------------------------------------------------------------------
# Temporal reachability
# ---------------------------------------------------------------------------

def compute_reached_by(n, edges):
    """reached_by[v][s] = earliest arrival time of s at v.
    Strict temporal: must have arrival < edge time to traverse."""
    sorted_edges = sorted(edges, key=lambda e: e[2])
    reached_by = [dict() for _ in range(n)]
    for v in range(n):
        reached_by[v][v] = -1  # present before all time

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
    """reachable_from[s] = set of vertices reachable from s temporally."""
    reached_by = compute_reached_by(n, edges)
    reachable_from = [set() for _ in range(n)]
    for v in range(n):
        for s in reached_by[v]:
            reachable_from[s].add(v)
    return reachable_from, reached_by


# ---------------------------------------------------------------------------
# Edge bisect scores
# ---------------------------------------------------------------------------

def compute_edge_bisect_scores(n, edges, k):
    """For each edge, compute In(e), Out(e), and bisect_score.
    Also classify edge type: V- internal, cross, V+ internal."""
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

        # Out(e): vertices reachable from {eu, ew} using edges with time > et
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
        intersection = in_set & out_set
        bisect = len(intersection) / n

        # Edge type
        if eu < k and ew < k:
            etype = "V-"
        elif eu >= k and ew >= k:
            etype = "V+"
        elif (eu < k and ew >= k) or (eu >= k and ew < k):
            etype = "cross"
        else:
            etype = "?"

        results.append({
            'edge': (eu, ew, et),
            'in_size': len(in_set),
            'out_size': len(out_set),
            'intersection': len(intersection),
            'bisect_score': bisect,
            'type': etype,
        })

    return results


# ---------------------------------------------------------------------------
# Vertex bisect scores (classic DAG median)
# ---------------------------------------------------------------------------

def compute_vertex_bisect_scores(n, edges):
    """For each vertex v:
      ancestors(v) = vertices that can temporally reach v (including v)
      descendants(v) = vertices reachable from v (including v)
      vertex_bisect(v) = min(|ancestors|, |descendants|) / n
    """
    reachable_from, reached_by = compute_reachable_from(n, edges)
    results = []
    for v in range(n):
        ancestors = set(reached_by[v].keys())  # sources that can reach v
        descendants = reachable_from[v]
        vb = min(len(ancestors), len(descendants)) / n
        results.append({
            'vertex': v,
            'ancestors': len(ancestors),
            'descendants': len(descendants),
            'vertex_bisect': vb,
        })
    return results


# ---------------------------------------------------------------------------
# Dilworth statistics
# ---------------------------------------------------------------------------

def compute_dilworth(n, edges):
    """Compute Dilworth statistics on the temporal reachability relation.

    Since temporal reachability is NOT antisymmetric (u can reach v AND v can
    reach u), we first compute the antisymmetric quotient:
    - SCC decomposition of the reachability relation
    - The DAG of SCCs is the partial order
    - Chain = longest path in SCC DAG (counting vertices, not SCCs)
    - Width = max antichain in the SCC partial order

    Also reports: number of SCCs, largest SCC size.
    """
    reachable_from, reached_by = compute_reachable_from(n, edges)

    # Build strict reachability
    reach = [set() for _ in range(n)]
    for s in range(n):
        reach[s] = reachable_from[s] - {s}

    # SCC decomposition (Tarjan's or simple: u and v in same SCC iff mutual reach)
    visited = [False] * n
    scc_id = [-1] * n
    num_sccs = 0
    for u in range(n):
        if scc_id[u] >= 0:
            continue
        # BFS to find all vertices mutually reachable with u
        component = {u}
        for v in reach[u]:
            if v in reach[u] and u in reach[v]:
                component.add(v)
        for v in component:
            scc_id[v] = num_sccs
        num_sccs += 1

    scc_sizes = [0] * num_sccs
    for v in range(n):
        scc_sizes[scc_id[v]] += 1

    # DAG of SCCs
    scc_reach = [set() for _ in range(num_sccs)]
    for u in range(n):
        for v in reach[u]:
            if scc_id[u] != scc_id[v]:
                scc_reach[scc_id[u]].add(scc_id[v])

    # Longest chain in SCC DAG (by number of original vertices along the path)
    # Use DP: for each SCC in topological order, longest chain ending there
    # Topological sort by reachability count
    in_count = [0] * num_sccs
    for s in range(num_sccs):
        for t in scc_reach[s]:
            in_count[t] += 1
    queue = [s for s in range(num_sccs) if in_count[s] == 0]
    topo = []
    while queue:
        s = queue.pop(0)
        topo.append(s)
        for t in scc_reach[s]:
            in_count[t] -= 1
            if in_count[t] == 0:
                queue.append(t)

    # DP for longest chain (sum of SCC sizes along a path)
    chain_dp = [0] * num_sccs
    for s in topo:
        chain_dp[s] = max(chain_dp[s], scc_sizes[s])
        for t in scc_reach[s]:
            chain_dp[t] = max(chain_dp[t], chain_dp[s] + scc_sizes[t])

    longest_chain = max(chain_dp) if chain_dp else 0

    # Width = max antichain in SCC DAG
    # For SCC DAG, use Dilworth: width = n_sccs - max_matching on transitive reduction
    # But since SCCs can be large, the "width" in terms of original vertices
    # is the max antichain weight (sum of SCC sizes in antichain).
    # For simplicity, report both SCC-level and vertex-level metrics.

    # Width in terms of number of SCCs that form an antichain
    scc_dag_reach = [set() for _ in range(num_sccs)]
    for s in range(num_sccs):
        # Transitive closure of SCC DAG
        visited_s = set()
        stack = list(scc_reach[s])
        while stack:
            t = stack.pop()
            if t in visited_s:
                continue
            visited_s.add(t)
            stack.extend(scc_reach[t])
        scc_dag_reach[s] = visited_s

    # Simple antichain: greedy (vertices not comparable to any selected)
    comparable = [[False] * num_sccs for _ in range(num_sccs)]
    for s in range(num_sccs):
        for t in scc_dag_reach[s]:
            comparable[s][t] = True
            comparable[t][s] = True

    # Max antichain = max independent set in comparability graph
    # For small num_sccs, brute force
    if num_sccs <= 20:
        best_antichain = 0
        best_weight = 0
        for mask in range(1 << num_sccs):
            nodes = [s for s in range(num_sccs) if mask & (1 << s)]
            ok = True
            for i in range(len(nodes)):
                for j in range(i+1, len(nodes)):
                    if comparable[nodes[i]][nodes[j]]:
                        ok = False
                        break
                if not ok:
                    break
            if ok:
                weight = sum(scc_sizes[s] for s in nodes)
                if weight > best_weight:
                    best_weight = weight
                    best_antichain = len(nodes)
        width = best_weight
    else:
        width = max(scc_sizes)  # lower bound

    return longest_chain, width, num_sccs, max(scc_sizes) if scc_sizes else 0


# ---------------------------------------------------------------------------
# SM(k) construction
# ---------------------------------------------------------------------------

def generate_sm(k):
    """SM(k): V-={0..k-1}, V+={k..2k-1}.
    Internal V- first, cross by diagonal, then internal V+."""
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


# ---------------------------------------------------------------------------
# Random extremally matched biclique (sandwich property)
# ---------------------------------------------------------------------------

def generate_biclique_constructive(k, max_attempts=1000):
    """Generate a random extremally matched biclique with sandwich property.
    Returns (n, edges) or None."""
    n = 2 * k
    num_vminus = k * (k - 1) // 2
    num_cross = k * k
    num_vplus = k * (k - 1) // 2

    for attempt in range(max_attempts):
        m_minus = list(range(k))
        random.shuffle(m_minus)
        m_plus = list(range(k))
        random.shuffle(m_plus)

        edge_list_cross = [(i, j) for i in range(k) for j in range(k)]
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


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def analyze(k, n, edges, label=""):
    """Full analysis: edge bisect, vertex bisect, Dilworth."""
    edge_results = compute_edge_bisect_scores(n, edges, k)
    vertex_results = compute_vertex_bisect_scores(n, edges)

    best_edge = max(edge_results, key=lambda r: r['bisect_score'])
    best_vertex = max(vertex_results, key=lambda r: r['vertex_bisect'])

    chain, width, num_sccs, max_scc = compute_dilworth(n, edges)

    return {
        'best_edge_bisect': best_edge['bisect_score'],
        'best_edge': best_edge,
        'best_vertex_bisect': best_vertex['vertex_bisect'],
        'best_vertex': best_vertex,
        'chain': chain,
        'width': width,
        'num_sccs': num_sccs,
        'max_scc': max_scc,
        'edge_results': edge_results,
        'vertex_results': vertex_results,
    }


def print_analysis(k, info, label=""):
    n = 2 * k
    be = info['best_edge']
    bv = info['best_vertex']
    print(f"  Best EDGE bisect:   {be['bisect_score']:.4f}  "
          f"(type={be['type']}, edge={be['edge']}, "
          f"|In|={be['in_size']}, |Out|={be['out_size']}, "
          f"|In∩Out|={be['intersection']})")
    print(f"  Best VERTEX bisect: {bv['vertex_bisect']:.4f}  "
          f"(v={bv['vertex']}, |anc|={bv['ancestors']}, "
          f"|desc|={bv['descendants']})")
    print(f"  Dilworth: chain={info['chain']}, width={info['width']}, "
          f"SCCs={info['num_sccs']}, max_SCC={info['max_scc']}, "
          f"chain×width={info['chain']*info['width']} vs n={n}")
    print(f"  Edge bisect ≥ 0.5: {be['bisect_score'] >= 0.5}")

    # Best by edge type
    by_type = defaultdict(list)
    for r in info['edge_results']:
        by_type[r['type']].append(r['bisect_score'])
    for t in ['V-', 'cross', 'V+']:
        if by_type[t]:
            scores = by_type[t]
            print(f"    {t:6s}: max={max(scores):.4f}, "
                  f"avg={sum(scores)/len(scores):.4f}, count={len(scores)}")


def main():
    print("=" * 72)
    print("BISECT QUALITY OF TEMPORAL REACHABILITY DAGs")
    print("=" * 72)

    # ------------------------------------------------------------------
    # Part 1: SM(k) for k=3..7
    # ------------------------------------------------------------------
    print("\n" + "-" * 72)
    print("PART 1: SM(k), k=3..7")
    print("-" * 72)

    for k in range(3, 8):
        n, edges = generate_sm(k)
        print(f"\n--- SM({k}), n={n}, edges={len(edges)} ---")
        info = analyze(k, n, edges)
        print_analysis(k, info)

    # ------------------------------------------------------------------
    # Part 2: Random extremally matched bicliques, k=3,4,5
    # ------------------------------------------------------------------
    print("\n" + "-" * 72)
    print("PART 2: Random extremally matched bicliques (500 samples)")
    print("-" * 72)

    for k in range(3, 6):
        n = 2 * k
        num_samples = 500
        print(f"\n--- k={k}, n={n}, {num_samples} samples ---")

        edge_bisects = []
        vertex_bisects = []
        chains = []
        widths = []
        num_sccs_list = []
        best_types = defaultdict(int)
        failures = 0
        worst_edge_bisect = None

        for trial in range(num_samples):
            result = generate_biclique_constructive(k)
            if result is None:
                failures += 1
                continue

            bn, bedges = result
            info = analyze(k, bn, bedges)

            eb = info['best_edge_bisect']
            vb = info['best_vertex_bisect']
            edge_bisects.append(eb)
            vertex_bisects.append(vb)
            chains.append(info['chain'])
            widths.append(info['width'])
            num_sccs_list.append(info['num_sccs'])
            best_types[info['best_edge']['type']] += 1

            if worst_edge_bisect is None or eb < worst_edge_bisect:
                worst_edge_bisect = eb

        valid = len(edge_bisects)
        if valid == 0:
            print("  No valid bicliques generated!")
            continue

        print(f"  Generated: {valid}/{num_samples} (failures={failures})")
        print(f"  Edge bisect:   min={min(edge_bisects):.4f}, "
              f"max={max(edge_bisects):.4f}, "
              f"avg={sum(edge_bisects)/valid:.4f}")
        print(f"  Vertex bisect: min={min(vertex_bisects):.4f}, "
              f"max={max(vertex_bisects):.4f}, "
              f"avg={sum(vertex_bisects)/valid:.4f}")
        print(f"  Chain:  min={min(chains)}, max={max(chains)}, "
              f"avg={sum(chains)/valid:.1f}")
        print(f"  Width:  min={min(widths)}, max={max(widths)}, "
              f"avg={sum(widths)/valid:.1f}")
        print(f"  Chain×Width vs n={n}: "
              f"min={min(c*w for c,w in zip(chains,widths))}, "
              f"max={max(c*w for c,w in zip(chains,widths))}")
        print(f"  SCCs:   min={min(num_sccs_list)}, max={max(num_sccs_list)}, "
              f"avg={sum(num_sccs_list)/valid:.1f}")
        print(f"  Best edge type distribution: {dict(best_types)}")
        print(f"  ALL edge bisect ≥ 0.5: "
              f"{all(eb >= 0.5 for eb in edge_bisects)}")
        print(f"  ALL vertex bisect ≥ 0.5: "
              f"{all(vb >= 0.5 for vb in vertex_bisects)}")

        # Histogram of edge bisect scores
        buckets = defaultdict(int)
        for eb in edge_bisects:
            b = int(eb * 20) / 20
            buckets[b] += 1
        print(f"  Edge bisect distribution (0.05 bins):")
        for b in sorted(buckets.keys()):
            bar = '#' * min(buckets[b], 60)
            print(f"    [{b:.2f}, {b+0.05:.2f}): {buckets[b]:4d} {bar}")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print("If max edge bisect ≥ 0.5 always holds, one test eliminates half")
    print("the search space — the git bisect guarantee for temporal DAGs.")


if __name__ == '__main__':
    main()
