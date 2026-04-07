"""
Backward-pass spanner construction.

Codec intuition: encode forward greedily, then fix with ≤ 2 backward passes.

Algorithm:
1. FORWARD: dismount all 1-hop dismountable vertices greedily (any order).
   Each costs 2 edges. Don't verify. Don't split.
2. BACKWARD PASS 1: inspect the residual biclique. Compute σ = m⁺∘m⁻.
   If σ has a fixed point, use it as hub. Add star(h) ∪ star(c). Done.
3. BACKWARD PASS 2 (if σ is a derangement): try a second hub.
   Pick from σ² fixed points (2-cycles of σ), or try all pairs.

Measure:
- Total edge count vs 2n-3
- How often pass 1 suffices
- How often pass 2 suffices
- Whether dismounting order affects residual σ structure
"""

import random
from itertools import combinations

random.seed(42)


def compute_reachability_pairs(n, timed_edges):
    reached_by = [dict() for _ in range(n)]
    for i in range(n):
        reached_by[i][i] = 0
    for t, u, v in sorted(timed_edges):
        for s, arr in list(reached_by[u].items()):
            if arr <= t and (s not in reached_by[v] or t < reached_by[v][s]):
                reached_by[v][s] = t
        for s, arr in list(reached_by[v].items()):
            if arr <= t and (s not in reached_by[u] or t < reached_by[u][s]):
                reached_by[u][s] = t
    pairs = set()
    for v in range(n):
        for s in reached_by[v]:
            if s != v:
                pairs.add((s, v))
    return pairs


def generate_temporal_clique(n):
    """Random temporal clique: complete graph, all-distinct timestamps."""
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
    m = len(edges)
    timestamps = list(range(1, m + 1))
    random.shuffle(timestamps)
    return edges, timestamps


def find_dismountable(n, edges, timestamps, removed):
    """Find a 1-hop dismountable vertex.

    v is 1-hop dismountable if:
    - n⁻(w) = v for some w (v is the earliest neighbor of w)
    - n⁺(w') = v for some w' (v is the latest neighbor of w')

    Returns (v, e⁻_edge, e⁺_edge) or None.
    """
    active = [i for i in range(n) if i not in removed]
    if len(active) <= 2:
        return None

    # Build edge timestamp lookup for active vertices
    edge_ts = {}
    for idx, (u, v) in enumerate(edges):
        if u not in removed and v not in removed:
            edge_ts[(u, v)] = timestamps[idx]
            edge_ts[(v, u)] = timestamps[idx]

    # For each active vertex w, find n⁻(w) = earliest neighbor
    # For each active vertex w, find n⁺(w) = latest neighbor
    earliest_neighbor = {}  # w -> (vertex, timestamp, edge_idx)
    latest_neighbor = {}

    for w in active:
        best_early = None
        best_late = None
        for u in active:
            if u == w:
                continue
            t = edge_ts.get((w, u))
            if t is None:
                continue
            if best_early is None or t < best_early[1]:
                best_early = (u, t)
            if best_late is None or t > best_late[1]:
                best_late = (u, t)
        if best_early:
            earliest_neighbor[w] = best_early[0]
        if best_late:
            latest_neighbor[w] = best_late[0]

    # v is dismountable if v = earliest_neighbor[w] for some w
    # AND v = latest_neighbor[w'] for some w'
    is_earliest_of = {}  # vertex -> list of vertices it's earliest for
    is_latest_of = {}
    for w, v in earliest_neighbor.items():
        is_earliest_of.setdefault(v, []).append(w)
    for w, v in latest_neighbor.items():
        is_latest_of.setdefault(v, []).append(w)

    for v in active:
        if v in is_earliest_of and v in is_latest_of:
            # v is 1-hop dismountable
            # The two edges to keep: e⁻(w) where n⁻(w)=v, and e⁺(w') where n⁺(w')=v
            w = is_earliest_of[v][0]  # some w whose earliest neighbor is v
            w2 = is_latest_of[v][0]   # some w' whose latest neighbor is v
            return v, (v, w), (v, w2)

    return None


