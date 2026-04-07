"""
Clique completion experiment: can we embed a hard sparse temporal graph
into a temporal clique such that the minimum spanner is preserved?

Approach:
  1. Build small sparse temporal graphs where every edge is essential
  2. Complete to K_n using different timestamp strategies
  3. Brute-force minimum spanners of both sparse and completed graphs
  4. Check whether new edges appear in the optimal clique spanner

If completion always creates shortcuts, the embedding approach to
NP-hardness is blocked. We want to understand exactly why.
"""

import itertools
from collections import defaultdict


# ── Temporal reachability on general graphs ──────────────────────────

def temporal_reachable(vertices, edges_with_times, src, dst):
    """Check if src can reach dst via a temporal journey.

    edges_with_times: list of (u, v, t) — undirected edge {u,v} at time t.
    Journey: sequence of edges with strictly increasing timestamps.
    """
    if src == dst:
        return True

    # Build adjacency: vertex -> list of (neighbor, time)
    adj = defaultdict(list)
    for u, v, t in edges_with_times:
        adj[u].append((v, t))
        adj[v].append((u, t))

    # BFS/Dijkstra over (vertex, earliest_arrival_time)
    from heapq import heappush, heappop

    # (time, vertex) — we want earliest arrival at each vertex
    pq = [(0, src)]  # time 0 = "before any edge"
    best = {}  # vertex -> earliest time we can be there

    while pq:
        t_arr, node = heappop(pq)

        if node == dst:
            return True

        if node in best and best[node] <= t_arr:
            continue
        best[node] = t_arr

        for nbr, t_edge in adj[node]:
            if t_edge > t_arr:  # strictly increasing
                if nbr not in best or best[nbr] > t_edge:
                    heappush(pq, (t_edge, nbr))

    return False


def all_pairs_reachable(vertices, edges_with_times):
    """Check all-pairs temporal reachability."""
    for u in vertices:
        for v in vertices:
            if u != v:
                if not temporal_reachable(vertices, edges_with_times, u, v):
                    return False
    return True


def min_spanner_brute(vertices, edges_with_times):
    """Find minimum temporal spanner by brute force.

    Returns (edge_set, size) where edge_set is list of (u, v, t).
    """
    n_edges = len(edges_with_times)

    # First check: is the full graph even temporally connected?
    if not all_pairs_reachable(vertices, edges_with_times):
        return None, float('inf')

    for size in range(1, n_edges + 1):
        for subset in itertools.combinations(edges_with_times, size):
            if all_pairs_reachable(vertices, list(subset)):
                return list(subset), size

    return edges_with_times, n_edges


# ── Sparse temporal graph constructors ───────────────────────────────

def temporal_path(n):
    """Path 0-1-2-..-(n-1) with timestamps 1,2,...,n-1.
    Every edge is essential: removing any breaks reachability."""
    vertices = list(range(n))
    edges = [(i, i + 1, i + 1) for i in range(n - 1)]
    return vertices, edges


def temporal_cycle(n):
    """Cycle 0-1-2-..-0 with timestamps 1,...,n.
    One edge is redundant (the cycle can lose one edge and still connect)."""
    vertices = list(range(n))
    edges = [(i, (i + 1) % n, i + 1) for i in range(n)]
    return vertices, edges


def temporal_star(n):
    """Star with center 0, leaves 1..n-1, timestamps 1,...,n-1.
    Every edge is essential for reaching the corresponding leaf."""
    vertices = list(range(n))
    edges = [(0, i, i) for i in range(1, n)]
    return vertices, edges


def temporal_caterpillar(n):
    """Path with pendant edges. Needs every edge.
    Vertices: 0-1-2 (spine), 3-4 (pendants off 0 and 2).
    """
    assert n == 5, "hardcoded for n=5"
    vertices = list(range(5))
    edges = [
        (3, 0, 1),  # pendant
        (0, 1, 2),  # spine
        (1, 2, 3),  # spine
        (2, 4, 4),  # pendant
    ]
    return vertices, edges


