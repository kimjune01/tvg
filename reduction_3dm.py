"""
Attempt to reduce 3-Dimensional Matching (3DM) to minimum temporal clique spanner.

3DM: Given X, Y, Z of size n and triples T ⊆ X×Y×Z, does a perfect matching
exist (n disjoint triples covering each element exactly once)?

Temporal biclique has three natural dimensions:
  - rows (A-side) ↔ X
  - columns (B-side) ↔ Y
  - timestamps ↔ Z

The chain inequality M[i][j1] < M[i'][j1] < M[i'][j2] < M[i''][j2] relates
three edges: (i,j1), (i',j1), (i',j2), (i'',j2). The middle two share row i'
and the ternary relationship (i, j1, timestamp_rank) echoes a 3DM triple.

Strategy: construct a k×k all-distinct matrix M from a 3DM instance such that
  min spanner = |F| + n  iff  3DM has a perfect matching.
"""

import itertools
import numpy as np
from x3c_reduction import temporal_reachable, covering_hypergraph, all_reachable


# ============================================================
# 3DM instances
# ============================================================

def make_3dm_yes():
    """A small 3DM instance that HAS a perfect matching."""
    n = 3
    # Matching: (0,0,0), (1,1,1), (2,2,2) — the diagonal
    # Plus some distractors
    T = [
        (0, 0, 0), (1, 1, 1), (2, 2, 2),  # the matching
        (0, 1, 0), (1, 0, 1), (2, 0, 2),  # distractors
        (0, 2, 1), (1, 2, 0), (2, 1, 0),  # more distractors
    ]
    matching = find_perfect_matching(n, T)
    assert matching is not None, f"Expected matching, got None"
    return n, T, matching


def make_3dm_no():
    """A small 3DM instance that does NOT have a perfect matching."""
    n = 3
    T = [
        (0, 0, 0), (0, 1, 0), (0, 2, 0),  # all use z=0
        (1, 0, 1), (1, 1, 1),              # all use z=1
        (2, 0, 2), (2, 1, 2),              # all use z=2
    ]
    # Every triple with x=0 uses z=0. So matching must pick one with x=0,z=0.
    # Then z=0 is used. Remaining: x=1,2 need y,z coverage.
    # But no triple covers y=2 except (0,2,0) which uses x=0.
    # Actually (0,2,0) + (1,0,1) + (2,1,2) = covers x={0,1,2}, y={2,0,1}={0,1,2}, z={0,1,2}
    # That IS a matching! Let me make a truly impossible one.
    T_no = [
        (0, 0, 0), (1, 0, 0), (2, 0, 0),  # all use y=0, z=0
        (0, 1, 1), (1, 1, 1), (2, 1, 1),  # all use y=1, z=1
        (0, 2, 2), (1, 2, 2), (2, 2, 2),  # all use y=2, z=2
    ]
    # Any matching must pick 3 triples covering x={0,1,2}, y={0,1,2}, z={0,1,2}.
    # But y=j forces z=j. So we need 3 distinct y-values, giving z={0,1,2} auto.
    # Pick one triple per y: (x0,0,0),(x1,1,1),(x2,2,2) with x0,x1,x2 distinct.
    # That works: e.g. (0,0,0),(1,1,1),(2,2,2). So this IS matchable too!

    # Truly no-match instance:
    T_no = [
        (0, 0, 0), (0, 1, 0), (0, 0, 1),
        (1, 1, 1), (1, 0, 1),
        (2, 0, 0), (2, 1, 0),
    ]
    # x=0 uses z∈{0,1}, x=1 uses z=1, x=2 uses z=0.
    # No triple covers z=2 → no perfect matching.
    matching = find_perfect_matching(n, T_no)
    assert matching is None, f"Expected no matching, got {matching}"
    return n, T_no, None


def find_perfect_matching(n, triples):
    """Brute force: find n disjoint triples covering X, Y, Z exactly."""
    for combo in itertools.combinations(triples, n):
        xs = set(t[0] for t in combo)
        ys = set(t[1] for t in combo)
        zs = set(t[2] for t in combo)
        if xs == set(range(n)) and ys == set(range(n)) and zs == set(range(n)):
            return list(combo)
    return None


# ============================================================
# Reduction attempt 1: Direct timestamp assignment
# ============================================================