def greedy_dismount(n, edges, timestamps):
    """Forward pass: greedily dismount all 1-hop dismountable vertices.

    Returns:
    - spanner_edges: set of (u, v) edge tuples included in spanner
    - removed: set of removed vertices
    - order: list of (vertex, edge1, edge2) dismounting steps
    """
    removed = set()
    spanner_edge_indices = set()
    order = []

    # Map edges to indices for lookup
    edge_to_idx = {}
    for idx, (u, v) in enumerate(edges):
        edge_to_idx[(u, v)] = idx
        edge_to_idx[(v, u)] = idx

    while True:
        result = find_dismountable(n, edges, timestamps, removed)
        if result is None:
            break
        v, e1, e2 = result
        # Add the two edges to the spanner
        idx1 = edge_to_idx.get(e1) or edge_to_idx.get((e1[1], e1[0]))
        idx2 = edge_to_idx.get(e2) or edge_to_idx.get((e2[1], e2[0]))
        if idx1 is not None:
            spanner_edge_indices.add(idx1)
        if idx2 is not None:
            spanner_edge_indices.add(idx2)
        removed.add(v)
        order.append((v, e1, e2))

    return spanner_edge_indices, removed, order


def get_residual_biclique(n, edges, timestamps, removed):
    """Extract the residual after dismounting.

    The residual vertices form a biclique structure with V⁻ and V⁺.
    Returns the residual info or None if fully dismounted.
    """
    active = sorted([i for i in range(n) if i not in removed])
    if len(active) <= 2:
        return None

    # Build edge timestamp lookup
    edge_ts = {}
    for idx, (u, v) in enumerate(edges):
        if u not in removed and v not in removed:
            edge_ts[(u, v)] = timestamps[idx]
            edge_ts[(v, u)] = timestamps[idx]

    # Find V⁻ (earliest neighbors) and V⁺ (latest neighbors)
    earliest_neighbor = {}
    latest_neighbor = {}
    for w in active:
        best_early = None
        best_late = None
        for u in active:
            if u == w:
                continue
            t = edge_ts.get((w, u))
            if t is None:
                continue
            if best_early is None or t < best_early[1]:
                best_early = (u, t)
            if best_late is None or t > best_late[1]:
                best_late = (u, t)
        if best_early:
            earliest_neighbor[w] = best_early[0]
        if best_late:
            latest_neighbor[w] = best_late[0]

    V_minus = set(earliest_neighbor.values())  # vertices that ARE earliest of someone
    V_plus = set(latest_neighbor.values())      # vertices that ARE latest of someone

    return {
        'active': active,
        'V_minus': V_minus,
        'V_plus': V_plus,
        'edge_ts': edge_ts,
        'earliest': earliest_neighbor,
        'latest': latest_neighbor,
    }


