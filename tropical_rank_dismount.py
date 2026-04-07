"""
Tropical rank vs dismountability experiment.

For random k×k matrices (all distinct entries), compute:
1. Column ordering graph connectivity (non-dismountable?)
2. Tropical rank (relay-based factorization rank)
3. Pairwise tropical column independence (constant difference?)
4. Uniform ordering pairs (j1 < j2 in ALL rows?)

Key question: among non-dismountable matrices, do any connected pairs
have uniform ordering in one direction (breaking relay feasibility)?
"""

import numpy as np
from itertools import combinations
from collections import defaultdict

np.random.seed(42)


def column_ordering_graph(M):
    """Return adjacency list of the column ordering graph.
    Edge (j1, j2) if j1 and j2 are adjacent in the column-sort of some row.
    """
    k = M.shape[1]
    adj = defaultdict(set)
    for i in range(M.shape[0]):
        perm = np.argsort(M[i])  # columns sorted by value
        for pos in range(len(perm) - 1):
            a, b = int(perm[pos]), int(perm[pos + 1])
            adj[a].add(b)
            adj[b].add(a)
    return adj


def is_connected(adj, k):
    """BFS connectivity check on k nodes."""
    if k <= 1:
        return True
    visited = set()
    stack = [0]
    while stack:
        node = stack.pop()
        if node in visited:
            continue
        visited.add(node)
        for nb in adj.get(node, []):
            if nb not in visited:
                stack.append(nb)
    return len(visited) == k


def tropical_rank_relay(M):
    """Compute relay rank: min |S| such that for all i,j:
    M[i][j] = min_{l in S} (M[i][l] + M[l][j] - M[l][l])

    This is the Barvinok-style factorization through relay columns.
    """
    k = M.shape[0]
    assert M.shape[0] == M.shape[1]

    def relay_covers(S):
        for i in range(k):
            for j in range(k):
                val = min(M[i, l] + M[l, j] - M[l, l] for l in S)
                if abs(val - M[i, j]) > 1e-9:
                    return False
        return True

    for r in range(1, k + 1):
        for S in combinations(range(k), r):
            if relay_covers(S):
                return r
    return k  # fallback


def check_tropical_dependence(M):
    """Check all column pairs for tropical dependence.
    Columns j1, j2 are tropically dependent if M[:,j2] - M[:,j1] is constant.
    Returns set of dependent pairs.
    """
    k = M.shape[1]
    dependent = set()
    for j1, j2 in combinations(range(k), 2):
        diff = M[:, j2] - M[:, j1]
        if np.allclose(diff, diff[0]):
            dependent.add((j1, j2))
    return dependent


def check_uniform_ordering(M):
    """Check all column pairs for uniform ordering.
    Pair (j1, j2) is uniformly ordered if M[i][j1] < M[i][j2] for ALL i,
    or M[i][j1] > M[i][j2] for ALL i.
    Returns set of uniformly-ordered pairs (as frozensets).
    """
    k = M.shape[1]
    uniform = set()
    for j1, j2 in combinations(range(k), 2):
        diff = M[:, j1] - M[:, j2]
        if np.all(diff < 0) or np.all(diff > 0):
            uniform.add(frozenset((j1, j2)))
    return uniform


def check_relay_failure(M, adj):
    """For each connected pair (j1, j2) in the column ordering graph,
    check if there exists a row where j2 <= j1 AND a row where j1 <= j2.
    If one direction has NO valid relay row, that's a failure.

    Returns list of (j1, j2, direction) where relay fails.
    """
    k = M.shape[0]
    failures = []
    checked = set()
    for j1 in adj:
        for j2 in adj[j1]:
            pair = frozenset((j1, j2))
            if pair in checked:
                continue
            checked.add(pair)
            # Check j1->j2 direction: need row i' with M[i'][j1] <= M[i'][j2]
            has_j1_to_j2 = any(M[i, j1] <= M[i, j2] for i in range(k))
            # Check j2->j1 direction: need row i' with M[i'][j2] <= M[i'][j1]
            has_j2_to_j1 = any(M[i, j2] <= M[i, j1] for i in range(k))
            if not has_j1_to_j2:
                failures.append((j1, j2, "j1->j2"))
            if not has_j2_to_j1:
                failures.append((j1, j2, "j2->j1"))
    return failures


def generate_distinct_matrix(k):
    """Generate k×k matrix with all k² entries distinct."""
    vals = np.random.permutation(k * k).astype(float)
    return vals.reshape(k, k)