def attempt1_direct_encoding(n, triples):
    """
    Map 3DM triple (x, y, z) → matrix entry M[x][y] gets timestamp related to z.

    Idea: row=x, col=y, timestamp_rank=z. If triple (x,y,z) ∈ T, then M[x][y]
    is set to z (or z-related). Non-triple entries get large/small filler values.

    Problem: M must be all-distinct. Also, k=n, and we need k² distinct timestamps
    for only nk = n² entries. Each triple fixes one entry; we have |T| ≤ n³
    triples but only n² entries.
    """
    print("\n" + "="*60)
    print("ATTEMPT 1: Direct encoding (row=x, col=y, timestamp~z)")
    print("="*60)

    k = n  # k×k matrix
    # For each (x,y), pick the z-value from T (if unique)
    entry_candidates = {}
    for (x, y, z) in triples:
        entry_candidates.setdefault((x, y), []).append(z)

    print(f"n={n}, |T|={len(triples)}, k={k}")
    print(f"Entry candidates: {dict(entry_candidates)}")

    # Problem: multiple triples can map to same (x,y) with different z.
    # The matrix has one value per (x,y). Can't encode multiple z's.
    multi = {pos: zs for pos, zs in entry_candidates.items() if len(zs) > 1}
    if multi:
        print(f"\nFATAL: Multiple z-values for same (x,y): {multi}")
        print("Cannot encode multiple triples at same matrix position.")
        print("This is the fundamental obstacle for direct encoding.")
        return False

    # Even if unique, try to build the matrix
    # Assign timestamps: triple entries get z*n + offset, others get filler
    M = np.zeros((k, k), dtype=int)
    used = set()
    # First assign triple entries
    for (x, y), zs in entry_candidates.items():
        z = zs[0]
        # Map z to a timestamp that preserves ordering
        # Use z * k² to spread them out
        t = z * k * k + x * k + y  # unique per (x,y,z)
        M[x][y] = t
        used.add(t)

    # Fill remaining entries
    filler = max(used) + 1 if used else 0
    for i in range(k):
        for j in range(k):
            if (i, j) not in entry_candidates:
                while filler in used:
                    filler += 1
                M[i][j] = filler
                used.add(filler)
                filler += 1

    # Check all-distinct
    vals = M.flatten()
    assert len(set(vals)) == k * k, "Not all-distinct!"

    print(f"\nMatrix M:\n{M}")

    # Analyze covering structure
    forced, uncovered, rescue_map = covering_hypergraph(M)
    print(f"\nForced edges: {len(forced)}")
    print(f"Uncovered pairs: {len(uncovered)}")
    print(f"Rescue edges: {len(rescue_map)}")

    if rescue_map:
        for e, pairs in sorted(rescue_map.items()):
            print(f"  Edge {e}: covers {len(pairs)} pairs")

    # Check if covering structure maps to 3DM
    # Want: each rescue edge ↔ a triple, each pair ↔ a universe element
    # And min cover = n iff perfect matching exists
    print(f"\nDesired: {n} rescue edges forming perfect cover")
    print(f"Actual: {len(rescue_map)} rescue edges, {len(uncovered)} uncovered pairs")

    return True


# ============================================================
# Reduction attempt 2: Expanded matrix (gadget construction)
# ============================================================