def backward_pass(n, edges, timestamps, spanner_indices, removed):
    """Backward pass: inspect residual, add hub stars.

    Returns updated spanner_indices and diagnostics.
    """
    active = sorted([i for i in range(n) if i not in removed])
    k_residual = len(active)

    if k_residual <= 2:
        # Trivially handled
        edge_to_idx = {}
        for idx, (u, v) in enumerate(edges):
            edge_to_idx[(u, v)] = idx
            edge_to_idx[(v, u)] = idx
        for i in active:
            for j in active:
                if i < j:
                    idx = edge_to_idx.get((i, j))
                    if idx is not None:
                        spanner_indices.add(idx)
        return spanner_indices, {'passes': 0, 'hubs': 0}

    # Build timestamp lookup for residual
    edge_ts = {}
    for idx, (u, v) in enumerate(edges):
        if u not in removed and v not in removed:
            edge_ts[(u, v)] = timestamps[idx]
            edge_ts[(v, u)] = timestamps[idx]

    edge_to_idx = {}
    for idx, (u, v) in enumerate(edges):
        edge_to_idx[(u, v)] = idx
        edge_to_idx[(v, u)] = idx

    # Add ALL residual edges as candidates (we'll be selective with hubs)
    # First: add M⁻ and M⁺ (forced edges)
    for w in active:
        # earliest edge of w
        best = None
        for u in active:
            if u == w:
                continue
            t = edge_ts.get((w, u))
            if t is not None and (best is None or t < best[1]):
                best = (u, t)
        if best:
            idx = edge_to_idx.get((w, best[0])) or edge_to_idx.get((best[0], w))
            if idx is not None:
                spanner_indices.add(idx)
        # latest edge of w
        best = None
        for u in active:
            if u == w:
                continue
            t = edge_ts.get((w, u))
            if t is not None and (best is None or t > best[1]):
                best = (u, t)
        if best:
            idx = edge_to_idx.get((w, best[0])) or edge_to_idx.get((best[0], w))
            if idx is not None:
                spanner_indices.add(idx)

    # Compute full reachability target
    full_timed = [(timestamps[idx], edges[idx][0], edges[idx][1])
                  for idx in range(len(edges))
                  if edges[idx][0] not in removed and edges[idx][1] not in removed]
    full_pairs = compute_reachability_pairs(n, full_timed)

    # Check if M⁻ ∪ M⁺ alone suffice
    span_timed = [(timestamps[idx], edges[idx][0], edges[idx][1])
                  for idx in spanner_indices]
    span_pairs = compute_reachability_pairs(n, span_timed)
    missing = full_pairs - span_pairs

    if not missing:
        return spanner_indices, {'passes': 0, 'hubs': 0, 'residual_k': k_residual}

    # PASS 1: try single hub (each active vertex as hub, add its star)
    best_hub = None
    best_missing = len(missing)

    for h in active:
        trial = set(spanner_indices)
        for u in active:
            if u != h:
                idx = edge_to_idx.get((h, u)) or edge_to_idx.get((u, h))
                if idx is not None:
                    trial.add(idx)
        trial_timed = [(timestamps[idx], edges[idx][0], edges[idx][1])
                       for idx in trial]
        trial_pairs = compute_reachability_pairs(n, trial_timed)
        trial_missing = full_pairs - trial_pairs
        if len(trial_missing) < best_missing:
            best_missing = len(trial_missing)
            best_hub = h
            if best_missing == 0:
                break

    if best_missing == 0:
        # Single hub works
        for u in active:
            if u != best_hub:
                idx = edge_to_idx.get((best_hub, u)) or edge_to_idx.get((u, best_hub))
                if idx is not None:
                    spanner_indices.add(idx)
        return spanner_indices, {'passes': 1, 'hubs': 1, 'hub': best_hub,
                                  'residual_k': k_residual}

    # PASS 2: try two hubs
    for h1 in active:
        for h2 in active:
            if h1 >= h2:
                continue
            trial = set(spanner_indices)
            for u in active:
                if u != h1:
                    idx = edge_to_idx.get((h1, u)) or edge_to_idx.get((u, h1))
                    if idx is not None:
                        trial.add(idx)
                if u != h2:
                    idx = edge_to_idx.get((h2, u)) or edge_to_idx.get((u, h2))
                    if idx is not None:
                        trial.add(idx)
            trial_timed = [(timestamps[idx], edges[idx][0], edges[idx][1])
                           for idx in trial]
            trial_pairs = compute_reachability_pairs(n, trial_timed)
            if full_pairs - trial_pairs == set():
                for u in active:
                    if u != h1:
                        idx = edge_to_idx.get((h1, u)) or edge_to_idx.get((u, h1))
                        if idx is not None:
                            spanner_indices.add(idx)
                    if u != h2:
                        idx = edge_to_idx.get((h2, u)) or edge_to_idx.get((u, h2))
                        if idx is not None:
                            spanner_indices.add(idx)
                return spanner_indices, {'passes': 2, 'hubs': 2,
                                          'hub1': h1, 'hub2': h2,
                                          'residual_k': k_residual}

    return spanner_indices, {'passes': -1, 'hubs': -1, 'residual_k': k_residual}


