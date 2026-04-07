"""
Empirical test of the temporal spanner conjecture via mean payoff games.

For non-dismountable k×k biclique timestamp matrices:
1. Generate random matrices, filter for non-dismountable (connected column ordering graph)
2. Check compound tropical feasibility at c=0
3. If c=0 fails, use gradient descent on potentials
4. Construct mean payoff game and compute value by value iteration
5. Report summary statistics
"""

import numpy as np
from itertools import permutations
from collections import defaultdict
import random

random.seed(42)
np.random.seed(42)


def column_ordering_graph(M):
    """
    For each row, sort columns by timestamp to get permutation σ_i.
    Union of adjacent transpositions in all σ_i forms the column ordering graph.
    Returns set of edges (undirected, as tuples with min first).
    """
    k = M.shape[1]
    edges = set()
    for i in range(M.shape[0]):
        sigma = np.argsort(M[i])
        for pos in range(len(sigma) - 1):
            j1, j2 = int(sigma[pos]), int(sigma[pos + 1])
            edges.add((min(j1, j2), max(j1, j2)))
    return edges


def is_connected(k, edges):
    """Check if the graph on vertices {0,...,k-1} with given edges is connected."""
    if k <= 1:
        return True
    adj = defaultdict(set)
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    visited = set()
    stack = [0]
    while stack:
        v = stack.pop()
        if v in visited:
            continue
        visited.add(v)
        for u in adj[v]:
            if u not in visited:
                stack.append(u)
    return len(visited) == k


def is_non_dismountable(M):
    """A biclique is non-dismountable if its column ordering graph is connected."""
    k = M.shape[1]
    edges = column_ordering_graph(M)
    return is_connected(k, edges)


def generate_random_matrices(k, count):
    """Generate random k×k matrices with distinct entries."""
    matrices = []
    for _ in range(count):
        vals = random.sample(range(1, k * k * 10), k * k)
        M = np.array(vals).reshape(k, k)
        matrices.append(M)
    return matrices


def connected_pairs(M):
    """Return connected column pairs from the column ordering graph."""
    return list(column_ordering_graph(M))


def directed_pairs_from_edges(edges):
    """From undirected edges, produce both directed versions."""
    directed = []
    for j1, j2 in edges:
        directed.append((j1, j2))
        directed.append((j2, j1))
    return directed


def check_c0_directed(M, directed):
    """
    Check if c=0 works for ALL directed pairs: for every (j1, j2),
    does there exist row i' with M[i'][j2] - M[i'][j1] >= 0?
    """
    k = M.shape[0]
    for j1, j2 in directed:
        found = False
        for i in range(k):
            if M[i][j2] - M[i][j1] >= 0:
                found = True
                break
        if not found:
            return False
    return True


def check_c0_undirected(M, pairs):
    """
    Weaker check: for each undirected edge {j1, j2}, does there exist
    row i' such that M[i'][j2] >= M[i'][j1]? (Only one direction per edge,
    using the canonical ordering where j1 < j2.)
    """
    k = M.shape[0]
    for j1, j2 in pairs:
        found = False
        for i in range(k):
            if M[i][j2] >= M[i][j1]:
                found = True
                break
        if not found:
            return False
    return True


def solve_with_potentials(M, directed, max_iter=2000):
    """
    Gradient descent on potentials c.
    For each directed pair (j1->j2), we need max_{i'} (M[i'][j2] - M[i'][j1] + c[i']) >= 0.
    """
    k = M.shape[0]
    c = np.zeros(k, dtype=float)

    for iteration in range(max_iter):
        all_satisfied = True
        for j1, j2 in directed:
            vals = M[:, j2].astype(float) - M[:, j1].astype(float) + c
            max_val = np.max(vals)
            if max_val < 0:
                all_satisfied = False
                i_star = np.argmax(vals)
                c[i_star] += (-max_val) + 0.1
        if all_satisfied:
            return True, c
    return False, c


def mean_payoff_game_value(M, directed, max_iter=300):
    """
    Mean payoff game formulation:
    - Max (prover) wants to show potentials exist. Chooses which row to relay.
    - Min (adversary) picks directed pair to challenge.

    Game graph:
    - State: current directed pair being challenged
    - Min picks next directed pair (j1, j2)
    - Max picks row i to relay, collecting payoff M[i][j2] - M[i][j1]

    The conjecture holds iff Max has a strategy ensuring mean payoff >= 0.

    Value iteration: V[pair] = max_i { M[i][j2] - M[i][j1] + min_{pair'} V[pair'] }

    The mean payoff is the shift needed per iteration for convergence.
    """
    if not directed:
        return 0.0

    n = len(directed)
    V = np.zeros(n, dtype=float)

    shifts = []
    for t in range(max_iter):
        V_new = np.zeros(n, dtype=float)
        for idx, (j1, j2) in enumerate(directed):
            # Max picks best row
            weights = M[:, j2].astype(float) - M[:, j1].astype(float)
            max_weight = np.max(weights)
            # Min picks worst next state
            min_future = np.min(V)
            V_new[idx] = max_weight + min_future
        shift = np.mean(V_new)
        V = V_new - shift
        shifts.append(shift)

    # Mean payoff = average shift over last iterations (after convergence)
    return np.mean(shifts[-100:])