def attempt2_gadget_encoding(n, triples):
    """
    Use k > n. Encode each triple as a gadget that creates specific
    chain inequalities.

    Key idea: a 3-hop chain M[i][j1] < M[i'][j1] < M[i'][j2] < M[i''][j2]
    involves 3 rows (i, i', i'') and 2 columns (j1, j2). The middle row i'
    participates in both column-pairs. This is a ternary constraint.

    Map: each triple (x,y,z) → a specific cross edge whose presence enables
    a 3-hop chain covering some forced pair.

    Construction:
    - Element rows/cols for x, y, z checking
    - Triple rows/cols for each triple in T
    - Timestamp assignment forces specific chain patterns
    """
    print("\n" + "="*60)
    print("ATTEMPT 2: Gadget encoding with expanded matrix")
    print("="*60)

    # For n=3, try k = 2n = 6
    # Rows 0..n-1 = "element-X rows", rows n..2n-1 = "element-Z rows"
    # Cols 0..n-1 = "element-Y cols", cols n..2n-1 = "verification cols"
    k = 2 * n
    print(f"n={n}, k={k}, matrix size={k}×{k}={k*k} entries")

    # Strategy: assign timestamps so that:
    # - Forced edges cover "easy" pairs
    # - Each triple (x,y,z) corresponds to a cross edge that creates
    #   a chain through element-X row x, element-Y col y, element-Z row z+n

    # Build timestamp assignment
    # Use n phases: phase z has timestamps in range [z*k², (z+1)*k²)
    # Within phase z, triples with z-component = z get "good" timestamps

    M = np.zeros((k, k), dtype=int)
    timestamp = 1  # counter for all-distinct

    # Assign systematically: sweep through matrix positions
    # But we need to control which edges become forced (M⁻, M⁺)
    # M⁻ = column minima, M⁺ = row maxima

    # To control forced edges, we need to control which entry is
    # min in each column and max in each row.

    # Let's try: make element rows have very specific patterns
    # Row i (i < n): small values in "its" columns, large elsewhere
    # This controls which edges are forced.

    # Actually, let me think about what we need...
    # The spanner problem after removing forced edges becomes:
    # "choose minimum cross edges to cover uncovered pairs"
    # We need this residual problem to be exactly 3DM.

    # For 3DM, the residual problem must have:
    # - 3n "pair constraints" (one per element of X ∪ Y ∪ Z)
    # - |T| optional edges (one per triple)
    # - Each triple-edge covers exactly one x-constraint, one y-constraint, one z-constraint
    # - Min cover = n iff perfect matching exists

    # This requires EXACT control over the covering structure.
    # Let's try to build it directly.

    # Approach: Use 3 blocks of n consecutive timestamps per "phase"
    # n phases (one per matching slot)
    # Within phase p, 3 "element slots"

    # Actually, let me try a more systematic approach.
    # Build a k×k matrix where I can prove the covering structure.

    # Start with k = n + |T|. Each triple gets its own row.
    k = n + len(triples)
    print(f"Revised: k = n + |T| = {k}")

    # Rows 0..n-1: "element rows" (correspond to X elements)
    # Rows n..n+|T|-1: "triple rows" (one per triple)
    # Cols 0..n-1: "Y cols" (correspond to Y elements)
    # Cols n..n+|T|-1: "filler cols"

    # The idea: triple (x,y,z) uses cross edge (n+t, y) where t is triple index.
    # The z-component controls timestamp ordering.

    # This is getting complicated. Let me instead do a computational search:
    # for small instances, search for matrices whose covering structure
    # matches the desired 3DM structure.

    print("\nGadget construction is underdetermined.")
    print("Switching to computational search...")
    return search_matching_structure(n, triples)


def search_matching_structure(n, triples):
    """
    Search for a matrix M whose covering structure (rescue_map)
    is isomorphic to the 3DM instance.

    Want: rescue_map has |T| edges, covering 3n pairs,
    each edge covers exactly 3 pairs (one per dimension),
    and min cover = n iff perfect matching exists.
    """
    print(f"\nSearching for matrix with 3DM-isomorphic covering structure...")
    print(f"Target: {len(triples)} rescue edges, {3*n} uncovered pairs, each covers 3")

    target_n_pairs = 3 * n
    target_n_edges = len(triples)

    best_match = None
    best_score = -1

    for k in range(3, 7):
        for seed in range(2000):
            rng = np.random.default_rng(seed)
            vals = rng.permutation(k * k)
            M = vals.reshape(k, k)

            forced, uncovered, rescue_map = covering_hypergraph(M)

            if not uncovered:
                continue

            n_pairs = len(uncovered)
            n_edges = len(rescue_map)

            # Score: how close to target structure?
            coverage_sizes = [len(v) for v in rescue_map.values()]
            n_three = sum(1 for s in coverage_sizes if s == 3)

            score = 0
            if n_pairs == target_n_pairs:
                score += 10
            if n_edges == target_n_edges:
                score += 10
            score += n_three  # bonus for edges covering exactly 3

            if score > best_score:
                best_score = score
                best_match = (k, seed, n_pairs, n_edges, coverage_sizes)

            # Perfect match?
            if (n_pairs == target_n_pairs and n_edges == target_n_edges
                    and all(s == 3 for s in coverage_sizes)):
                print(f"\n  EXACT MATCH: k={k}, seed={seed}")
                print(f"  {n_pairs} pairs, {n_edges} edges, all cover 3")
                analyze_isomorphism(M, forced, uncovered, rescue_map, n, triples)
                return True

    if best_match:
        k, seed, np_, ne, sizes = best_match
        print(f"\n  Best match: k={k}, seed={seed}")
        print(f"  {np_} pairs (want {target_n_pairs}), {ne} edges (want {target_n_edges})")
        print(f"  Coverage sizes: {sorted(sizes)}")

    return False


