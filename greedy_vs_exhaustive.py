"""
Greedy vs Exhaustive: When a hub fails with greedy tree, is it a greedy artifact
or a genuine impossibility?

For each vertex v:
  - Greedy: star(v) + greedy edge addition (existing approach)
  - Exhaustive: star(v) + ALL spanning trees of K_{n-1} on non-hub vertices

Uses Prüfer sequences to enumerate all spanning trees of K_{n-1}.

Question: Are there vertices where greedy fails but some tree works?
"""

import random
import itertools
import time


def make_edges(n):
    return [(i, j) for i in range(n) for j in range(i + 1, n)]


def compute_reachability(n, timed_edges):
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


def star_tree_spans_greedy(n, edges, timestamps, hub):
    """star(hub) + greedy edge addition from non-hub edges."""
    m = len(edges)
    timed = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in range(m)])
    target = compute_reachability(n, timed)

    star_idx = [i for i, (u, v) in enumerate(edges) if u == hub or v == hub]
    current = set(star_idx)

    def current_reach():
        sub = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in current])
        return compute_reachability(n, sub)

    tree_candidates = [i for i in range(m) if i not in star_idx]

    for _ in range(n - 2):
        cr = current_reach()
        if cr == target:
            break
        current_covered = sum(bin(r).count('1') for r in cr)
        best_edge = None
        best_gain = -1
        for idx in tree_candidates:
            if idx in current:
                continue
            trial = current | {idx}
            sub = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in trial])
            tr = compute_reachability(n, sub)
            gain = sum(bin(r).count('1') for r in tr) - current_covered
            if gain > best_gain:
                best_gain = gain
                best_edge = idx
        if best_edge is None or best_gain <= 0:
            break
        current.add(best_edge)

    return current_reach() == target


def prufer_to_tree(prufer, nodes):
    """
    Convert a Prüfer sequence to a list of edges on the given node set.
    nodes: list of k node labels
    prufer: sequence of length k-2, each entry is an index into nodes
    Returns list of (u, v) edges.
    """
    k = len(nodes)
    degree = [1] * k
    for p in prufer:
        degree[p] += 1

    edges = []
    seq = list(prufer)
    remaining = list(range(k))

    for p in seq:
        # Find the lowest-index leaf
        leaf = next(i for i in remaining if degree[i] == 1)
        edges.append((nodes[leaf], nodes[p]))
        degree[leaf] -= 1
        degree[p] -= 1
        remaining.remove(leaf)

    # Last two nodes with degree 1
    last = [i for i in remaining if degree[i] == 1]
    edges.append((nodes[last[0]], nodes[last[1]]))

    return edges


def all_spanning_trees(node_list):
    """
    Enumerate all spanning trees of K_k where k = len(node_list).
    Uses Prüfer sequences: k^(k-2) trees total.
    For k=1 or k=2, return trivially.
    """
    k = len(node_list)
    if k == 1:
        yield []
        return
    if k == 2:
        yield [(node_list[0], node_list[1])]
        return
    # Prüfer sequences: (k-2)-tuples with entries in range(k)
    for prufer in itertools.product(range(k), repeat=k - 2):
        yield prufer_to_tree(prufer, node_list)


def star_tree_spans_exhaustive(n, edges, timestamps, hub):
    """
    star(hub) + ALL spanning trees of K_{n-1} on non-hub vertices.
    Returns True if ANY tree works.
    """
    m = len(edges)
    timed_full = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in range(m)])
    target = compute_reachability(n, timed_full)

    # Build edge index: (u,v) -> edge index in edges list (u < v)
    edge_index = {}
    for i, (u, v) in enumerate(edges):
        edge_index[(u, v)] = i
        edge_index[(v, u)] = i

    star_idx = set(i for i, (u, v) in enumerate(edges) if u == hub or v == hub)
    non_hub_nodes = [v for v in range(n) if v != hub]

    # Check if star alone already spans
    def check_subset(idx_set):
        sub = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in idx_set])
        return compute_reachability(n, sub) == target

    if check_subset(star_idx):
        return True

    for tree_edges in all_spanning_trees(non_hub_nodes):
        # Map tree edges to edge indices
        idx_set = set(star_idx)
        for (u, v) in tree_edges:
            key = (min(u, v), max(u, v))
            idx_set.add(edge_index[key])
        if check_subset(idx_set):
            return True

    return False