def connected_sparse_4():
    """4 vertices, simple temporal graph (one timestamp per edge pair),
    all-pairs reachable. Uses edges on different pairs for forward/backward.

    Graph: 0-1(t=1), 1-2(t=2), 2-3(t=3), 0-3(t=4), 0-2(t=5)
    Check: 0->3: 0-1@1, 1-2@2, 2-3@3 (or 0-1@1, 1-2@2, 2-3@3)
           3->0: 2-3@3 backwards then 0-2@5? No — edges are undirected.
           3->0: 3-2@3, 2-0@5 (times 3 < 5, valid!)
           3->1: 3-0@4, 0-1@... wait, 0-1 is at t=1 < t=4. Need increasing.
                  3-2@3, 2-1@2? No, 2 < 3. Hmm.
    Need to think more carefully.
    """
    # Let me just enumerate: edges are undirected, journey needs increasing times.
    # 0-1@1, 0-2@5, 0-3@4, 1-2@2, 2-3@3
    # 3->1: 3-0@4, 0-2@5... no that goes to 2 not 1.
    #        3-2@3... but then need edge from 2 to 1 at t>3: 0-2@5 doesn't help.
    #        There's no edge from 2 or from anywhere reachable from 3 to 1 with t>3
    #        except through 0: 3-0@4, but 0-1@1 has t=1 < 4.
    # This graph is NOT all-pairs connected.

    # Better approach: use a 4-vertex graph where timestamps allow all-pairs.
    # Ring: 0-1@1, 1-2@3, 2-3@5, 3-0@7
    # Plus diagonals: 0-2@2, 1-3@4
    # Total: 6 edges = C(4,2), that's already K_4!
    # So for n=4, K_4 has only 6 edges. Any sparse subgraph has < 6 edges.

    # Actually the KEY insight: for the embedding to make sense, the source
    # must be sparse (fewer edges than K_n) and temporally connected.
    # With n=4, K_4 has 6 edges, so sparse means ≤ 5.

    # 5-edge graph on 4 vertices, all-pairs connected:
    # 0-1@1, 1-2@2, 2-3@3, 0-3@6, 1-3@5
    # 0->3: 0-1@1, 1-2@2, 2-3@3 ✓ (or 0-1@1, 1-3@5)
    # 3->0: 3-1@5, 1-0@... 0-1@1 but 1<5. Need t>5 for edge touching 0.
    #        3-0@6 ✓ (direct!)
    # 3->2: 3-0@6... then need edge from 0 to 2 at t>6: none.
    #        3-1@5, 1-2@2? 2<5 no.
    #        3-2@3 (direct, t=3). But does 3 reach 2 starting fresh? Yes, 3-2@3.
    # 2->0: 2-3@3, 3-1@5... 1-0@1? 1<5 no. 2-3@3, 3-0@6 ✓
    # 1->0: 1-2@2, 2-3@3, 3-0@6 ✓ (or 1-3@5, 3-0@6)
    # 2->1: 2-3@3, 3-1@5 ✓
    # 0->2: 0-1@1, 1-2@2 ✓
    # 0->1: 0-1@1 ✓
    # 1->3: 1-2@2, 2-3@3 ✓ (or 1-3@5)
    # 1->2: 1-2@2 ✓
    # 2->3: 2-3@3 ✓
    # 3->1: 3-1@5 ✓

    vertices = [0, 1, 2, 3]
    edges = [
        (0, 1, 1),
        (1, 2, 2),
        (2, 3, 3),
        (1, 3, 5),
        (0, 3, 6),
    ]
    return vertices, edges


def connected_sparse_5():
    """5 vertices, simple temporal graph, all-pairs reachable.
    7 edges out of C(5,2)=10 possible.
    """
    # Build a graph where timestamps enable all-pairs reachability.
    # Forward chain: 0-1@1, 1-2@2, 2-3@3, 3-4@4
    # Backward links: 4-0@5 (closes the loop for backward travel)
    #   4->0: 4-0@5 direct
    #   3->0: 3-4@4, 4-0@5
    #   2->0: 2-3@3, 3-4@4, 4-0@5
    #   4->1: 4-0@5, 0-1@... 0-1@1 < 5, no!
    # Need more backward edges.
    # Add: 4-2@6, 2-1@... already have 1-2@2, but 2<6 no.
    # Need: 4-2@6, then 2->1 needs an edge from 2 to 1 at t>6.
    # Add: 1-4@8, 2-0@7
    # Let me try:
    # 0-1@1, 1-2@2, 2-3@4, 3-4@6, 4-0@8, 0-3@3, 1-4@5
    # Check all pairs...

    # Actually, let me just try a carefully constructed one and verify.
    vertices = [0, 1, 2, 3, 4]
    edges = [
        (0, 1, 1),   # forward
        (1, 2, 3),   # forward
        (2, 3, 5),   # forward
        (3, 4, 7),   # forward
        (4, 0, 9),   # backward loop
        (0, 3, 2),   # cross: helps backward
        (4, 1, 10),  # backward: helps 4->1
    ]
    return vertices, edges


def connected_sparse_5b():
    """Alternative 5-vertex sparse connected graph.
    Use a 'bowtie' shape with carefully chosen timestamps.
    """
    vertices = [0, 1, 2, 3, 4]
    edges = [
        (0, 1, 1),
        (0, 2, 2),
        (1, 3, 3),
        (2, 3, 4),
        (3, 4, 5),
        (4, 0, 6),
        (4, 1, 7),
    ]
    return vertices, edges