def analyze_isomorphism(M, forced, uncovered, rescue_map, n, triples):
    """Check if the covering structure is actually isomorphic to 3DM."""
    print("\n  Checking isomorphism to 3DM...")

    # The uncovered pairs must partition into 3 groups of n (one per dimension)
    # Each rescue edge covers one pair from each group
    # This would give 3-uniform 3-partite hypergraph = 3DM

    # Build incidence matrix: rows = edges, cols = pairs
    edges = list(rescue_map.keys())
    pairs = list(set(uncovered))
    inc = np.zeros((len(edges), len(pairs)), dtype=int)
    for i, e in enumerate(edges):
        for j, p in enumerate(pairs):
            if p in rescue_map[e]:
                inc[i][j] = 1

    print(f"  Incidence matrix shape: {inc.shape}")
    print(f"  Row sums (edge coverages): {list(inc.sum(axis=1))}")
    print(f"  Col sums (pair coverers): {list(inc.sum(axis=0))}")


# ============================================================
# Reduction attempt 3: Chain-based encoding
# ============================================================

def attempt3_chain_encoding(n, triples):
    """
    Focus on the chain structure directly.

    A 3-hop journey a_i → b_j → a_{i'} → b_{j'} requires:
      M[i][j] < M[i'][j] < M[i'][j'] < ...

    The "middle" edge (i',j) is shared between the (i,j)→(i',j) step
    and the (i',j)→(i',j') step. So edge (i',j) participates in
    covering BOTH the pair (a_i → a_{i'}) AND the pair (b_j → b_{j'}).

    This means a single edge can simultaneously serve constraints on
    BOTH the A-side and B-side. This is the ternary structure.

    Map triple (x,y,z) to an edge (row, col) such that:
    - It participates in covering x-constraint (via some A-A chain)
    - It participates in covering y-constraint (via some B-B chain)
    - Its timestamp relates to z-constraint (via ordering)

    The edge must serve as a "bridge" in a 3-hop chain.
    """
    print("\n" + "="*60)
    print("ATTEMPT 3: Chain-based encoding")
    print("="*60)

    # For a small instance, let's build the matrix constructively.
    # We need the forced edges to leave specific pairs uncovered.

    # Key insight: pair (a_i → a_{i'}) is covered by 2-hop if ∃j:
    #   (i,j) and (i',j) both in spanner with M[i][j] < M[i'][j]
    # If NO such j works with forced edges alone, then we need a cross edge.

    # For pair (a_i → a_{i'}) to NEED a cross edge, we need:
    #   For all j: either (i,j) or (i',j) is not forced,
    #              or M[i][j] > M[i'][j] (wrong direction)

    # Let's build a k=n matrix where we control forced edges tightly.
    k = n
    print(f"k={k}")

    # Try many random matrices and analyze the 3-hop chain structure
    print("\nAnalyzing chain structure for random matrices...")

    for seed in range(20):
        rng = np.random.default_rng(seed)
        vals = rng.permutation(k * k)
        M = vals.reshape(k, k)

        forced, uncovered, rescue_map = covering_hypergraph(M)

        if not uncovered or not rescue_map:
            continue

        # For each rescue edge, trace which chains it enables
        print(f"\n  seed={seed}: {len(uncovered)} uncovered, {len(rescue_map)} rescue edges")

        for e, pairs in rescue_map.items():
            # What chains does edge e enable?
            # Add e to forced, then for each newly covered pair,
            # find the actual journey
            chain_info = trace_chains(M, forced, e, pairs)
            print(f"    Edge {e} (t={M[e[0]][e[1]]}): covers {len(pairs)} pairs via:")
            for desc in chain_info[:3]:  # limit output
                print(f"      {desc}")


