"""
Find relays via tropical algebra.

In the max-plus semiring:
  (A ⊕ B)[i][j] = max(A[i][j], B[i][j])
  (A ⊗ B)[i][j] = max_l(A[i][l] + B[l][j])

The temporal reachability problem: aᵢ reaches aᵢ' iff ∃j with M[i][j] ≤ M[i'][j].
This is: in the matrix where R[i][i'] = max_j (M[i'][j] - M[i][j]),
row i reaches row i' iff R[i][i'] ≥ 0.

The tropical eigenvalues of R tell us the relay structure.
The dominant eigenvector identifies the best relay vertex.

Also: the tropical rank of M itself — can M be factored as
M = U ⊗ V (max-plus) with U: k×r, V: r×k, r small?
"""

import random
from itertools import combinations


def generate_sm_matrix(k):
    offset = k * (k - 1) // 2
    M = [[0] * k for _ in range(k)]
    for d in range(k):
        for i in range(k):
            j = (i + d) % k
            M[i][j] = offset + d * k + i + 1
    return M


def random_biclique_matrix(k):
    offset = k * (k - 1) // 2
    vals = list(range(offset + 1, offset + k * k + 1))
    random.shuffle(vals)
    M = [[0] * k for _ in range(k)]
    idx = 0
    for i in range(k):
        for j in range(k):
            M[i][j] = vals[idx]; idx += 1
    return M


def reachability_matrix(M):
    """R[i][i'] = max_j (M[i'][j] - M[i][j]).
    i reaches i' iff R[i][i'] ≥ 0."""
    k = len(M)
    R = [[0] * k for _ in range(k)]
    for i in range(k):
        for ip in range(k):
            R[i][ip] = max(M[ip][j] - M[i][j] for j in range(k))
    return R


def reachability_argmax(M):
    """For each pair (i, i'), which column j achieves the max of M[i'][j] - M[i][j]?
    This is the relay column for that pair."""
    k = len(M)
    relay = [[0] * k for _ in range(k)]
    for i in range(k):
        for ip in range(k):
            best_j = max(range(k), key=lambda j: M[ip][j] - M[i][j])
            relay[i][ip] = best_j
    return relay


def tropical_maxplus_matmul(A, B):
    """Max-plus matrix multiplication."""
    k = len(A)
    m = len(B[0])
    r = len(B)
    C = [[float('-inf')] * m for _ in range(k)]
    for i in range(k):
        for j in range(m):
            for l in range(r):
                C[i][j] = max(C[i][j], A[i][l] + B[l][j])
    return C


def tropical_eigenvalue(M):
    """Tropical eigenvalue of a square matrix (max-plus).
    λ = max over all cycles C of (weight(C) / length(C))
    where weight(C) = sum of M[i][next(i)] along the cycle.

    For the reachability matrix, this tells us the "growth rate"
    of reachability — how quickly journeys compose."""
    k = len(M)

    # Find all cycles and their average weight
    best_lambda = float('-inf')
    best_cycle = None

    # Check cycles of each length
    for length in range(1, k + 1):
        # For length 1: diagonal
        if length == 1:
            for i in range(k):
                lam = M[i][i]
                if lam > best_lambda:
                    best_lambda = lam
                    best_cycle = [i]
            continue

        # For length 2+: enumerate
        for start in range(k):
            def find_cycles(node, path, remaining):
                nonlocal best_lambda, best_cycle
                if remaining == 0:
                    # Check if we can close the cycle
                    weight = sum(M[path[i]][path[i+1]] for i in range(len(path)-1))
                    weight += M[path[-1]][path[0]]
                    avg = weight / len(path)
                    if avg > best_lambda:
                        best_lambda = avg
                        best_cycle = list(path)
                    return
                for next_node in range(k):
                    if next_node not in path:
                        path.append(next_node)
                        find_cycles(next_node, path, remaining - 1)
                        path.pop()

            find_cycles(start, [start], length - 1)

    return best_lambda, best_cycle