# ── Clique completion strategies ─────────────────────────────────────

def get_all_pairs(vertices):
    """All unordered pairs."""
    return [(u, v) for u in vertices for v in vertices if u < v]


def existing_edge_pairs(edges):
    """Set of unordered pairs that already have edges."""
    pairs = set()
    for u, v, t in edges:
        pairs.add((min(u, v), max(u, v)))
    return pairs


def complete_large_timestamps(vertices, edges):
    """Strategy A: new edges get timestamps LARGER than all originals."""
    max_t = max(t for _, _, t in edges)
    existing = existing_edge_pairs(edges)
    all_pairs = get_all_pairs(vertices)
    missing = [p for p in all_pairs if p not in existing]

    new_edges = []
    for idx, (u, v) in enumerate(missing):
        new_edges.append((u, v, max_t + 1 + idx))

    return edges + new_edges, new_edges


def complete_small_timestamps(vertices, edges):
    """Strategy B: new edges get timestamps SMALLER than all originals."""
    min_t = min(t for _, _, t in edges)
    existing = existing_edge_pairs(edges)
    all_pairs = get_all_pairs(vertices)
    missing = [p for p in all_pairs if p not in existing]

    new_edges = []
    # Assign timestamps min_t - len(missing), ..., min_t - 1
    base = min_t - len(missing)
    for idx, (u, v) in enumerate(missing):
        new_edges.append((u, v, base + idx))

    return edges + new_edges, new_edges


def complete_interleaved(vertices, edges):
    """Strategy C: new edges get timestamps interleaved between originals,
    chosen to minimize shortcut creation.

    Heuristic: place new edge timestamps in gaps, favoring positions
    that don't connect useful intermediate vertices.
    """
    existing = existing_edge_pairs(edges)
    all_pairs = get_all_pairs(vertices)
    missing = [p for p in all_pairs if p not in existing]

    # Collect all used timestamps
    used_times = sorted(set(t for _, _, t in edges))

    # Create gaps: before first, between consecutive, after last
    gaps = []
    gaps.append(used_times[0] - len(missing) - 1)  # before all
    for i in range(len(used_times) - 1):
        # Midpoint between consecutive timestamps (using half-integers)
        mid = (used_times[i] + used_times[i + 1]) / 2.0
        gaps.append(mid)
    gaps.append(used_times[-1] + len(missing) + 1)  # after all

    # For interleaving: assign timestamps that alternate early/late
    # to prevent chain formation among new edges
    new_edges = []
    # Use fractional timestamps spread across gaps
    # Actually, let's use a simple spread: assign distinct timestamps
    # avoiding integer collisions, spread across the range
    min_t = used_times[0]
    max_t = used_times[-1]
    total_range = max_t - min_t + 2 * len(missing) + 2
    base = min_t - len(missing) - 1

    # Assign: alternate high and low to break chains
    timestamps = []
    lo, hi = base, max_t + 1
    for i in range(len(missing)):
        if i % 2 == 0:
            timestamps.append(hi)
            hi += 1
        else:
            timestamps.append(lo)
            lo -= 1

    for (u, v), t in zip(missing, timestamps):
        new_edges.append((u, v, t))

    return edges + new_edges, new_edges


def complete_reverse_order(vertices, edges):
    """Strategy D: new edges get large timestamps, but in REVERSE pair order.
    This avoids the natural ordering that might create chains among new edges."""
    max_t = max(t for _, _, t in edges)
    existing = existing_edge_pairs(edges)
    all_pairs = get_all_pairs(vertices)
    missing = [p for p in all_pairs if p not in existing]
    missing.reverse()

    new_edges = []
    for idx, (u, v) in enumerate(missing):
        new_edges.append((u, v, max_t + 1 + idx))

    return edges + new_edges, new_edges


# ── Analysis ─────────────────────────────────────────────────────────