def trace_chains(M, forced, edge, covered_pairs):
    """Trace the journey chains that edge enables."""
    k = M.shape[0]
    test_edges = forced | {edge}
    descriptions = []

    for pair in list(covered_pairs)[:5]:
        s_side, s, d_side, d = pair
        # Find shortest journey
        journey = find_journey(M, test_edges, s_side, s, d_side, d)
        if journey:
            hops = len(journey)
            edge_in_journey = edge in [(e[1], e[2]) for e in journey]
            desc = f"{s_side}{s}→{d_side}{d}: {hops}-hop, edge {'USED' if edge_in_journey else 'indirect'}"
            descriptions.append(desc)

    return descriptions


def find_journey(M, edges, src_side, src_idx, dst_side, dst_idx):
    """Find a temporal journey, return list of (timestamp, row, col) tuples."""
    k = M.shape[0]
    edge_set = set(edges)

    from heapq import heappush, heappop

    # (timestamp, side, idx, path)
    pq = []
    visited = {}

    if src_side == 'A':
        for j in range(k):
            if (src_idx, j) in edge_set:
                t = M[src_idx, j]
                heappush(pq, (t, 'B', j, [(t, src_idx, j)]))
    else:
        for i in range(k):
            if (i, src_idx) in edge_set:
                t = M[i, src_idx]
                heappush(pq, (t, 'A', i, [(t, i, src_idx)]))

    while pq:
        t, side, idx, path = heappop(pq)

        if side == dst_side and idx == dst_idx:
            return path

        key = (side, idx)
        if key in visited and visited[key] <= t:
            continue
        visited[key] = t

        if side == 'A':
            for j in range(k):
                if (idx, j) in edge_set and M[idx, j] > t:
                    heappush(pq, (M[idx, j], 'B', j, path + [(M[idx, j], idx, j)]))
        else:
            for i in range(k):
                if (i, idx) in edge_set and M[i, idx] > t:
                    heappush(pq, (M[i, idx], 'A', i, path + [(M[i, idx], i, idx)]))

    return None


# ============================================================
# Attempt 4: Exhaustive verification on tiny instances
# ============================================================

def attempt4_verify_both_directions():
    """
    For every 3×3 all-distinct matrix (up to relabeling), compute
    the exact min spanner. Then check: does the spanner problem's
    complexity correlate with ANY 3DM-like structure?

    This is the falsification test: if no matrix has 3DM-like covering,
    the reduction can't work in this form.
    """
    print("\n" + "="*60)
    print("ATTEMPT 4: Exhaustive structural census at k=3")
    print("="*60)

    k = 3
    from collections import Counter

    structure_census = Counter()  # (n_uncovered, tuple of sorted coverage sizes)
    triple_synergy_count = 0
    total = 0

    # Sample many random permutations (9! = 362880 is feasible for covering_hypergraph)
    n_samples = 500
    for seed in range(n_samples):
        rng = np.random.default_rng(seed)
        vals = rng.permutation(k * k)
        M = vals.reshape(k, k)

        forced, uncovered, rescue_map = covering_hypergraph(M)
        total += 1

        if not uncovered:
            structure_census[("all_covered", ())] += 1
            continue

        coverage_sizes = tuple(sorted([len(v) for v in rescue_map.values()]))
        structure_census[(len(uncovered), coverage_sizes)] += 1

        # Check for triple synergy (3 edges needed together)
        if len(rescue_map) >= 3:
            edges = list(rescue_map.keys())
            for combo in itertools.combinations(edges, 3):
                # Does this triple cover something no pair of them covers?
                pair_coverage = set()
                for pair in itertools.combinations(combo, 2):
                    pair_edges = forced | set(pair)
                    for p in uncovered:
                        if temporal_reachable(M, pair_edges, *p):
                            pair_coverage.add(p)

                triple_edges = forced | set(combo)
                triple_coverage = set()
                for p in uncovered:
                    if temporal_reachable(M, triple_edges, *p):
                        triple_coverage.add(p)

                if triple_coverage - pair_coverage:
                    triple_synergy_count += 1
                    break  # one is enough to flag this instance

    print(f"\nStructural census ({n_samples} instances):")
    for key, count in sorted(structure_census.items(), key=lambda x: -x[1]):
        n_unc, sizes = key
        print(f"  {n_unc} uncovered, sizes={sizes}: {count} instances")

    print(f"\nInstances with triple synergy: {triple_synergy_count}/{total}")
    print("(Triple synergy = 3 edges cover a pair that no 2 of them cover)")
    print("If triple synergy is rare, the problem is pairwise-decomposable → not 3DM-like.")


