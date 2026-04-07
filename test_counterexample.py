"""
Test the inductive dismounting argument on the K_8 counterexample
from Carnevale-Casteigts-Corsini (2025).

For each vertex v: remove v, compute min spanner of K_{n-1},
then try reconnecting v with its earliest and latest incident edges.
Check if the result is a valid spanner of K_n.
"""

from itertools import combinations


def compute_reachability(n, vertices, timed_edges):
    """Compute reachability among a subset of vertices."""
    reached_by = {v: {v: 0} for v in vertices}
    for t, u, v in timed_edges:
        if u not in vertices or v not in vertices:
            continue
        sources_u = {s: arr for s, arr in reached_by[u].items() if arr <= t}
        sources_v = {s: arr for s, arr in reached_by[v].items() if arr <= t}
        for s, arr in sources_u.items():
            if s not in reached_by[v] or t < reached_by[v][s]:
                reached_by[v][s] = t
        for s, arr in sources_v.items():
            if s not in reached_by[u] or t < reached_by[u][s]:
                reached_by[u][s] = t

    pairs = set()
    for v in vertices:
        for s in reached_by[v]:
            if s != v:
                pairs.add((s, v))
    return pairs


def find_min_spanner_edges(n, vertices, edges_with_times):
    """Find minimum spanner edge set (greedy + exact)."""
    vset = set(vertices)
    relevant = [(t, u, v) for t, u, v in edges_with_times if u in vset and v in vset]
    target = compute_reachability(n, vertices, relevant)

    # Greedy removal
    included = list(range(len(relevant)))
    for idx in sorted(range(len(relevant)), key=lambda i: -relevant[i][0]):
        candidate = [i for i in included if i != idx]
        sub = [relevant[i] for i in candidate]
        if compute_reachability(n, vertices, sub) == target:
            included = candidate

    greedy_size = len(included)

    # Try exact below greedy
    for size in range(len(vertices) - 1, greedy_size):
        for subset in combinations(range(len(relevant)), size):
            sub = [relevant[i] for i in subset]
            if compute_reachability(n, vertices, sub) == target:
                return [relevant[i] for i in subset], size
        # If nothing found at this size, continue

    return [relevant[i] for i in included], greedy_size


# K_8 counterexample from Carnevale-Casteigts-Corsini (2025), Figure 12
# Vertices: 0-7
# V- = {0, 1, 2, 3}, V+ = {4, 5, 6, 7}
LABELS = {
    # Internal V- (small labels)
    (1, 0): 0,
    (2, 0): 1,
    (0, 3): 2,
    (2, 1): 3,
    (1, 3): 4,
    (2, 3): 5,
    # Cross edges (green, earliest)
    (7, 1): 6,
    (6, 3): 7,
    (4, 0): 8,
    (5, 2): 9,
    # Cross edges (gray, neutral)
    (0, 5): 10,
    (0, 7): 11,
    (2, 4): 12,
    (2, 6): 13,
    (3, 5): 14,
    (3, 7): 15,
    (1, 4): 16,
    (1, 6): 17,
    # Cross edges (red, latest)
    (5, 1): 18,
    (6, 0): 19,
    (4, 3): 20,
    (7, 2): 21,
    # Internal V+ (large labels)
    (5, 4): 22,
    (4, 6): 23,
    (7, 4): 24,
    (5, 6): 25,
    (5, 7): 26,
    (7, 6): 27,
}

def get_label(u, v):
    if (u, v) in LABELS:
        return LABELS[(u, v)]
    if (v, u) in LABELS:
        return LABELS[(v, u)]
    raise KeyError(f"Edge ({u},{v}) not found")


def build_timed_edges():
    """Build sorted list of (timestamp, u, v) for all edges."""
    edges = []
    seen = set()
    for (u, v), t in LABELS.items():
        key = (min(u, v), max(u, v))
        if key not in seen:
            seen.add(key)
            edges.append((t, u, v))
    return sorted(edges)


def test_inductive_dismounting():
    n = 8
    vertices = list(range(n))
    all_timed = build_timed_edges()
    full_reach = compute_reachability(n, vertices, all_timed)

    print(f"K_8 counterexample: {len(all_timed)} edges, {len(full_reach)} reachable pairs")
    print(f"Expected pairs: {n*(n-1)} = {8*7}")
    print(f"Fully connected: {len(full_reach) == n*(n-1)}")
    print()

    for v in range(n):
        remaining = [x for x in vertices if x != v]

        # Get v's incident edges
        v_edges = []
        for t, u, w in all_timed:
            if u == v or w == v:
                other = w if u == v else u
                v_edges.append((t, other))
        v_edges.sort()

        earliest_t, earliest_nbr = v_edges[0]
        latest_t, latest_nbr = v_edges[-1]

        print(f"Vertex {v}:")
        print(f"  Incident edges: {[(t, nbr) for t, nbr in v_edges]}")
        print(f"  Earliest: ({v},{earliest_nbr})@t={earliest_t}")
        print(f"  Latest:   ({v},{latest_nbr})@t={latest_t}")

        # Find min spanner of K_{n-1} (without v)
        spanner_edges, spanner_size = find_min_spanner_edges(n, remaining, all_timed)
        print(f"  K_7 spanner (without {v}): {spanner_size} edges (2*7-3={2*7-3})")

        # Add earliest and latest edges back
        augmented = spanner_edges + [(earliest_t, v, earliest_nbr), (latest_t, v, latest_nbr)]
        if earliest_nbr == latest_nbr:
            # Same neighbor — only 1 edge added
            augmented = spanner_edges + [(earliest_t, v, earliest_nbr)]
            print(f"  NOTE: earliest and latest go to same neighbor!")

        augmented.sort()
        aug_reach = compute_reachability(n, vertices, augmented)

        # Check which pairs are missing
        missing = full_reach - aug_reach
        extra_edges = 2 if earliest_nbr != latest_nbr else 1
        total = spanner_size + extra_edges

        if not missing:
            print(f"  Result: VALID spanner with {total} edges ✓")
        else:
            print(f"  Result: INVALID — {len(missing)} pairs missing")
            print(f"  Missing pairs: {sorted(missing)[:10]}{'...' if len(missing)>10 else ''}")

            # Try all pairs of v's edges instead of just earliest/latest
            print(f"  Trying all pairs of v's edges...")
            best_missing = len(full_reach)
            best_pair = None
            for i, (t1, n1) in enumerate(v_edges):
                for j, (t2, n2) in enumerate(v_edges):
                    if i >= j:
                        continue
                    aug2 = spanner_edges + [(t1, v, n1), (t2, v, n2)]
                    aug2.sort()
                    r = compute_reachability(n, vertices, aug2)
                    m = len(full_reach - r)
                    if m < best_missing:
                        best_missing = m
                        best_pair = ((t1, n1), (t2, n2))
            if best_missing == 0:
                print(f"  Found valid pair: {best_pair} ✓")
            else:
                print(f"  Best pair {best_pair}: still {best_missing} pairs missing")

                # Try 3 edges
                print(f"  Trying triples of v's edges...")
                for combo in combinations(range(len(v_edges)), 3):
                    aug3 = spanner_edges + [(v_edges[k][0], v, v_edges[k][1]) for k in combo]
                    aug3.sort()
                    r = compute_reachability(n, vertices, aug3)
                    if full_reach - r == set():
                        edges_used = [(v_edges[k][0], v_edges[k][1]) for k in combo]
                        print(f"  Found valid triple: {edges_used} ✓ (cost: 3 edges)")
                        break
                else:
                    print(f"  No triple works either!")
        print()


if __name__ == "__main__":
    test_inductive_dismounting()
