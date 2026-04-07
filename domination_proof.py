"""
Why cross edges alone span A-A and B-B pairs.

Claim: In an extremally matched biclique, no row dominates another row
and no column dominates another column.

Proof sketch:
- Row i dominates row i' means M[i][j] > M[i'][j] for ALL j.
- M⁻ is a permutation → m⁻(j₁) = i for some j₁ → M[i][j₁] ≤ M[r][j₁]
  for all r → M[i][j₁] ≤ M[i'][j₁]. Contradicts M[i][j₁] > M[i'][j₁].
- Column domination: symmetric using M⁺.

Consequence:
- For all i ≠ i': ∃ j with M[i][j] < M[i'][j] → a_i → b_j → a_{i'} is
  a valid 2-hop temporal journey.
- For all j ≠ j': ∃ i with M[i][j] < M[i][j'] → b_j → a_i → b_{j'} is
  a valid 2-hop temporal journey.

This is the foundation for cross-only spanning.

Let's verify this and understand the structure of the non-domination.
"""

import random
from collections import defaultdict

random.seed(42)


def generate_sm_matrix(k):
    """SM(k) cross-edge matrix: M[i][j] = (j - i) % k mapped to timestamps."""
    # In SM(k), diagonal d has timestamp base + d*k + position
    # More precisely: cross edges ordered by diagonal, then by row within diagonal
    M = [[0] * k for _ in range(k)]
    t = 1
    for d in range(k):
        for i in range(k):
            j = (i + d) % k
            M[i][j] = t
            t += 1
    return M


def generate_random_extremal_matrix(k, max_attempts=1000):
    """Generate a k×k all-distinct matrix with M⁻ and M⁺ being permutations."""
    for _ in range(max_attempts):
        m_minus = list(range(k))
        random.shuffle(m_minus)
        m_plus = list(range(k))
        random.shuffle(m_plus)

        # Build partial order on cross edges
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

        M = [[0] * k for _ in range(k)]
        time_map = [0] * (k * k)
        for rank, node in enumerate(order):
            time_map[node] = rank + 1

        for i in range(k):
            for j in range(k):
                M[i][j] = time_map[edge_idx[(i, j)]]

        return M, m_minus, m_plus

    return None


def check_row_domination(M, k):
    """Check if any row dominates another. Return dominating pairs."""
    dominates = []
    for i in range(k):
        for ip in range(k):
            if i == ip:
                continue
            if all(M[i][j] > M[ip][j] for j in range(k)):
                dominates.append((i, ip))
    return dominates


def check_col_domination(M, k):
    """Check if any column dominates another."""
    dominates = []
    for j in range(k):
        for jp in range(k):
            if j == jp:
                continue
            if all(M[i][j] > M[i][jp] for i in range(k)):
                dominates.append((j, jp))
    return dominates


def non_domination_witnesses(M, k):
    """For each pair (i, i'), find the column j where M[i][j] < M[i'][j].
    For each pair (j, j'), find the row i where M[i][j] < M[i][j'].
    Return the witness structure."""
    row_witnesses = {}
    for i in range(k):
        for ip in range(k):
            if i == ip:
                continue
            witnesses = [j for j in range(k) if M[i][j] < M[ip][j]]
            row_witnesses[(i, ip)] = witnesses

    col_witnesses = {}
    for j in range(k):
        for jp in range(k):
            if j == jp:
                continue
            witnesses = [i for i in range(k) if M[i][j] < M[i][jp]]
            col_witnesses[(j, jp)] = witnesses

    return row_witnesses, col_witnesses