def run(n, num_samples):
    edges = make_edges(n)
    m = len(edges)
    non_hub_size = n - 1
    num_trees = non_hub_size ** max(0, non_hub_size - 2) if non_hub_size >= 2 else 1

    print(f"\n{'='*60}")
    print(f"n={n}: K_{n}, {m} edges, Prüfer trees on K_{non_hub_size}: {num_trees} per hub")
    print(f"Samples: {num_samples}")
    print(f"{'='*60}")

    # Counters per vertex across all samples:
    #   greedy_ok, exhaustive_ok, greedy_fail_exhaust_ok, both_fail
    total_greedy_ok = 0
    total_exhaust_ok = 0
    total_greedy_fail_exhaust_ok = 0  # greedy artifact
    total_both_fail = 0               # genuine hub failure
    total_vertex_checks = 0

    # Per-instance: does ANY vertex work?
    instance_greedy_any = 0
    instance_exhaust_any = 0

    start = time.time()

    for trial in range(num_samples):
        ts = list(range(1, m + 1))
        random.shuffle(ts)

        greedy_any = False
        exhaust_any = False

        for v in range(n):
            g_ok = star_tree_spans_greedy(n, edges, ts, v)
            e_ok = star_tree_spans_exhaustive(n, edges, ts, v)

            total_vertex_checks += 1
            if g_ok:
                total_greedy_ok += 1
            if e_ok:
                total_exhaust_ok += 1
            if not g_ok and e_ok:
                total_greedy_fail_exhaust_ok += 1
            if not g_ok and not e_ok:
                total_both_fail += 1

            if g_ok:
                greedy_any = True
            if e_ok:
                exhaust_any = True

        if greedy_any:
            instance_greedy_any += 1
        if exhaust_any:
            instance_exhaust_any += 1

        if (trial + 1) % max(1, num_samples // 5) == 0:
            elapsed = time.time() - start
            pct = (trial + 1) / num_samples * 100
            print(f"  {trial+1:>6}/{num_samples} ({pct:.0f}%)  elapsed={elapsed:.1f}s  "
                  f"greedy_artifact={total_greedy_fail_exhaust_ok}  "
                  f"genuine_fail={total_both_fail}")

    elapsed = time.time() - start
    V = total_vertex_checks

    print(f"\nResults for n={n} ({num_samples} samples, {elapsed:.1f}s):")
    print(f"  Total vertex checks:         {V}")
    print(f"  Greedy OK:                   {total_greedy_ok:>8}  ({total_greedy_ok/V*100:.2f}%)")
    print(f"  Exhaustive OK:               {total_exhaust_ok:>8}  ({total_exhaust_ok/V*100:.2f}%)")
    print(f"  Greedy fail, exhaust OK:     {total_greedy_fail_exhaust_ok:>8}  ({total_greedy_fail_exhaust_ok/V*100:.2f}%)  <- greedy artifact")
    print(f"  Both fail (genuine):         {total_both_fail:>8}  ({total_both_fail/V*100:.2f}%)  <- genuine hub failure")
    print(f"  Greedy agree rate:           {(V - total_greedy_fail_exhaust_ok)/V*100:.4f}%")
    print(f"  Instances w/ greedy hub:     {instance_greedy_any}/{num_samples} ({instance_greedy_any/num_samples*100:.2f}%)")
    print(f"  Instances w/ exhaust hub:    {instance_exhaust_any}/{num_samples} ({instance_exhaust_any/num_samples*100:.2f}%)")
    print()


def main():
    random.seed(42)
    print("Greedy vs Exhaustive Hub Spanning")
    print("Question: When greedy fails, is it a greedy artifact or genuine impossibility?")

    for n, samples in [(4, 10000), (5, 10000), (6, 3000)]:
        run(n, samples)

    print("Done.")


if __name__ == "__main__":
    main()