def run_experiment(k, n_samples):
    print(f"\n{'='*70}")
    print(f"k={k}, samples={n_samples}")
    print(f"{'='*70}")

    stats = {
        "dismountable": {
            "count": 0,
            "trop_ranks": [],
            "has_dependent": 0,
            "has_uniform": 0,
            "relay_failures": 0,
        },
        "non_dismountable": {
            "count": 0,
            "trop_ranks": [],
            "has_dependent": 0,
            "has_uniform": 0,
            "relay_failures": 0,
            "relay_failure_examples": [],
            "uniform_connected_pairs": 0,
            "uniform_connected_examples": [],
        },
    }

    for trial in range(n_samples):
        if (trial + 1) % max(1, n_samples // 10) == 0:
            print(f"  Progress: {trial+1}/{n_samples}")

        M = generate_distinct_matrix(k)
        adj = column_ordering_graph(M)
        connected = is_connected(adj, k)

        key = "non_dismountable" if connected else "dismountable"
        s = stats[key]
        s["count"] += 1

        # Tropical rank (skip for k>=6 to save time on dismountable)
        if k <= 5 or key == "non_dismountable" or s["count"] <= 200:
            tr = tropical_rank_relay(M)
            s["trop_ranks"].append(tr)

        # Tropical dependence
        dep = check_tropical_dependence(M)
        if dep:
            s["has_dependent"] += 1

        # Uniform ordering
        uniform = check_uniform_ordering(M)
        if uniform:
            s["has_uniform"] += 1

        # For non-dismountable: check relay failures and uniform connected pairs
        if key == "non_dismountable":
            failures = check_relay_failure(M, adj)
            if failures:
                s["relay_failures"] += 1
                if len(s["relay_failure_examples"]) < 3:
                    s["relay_failure_examples"].append((M.copy(), failures))

            # Check uniform pairs that are connected
            connected_edges = set()
            for j1 in adj:
                for j2 in adj[j1]:
                    connected_edges.add(frozenset((j1, j2)))
            uniform_and_connected = uniform & connected_edges
            if uniform_and_connected:
                s["uniform_connected_pairs"] += 1
                if len(s["uniform_connected_examples"]) < 3:
                    s["uniform_connected_examples"].append(
                        (M.copy(), uniform_and_connected)
                    )

    # Print results
    for label, s in stats.items():
        print(f"\n--- {label} (n={s['count']}) ---")
        if s["count"] == 0:
            print("  (no samples)")
            continue

        if s["trop_ranks"]:
            ranks = np.array(s["trop_ranks"])
            print(f"  Tropical rank: avg={ranks.mean():.2f}, min={ranks.min()}, max={ranks.max()}")
            print(f"    Full rank (={k}): {np.sum(ranks == k)}/{len(ranks)} = {100*np.mean(ranks == k):.1f}%")
            for r in range(1, k + 1):
                ct = np.sum(ranks == r)
                if ct > 0:
                    print(f"    rank={r}: {ct}/{len(ranks)} = {100*ct/len(ranks):.1f}%")

        print(f"  Has tropically dependent pair: {s['has_dependent']}/{s['count']} = {100*s['has_dependent']/s['count']:.2f}%")
        print(f"  Has uniformly-ordered pair: {s['has_uniform']}/{s['count']} = {100*s['has_uniform']/s['count']:.2f}%")

        if label == "non_dismountable":
            print(f"\n  ** KEY: Relay failures (connected pair missing one direction): {s['relay_failures']}/{s['count']}")
            if s["relay_failure_examples"]:
                for idx, (M_ex, fails) in enumerate(s["relay_failure_examples"]):
                    print(f"    Example {idx+1}: {fails}")
                    print(f"    Matrix:\n{M_ex}")

            print(f"  ** KEY: Uniform-ordered connected pairs: {s['uniform_connected_pairs']}/{s['count']}")
            if s["uniform_connected_examples"]:
                for idx, (M_ex, pairs) in enumerate(s["uniform_connected_examples"]):
                    print(f"    Example {idx+1}: pairs={pairs}")
                    print(f"    Matrix:\n{M_ex}")


if __name__ == "__main__":
    # k=3,4: 10000 samples; k=5: 5000; k=6: 1000
    for k, n in [(3, 10000), (4, 10000), (5, 5000), (6, 1000)]:
        run_experiment(k, n)

    print("\n\nDONE.")