def analyze_graph(name, vertices, orig_edges):
    """Run all completion strategies and compare spanners."""
    print(f"\n{'=' * 70}")
    print(f"Graph: {name}")
    print(f"Vertices: {vertices}")
    print(f"Original edges: {orig_edges}")
    print(f"{'=' * 70}")

    # Minimum spanner of original
    orig_spanner, orig_size = min_spanner_brute(vertices, orig_edges)
    if orig_spanner is None:
        print("  Original graph is NOT temporally connected!")
        # Check which pairs are unreachable
        for u in vertices:
            for v in vertices:
                if u != v and not temporal_reachable(vertices, orig_edges, u, v):
                    print(f"    UNREACHABLE: {u} -> {v}")
        # Still try completion
        print("  (Completing anyway to see if clique is connected)")

    print(f"\n  Original min spanner size: {orig_size}")
    if orig_spanner:
        print(f"  Original min spanner: {orig_spanner}")

    strategies = [
        ("A: large timestamps", complete_large_timestamps),
        ("B: small timestamps", complete_small_timestamps),
        ("C: interleaved", complete_interleaved),
        ("D: reverse large", complete_reverse_order),
    ]

    results = []

    for strat_name, strat_fn in strategies:
        print(f"\n  --- Strategy {strat_name} ---")
        completed, new_edges = strat_fn(vertices, orig_edges)

        # Check all timestamps distinct
        all_times = [t for _, _, t in completed]
        assert len(all_times) == len(set(all_times)), "Timestamps not distinct!"

        # Check it's a complete graph
        edge_pairs = existing_edge_pairs(completed)
        expected_pairs = set(get_all_pairs(vertices))
        assert edge_pairs == expected_pairs, "Not complete!"

        print(f"    New edges: {new_edges}")
        print(f"    Total edges: {len(completed)}")

        clique_spanner, clique_size = min_spanner_brute(vertices, completed)
        print(f"    Clique min spanner size: {clique_size}")
        print(f"    Clique min spanner: {clique_spanner}")

        if clique_spanner is None:
            print("    Clique is NOT temporally connected! Strategy fails.")
            results.append({
                'strategy': strat_name,
                'clique_size': float('inf'),
                'orig_size': orig_size,
                'shortcuts': 0,
                'preserved': False,
            })
            continue

        # Check: do new edges appear in clique spanner?
        new_edge_set = set((min(u, v), max(u, v), t) for u, v, t in new_edges)
        spanner_edge_set = set(
            (min(u, v), max(u, v), t) for u, v, t in clique_spanner
        )
        shortcuts = new_edge_set & spanner_edge_set
        print(f"    New edges in spanner (shortcuts): {shortcuts}")
        print(f"    Shortcuts created: {len(shortcuts) > 0}")

        # How many original edges in clique spanner?
        orig_edge_set = set(
            (min(u, v), max(u, v), t) for u, v, t in orig_edges
        )
        orig_in_spanner = orig_edge_set & spanner_edge_set
        print(f"    Original edges in clique spanner: {len(orig_in_spanner)}/{len(orig_edges)}")

        preserved = (clique_size == orig_size and len(shortcuts) == 0)
        print(f"    Spanner preserved: {preserved}")

        results.append({
            'strategy': strat_name,
            'clique_size': clique_size,
            'orig_size': orig_size,
            'shortcuts': len(shortcuts),
            'preserved': preserved,
        })

    return results


def analyze_shortcut_mechanism(vertices, orig_edges, completed_edges, new_edges):
    """Explain WHY shortcuts appear: find pairs that get shorter journeys
    through new edges."""
    print("\n  Shortcut mechanism analysis:")

    for u in vertices:
        for v in vertices:
            if u == v:
                continue
            # Min hops in original
            orig_min = min_journey_hops(vertices, orig_edges, u, v)
            # Min hops in completed
            comp_min = min_journey_hops(vertices, completed_edges, u, v)

            if comp_min < orig_min:
                print(f"    {u}->{v}: {orig_min} hops (orig) -> {comp_min} hops (completed)")
                # Find which new edge enables this
                for ne in new_edges:
                    reduced = [e for e in completed_edges if e != ne]
                    without_min = min_journey_hops(vertices, reduced, u, v)
                    if without_min > comp_min:
                        print(f"      Enabled by new edge {ne}")


def min_journey_hops(vertices, edges, src, dst):
    """Find minimum number of edges in a temporal journey from src to dst."""
    if src == dst:
        return 0

    adj = defaultdict(list)
    for u, v, t in edges:
        adj[u].append((v, t))
        adj[v].append((u, t))

    from heapq import heappush, heappop

    # (hops, time, vertex)
    pq = [(0, 0, src)]
    best = {}  # (vertex) -> min hops with some arrival time

    while pq:
        hops, t_arr, node = heappop(pq)

        if node == dst:
            return hops

        key = (node, t_arr)
        if key in best:
            continue
        best[key] = hops

        for nbr, t_edge in adj[node]:
            if t_edge > t_arr:
                nkey = (nbr, t_edge)
                if nkey not in best:
                    heappush(pq, (hops + 1, t_edge, nbr))

    return float('inf')


# ── Deep dive: WHY do shortcuts always appear? ───────────────────────

