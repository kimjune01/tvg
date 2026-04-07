"""
Prove: in a k×k matrix with distinct entries, every dominated pair
has a crossing intermediate.

Dominated: row i dominates row i' iff M[i][j] > M[i'][j] for all j.

Crossing intermediate for (i, i'): row i'' such that
  ∃ j₁, j₂: M[i][j₁] ≤ M[i''][j₁] AND M[i''][j₂] ≤ M[i'][j₂]
  (i'' is above i in col j₁ and below i' in col j₂)

Bridge-less: no crossing intermediate exists for ANY column pair.
Equivalent: every other row is either
  - never above i (dominated by i), or
  - never below i' (dominates i'), or
  - strictly between in every column

Proof attempt: show bridge-less is impossible by analyzing the value
distribution forced by the permutation structure.

Key lemma: if row i dominates row i', consider column j* where
M[i][j*] - M[i'][j*] is MINIMIZED (tightest gap). In this column,
there are few values between M[i'][j*] and M[i][j*]. These few
values must be distributed among the "between" rows. But the between
rows also need values in OTHER columns, where the gaps are wider.
The permutation constraint forces at least one between-row to have
a value outside the gap in some column — creating a crossing.

Let's verify this and find the exact condition.
"""

import random
from itertools import combinations
from collections import defaultdict


def check_crossing(M, i, ip):
    """Check if dominated pair (i, i') has a crossing intermediate."""
    k = len(M)
    for ipp in range(k):
        if ipp == i or ipp == ip:
            continue
        above_i_cols = [j for j in range(k) if M[ipp][j] >= M[i][j]]
        below_ip_cols = [j for j in range(k) if M[ipp][j] <= M[ip][j]]
        if above_i_cols and below_ip_cols:
            return True, ipp, above_i_cols[0], below_ip_cols[0]
    return False, None, None, None


def check_bridge_less(M, i, ip):
    """Characterize the bridge-less structure."""
    k = len(M)
    zones = {}
    for ipp in range(k):
        if ipp == i or ipp == ip:
            continue
        above_i = [j for j in range(k) if M[ipp][j] >= M[i][j]]
        below_ip = [j for j in range(k) if M[ipp][j] <= M[ip][j]]
        between = all(M[ip][j] < M[ipp][j] < M[i][j] for j in range(k))

        if above_i and below_ip:
            zones[ipp] = 'crossing'
        elif not above_i and not below_ip:
            zones[ipp] = 'between'
        elif not above_i:
            zones[ipp] = 'dominated_by_i'
        elif not below_ip:
            zones[ipp] = 'dominates_ip'
        else:
            zones[ipp] = 'other'
    return zones


def analyze_gap_structure(M, i, ip):
    """Analyze the gap M[i][j] - M[i'][j] per column."""
    k = len(M)
    gaps = [(M[i][j] - M[ip][j], j) for j in range(k)]
    gaps.sort()
    return gaps


def try_prove_crossing(M, i, ip):
    """Attempt the proof: tight gap column forces crossing.

    In the column with minimum gap g = M[i][j*] - M[i'][j*],
    there are at most g-1 values strictly between M[i'][j*] and M[i][j*].
    The "between" rows (those between i and i' in EVERY column) each need
    one of these g-1 values. So at most g-1 between rows.

    The remaining k-2-(g-1) = k-1-g intermediate rows must be in zone A
    (dominated by i) or zone B (dominates i'). But are there enough?

    If k-1-g > 0, there are rows NOT in the between zone. These rows
    must have M[ipp][j*] outside [M[ip][j*], M[i][j*]] for column j*.
    Either M[ipp][j*] > M[i][j*] (above i in j*) or M[ipp][j*] < M[ip][j*]
    (below i' in j*). For bridge-less, if above i in j*, must NEVER be
    below i' in any column. And vice versa.

    The question: can all non-between rows be cleanly partitioned?
    """
    k = len(M)
    gaps = [(M[i][j] - M[ip][j], j) for j in range(k)]
    gaps.sort()
    min_gap, j_star = gaps[0]

    # Count between rows
    between_rows = []
    non_between = []
    for ipp in range(k):
        if ipp == i or ipp == ip:
            continue
        if all(M[ip][j] < M[ipp][j] < M[i][j] for j in range(k)):
            between_rows.append(ipp)
        else:
            non_between.append(ipp)

    # Non-between rows: above i or below i' in some column
    # For bridge-less: each must be ONLY above or ONLY below (never both)
    crossings = []
    for ipp in non_between:
        above_cols = [j for j in range(k) if M[ipp][j] >= M[i][j]]
        below_cols = [j for j in range(k) if M[ipp][j] <= M[ip][j]]
        if above_cols and below_cols:
            crossings.append((ipp, above_cols, below_cols))

    return {
        'min_gap': min_gap,
        'j_star': j_star,
        'between_count': len(between_rows),
        'non_between_count': len(non_between),
        'crossings': crossings,
        'max_between_possible': min_gap - 1,
    }


def search_counterexample():
    """Search for a dominated pair with NO crossing intermediate.
    If found, bridge-less is possible. If never found, crossing always exists."""
    random.seed(42)

    for k in range(3, 9):
        print(f"\nk={k}: searching for bridge-less dominated pairs...")
        found_dominated = 0
        found_bridge_less = 0
        gap_analysis = []

        samples = 100000 if k <= 4 else (20000 if k <= 5 else (5000 if k <= 6 else 1000))
        for _ in range(samples):
            vals = list(range(1, k * k + 1))
            random.shuffle(vals)
            M = []
            for r in range(k):
                M.append(vals[r * k:(r + 1) * k])

            # Check all pairs for domination
            for i in range(k):
                for ip in range(k):
                    if i == ip:
                        continue
                    if all(M[i][j] > M[ip][j] for j in range(k)):
                        found_dominated += 1
                        has_crossing, _, _, _ = check_crossing(M, i, ip)
                        if not has_crossing:
                            found_bridge_less += 1
                            proof = try_prove_crossing(M, i, ip)
                            gap_analysis.append(proof)
                            if found_bridge_less <= 3:
                                print(f"\n  BRIDGE-LESS FOUND!")
                                print(f"    Matrix: {M}")
                                print(f"    Dominator row {i}: {M[i]}")
                                print(f"    Dominated row {ip}: {M[ip]}")
                                zones = check_bridge_less(M, i, ip)
                                for ipp, zone in zones.items():
                                    print(f"    Row {ipp} ({M[ipp]}): {zone}")
                                print(f"    Gap analysis: {proof}")

        print(f"  Dominated pairs found: {found_dominated}")
        print(f"  Bridge-less among them: {found_bridge_less}")
        if found_dominated > 0:
            print(f"  Bridge-less rate: {found_bridge_less/found_dominated*100:.4f}%")
        if gap_analysis:
            avg_gap = sum(g['min_gap'] for g in gap_analysis) / len(gap_analysis)
            avg_between = sum(g['between_count'] for g in gap_analysis) / len(gap_analysis)
            print(f"  Avg min gap: {avg_gap:.1f}, avg between rows: {avg_between:.1f}")


if __name__ == "__main__":
    search_counterexample()
