"""
Tropical rank of bi-clique timestamp matrices.

M[i][j] = t(a_i, b_j) for the bi-clique.

Barvinok tropical rank: min r such that M = U ⊗ V (min-plus)
where U is k×r, V is r×k, and (U ⊗ V)[i][j] = min_l (U[i][l] + V[l][j]).

Kapranov rank: min r such that M = trop_sum of r rank-1 matrices.
A tropical rank-1 matrix has form u_i + v_j.

For the reachability problem, we care about a different "rank":
the min r such that all temporal reachability in M can be routed
through r intermediate "relay" columns.

Specifically: define R[i][i'] = 1 iff ∃j with M[i][j] ≤ M[i'][j].
The "reachability rank" is the min number of columns j needed so that
R is fully preserved.

Also compute: tropical eigenvalues of the circulant SM(k).
"""

import random
from itertools import combinations


def generate_sm_matrix(k):
    """Return the k×k cross-edge matrix of SM(k)."""
    # M[i][j] = timestamp of edge (a_i, b_j)
    # In SM(k), diagonal d = (j-i) mod k gets timestamps in order
    # Internal V- edges: 1..k(k-1)/2
    # Cross diagonal d: k(k-1)/2 + d*k + 1 .. k(k-1)/2 + (d+1)*k
    offset = k * (k - 1) // 2
    M = [[0] * k for _ in range(k)]
    for d in range(k):
        for i in range(k):
            j = (i + d) % k
            M[i][j] = offset + d * k + i + 1
    return M


def tropical_matmul_minplus(U, V):
    """Min-plus matrix multiplication."""
    r1 = len(U)
    r2 = len(U[0])
    c2 = len(V[0])
    result = [[float('inf')] * c2 for _ in range(r1)]
    for i in range(r1):
        for j in range(c2):
            for l in range(r2):
                result[i][j] = min(result[i][j], U[i][l] + V[l][j])
    return result


def kapranov_rank(M):
    """Compute Kapranov rank: min r such that M[i][j] = min over r terms of (u_l[i] + v_l[j]).
    Brute force for small matrices."""
    k = len(M)

    for r in range(1, k + 1):
        # Try to find r rank-1 tropical matrices that sum (min) to M
        # Rank-1: A_l[i][j] = u_l[i] + v_l[j]
        # M[i][j] = min_l (u_l[i] + v_l[j])
        # This is equivalent to tropical rank.

        # For r=1: M[i][j] = u[i] + v[j]. Check: M[i][j] - M[i][0] = v[j] - v[0]
        # must be same for all i.
        if r == 1:
            diffs = set()
            for j in range(k):
                col_diffs = tuple(M[i][j] - M[i][0] for i in range(k))
                diffs.add(col_diffs)
            if len(diffs) == 1:
                return 1
            continue

        # For general r: NP-hard in general, but k is small enough to check
        # We use a heuristic: try columns of M as the relay points
        # If we pick r columns j_1..j_r, define:
        # U[i][l] = M[i][j_l], V[l][j] = M[??][j] - hmm, this doesn't work directly

        # Actually, for Barvinok rank: M = U ⊗ V means
        # M[i][j] = min_l (U[i][l] + V[l][j])
        # Try: U[i][l] = M[i][j_l] - c_l, V[l][j] = c_l + M[j_l][j] for some columns j_l
        # Then (U⊗V)[i][j] = min_l (M[i][j_l] + M[j_l][j] - c_l + c_l) = min_l(M[i][j_l] + M[j_l][j])
        # Nope, that's the min-plus square of M through specific relays.

        # Different approach: check all subsets of r columns
        # If restricting to r relay columns preserves reachability, the "reachability rank" is r
        pass

    return k  # full rank fallback


def reachability_rank(M):
    """Min number of relay columns needed to preserve all temporal reachability.

    R[i][i'] = 1 iff ∃j with M[i][j] ≤ M[i'][j] (can go a_i → b_j → a_i').
    Reachability rank = min r columns that preserve R.

    Also compute multi-hop reachability (4-hop, 6-hop...).
    """
    k = len(M)

    # Full reachability matrix (2-hop): R[i][i'] via single relay
    R2 = [[False] * k for _ in range(k)]
    for i in range(k):
        R2[i][i] = True
        for ip in range(k):
            if i == ip:
                continue
            for j in range(k):
                if M[i][j] <= M[ip][j]:
                    R2[i][ip] = True
                    break

    # Multi-hop reachability (transitive closure)
    R_full = [row[:] for row in R2]
    changed = True
    while changed:
        changed = False
        for i in range(k):
            for ip in range(k):
                if R_full[i][ip]:
                    for ipp in range(k):
                        if R_full[ip][ipp] and not R_full[i][ipp]:
                            R_full[i][ipp] = True
                            changed = True

    # Count how many 2-hop pairs are reachable
    r2_count = sum(1 for i in range(k) for j in range(k) if R2[i][j] and i != j)
    rf_count = sum(1 for i in range(k) for j in range(k) if R_full[i][j] and i != j)
    total = k * (k - 1)

    print(f"    2-hop reachability: {r2_count}/{total} ({r2_count/total*100:.0f}%)")
    print(f"    Full reachability:  {rf_count}/{total} ({rf_count/total*100:.0f}%)")

    # Reachability rank: min columns to preserve R_full
    for r in range(1, k + 1):
        for cols in combinations(range(k), r):
            # Check: using only relay columns in 'cols', does reachability survive?
            R_sub = [[False] * k for _ in range(k)]
            for i in range(k):
                R_sub[i][i] = True
                for ip in range(k):
                    if i == ip:
                        continue
                    for j in cols:
                        if M[i][j] <= M[ip][j]:
                            R_sub[i][ip] = True
                            break

            # Transitive closure of R_sub
            changed = True
            while changed:
                changed = False
                for i in range(k):
                    for ip in range(k):
                        if R_sub[i][ip]:
                            for ipp in range(k):
                                if R_sub[ip][ipp] and not R_sub[i][ipp]:
                                    R_sub[i][ipp] = True
                                    changed = True

            if R_sub == R_full:
                return r, list(cols)

    return k, list(range(k))