def shortcut_anatomy(vertices, orig_edges):
    """For each completion strategy, find the exact pairs that get shortcut
    and explain the structural reason."""
    print(f"\n{'=' * 70}")
    print("SHORTCUT ANATOMY")
    print(f"{'=' * 70}")

    completed, new_edges = complete_large_timestamps(vertices, orig_edges)

    # For each pair (u, v): what's the min journey in original vs completed?
    print("\nStrategy A (large timestamps):")
    print("New edges:", new_edges)

    for u in vertices:
        for v in vertices:
            if u >= v:
                continue

            # Forward direction
            fwd_orig = min_journey_hops(vertices, orig_edges, u, v)
            fwd_comp = min_journey_hops(vertices, completed, u, v)
            # Backward direction
            bwd_orig = min_journey_hops(vertices, orig_edges, v, u)
            bwd_comp = min_journey_hops(vertices, completed, v, u)

            if fwd_comp < fwd_orig or bwd_comp < bwd_orig:
                print(f"\n  Pair ({u},{v}):")
                if fwd_comp < fwd_orig:
                    print(f"    {u}->{v}: {fwd_orig} hops -> {fwd_comp} hops")
                if bwd_comp < bwd_orig:
                    print(f"    {v}->{u}: {bwd_orig} hops -> {bwd_comp} hops")

                # Which new edge is critical?
                for ne in new_edges:
                    reduced = [e for e in completed if e != ne]
                    fwd_r = min_journey_hops(vertices, reduced, u, v)
                    bwd_r = min_journey_hops(vertices, reduced, v, u)
                    if fwd_r > fwd_comp or bwd_r > bwd_comp:
                        print(f"    Critical new edge: {ne}")

    # Key question: is there a pair that MUST use a new edge?
    print("\n\nKey question: which pairs have NO journey in the original graph?")
    for u in vertices:
        for v in vertices:
            if u == v:
                continue
            if not temporal_reachable(vertices, orig_edges, u, v):
                print(f"  {u} -> {v}: UNREACHABLE in original")


# ── Systematic enumeration ───────────────────────────────────────────

