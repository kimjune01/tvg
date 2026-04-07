"""
Deferred-commit spanner construction.

Forward pass: identify dismounting order but DON'T commit edges.
Backward pass: add hub stars first, then only add dismounting edges
that aren't already covered by the hubs.

The insight: hub stars cover some dismounting edges for free.
Paying 2 edges per dismount AND full hub stars double-counts.
"""

import random

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
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
    m = len(edges)
    timestamps = list(range(1, m + 1))
    random.shuffle(timestamps)
    return edges, timestamps


def find_dismountable(n, edges, timestamps, removed):
    """Find a 1-hop dismountable vertex. Returns (v, (v,w), (v,w')) or None."""
    active = [i for i in range(n) if i not in removed]
    if len(active) <= 2:
        return None

    edge_ts = {}
    for idx, (u, v) in enumerate(edges):
        if u not in removed and v not in removed:
            edge_ts[(u, v)] = timestamps[idx]
            edge_ts[(v, u)] = timestamps[idx]

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

    is_earliest_of = {}
    is_latest_of = {}
    for w, v in earliest_neighbor.items():
        is_earliest_of.setdefault(v, []).append(w)
    for w, v in latest_neighbor.items():
        is_latest_of.setdefault(v, []).append(w)

    for v in active:
        if v in is_earliest_of and v in is_latest_of:
            w = is_earliest_of[v][0]
            w2 = is_latest_of[v][0]
            return v, (v, w), (v, w2)
    return None


def identify_dismount_order(n, edges, timestamps):
    """Forward pass: just identify the dismounting order and edges.
    Don't commit anything yet."""
    removed = set()
    dismount_plan = []  # [(vertex, edge1, edge2), ...]

    while True:
        result = find_dismountable(n, edges, timestamps, removed)
        if result is None:
            break
        v, e1, e2 = result
        dismount_plan.append((v, e1, e2))
        removed.add(v)

    residual = sorted([i for i in range(n) if i not in removed])
    return dismount_plan, residual


def build_spanner_deferred(n, edges, timestamps, dismount_plan, residual):
    """Backward pass: build hub stars first, then add dismounting edges
    only where needed."""
    edge_to_idx = {}
    for idx, (u, v) in enumerate(edges):
        edge_to_idx[(u, v)] = idx
        edge_to_idx[(v, u)] = idx

    # Full reachability target
    full_timed = [(timestamps[idx], edges[idx][0], edges[idx][1])
                  for idx in range(len(edges))]
    full_pairs = compute_reachability_pairs(n, full_timed)

    def current_pairs(indices):
        timed = [(timestamps[idx], edges[idx][0], edges[idx][1])
                 for idx in indices]
        return compute_reachability_pairs(n, timed)

    def add_star(spanner, vertex):
        for u in range(n):
            if u != vertex:
                idx = edge_to_idx.get((vertex, u)) or edge_to_idx.get((u, vertex))
                if idx is not None:
                    spanner.add(idx)

    # Start empty
    spanner = set()

    # STEP 1: Add forced edges (earliest and latest of each vertex in full graph)
    for w in range(n):
        best_early = None
        best_late = None
        for u in range(n):
            if u == w:
                continue
            key = (w, u) if (w, u) in edge_to_idx else (u, w)
            idx = edge_to_idx[key]
            t = timestamps[idx]
            if best_early is None or t < best_early[1]:
                best_early = (idx, t)
            if best_late is None or t > best_late[1]:
                best_late = (idx, t)
        if best_early:
            spanner.add(best_early[0])
        if best_late:
            spanner.add(best_late[0])

    # Check if forced edges alone suffice
    missing = full_pairs - current_pairs(spanner)
    if not missing:
        return spanner, {'hubs': 0}

    # STEP 2: Try single hub from residual
    best_hub = None
    best_count = len(missing)
    for h in residual:
        trial = set(spanner)
        add_star(trial, h)
        trial_missing = full_pairs - current_pairs(trial)
        if len(trial_missing) < best_count:
            best_count = len(trial_missing)
            best_hub = h
            if best_count == 0:
                break

    if best_count == 0 and best_hub is not None:
        add_star(spanner, best_hub)
        # Now add dismounting edges only if still needed
        missing = full_pairs - current_pairs(spanner)
        if not missing:
            return spanner, {'hubs': 1, 'hub': best_hub}

        # Add dismounting edges one at a time, checking each
        for v, e1, e2 in reversed(dismount_plan):
            if not missing:
                break
            for e in [e1, e2]:
                idx = edge_to_idx.get(e) or edge_to_idx.get((e[1], e[0]))
                if idx is not None and idx not in spanner:
                    spanner.add(idx)
            missing = full_pairs - current_pairs(spanner)

        return spanner, {'hubs': 1, 'hub': best_hub}

    # STEP 3: Try two hubs from residual
    for i, h1 in enumerate(residual):
        for h2 in residual[i+1:]:
            trial = set(spanner)
            add_star(trial, h1)
            add_star(trial, h2)
            trial_missing = full_pairs - current_pairs(trial)
            if not trial_missing:
                add_star(spanner, h1)
                add_star(spanner, h2)
                # Add dismounting edges only if needed
                missing = full_pairs - current_pairs(spanner)
                if not missing:
                    return spanner, {'hubs': 2}
                for v, e1, e2 in reversed(dismount_plan):
                    if not missing:
                        break
                    for e in [e1, e2]:
                        idx = edge_to_idx.get(e) or edge_to_idx.get((e[1], e[0]))
                        if idx is not None and idx not in spanner:
                            spanner.add(idx)
                    missing = full_pairs - current_pairs(spanner)
                return spanner, {'hubs': 2}

    # STEP 4: Fallback — add all dismounting edges
    for v, e1, e2 in dismount_plan:
        for e in [e1, e2]:
            idx = edge_to_idx.get(e) or edge_to_idx.get((e[1], e[0]))
            if idx is not None:
                spanner.add(idx)
    return spanner, {'hubs': -1}