def reachability_rank_bidir(M):
    """Reachability rank considering both directions:
    V- to V- (through V+) AND V+ to V+ (through V-).

    For V+ to V+: R_plus[j][j'] = 1 iff ∃i with M[i][j] >= M[i][j']
    (going from b_j to a_i at time M[i][j], then a_i to b_j' at time M[i][j'] ≥ M[i][j]...
    wait, that's backwards. Let me think.)

    Journey b_j → a_i requires using edge (a_i, b_j) at time M[i][j].
    Then a_i → b_j' at time M[i][j'] ≥ M[i][j].
    So R_plus[j][j'] iff ∃i with M[i][j] ≤ M[i][j'].
    Same form as R_minus but with rows as relays and columns as endpoints.
    """
    k = len(M)

    # V- to V-: relay through columns (V+ vertices)
    # V+ to V+: relay through rows (V- vertices)

    # V+ reachability
    R_plus = [[False] * k for _ in range(k)]
    for j in range(k):
        R_plus[j][j] = True
        for jp in range(k):
            if j == jp:
                continue
            for i in range(k):
                if M[i][j] <= M[i][jp]:
                    R_plus[j][jp] = True
                    break

    rp_count = sum(1 for j in range(k) for jp in range(k) if R_plus[j][jp] and j != jp)
    total = k * (k - 1)
    print(f"    V+ 2-hop reach: {rp_count}/{total}")

    # V+ reachability rank: min rows needed
    for r in range(1, k + 1):
        for rows in combinations(range(k), r):
            R_sub = [[False] * k for _ in range(k)]
            for j in range(k):
                R_sub[j][j] = True
                for jp in range(k):
                    if j == jp: continue
                    for i in rows:
                        if M[i][j] <= M[i][jp]:
                            R_sub[j][jp] = True
                            break
            changed = True
            while changed:
                changed = False
                for j in range(k):
                    for jp in range(k):
                        if R_sub[j][jp]:
                            for jpp in range(k):
                                if R_sub[jp][jpp] and not R_sub[j][jpp]:
                                    R_sub[j][jpp] = True
                                    changed = True
            # Check full closure
            R_full_p = [row[:] for row in R_plus]
            ch = True
            while ch:
                ch = False
                for j in range(k):
                    for jp in range(k):
                        if R_full_p[j][jp]:
                            for jpp in range(k):
                                if R_full_p[jp][jpp] and not R_full_p[j][jpp]:
                                    R_full_p[j][jpp] = True
                                    ch = True
            if R_sub == R_full_p:
                return r, list(rows)

    return k, list(range(k))


def run():
    print("Tropical analysis of SM(k) bi-clique matrices")
    print("=" * 70)

    for k in range(3, 10):
        M = generate_sm_matrix(k)
        print(f"\nSM({k}): {k}×{k} matrix")

        # Show matrix
        if k <= 7:
            for i in range(k):
                print(f"    {M[i]}")

        # V- reachability rank
        print(f"\n  V- reachability (relay through V+ columns):")
        r_minus, cols = reachability_rank(M)
        print(f"    Reachability rank: {r_minus}, relay cols: {cols}")

        # V+ reachability rank
        print(f"\n  V+ reachability (relay through V- rows):")
        r_plus, rows = reachability_rank_bidir(M)
        print(f"    Reachability rank: {r_plus}, relay rows: {rows}")

        # Cross reachability: a_i to b_j
        # Direct: just use M[i][j]. Always reachable. 0 extra edges needed.
        # But for spanner: we only keep a subset of entries.
        # The "cross rank" is: min entries of M to keep so all a→b and b→a are reachable.

        print(f"\n  Summary: V- rank={r_minus}, V+ rank={r_plus}, "
              f"spanner ≈ 2k + rank relays = {2*k} + O({r_minus + r_plus})")


if __name__ == "__main__":
    run()