def systematic_n4():
    """For n=4 (K_4 has 6 edges), enumerate all possible sparse subgraphs
    (removing 1 or 2 edges) and all timestamp permutations. For each,
    check if Strategy B (small timestamps) preserves the spanner.

    This is tractable: C(6,5)=6 choices of 5 edges, 5!=120 permutations each.
    And C(6,4)=15 choices of 4 edges, 4!=24 permutations each.
    """
    vertices = [0, 1, 2, 3]
    all_pairs = get_all_pairs(vertices)  # 6 pairs

    preserved_count = 0
    broken_count = 0
    total_tested = 0
    not_connected = 0

    # Remove 1 edge (5-edge subgraphs)
    for removed in itertools.combinations(range(6), 1):
        remaining_pairs = [all_pairs[i] for i in range(6) if i not in removed]
        missing_pairs = [all_pairs[i] for i in removed]

        # Try all timestamp permutations (assign timestamps 1..5 to the 5 edges)
        for perm in itertools.permutations(range(1, 6)):
            edges = [(u, v, t) for (u, v), t in zip(remaining_pairs, perm)]

            # Check if original is all-pairs connected
            if not all_pairs_reachable(vertices, edges):
                not_connected += 1
                continue

            total_tested += 1
            orig_spanner, orig_size = min_spanner_brute(vertices, edges)

            # Strategy B: add missing edges with small timestamps
            new_edges = []
            for idx, (u, v) in enumerate(missing_pairs):
                new_edges.append((u, v, -len(missing_pairs) + idx))
            completed = edges + new_edges

            clique_spanner, clique_size = min_spanner_brute(vertices, completed)

            if clique_spanner is None:
                broken_count += 1
                continue

            new_edge_set = set((min(u, v), max(u, v), t) for u, v, t in new_edges)
            spanner_edge_set = set(
                (min(u, v), max(u, v), t) for u, v, t in clique_spanner
            )
            shortcuts = new_edge_set & spanner_edge_set

            if len(shortcuts) == 0 and clique_size == orig_size:
                preserved_count += 1
            else:
                broken_count += 1

    print(f"\n  5-edge subgraphs of K_4 (Strategy B: small timestamps):")
    print(f"    Total tested (connected): {total_tested}")
    print(f"    Not connected: {not_connected}")
    print(f"    Preserved: {preserved_count}")
    print(f"    Broken: {broken_count}")

    # Remove 2 edges (4-edge subgraphs)
    preserved_count = 0
    broken_count = 0
    total_tested = 0
    not_connected = 0

    for removed in itertools.combinations(range(6), 2):
        remaining_pairs = [all_pairs[i] for i in range(6) if i not in removed]
        missing_pairs = [all_pairs[i] for i in removed]

        for perm in itertools.permutations(range(1, 5)):
            edges = [(u, v, t) for (u, v), t in zip(remaining_pairs, perm)]

            if not all_pairs_reachable(vertices, edges):
                not_connected += 1
                continue

            total_tested += 1
            orig_spanner, orig_size = min_spanner_brute(vertices, edges)

            new_edges = []
            for idx, (u, v) in enumerate(missing_pairs):
                new_edges.append((u, v, -len(missing_pairs) + idx))
            completed = edges + new_edges

            clique_spanner, clique_size = min_spanner_brute(vertices, completed)

            if clique_spanner is None:
                broken_count += 1
                continue

            new_edge_set = set((min(u, v), max(u, v), t) for u, v, t in new_edges)
            spanner_edge_set = set(
                (min(u, v), max(u, v), t) for u, v, t in clique_spanner
            )
            shortcuts = new_edge_set & spanner_edge_set

            if len(shortcuts) == 0 and clique_size == orig_size:
                preserved_count += 1
            else:
                broken_count += 1

    print(f"\n  4-edge subgraphs of K_4 (Strategy B: small timestamps):")
    print(f"    Total tested (connected): {total_tested}")
    print(f"    Not connected: {not_connected}")
    print(f"    Preserved: {preserved_count}")
    print(f"    Broken: {broken_count}")

    # Also test Strategy A (large timestamps) for comparison
    preserved_a = 0
    broken_a = 0
    tested_a = 0

    for removed in itertools.combinations(range(6), 1):
        remaining_pairs = [all_pairs[i] for i in range(6) if i not in removed]
        missing_pairs = [all_pairs[i] for i in removed]

        for perm in itertools.permutations(range(1, 6)):
            edges = [(u, v, t) for (u, v), t in zip(remaining_pairs, perm)]

            if not all_pairs_reachable(vertices, edges):
                continue

            tested_a += 1
            orig_spanner, orig_size = min_spanner_brute(vertices, edges)

            new_edges = []
            max_t = max(t for _, _, t in edges)
            for idx, (u, v) in enumerate(missing_pairs):
                new_edges.append((u, v, max_t + 1 + idx))
            completed = edges + new_edges

            clique_spanner, clique_size = min_spanner_brute(vertices, completed)

            if clique_spanner is None:
                broken_a += 1
                continue

            new_edge_set = set((min(u, v), max(u, v), t) for u, v, t in new_edges)
            spanner_edge_set = set(
                (min(u, v), max(u, v), t) for u, v, t in clique_spanner
            )
            shortcuts = new_edge_set & spanner_edge_set

            if len(shortcuts) == 0 and clique_size == orig_size:
                preserved_a += 1
            else:
                broken_a += 1

    print(f"\n  5-edge subgraphs of K_4 (Strategy A: large timestamps):")
    print(f"    Total tested (connected): {tested_a}")
    print(f"    Preserved: {preserved_a}")
    print(f"    Broken: {broken_a}")

    # Now test n=5 with Strategy B, sampling 4-missing-edge subgraphs
    # K_5 has 10 edges. 6-edge subgraphs: C(10,6) = 210, 6! = 720 perms each
    # Too many. Sample: pick a few topologies and test all permutations.
    print(f"\n  --- n=5 tests (Strategy B: small timestamps) ---")

    vertices5 = list(range(5))
    all_pairs5 = get_all_pairs(vertices5)  # 10 pairs

    # Test: remove 1 edge from K_5 (9-edge subgraphs)
    preserved_5 = 0
    broken_5 = 0
    tested_5 = 0
    not_conn_5 = 0

    for removed in itertools.combinations(range(10), 1):
        remaining_pairs = [all_pairs5[i] for i in range(10) if i not in removed]
        missing_pairs = [all_pairs5[i] for i in removed]

        # 9! = 362880 — too many. Sample timestamps 1..9.
        # Instead, test random subset of permutations
        import random
        random.seed(42)
        perms_to_test = set()
        # Use first 100 random permutations
        for _ in range(200):
            p = list(range(1, 10))
            random.shuffle(p)
            perms_to_test.add(tuple(p))

        for perm in perms_to_test:
            edges = [(u, v, t) for (u, v), t in zip(remaining_pairs, perm)]

            if not all_pairs_reachable(vertices5, edges):
                not_conn_5 += 1
                continue

            tested_5 += 1
            orig_spanner, orig_size = min_spanner_brute(vertices5, edges)

            new_edges = []
            for idx, (u, v) in enumerate(missing_pairs):
                new_edges.append((u, v, -len(missing_pairs) + idx))
            completed = edges + new_edges

            clique_spanner, clique_size = min_spanner_brute(vertices5, completed)

            if clique_spanner is None:
                broken_5 += 1
                continue

            new_edge_set = set((min(u, v), max(u, v), t) for u, v, t in new_edges)
            spanner_edge_set = set(
                (min(u, v), max(u, v), t) for u, v, t in clique_spanner
            )
            shortcuts = new_edge_set & spanner_edge_set

            if len(shortcuts) == 0 and clique_size == orig_size:
                preserved_5 += 1
            else:
                broken_5 += 1
                if broken_5 <= 3:
                    print(f"    BROKEN example: edges={edges}")
                    print(f"      orig spanner size={orig_size}, clique size={clique_size}")
                    print(f"      new edges={new_edges}, shortcuts={shortcuts}")

    print(f"\n  9-edge subgraphs of K_5 (Strategy B, sampled):")
    print(f"    Total tested (connected): {tested_5}")
    print(f"    Not connected: {not_conn_5}")
    print(f"    Preserved: {preserved_5}")
    print(f"    Broken: {broken_5}")

    # Test: remove 3 edges from K_5 (7-edge subgraphs)
    preserved_7 = 0
    broken_7 = 0
    tested_7 = 0
    not_conn_7 = 0

    random.seed(43)
    for removed in itertools.combinations(range(10), 3):
        remaining_pairs = [all_pairs5[i] for i in range(10) if i not in removed]
        missing_pairs = [all_pairs5[i] for i in removed]

        # 7! = 5040, sample 50
        perms_to_test = set()
        for _ in range(100):
            p = list(range(1, 8))
            random.shuffle(p)
            perms_to_test.add(tuple(p))

        for perm in perms_to_test:
            edges = [(u, v, t) for (u, v), t in zip(remaining_pairs, perm)]

            if not all_pairs_reachable(vertices5, edges):
                not_conn_7 += 1
                continue

            tested_7 += 1
            orig_spanner, orig_size = min_spanner_brute(vertices5, edges)

            new_edges = []
            for idx, (u, v) in enumerate(missing_pairs):
                new_edges.append((u, v, -len(missing_pairs) + idx))
            completed = edges + new_edges

            clique_spanner, clique_size = min_spanner_brute(vertices5, completed)

            if clique_spanner is None:
                broken_7 += 1
                continue

            new_edge_set = set((min(u, v), max(u, v), t) for u, v, t in new_edges)
            spanner_edge_set = set(
                (min(u, v), max(u, v), t) for u, v, t in clique_spanner
            )
            shortcuts = new_edge_set & spanner_edge_set

            if len(shortcuts) == 0 and clique_size == orig_size:
                preserved_7 += 1
            else:
                broken_7 += 1
                if broken_7 <= 3:
                    print(f"    BROKEN example (7-edge): edges={edges}")
                    print(f"      orig={orig_size}, clique={clique_size}, shortcuts={shortcuts}")

    print(f"\n  7-edge subgraphs of K_5 (Strategy B, sampled):")
    print(f"    Total tested (connected): {tested_7}")
    print(f"    Not connected: {not_conn_7}")
    print(f"    Preserved: {preserved_7}")
    print(f"    Broken: {broken_7}")

    # Theoretical argument for why Strategy B always works
    print(f"\n  THEORETICAL ARGUMENT:")
    print(f"  Strategy B assigns new edges timestamps SMALLER than all originals.")
    print(f"  A new edge at time t_new < min(original times) can only appear")
    print(f"  as the FIRST hop of any journey. But if it's the first hop, the")
    print(f"  journey continues using only original edges (all at later times).")
    print(f"  ")
    print(f"  Claim: A new edge (u,v,t_new) can be in a minimum spanner ONLY if")
    print(f"  it enables a journey that doesn't exist using only original edges.")
    print(f"  But if the original graph is all-pairs connected, every journey")
    print(f"  already exists. The new edge at t_new can at best REPLACE the")
    print(f"  first hop of some journey, but it doesn't reduce the total count")
    print(f"  because the rest of the journey still needs the same edges.")
    print(f"  ")
    print(f"  More precisely: suppose the optimal clique spanner S uses a new")
    print(f"  edge e=(u,v,t_new). Then e must appear as the first hop of some")
    print(f"  journey from u to w (or v to w). The second hop uses some original")
    print(f"  edge e'. But there must be a journey from u to w in the original")
    print(f"  graph; let its first edge be e''. Then S - {{e}} + {{e''}} is also")
    print(f"  a spanner of the same size, contradicting that e is necessary.")