def mean_payoff_game_value_v2(M, directed, max_iter=300):
    """
    Alternative formulation where roles are swapped to match the conjecture:
    - For the conjecture to hold, we need: for ALL pairs, EXIST row with positive relay.
    - Min (adversary) picks the pair. Max (prover) picks the row.
    - Game value >= 0 iff the conjecture holds.

    This is a turn-based game:
    V = min_{pair (j1,j2)} max_{row i} { M[i][j2] - M[i][j1] + V }

    In the repeated game, the value is:
    lambda = min_{(j1,j2)} max_i { M[i][j2] - M[i][j1] }

    (Since Min always picks the worst pair and Max always picks best row,
     in the single-stage game repeated, the value is just the min over pairs
     of the max row difference.)
    """
    if not directed:
        return 0.0

    pair_values = []
    for j1, j2 in directed:
        weights = M[:, j2].astype(float) - M[:, j1].astype(float)
        pair_values.append(np.max(weights))

    # Min picks the worst pair
    return min(pair_values)


def analyze_k(k, num_samples):
    """Analyze all non-dismountable matrices for given k."""
    print(f"\n--- k={k}, sampling {num_samples} random matrices ---")

    matrices = generate_random_matrices(k, num_samples)

    non_dismountable = []
    for M in matrices:
        if is_non_dismountable(M):
            non_dismountable.append(M)

    n_nd = len(non_dismountable)
    print(f"  Non-dismountable: {n_nd}/{num_samples} ({100*n_nd/num_samples:.1f}%)")

    if n_nd == 0:
        return {
            'k': k, 'n_nd': 0,
            'c0_dir_pct': 0, 'c0_undir_pct': 0,
            'pot_needed': 0, 'pot_found': 0,
            'gv1_nonneg': 0, 'gv2_nonneg': 0,
            'gv2_values': []
        }

    c0_dir_works = 0
    c0_undir_works = 0
    potentials_needed = 0
    potentials_found = 0
    gv1_values = []
    gv2_values = []

    for idx, M in enumerate(non_dismountable):
        pairs = connected_pairs(M)
        directed = directed_pairs_from_edges(pairs)

        # Check c=0, directed (strict: both directions for every edge)
        if check_c0_directed(M, directed):
            c0_dir_works += 1

        # Check c=0, undirected (only canonical direction j1 < j2)
        if check_c0_undirected(M, pairs):
            c0_undir_works += 1

        # Check if potentials needed (directed check is the real test)
        if not check_c0_directed(M, directed):
            found, c = solve_with_potentials(M, directed)
            if found:
                potentials_found += 1
            potentials_needed += 1

        # Mean payoff game: simple formula (v2)
        gv2 = mean_payoff_game_value_v2(M, directed)
        gv2_values.append(gv2)

        if (idx + 1) % 2000 == 0:
            print(f"  Processed {idx+1}/{n_nd}...")

    # Also compute full value iteration for a subset
    gv1_subset = min(500, n_nd)
    for M in non_dismountable[:gv1_subset]:
        pairs = connected_pairs(M)
        directed = directed_pairs_from_edges(pairs)
        gv1 = mean_payoff_game_value(M, directed, max_iter=200)
        gv1_values.append(gv1)

    gv1_nonneg = sum(1 for v in gv1_values if v >= -1e-6)
    gv2_nonneg = sum(1 for v in gv2_values if v >= -1e-6)

    c0_dir_pct = 100 * c0_dir_works / n_nd
    c0_undir_pct = 100 * c0_undir_works / n_nd
    pot_needed_pct = 100 * potentials_needed / n_nd
    pot_found_pct = 100 * potentials_found / potentials_needed if potentials_needed > 0 else 100

    print(f"  c=0 works (directed, both dirs): {c0_dir_works}/{n_nd} ({c0_dir_pct:.1f}%)")
    print(f"  c=0 works (undirected, j1<j2):   {c0_undir_works}/{n_nd} ({c0_undir_pct:.1f}%)")
    print(f"  Potentials needed (directed fails): {potentials_needed}/{n_nd} ({pot_needed_pct:.1f}%)")
    if potentials_needed > 0:
        print(f"  Potentials found by GD: {potentials_found}/{potentials_needed} ({pot_found_pct:.1f}%)")
    print(f"  Game value v2 (min-max) >= 0: {gv2_nonneg}/{n_nd} ({100*gv2_nonneg/n_nd:.1f}%)")
    print(f"  Game value v1 (iteration, {gv1_subset} samples) >= 0: {gv1_nonneg}/{gv1_subset} ({100*gv1_nonneg/gv1_subset:.1f}%)")
    if gv2_values:
        print(f"  Game v2 stats: min={min(gv2_values):.1f}, max={max(gv2_values):.1f}, "
              f"mean={np.mean(gv2_values):.1f}")

    return {
        'k': k, 'n_nd': n_nd,
        'c0_dir_pct': c0_dir_pct, 'c0_undir_pct': c0_undir_pct,
        'pot_needed': potentials_needed, 'pot_found': potentials_found,
        'pot_found_pct': pot_found_pct,
        'gv2_nonneg_pct': 100 * gv2_nonneg / n_nd,
        'gv2_values': gv2_values
    }