# ============================================================
# Attempt 5: Explicit construction for n=2
# ============================================================

def attempt5_explicit_n2():
    """
    Build the smallest possible reduction: n=2.
    3DM instance: X={0,1}, Y={0,1}, Z={0,1}.
    Triples: T = {(0,0,0), (0,1,1), (1,0,1), (1,1,0)}
    Perfect matching: (0,0,0),(1,1,0) or (0,1,1),(1,0,1)

    Need: a matrix M such that 4 optional edges correspond to 4 triples,
    covering 6 pair-constraints (2 per dimension), with min cover = 2.
    """
    print("\n" + "="*60)
    print("ATTEMPT 5: Explicit construction for n=2")
    print("="*60)

    n = 2
    T = [(0,0,0), (0,1,1), (1,0,1), (1,1,0)]
    # Check: (0,0,0)+(1,1,1)? (1,1,1) not in T. (0,1,1)+(1,0,0)? (1,0,0) not in T.
    # This instance has NO matching. Fix:
    T = [(0,0,0), (0,1,1), (1,0,1), (1,1,0), (1,1,1)]
    # Matching: (0,0,0)+(1,1,1)
    matching = find_perfect_matching(n, T)
    print(f"3DM instance: T={T}")
    print(f"Perfect matching: {matching}")
    assert matching is not None

    # Search k=3,4,5 for matrices where covering structure has:
    # - exactly 6 uncovered pairs
    # - exactly 4 rescue edges
    # - each rescue edge covers exactly 3 pairs (one per "dimension group")
    # - min hitting set = 2

    for k in range(3, 6):
        print(f"\nSearching k={k}...")
        hits = 0
        for seed in range(5000):
            rng = np.random.default_rng(seed)
            vals = rng.permutation(k * k)
            M = vals.reshape(k, k)

            forced, uncovered, rescue_map = covering_hypergraph(M)

            if len(uncovered) != 6 or len(rescue_map) != 4:
                continue

            sizes = sorted([len(v) for v in rescue_map.values()])
            if sizes != [3, 3, 3, 3]:
                continue

            hits += 1
            if hits <= 3:
                print(f"  seed={seed}: 6 pairs, 4 edges, all cover 3")
                # Check if it's 3-partite (pairs split into 3 groups of 2)
                edges = list(rescue_map.keys())
                pairs_list = list(set().union(*rescue_map.values()))

                # Build bipartite incidence
                for e in edges:
                    ps = rescue_map[e]
                    print(f"    Edge {e}: {sorted(ps)}")

                # Check min cover
                for combo in itertools.combinations(edges, 2):
                    covered = rescue_map[combo[0]] | rescue_map[combo[1]]
                    if len(covered) == 6:
                        print(f"    → COVER of size 2: {combo}")

        print(f"  Total matches: {hits}/5000")


# ============================================================
# Meta-analysis: WHY might this fail?
# ============================================================