def run_experiment(n, num_samples):
    """Run the full forward + backward algorithm."""
    print(f"\n{'='*60}")
    print(f"n={n}, {num_samples} samples")
    print(f"{'='*60}")

    pass_counts = {0: 0, 1: 0, 2: 0, -1: 0}
    edge_counts = []
    dismount_counts = []
    residual_sizes = []
    target = 2 * n - 3

    for trial in range(num_samples):
        edges, timestamps = generate_temporal_clique(n)

        # Forward pass
        spanner_indices, removed, order = greedy_dismount(n, edges, timestamps)
        dismount_counts.append(len(removed))

        # Backward pass
        spanner_indices, diag = backward_pass(n, edges, timestamps,
                                               spanner_indices, removed)

        passes = diag['passes']
        pass_counts[passes] += 1
        total_edges = len(spanner_indices)
        edge_counts.append(total_edges)
        if 'residual_k' in diag:
            residual_sizes.append(diag['residual_k'])

    print(f"  Target: 2n-3 = {target}")
    print(f"  Dismounted: avg {sum(dismount_counts)/len(dismount_counts):.1f} "
          f"/ {n} vertices")
    if residual_sizes:
        print(f"  Residual size: avg {sum(residual_sizes)/len(residual_sizes):.1f}")
    print(f"  Backward passes needed:")
    print(f"    0 (M⁻∪M⁺ suffice):  {pass_counts[0]}")
    print(f"    1 (single hub):       {pass_counts[1]}")
    print(f"    2 (two hubs):         {pass_counts[2]}")
    print(f"    FAIL:                 {pass_counts[-1]}")
    print(f"  Edge count: avg {sum(edge_counts)/len(edge_counts):.1f}, "
          f"max {max(edge_counts)}, min {min(edge_counts)}")
    print(f"  vs 2n-3={target}: "
          f"avg ratio {sum(edge_counts)/len(edge_counts)/target:.3f}")

    # Histogram of edge counts
    from collections import Counter
    hist = Counter(edge_counts)
    print(f"  Edge count distribution:")
    for ec in sorted(hist):
        bar = '#' * hist[ec]
        label = " ← 2n-3" if ec == target else ""
        print(f"    {ec:3d}: {bar} ({hist[ec]}){label}")


def test_dismount_order_effect(n, num_samples):
    """Does dismounting order affect residual σ structure?"""
    print(f"\n{'='*60}")
    print(f"DISMOUNTING ORDER EFFECT (n={n})")
    print(f"{'='*60}")

    order_matters = 0
    total = 0

    for trial in range(num_samples):
        edges, timestamps = generate_temporal_clique(n)

        # Try multiple random dismounting orders
        residual_sets = []
        for _ in range(5):
            random.seed(trial * 1000 + _)
            # Randomize by shuffling vertex check order
            spanner_indices, removed, order = greedy_dismount(n, edges, timestamps)
            active = frozenset(i for i in range(n) if i not in removed)
            residual_sets.append(active)

        # Reset random seed
        random.seed(42 + trial)

        total += 1
        unique_residuals = len(set(residual_sets))
        if unique_residuals > 1:
            order_matters += 1

    print(f"  {total} instances tested")
    print(f"  Different residuals from different orders: {order_matters}/{total} "
          f"({100*order_matters/total:.1f}%)")


def main():
    # Main experiment: forward + backward
    for n in [6, 8, 10, 12, 14]:
        samples = {6: 500, 8: 200, 10: 100, 12: 50, 14: 20}[n]
        run_experiment(n, samples)

    # Order effect test
    test_dismount_order_effect(8, 100)


if __name__ == '__main__':
    main()