def build_spanner_optimal_deferred(n, edges, timestamps, dismount_plan, residual):
    """Smarter deferred commit: add hub stars, then greedily add
    dismounting edges only when they fix broken pairs."""
    edge_to_idx = {}
    for idx, (u, v) in enumerate(edges):
        edge_to_idx[(u, v)] = idx
        edge_to_idx[(v, u)] = idx

    full_timed = [(timestamps[idx], edges[idx][0], edges[idx][1])
                  for idx in range(len(edges))]
    full_pairs = compute_reachability_pairs(n, full_timed)

    def current_pairs(indices):
        timed = [(timestamps[idx], edges[idx][0], edges[idx][1])
                 for idx in indices]
        return compute_reachability_pairs(n, timed)

    def add_star(spanner, vertex):
        for u in range(n):
            if u != vertex:
                idx = edge_to_idx.get((vertex, u)) or edge_to_idx.get((u, vertex))
                if idx is not None:
                    spanner.add(idx)

    spanner = set()

    # Forced edges: e⁻ and e⁺ for each vertex
    for w in range(n):
        best_early = None
        best_late = None
        for u in range(n):
            if u == w:
                continue
            key = (w, u) if (w, u) in edge_to_idx else (u, w)
            idx = edge_to_idx[key]
            t = timestamps[idx]
            if best_early is None or t < best_early[1]:
                best_early = (idx, t)
            if best_late is None or t > best_late[1]:
                best_late = (idx, t)
        if best_early:
            spanner.add(best_early[0])
        if best_late:
            spanner.add(best_late[0])

    missing = full_pairs - current_pairs(spanner)
    if not missing:
        return spanner, 0

    # Try each single hub
    best_hub = None
    best_remaining = len(missing)
    for h in residual:
        trial = set(spanner)
        add_star(trial, h)
        rem = len(full_pairs - current_pairs(trial))
        if rem < best_remaining:
            best_remaining = rem
            best_hub = h

    if best_hub is not None:
        add_star(spanner, best_hub)

    missing = full_pairs - current_pairs(spanner)

    if missing and len(residual) >= 2:
        # Try second hub
        best_h2 = None
        best_rem2 = len(missing)
        for h2 in residual:
            if h2 == best_hub:
                continue
            trial = set(spanner)
            add_star(trial, h2)
            rem = len(full_pairs - current_pairs(trial))
            if rem < best_rem2:
                best_rem2 = rem
                best_h2 = h2
        if best_h2 is not None:
            add_star(spanner, best_h2)

    missing = full_pairs - current_pairs(spanner)

    # Greedy repair: add dismounting edges one at a time, most impactful first
    dismount_edges = []
    for v, e1, e2 in dismount_plan:
        for e in [e1, e2]:
            idx = edge_to_idx.get(e) or edge_to_idx.get((e[1], e[0]))
            if idx is not None and idx not in spanner:
                dismount_edges.append(idx)

    while missing and dismount_edges:
        best_edge = None
        best_fix = 0
        for idx in dismount_edges:
            trial = set(spanner) | {idx}
            trial_missing = full_pairs - current_pairs(trial)
            fix = len(missing) - len(trial_missing)
            if fix > best_fix:
                best_fix = fix
                best_edge = idx
        if best_edge is None or best_fix == 0:
            # Add all remaining
            for idx in dismount_edges:
                spanner.add(idx)
            break
        spanner.add(best_edge)
        dismount_edges.remove(best_edge)
        missing = full_pairs - current_pairs(spanner)

    hubs_used = (1 if best_hub is not None else 0) + (1 if 'best_h2' in dir() and best_h2 is not None else 0)
    return spanner, hubs_used