def analyze_witness_coverage(row_witnesses, col_witnesses, k):
    """Which columns are used as witnesses for A-A pairs?
    Which rows are used as witnesses for B-B pairs?
    Can we cover all pairs with O(k) witness edges?"""

    # For A-A: pair (i, i') uses column j → needs edges (i, j) and (i', j)
    # For B-B: pair (j, j') uses row i → needs edges (i, j) and (i, j')
    # For A-B: pair (i, j) needs edge (i, j) directly

    # Greedy set cover: pick the column that covers the most A-A pairs
    uncovered_aa = set()
    for i in range(k):
        for ip in range(k):
            if i != ip:
                uncovered_aa.add((i, ip))

    col_usage = defaultdict(int)
    greedy_cols = []
    while uncovered_aa:
        # Count how many uncovered pairs each column covers
        col_covers = defaultdict(set)
        for (i, ip) in uncovered_aa:
            for j in row_witnesses[(i, ip)]:
                col_covers[j].add((i, ip))
        best_col = max(col_covers, key=lambda j: len(col_covers[j]))
        greedy_cols.append((best_col, len(col_covers[best_col])))
        uncovered_aa -= col_covers[best_col]

    uncovered_bb = set()
    for j in range(k):
        for jp in range(k):
            if j != jp:
                uncovered_bb.add((j, jp))

    greedy_rows = []
    while uncovered_bb:
        row_covers = defaultdict(set)
        for (j, jp) in uncovered_bb:
            for i in col_witnesses[(j, jp)]:
                row_covers[i].add((j, jp))
        best_row = max(row_covers, key=lambda i: len(row_covers[i]))
        greedy_rows.append((best_row, len(row_covers[best_row])))
        uncovered_bb -= row_covers[best_row]

    return greedy_cols, greedy_rows


