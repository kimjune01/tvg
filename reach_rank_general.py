"""
Reachability rank for general bi-cliques, not just SM(k).

Test: is the reachability rank always ≤ 2?
If so, that's the proof: 2 relay columns + 2 relay rows = O(k) spanner.
"""

import random
from itertools import combinations


def compute_full_reach_minus(M):
    """V- to V- reachability: R[i][i'] iff ∃ path a_i → ... → a_i'
    through the bipartite graph with non-decreasing timestamps."""
    k = len(M)
    # 2-hop: R[i][i'] iff ∃j with M[i][j] ≤ M[i'][j]
    R = [[False] * k for _ in range(k)]
    for i in range(k):
        R[i][i] = True
        for ip in range(k):
            if i == ip: continue
            for j in range(k):
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
    return R


def compute_full_reach_plus(M):
    """V+ to V+ reachability: R[j][j'] iff ∃i with M[i][j] ≤ M[i][j']."""
    k = len(M)
    R = [[False] * k for _ in range(k)]
    for j in range(k):
        R[j][j] = True
        for jp in range(k):
            if j == jp: continue
            for i in range(k):
                if M[i][j] <= M[i][jp]:
                    R[j][jp] = True
                    break
    changed = True
    while changed:
        changed = False
        for j in range(k):
            for jp in range(k):
                if R[j][jp]:
                    for jpp in range(k):
                        if R[jp][jpp] and not R[j][jpp]:
                            R[j][jpp] = True
                            changed = True
    return R


def reach_rank_minus(M, R_target):
    """Min columns to preserve V- reachability."""
    k = len(M)
    for r in range(1, k + 1):
        for cols in combinations(range(k), r):
            R = [[False] * k for _ in range(k)]
            for i in range(k):
                R[i][i] = True
                for ip in range(k):
                    if i == ip: continue
                    for j in cols:
                        if M[i][j] <= M[ip][j]:
                            R[i][ip] = True
                            break
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
            if R == R_target:
                return r, list(cols)
    return k, list(range(k))


def reach_rank_plus(M, R_target):
    """Min rows to preserve V+ reachability."""
    k = len(M)
    for r in range(1, k + 1):
        for rows in combinations(range(k), r):
            R = [[False] * k for _ in range(k)]
            for j in range(k):
                R[j][j] = True
                for jp in range(k):
                    if j == jp: continue
                    for i in rows:
                        if M[i][j] <= M[i][jp]:
                            R[j][jp] = True
                            break
            changed = True
            while changed:
                changed = False
                for j in range(k):
                    for jp in range(k):
                        if R[j][jp]:
                            for jpp in range(k):
                                if R[jp][jpp] and not R[j][jpp]:
                                    R[j][jpp] = True
                                    changed = True
            if R == R_target:
                return r, list(rows)
    return k, list(range(k))


def random_biclique_matrix(k):
    """Random k×k bi-clique with structure:
    V- internal edges earliest, cross edges middle, V+ internal latest.
    Returns the cross-edge matrix only."""
    # Cross edges get timestamps in [offset+1, offset+k^2]
    offset = k * (k - 1) // 2
    vals = list(range(offset + 1, offset + k * k + 1))
    random.shuffle(vals)
    M = [[0] * k for _ in range(k)]
    idx = 0
    for i in range(k):
        for j in range(k):
            M[i][j] = vals[idx]
            idx += 1
    return M


def fully_random_matrix(k):
    """Fully random k×k matrix with distinct values 1..k^2."""
    vals = list(range(1, k * k + 1))
    random.shuffle(vals)
    M = [[0] * k for _ in range(k)]
    idx = 0
    for i in range(k):
        for j in range(k):
            M[i][j] = vals[idx]
            idx += 1
    return M


def run():
    random.seed(42)

    for matrix_type in ['biclique', 'fully_random']:
        print(f"\n{'='*70}")
        print(f"Matrix type: {matrix_type}")
        print(f"{'='*70}")

        for k in [3, 4, 5, 6, 7, 8]:
            samples = 500 if k <= 5 else (200 if k <= 6 else (50 if k <= 7 else 20))

            rank_minus_dist = {}
            rank_plus_dist = {}
            max_rank = 0

            for _ in range(samples):
                if matrix_type == 'biclique':
                    M = random_biclique_matrix(k)
                else:
                    M = fully_random_matrix(k)

                R_minus = compute_full_reach_minus(M)
                R_plus = compute_full_reach_plus(M)

                rm, _ = reach_rank_minus(M, R_minus)
                rp, _ = reach_rank_plus(M, R_plus)

                rank_minus_dist[rm] = rank_minus_dist.get(rm, 0) + 1
                rank_plus_dist[rp] = rank_plus_dist.get(rp, 0) + 1
                max_rank = max(max_rank, rm, rp)

            print(f"\n  k={k} ({samples} samples):")
            print(f"    V- rank dist: {dict(sorted(rank_minus_dist.items()))}")
            print(f"    V+ rank dist: {dict(sorted(rank_plus_dist.items()))}")
            print(f"    Max rank seen: {max_rank}")


if __name__ == "__main__":
    run()