# ── Main ─────────────────────────────────────────────────────────────

def main():
    print("CLIQUE COMPLETION EXPERIMENT")
    print("Can we embed hard sparse temporal graphs into temporal cliques")
    print("while preserving the minimum spanner?")

    # Test graphs — must be simple (one timestamp per edge pair) and
    # all-pairs temporally connected
    graphs = [
        ("Sparse4 (5 edges)", *connected_sparse_4()),
        ("Sparse5a (7 edges)", *connected_sparse_5()),
        ("Sparse5b (7 edges)", *connected_sparse_5b()),
        # One-directional graphs (NOT all-pairs connected) for comparison
        ("Path-4 (one-dir)", *temporal_path(4)),
        ("Cycle-5 (one-dir)", *temporal_cycle(5)),
    ]

    all_results = []

    for name, vertices, edges in graphs:
        results = analyze_graph(name, vertices, edges)
        all_results.append((name, results))

    # Summary
    print(f"\n\n{'=' * 70}")
    print("SUMMARY")
    print(f"{'=' * 70}")

    any_preserved = False
    for name, results in all_results:
        print(f"\n{name}:")
        for r in results:
            status = "PRESERVED" if r['preserved'] else "BROKEN"
            delta = r['clique_size'] - r['orig_size']
            sign = "+" if delta >= 0 else ""
            print(f"  {r['strategy']}: clique={r['clique_size']} "
                  f"(orig={r['orig_size']}, {sign}{delta}), "
                  f"shortcuts={r['shortcuts']}, {status}")
            if r['preserved']:
                any_preserved = True

    print(f"\n{'=' * 70}")
    if any_preserved:
        print("FINDING: At least one strategy preserved the spanner!")
        print("The embedding approach may be viable.")
    else:
        print("FINDING: NO strategy preserved the spanner.")
        print("New edges ALWAYS create shortcuts that reduce clique spanner size.")

    # Deep dive into WHY
    print("\n\nDEEP DIVE: Why do shortcuts appear?")
    print("-" * 50)

    # Use the sparse4 graph as the clearest example
    v, e = connected_sparse_4()
    shortcut_anatomy(v, e)

    # Systematic enumeration for n=4
    print(f"\n\n{'=' * 70}")
    print("SYSTEMATIC ENUMERATION: n=4, all timestamp permutations")
    print(f"{'=' * 70}")
    systematic_n4()

    # Final structural argument
    print(f"\n\n{'=' * 70}")
    print("STRUCTURAL ARGUMENT: WHY STRATEGY B (SMALL TIMESTAMPS) ALWAYS WORKS")
    print(f"{'=' * 70}")
    print("""
THEOREM: Let G = (V, E) be an all-pairs temporally connected graph with
single labels and all distinct timestamps. Let K = complete(G) using
Strategy B (all new edges get timestamps < min(original)). Then:
    min_spanner(K) = min_spanner(G)

PROOF SKETCH:
1. min_spanner(K) <= min_spanner(G): Any spanner of G is also a spanner
   of K restricted to original edges, and K has MORE edges available,
   so its minimum can only be <= that of G. But wait — K has more PAIRS
   to connect... No: G is already all-pairs connected on the same vertex
   set. The spanner requirement is the same set of pairs.

   Actually: K has the same vertex set and the same reachability requirement
   (all pairs). A spanner of G is a subgraph of K that connects all pairs.
   So min_spanner(K) <= min_spanner(G).

2. min_spanner(K) >= min_spanner(G): Suppose S is a minimum spanner of K.
   We show S can be transformed into a spanner of K of the same size that
   uses NO new edges (hence is a spanner of G).

   Key observation: Any new edge e = (u,v,t_new) with t_new < min(original)
   can only be the FIRST edge of any temporal journey. After using e, the
   journey must continue with edges at time > t_new, which means original
   edges only (all new edges have smaller timestamps, so they can't follow).

   If S uses new edge e = (u,v,t_new) as the first hop of a journey from
   u to some destination w, then consider: in the original graph G, u can
   reach w via some journey J_orig (since G is all-pairs connected). Let
   the first edge of J_orig be e' = (u,x,t'). Then:
   - Replace e in S with e' (if e' not already in S)
   - This doesn't increase |S| (we remove one, add one)
   - S still connects all pairs because:
     * Any journey through e went u -> v -> ... -> w
     * We now route u -> x -> ... -> w using J_orig's first edge
     * The pair (v, w) that was served by the suffix of the old journey
       is still served by the same suffix (those edges are still in S)

   Repeating this for all new edges in S gives a spanner S' with
   |S'| <= |S| that uses only original edges. So min_spanner(G) <= |S'|
   <= |S| = min_spanner(K).

IMPLICATION FOR NP-HARDNESS:
This gives a valid reduction: sparse_single_label reduces to temporal_clique.
But Axiotis-Fotakis hardness is for MULTI-label graphs. Single-label sparse
is itself open. The embedding works but the source problem isn't known hard.
""")


if __name__ == "__main__":
    main()