def structural_obstruction_analysis():
    """
    Analyze why 3DM reduction might be structurally impossible.

    The temporal clique's covering structure has specific constraints:
    1. Forced edges are determined by M⁻ ∪ M⁺ (column-min + row-max matchings)
    2. Coverage is through chains: M[i][j] < M[i'][j] (column ordering)
    3. The matrix entries are a PERMUTATION of 0..k²-1

    These constraints heavily restrict what covering hypergraphs can arise.
    """
    print("\n" + "="*60)
    print("STRUCTURAL OBSTRUCTION ANALYSIS")
    print("="*60)

    # Key question: can the covering hypergraph be 3-uniform AND 3-partite?

    # Observation 1: Coverage is DIRECTIONAL
    # Pair (a_i → a_{i'}) via column j requires M[i][j] < M[i'][j].
    # This is asymmetric: if j covers (i→i'), it does NOT cover (i'→i)
    # unless M[i'][j] < M[i][j], which contradicts.
    print("\nObservation 1: Coverage is directional (asymmetric)")
    print("  Pair (a_i→a_{i'}) via col j needs M[i][j]<M[i'][j]")
    print("  Pair (a_{i'}→a_i) via col j needs M[i'][j]<M[i][j]")
    print("  → Same edge CANNOT cover both directions")
    print("  → Uncovered pairs come in DIRECTED pairs, not undirected")

    # Observation 2: Column ordering is transitive
    # If M[i][j] < M[i'][j] and M[i'][j] < M[i''][j], then M[i][j] < M[i''][j].
    # So if column j covers (i→i') and (i'→i''), it also covers (i→i'').
    print("\nObservation 2: Column ordering is transitive")
    print("  If col j covers (i→i') and (i'→i''), it covers (i→i'')")
    print("  → Coverage through a column is a TOTAL ORDER on rows")
    print("  → Individual columns can't create independent coverage")

    # Observation 3: Forced edges create a rigid scaffold
    # M⁻ (column minima): one forced edge per column (the smallest in each col)
    # M⁺ (row maxima): one forced edge per row (the largest in each row)
    # Together: a bipartite graph with ≤ 2k edges.
    print("\nObservation 3: Forced edges form a rigid scaffold")
    print("  M⁻: k edges (column minima), M⁺: k edges (row maxima)")
    print("  Overlaps reduce total. The scaffold is nearly fixed by M.")

    # Observation 4: Non-forced coverage is RARE at small k
    # At k=3: most matrices have 0-4 uncovered pairs
    # At k=4: 0-8 uncovered pairs
    # 3DM with n=3 needs 9 universe elements = 9 uncovered pairs
    print("\nObservation 4: Uncovered pair count is limited")
    for k in [3, 4, 5]:
        max_unc = 0
        for seed in range(1000):
            rng = np.random.default_rng(seed)
            M = rng.permutation(k*k).reshape(k, k)
            forced, uncovered, _ = covering_hypergraph(M)
            max_unc = max(max_unc, len(uncovered))
        print(f"  k={k}: max uncovered pairs in 1000 trials = {max_unc}")

    # Observation 5: Pairwise vs ternary decomposability
    print("\nObservation 5: Checking pairwise decomposability")
    print("  If every pair constraint can be solved by choosing ONE edge,")
    print("  the problem reduces to Set Cover (not 3DM).")
    print("  3DM needs edges to serve MULTIPLE constraints simultaneously.")
    print("  Checking if rescue edges naturally serve multiple pair types...")

    k = 4
    aa_bb_mixed = 0
    total_with_rescue = 0
    for seed in range(500):
        rng = np.random.default_rng(seed)
        M = rng.permutation(k*k).reshape(k, k)
        forced, uncovered, rescue_map = covering_hypergraph(M)
        if not rescue_map:
            continue
        total_with_rescue += 1

        for e, pairs in rescue_map.items():
            pair_types = set()
            for p in pairs:
                pair_types.add((p[0], p[2]))  # (src_side, dst_side)
            if len(pair_types) > 1:
                aa_bb_mixed += 1
                break

    print(f"  k={k}: {aa_bb_mixed}/{total_with_rescue} instances have edges covering mixed pair types (A→A and B→B)")
    print("  Mixed coverage = ternary structure. If rare, 3DM reduction unlikely.")


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    # Test 3DM instances
    print("="*60)
    print("3-DIMENSIONAL MATCHING REDUCTION ATTEMPT")
    print("="*60)

    # Create instances
    n_yes, T_yes, matching_yes = make_3dm_yes()
    if matching_yes:
        print(f"YES instance: n={n_yes}, |T|={len(T_yes)}, matching={matching_yes}")
    else:
        print(f"YES instance: n={n_yes}, |T|={len(T_yes)}, no matching found (BUG)")

    n_no, T_no, _ = make_3dm_no()
    print(f"NO instance: n={n_no}, |T|={len(T_no)}, no matching (confirmed)")

    # Run all attempts
    attempt1_direct_encoding(n_yes, T_yes)
    attempt2_gadget_encoding(n_yes, T_yes)
    attempt3_chain_encoding(n_yes, T_yes)
    attempt4_verify_both_directions()
    attempt5_explicit_n2()
    structural_obstruction_analysis()