def main():
    from collections import Counter

    for n in [6, 8, 10, 12, 14]:
        samples = {6: 500, 8: 200, 10: 100, 12: 50, 14: 20}[n]
        target = 2 * n - 3

        print(f"\n{'='*60}")
        print(f"n={n}, target 2n-3={target}, {samples} samples")
        print(f"{'='*60}")

        edge_counts_naive = []
        edge_counts_deferred = []
        edge_counts_optimal = []
        at_target = [0, 0, 0]
        under_target = [0, 0, 0]
        failures = 0

        for trial in range(samples):
            edges, timestamps = generate_temporal_clique(n)
            dismount_plan, residual = identify_dismount_order(n, edges, timestamps)

            full_timed = [(timestamps[idx], edges[idx][0], edges[idx][1])
                          for idx in range(len(edges))]
            full_pairs = compute_reachability_pairs(n, full_timed)

            # Method 1: naive (commit everything upfront)
            edge_to_idx = {}
            for idx, (u, v) in enumerate(edges):
                edge_to_idx[(u, v)] = idx
                edge_to_idx[(v, u)] = idx

            naive_spanner = set()
            for v, e1, e2 in dismount_plan:
                for e in [e1, e2]:
                    idx = edge_to_idx.get(e) or edge_to_idx.get((e[1], e[0]))
                    if idx is not None:
                        naive_spanner.add(idx)
            # Add residual edges (all pairs)
            for i in residual:
                for j in residual:
                    if i < j:
                        idx = edge_to_idx.get((i, j))
                        if idx is not None:
                            naive_spanner.add(idx)
            edge_counts_naive.append(len(naive_spanner))
            if len(naive_spanner) <= target:
                at_target[0] += 1

            # Method 2: deferred commit
            spanner2, diag2 = build_spanner_deferred(
                n, edges, timestamps, dismount_plan, residual)
            # Verify
            span_pairs = compute_reachability_pairs(
                n, [(timestamps[idx], edges[idx][0], edges[idx][1])
                    for idx in spanner2])
            if full_pairs - span_pairs:
                failures += 1
            edge_counts_deferred.append(len(spanner2))
            if len(spanner2) <= target:
                at_target[1] += 1

            # Method 3: optimal deferred
            spanner3, hubs3 = build_spanner_optimal_deferred(
                n, edges, timestamps, dismount_plan, residual)
            span_pairs3 = compute_reachability_pairs(
                n, [(timestamps[idx], edges[idx][0], edges[idx][1])
                    for idx in spanner3])
            if full_pairs - span_pairs3:
                failures += 1
            edge_counts_optimal.append(len(spanner3))
            if len(spanner3) <= target:
                at_target[2] += 1

        def stats(counts):
            return (f"avg {sum(counts)/len(counts):.1f}, "
                    f"min {min(counts)}, max {max(counts)}")

        print(f"  Naive (commit all):     {stats(edge_counts_naive)}  "
              f"≤2n-3: {at_target[0]}/{samples}")
        print(f"  Deferred commit:        {stats(edge_counts_deferred)}  "
              f"≤2n-3: {at_target[1]}/{samples}")
        print(f"  Optimal deferred:       {stats(edge_counts_optimal)}  "
              f"≤2n-3: {at_target[2]}/{samples}")
        if failures:
            print(f"  VERIFICATION FAILURES: {failures}")

        # Distribution for optimal
        hist = Counter(edge_counts_optimal)
        print(f"  Optimal edge distribution:")
        for ec in sorted(hist):
            bar = '#' * min(hist[ec], 60)
            label = " ← 2n-3" if ec == target else ""
            print(f"    {ec:3d}: {bar} ({hist[ec]}){label}")


if __name__ == '__main__':
    main()
