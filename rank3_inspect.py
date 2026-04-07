"""
Inspect the rank-3 cases. What matrices have reachability rank > 2?
"""

import random
from itertools import combinations


def compute_full_reach_minus(M):
    k = len(M)
    R = [[False] * k for _ in range(k)]
    for i in range(k):
        R[i][i] = True
        for ip in range(k):
            if i == ip: continue
            for j in range(k):
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
    return R


def reach_rank_minus(M, R_target):
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


def compute_full_reach_plus(M):
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


def reach_rank_plus(M, R_target):
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


def run():
    random.seed(42)

    # Find rank-3 instances
    print("Searching for rank-3 matrices...")
    rank3_examples = []

    for trial in range(100000):
        k = 4
        vals = list(range(1, k * k + 1))
        random.shuffle(vals)
        M = [[0] * k for _ in range(k)]
        idx = 0
        for i in range(k):
            for j in range(k):
                M[i][j] = vals[idx]; idx += 1

        R_minus = compute_full_reach_minus(M)
        rm, cols = reach_rank_minus(M, R_minus)
        if rm >= 3:
            rank3_examples.append((M, R_minus, rm, cols, 'V-'))

        R_plus = compute_full_reach_plus(M)
        rp, rows = reach_rank_plus(M, R_plus)
        if rp >= 3:
            rank3_examples.append((M, R_plus, rp, rows, 'V+'))

        if len(rank3_examples) >= 10:
            break

    print(f"Found {len(rank3_examples)} rank-3 examples in {trial+1} trials")

    for idx, (M, R, rank, relays, side) in enumerate(rank3_examples[:5]):
        k = len(M)
        print(f"\nExample {idx+1} ({side}, rank={rank}):")
        print(f"  Matrix:")
        for row in M:
            print(f"    {row}")

        print(f"  Reachability (R[i][j] = can i reach j):")
        for i in range(k):
            row = ""
            for j in range(k):
                row += "1 " if R[i][j] else ". "
            print(f"    {row}")

        # Which pair needs 3 relays?
        # For each pair of columns, which pairs are NOT reachable?
        print(f"  Pairs requiring 3rd relay:")
        for c1 in range(k):
            for c2 in range(c1 + 1, k):
                R_sub = [[False] * k for _ in range(k)]
                for i in range(k):
                    R_sub[i][i] = True
                    for ip in range(k):
                        if i == ip: continue
                        for j in [c1, c2]:
                            if M[i][j] <= M[ip][j]:
                                R_sub[i][ip] = True
                                break
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
                missing = []
                for i in range(k):
                    for ip in range(k):
                        if R[i][ip] and not R_sub[i][ip]:
                            missing.append((i, ip))
                if missing:
                    print(f"    cols {{{c1},{c2}}}: missing {missing}")

        # What's special about these row/column values?
        print(f"  Column analysis:")
        for j in range(k):
            col = [M[i][j] for i in range(k)]
            sorted_col = sorted(range(k), key=lambda i: col[i])
            print(f"    col {j}: values={col}, sorted_rows={sorted_col}")

        # Check: is the 2-hop reachability already incomplete?
        R2 = [[False] * k for _ in range(k)]
        for i in range(k):
            R2[i][i] = True
            for ip in range(k):
                if i == ip: continue
                for j in range(k):
                    if M[i][j] <= M[ip][j]:
                        R2[i][ip] = True
                        break
        r2_complete = all(R2[i][ip] for i in range(k) for ip in range(k))
        print(f"  2-hop reachability complete: {r2_complete}")
        if not r2_complete:
            for i in range(k):
                for ip in range(k):
                    if i != ip and not R2[i][ip]:
                        print(f"    NOT reachable in 2-hop: {i} → {ip}")
                        # Why? For all j: M[i][j] > M[ip][j]
                        for j in range(k):
                            print(f"      col {j}: M[{i}][{j}]={M[i][j]} vs M[{ip}][{j}]={M[ip][j]} {'≤' if M[i][j] <= M[ip][j] else '>'}")


if __name__ == "__main__":
    run()