def analyze_relay_structure(M):
    """For each pair, find which column is the natural relay.
    If the same 2 columns appear for most pairs, those are the relays."""
    k = len(M)
    relay_map = reachability_argmax(M)

    # Count how often each column appears as relay
    col_counts = [0] * k
    for i in range(k):
        for ip in range(k):
            if i != ip:
                col_counts[relay_map[i][ip]] += 1

    # Top 2 columns
    ranked = sorted(range(k), key=lambda j: -col_counts[j])
    top2 = ranked[:2]
    top2_coverage = sum(1 for i in range(k) for ip in range(k)
                        if i != ip and relay_map[i][ip] in top2)
    total = k * (k - 1)

    return {
        'col_counts': col_counts,
        'top2': top2,
        'top2_coverage': top2_coverage,
        'total': total,
        'top2_pct': top2_coverage / total * 100 if total > 0 else 0,
    }


def check_2col_sufficiency(M, cols):
    """Do these 2 columns preserve all reachability (with transitive closure)?"""
    k = len(M)
    # Direct reachability via these columns
    R = [[False] * k for _ in range(k)]
    for i in range(k):
        R[i][i] = True
        for ip in range(k):
            if i == ip: continue
            for j in cols:
                if M[i][j] <= M[ip][j]:
                    R[i][ip] = True
                    break
    # Transitive closure
    changed = True
    while changed:
        changed = False
        for i in range(k):
            for ip in range(k):
                if R[i][ip]:
                    for ipp in range(k):
                        if R[ip][ipp] and not R[i][ipp]:
                            R[i][ipp] = True
                            changed = True
    # Full reachability
    R_full = [[False] * k for _ in range(k)]
    for i in range(k):
        R_full[i][i] = True
        for ip in range(k):
            if i == ip: continue
            for j in range(k):
                if M[i][j] <= M[ip][j]:
                    R_full[i][ip] = True
                    break
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

    return R == R_full


def run():
    random.seed(42)

    print("Tropical relay identification")
    print("=" * 60)

    for k in range(3, 9):
        M = generate_sm_matrix(k)
        print(f"\nSM({k}):")

        # Reachability matrix
        R = reachability_matrix(M)
        relay = analyze_relay_structure(M)
        print(f"  Relay column frequency: {relay['col_counts']}")
        print(f"  Top 2 columns: {relay['top2']} ({relay['top2_pct']:.0f}% coverage)")

        # Check if top 2 columns actually suffice
        suffices = check_2col_sufficiency(M, relay['top2'])
        print(f"  Top 2 suffice: {suffices}")

        # Tropical eigenvalue of reachability matrix
        if k <= 7:
            lam, cycle = tropical_eigenvalue(R)
            print(f"  Tropical eigenvalue: {lam:.2f}, cycle: {cycle}")

    print(f"\n{'='*60}")
    print("Random bicliques")
    print("=" * 60)

    for k in [4, 5, 6, 7]:
        top2_works = 0
        argmax_works = 0
        samples = 500 if k <= 5 else 100
        for _ in range(samples):
            M = random_biclique_matrix(k)
            relay = analyze_relay_structure(M)

            # Do top-2 argmax columns suffice?
            if check_2col_sufficiency(M, relay['top2']):
                argmax_works += 1

            # Do ANY 2 columns suffice?
            for c1 in range(k):
                for c2 in range(c1+1, k):
                    if check_2col_sufficiency(M, [c1, c2]):
                        top2_works += 1
                        break
                else:
                    continue
                break

        print(f"\n  k={k} ({samples} samples):")
        print(f"    Any 2 cols suffice: {top2_works}/{samples} ({top2_works/samples*100:.1f}%)")
        print(f"    Top-2 argmax suffice: {argmax_works}/{samples} ({argmax_works/samples*100:.1f}%)")


if __name__ == "__main__":
    run()