def main():
    print("=" * 70)
    print("NON-DOMINATION PROOF VERIFICATION")
    print("=" * 70)

    # Part 1: Verify non-domination for SM(k) and random bicliques
    print("\n--- Non-domination check ---")
    for k in range(3, 10):
        M = generate_sm_matrix(k)
        row_dom = check_row_domination(M, k)
        col_dom = check_col_domination(M, k)
        print(f"SM({k}): row_dom={len(row_dom)}, col_dom={len(col_dom)}")

    print()
    for k in range(3, 9):
        n_samples = {3: 1000, 4: 500, 5: 200, 6: 100, 7: 50, 8: 20}[k]
        row_dom_found = 0
        col_dom_found = 0
        for _ in range(n_samples):
            result = generate_random_extremal_matrix(k)
            if result is None:
                continue
            M, mm, mp = result
            if check_row_domination(M, k):
                row_dom_found += 1
            if check_col_domination(M, k):
                col_dom_found += 1
        print(f"Random k={k} ({n_samples} samples): "
              f"row_dom={row_dom_found}, col_dom={col_dom_found}")

    # Part 2: Proof verification — the specific argument
    print("\n\n--- Proof argument verification ---")
    print("Claim: M⁻ permutation → no row dominates another")
    print()
    for k in [4, 5, 6]:
        M = generate_sm_matrix(k)
        # M⁻ for SM(k): m_minus[j] = j (diagonal 0 is earliest per column)
        m_minus = list(range(k))

        print(f"SM({k}) matrix:")
        for i in range(k):
            print(f"  row {i}: {M[i]}")
        print(f"  M⁻: {m_minus}")

        # For each pair, show the witness
        row_w, col_w = non_domination_witnesses(M, k)
        print(f"  A-A witnesses (column j where M[i][j] < M[i'][j]):")
        for i in range(min(k, 4)):
            for ip in range(min(k, 4)):
                if i != ip:
                    ws = row_w[(i, ip)]
                    print(f"    a{i}→a{ip}: columns {ws} "
                          f"(use j={ws[0]}: M[{i}][{ws[0]}]={M[i][ws[0]]} "
                          f"< M[{ip}][{ws[0]}]={M[ip][ws[0]]})")

        print(f"  B-B witnesses (row i where M[i][j] < M[i][j']):")
        for j in range(min(k, 4)):
            for jp in range(min(k, 4)):
                if j != jp:
                    ws = col_w[(j, jp)]
                    print(f"    b{j}→b{jp}: rows {ws[:3]}{'...' if len(ws)>3 else ''}")
        print()

    # Part 3: Witness coverage — can O(k) witness columns cover all A-A pairs?
    print("\n--- Witness coverage analysis ---")
    for k in range(3, 10):
        M = generate_sm_matrix(k)
        row_w, col_w = non_domination_witnesses(M, k)
        greedy_cols, greedy_rows = analyze_witness_coverage(row_w, col_w, k)

        total_aa = k * (k - 1)
        total_bb = k * (k - 1)

        print(f"\nSM({k}):")
        print(f"  A-A pairs: {total_aa}, covered by {len(greedy_cols)} columns:")
        for col, count in greedy_cols:
            print(f"    col {col}: covers {count} pairs")
        print(f"  B-B pairs: {total_bb}, covered by {len(greedy_rows)} rows:")
        for row, count in greedy_rows:
            print(f"    row {row}: covers {count} pairs")

        # Minimum edges needed for witness coverage
        # Each witness column j used for A-A needs edges (i, j) for all i in covered pairs
        # This is at most k edges per column (all rows connect to that column)
        # But we only need the edges for the specific pairs
        witness_edges = set()
        for (i, ip), cols in row_w.items():
            j = cols[0]  # use first witness
            witness_edges.add((i, j))
            witness_edges.add((ip, j))
        for (j, jp), rows in col_w.items():
            i = rows[0]
            witness_edges.add((i, j))
            witness_edges.add((i, jp))
        # Also need M⁻ and M⁺ for A-B connectivity
        m_minus = list(range(k))  # SM(k)
        m_plus = [(i + k - 1) % k for i in range(k)]
        for j in range(k):
            witness_edges.add((m_minus[j], j))
        for i in range(k):
            witness_edges.add((i, m_plus[i]))

        print(f"  Total witness edges (naive): {len(witness_edges)}")
        print(f"  2n-3 = {2*(2*k)-3}, witness/bound = "
              f"{len(witness_edges)/(2*(2*k)-3):.2f}")

    # Part 4: The proof sketch
    print("\n\n" + "=" * 70)
    print("PROOF SKETCH: Cross-only spanning via non-domination")
    print("=" * 70)
    print("""
Theorem: In an extremally matched biclique with k×k timestamp matrix M,
cross edges alone provide 2-hop temporal connectivity for all pairs.

Proof:
  (A-A pairs) Fix i ≠ i'. Since M⁻ is a permutation, ∃ j₁ with
  m⁻(j₁) = i, meaning M[i][j₁] ≤ M[r][j₁] for all r. In particular,
  M[i][j₁] ≤ M[i'][j₁]. If strict: done (column j₁ witnesses).
  If equal: contradicts all-distinct. So M[i][j₁] < M[i'][j₁].
  Journey: a_i →[cross(i,j₁)] b_{j₁} →[cross(i',j₁)] a_{i'}.  ∎

  (B-B pairs) Fix j ≠ j'. Since M⁺ is a permutation, ∃ i₁ with
  m⁺(i₁) = j, meaning M[i₁][j] ≥ M[i₁][r] for all r. In particular,
  M[i₁][j] ≥ M[i₁][j']. If strict: column j has larger value than j'
  in row i₁ → M[i₁][j'] < M[i₁][j].
  Journey: b_{j'} ←[cross(i₁,j')] a_{i₁} →[cross(i₁,j)] b_j.
  Wait — this goes b_{j'} → a_{i₁} → b_j, which needs M[i₁][j'] < M[i₁][j].
  We showed M[i₁][j'] < M[i₁][j]. ✓
  But we want b_j → b_{j'}, not b_{j'} → b_j!

  Fix: we want b_j → b_{j'}. Need row i with M[i][j] < M[i][j'].
  This is "column j doesn't dominate column j'."
  Suppose column j dominates j': M[i][j] > M[i][j'] for all i.
  Since M⁺ is a permutation, ∃ i₁ with m⁺(i₁) = j'.
  Then M[i₁][j'] ≥ M[i₁][r] for all r, including r = j.
  So M[i₁][j'] ≥ M[i₁][j]. But domination gives M[i₁][j] > M[i₁][j'].
  Contradiction. ∎
""")


if __name__ == '__main__':
    main()