def examine_counterexamples(k, num_check=2000):
    """Find and display counterexamples where c=0 fails."""
    matrices = generate_random_matrices(k, num_check)
    count = 0
    for M in matrices:
        if not is_non_dismountable(M):
            continue
        pairs = connected_pairs(M)
        directed = directed_pairs_from_edges(pairs)
        if not check_c0_directed(M, directed):
            print(f"\n  k={k} counterexample to c=0 (directed):")
            print(f"  M = {M.tolist()}")
            # Find which directed pair fails
            for j1, j2 in directed:
                diffs = [int(M[i][j2] - M[i][j1]) for i in range(k)]
                if max(diffs) < 0:
                    print(f"    FAILS ({j1}->{j2}): diffs={diffs}, max={max(diffs)}")
            found, c = solve_with_potentials(M, directed)
            print(f"    Potentials found: {found}, c={[round(x,1) for x in c]}")
            # Verify potentials
            if found:
                all_ok = True
                for j1, j2 in directed:
                    vals = [M[i][j2] - M[i][j1] + c[i] for i in range(k)]
                    if max(vals) < 0:
                        all_ok = False
                        print(f"    VERIFICATION FAIL ({j1}->{j2}): max relay = {max(vals):.1f}")
                if all_ok:
                    print(f"    Verified: all directed pairs satisfied with potentials.")
            count += 1
            if count >= 2:
                break


def main():
    print("=" * 70)
    print("Temporal Spanner Conjecture: Mean Payoff Game Empirical Test")
    print("=" * 70)

    results = []
    configs = [(3, 10000), (4, 10000), (5, 5000)]

    for k, n in configs:
        r = analyze_k(k, n)
        results.append(r)

    # Summary table
    print("\n" + "=" * 70)
    print("SUMMARY TABLE")
    print("=" * 70)
    print(f"{'k':>3} | {'#ND':>6} | {'c=0 dir%':>9} | {'c=0 und%':>9} | {'pot GD%':>8} | {'game>=0%':>9}")
    print("-" * 60)
    for r in results:
        print(f"{r['k']:>3} | {r['n_nd']:>6} | {r['c0_dir_pct']:>8.1f}% | {r['c0_undir_pct']:>8.1f}% | "
              f"{r['pot_found_pct']:>7.1f}% | {r['gv2_nonneg_pct']:>8.1f}%")

    # Key findings
    print("\n" + "=" * 70)
    print("KEY FINDINGS")
    print("=" * 70)

    all_c0_undir = all(r['c0_undir_pct'] == 100.0 for r in results)
    all_c0_dir = all(r['c0_dir_pct'] == 100.0 for r in results)
    all_pot_found = all(r['pot_found_pct'] == 100.0 for r in results)

    print(f"Q1: c=0 always works (undirected)?  {'YES' if all_c0_undir else 'NO'}")
    print(f"Q2: c=0 always works (directed)?    {'YES' if all_c0_dir else 'NO'}")
    print(f"Q3: GD always finds potentials?      {'YES' if all_pot_found else 'NO'}")

    if not all_c0_dir:
        print(f"\nc=0 fails for directed pairs. The backward direction (j2->j1)")
        print(f"requires that SOME row has M[i][j1] > M[i][j2], which fails when")
        print(f"column j2 dominates column j1 across all rows.")

    # Check the undirected question more carefully
    if all_c0_undir:
        print(f"\nSTRONG RESULT: For the canonical direction (j1 < j2 in the column")
        print(f"ordering graph), c=0 ALWAYS works. This means: for every connected")
        print(f"edge in the column ordering graph, there exists a row where the")
        print(f"higher-indexed column has a larger timestamp. Potentials are only")
        print(f"needed for the reverse direction.")

    # Show counterexamples
    print("\n" + "=" * 70)
    print("COUNTEREXAMPLES (c=0 directed failures)")
    print("=" * 70)
    random.seed(42)
    np.random.seed(42)
    for k in [3, 4]:
        examine_counterexamples(k)


if __name__ == "__main__":
    main()
