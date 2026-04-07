"""
Joint optimization of per-diagonal edge selection.

For SM(k), the optimal spanner has ~2 edges per intermediate diagonal.
The per-diagonal greedy fails because cross-diagonal interactions matter.

This script:
1. Exhaustive search over per-diagonal assignments (for small k)
2. Identifies WHICH 2-per-diagonal selections work
3. Characterizes what makes a selection valid vs invalid
"""

import random
from itertools import combinations, product
from collections import defaultdict

random.seed(42)


def compute_reachability_pairs(n, timed_edges):
    reached_by = [dict() for _ in range(n)]
    for i in range(n):
        reached_by[i][i] = 0
    for t, u, v in sorted(timed_edges):
        for s, arr in list(reached_by[u].items()):
            if arr <= t and (s not in reached_by[v] or t < reached_by[v][s]):
                reached_by[v][s] = t
        for s, arr in list(reached_by[v].items()):
            if arr <= t and (s not in reached_by[u] or t < reached_by[u][s]):
                reached_by[u][s] = t
    pairs = set()
    for v in range(n):
        for s in reached_by[v]:
            if s != v:
                pairs.add((s, v))
    return pairs


def generate_sm_matrix(k):
    M = [[0] * k for _ in range(k)]
    t = 1
    for d in range(k):
        for i in range(k):
            j = (i + d) % k
            M[i][j] = t
            t += 1
    return M


def get_base_edges(M, k):
    """M⁻ ∪ M⁺ edges."""
    base = set()
    for j in range(k):
        best_i = min(range(k), key=lambda i: M[i][j])
        base.add((best_i, j))
    for i in range(k):
        best_j = max(range(k), key=lambda j: M[i][j])
        base.add((i, best_j))
    return base


def check_selection(k, M, base, diag_selections, full_pairs):
    """Check if M⁻∪M⁺ + given diagonal selections form a valid spanner."""
    n = 2 * k
    spanner = set(base)
    for d, rows in diag_selections.items():
        for row_idx in rows:
            j = (row_idx + d) % k
            spanner.add((row_idx, j))

    timed = [(M[i][j], i, k + j) for i, j in spanner]
    span_pairs = compute_reachability_pairs(n, timed)
    missing = full_pairs - span_pairs
    return len(missing), spanner


def exhaustive_2per_diag(k, M):
    """Try all possible 2-per-diagonal selections. Return valid ones."""
    n = 2 * k
    base = get_base_edges(M, k)

    full_timed = [(M[i][j], i, k + j) for i in range(k) for j in range(k)]
    full_pairs = compute_reachability_pairs(n, full_timed)

    intermediate_diags = list(range(1, k - 1))
    if not intermediate_diags:
        return [], base, full_pairs

    # For each diagonal, enumerate all C(k, 2) row pairs
    diag_options = {}
    for d in intermediate_diags:
        diag_options[d] = list(combinations(range(k), 2))

    # Enumerate all joint selections
    valid_selections = []
    total_checked = 0
    option_lists = [diag_options[d] for d in intermediate_diags]

    for combo in product(*option_lists):
        total_checked += 1
        selection = {}
        for idx, d in enumerate(intermediate_diags):
            selection[d] = combo[idx]

        missing, spanner = check_selection(k, M, base, selection, full_pairs)
        if missing == 0:
            valid_selections.append((selection, len(spanner)))

    return valid_selections, total_checked, base, full_pairs


def characterize_valid(k, M, valid_selections):
    """What do valid 2-per-diagonal selections have in common?"""
    if not valid_selections:
        return {}

    # Count how often each row appears per diagonal
    row_freq = defaultdict(lambda: defaultdict(int))
    pair_freq = defaultdict(lambda: defaultdict(int))

    for selection, size in valid_selections:
        for d, (r1, r2) in selection.items():
            row_freq[d][r1] += 1
            row_freq[d][r2] += 1
            pair_freq[d][(r1, r2)] += 1

    return row_freq, pair_freq


def main():
    print("=" * 70)
    print("JOINT DIAGONAL OPTIMIZATION")
    print("=" * 70)

    for k in range(3, 8):
        M = generate_sm_matrix(k)
        n = 2 * k

        print(f"\n{'='*60}")
        print(f"SM({k}) (n={n}, 2n-3={2*n-3})")
        print(f"{'='*60}")

        num_intermediate = k - 2
        if num_intermediate <= 0:
            print("  No intermediate diagonals")
            continue

        # Estimate search space
        from math import comb
        space = comb(k, 2) ** num_intermediate
        print(f"  Intermediate diagonals: {num_intermediate}")
        print(f"  Options per diagonal: C({k},2) = {comb(k,2)}")
        print(f"  Total search space: {space}")

        if space > 5_000_000:
            print("  Too large for exhaustive search, skipping")
            continue

        valid, total_checked, base, full_pairs = exhaustive_2per_diag(k, M)

        print(f"  Checked: {total_checked}")
        print(f"  Valid 2-per-diagonal selections: {len(valid)}/{total_checked} "
              f"({100*len(valid)/total_checked:.2f}%)")

        if valid:
            sizes = [s for _, s in valid]
            print(f"  Spanner sizes: min={min(sizes)}, max={max(sizes)}")

            # Show a few valid selections
            print(f"\n  First 5 valid selections:")
            for sel, size in valid[:5]:
                parts = [f"d={d}: rows {rows}" for d, rows in sorted(sel.items())]
                print(f"    {', '.join(parts)} → {size} edges")

            # Characterize
            row_freq, pair_freq = characterize_valid(k, M, valid)

            print(f"\n  Row frequency per diagonal (across all valid selections):")
            for d in sorted(row_freq.keys()):
                total_appearances = sum(row_freq[d].values())
                sorted_rows = sorted(row_freq[d].items(), key=lambda x: -x[1])
                top = [(r, f"{c}/{len(valid)}" ) for r, c in sorted_rows[:5]]
                print(f"    d={d}: {top}")

            # What's ALWAYS present?
            print(f"\n  Rows that appear in ALL valid selections:")
            for d in sorted(row_freq.keys()):
                always = [r for r, c in row_freq[d].items()
                          if c == len(valid)]
                if always:
                    print(f"    d={d}: rows {always} (mandatory)")
                else:
                    # Rows in >50% of valid selections
                    common = [(r, c) for r, c in row_freq[d].items()
                              if c > len(valid) / 2]
                    common.sort(key=lambda x: -x[1])
                    print(f"    d={d}: none mandatory. "
                          f"Most common: {[(r, f'{c}/{len(valid)}') for r, c in common[:3]]}")

        else:
            print(f"\n  NO valid 2-per-diagonal selection exists!")
            # What's the best we can do with 2/diag?
            best_missing = float('inf')
            best_sel = None
            intermediate_diags = list(range(1, k - 1))
            diag_options = {d: list(combinations(range(k), 2))
                          for d in intermediate_diags}

            # Sample some random selections
            for _ in range(min(10000, space)):
                selection = {}
                for d in intermediate_diags:
                    selection[d] = random.choice(diag_options[d])
                missing, spanner = check_selection(
                    k, M, base, selection, full_pairs)
                if missing < best_missing:
                    best_missing = missing
                    best_sel = selection

            print(f"  Best 2-per-diagonal: {best_missing} missing pairs")
            if best_sel:
                parts = [f"d={d}: rows {rows}"
                         for d, rows in sorted(best_sel.items())]
                print(f"    Selection: {', '.join(parts)}")

            # Try 3-per-diagonal for the problematic diagonals
            print(f"\n  Identifying which diagonals need >2 edges:")
            for d in intermediate_diags:
                # Fix all other diags at their best-2, vary this one
                # with 1, 2, 3 edges
                for num_edges in [1, 2, 3, 4]:
                    best_d_missing = float('inf')
                    for combo in combinations(range(k), num_edges):
                        sel = dict(best_sel) if best_sel else {}
                        sel[d] = combo
                        missing, _ = check_selection(
                            k, M, base, sel, full_pairs)
                        best_d_missing = min(best_d_missing, missing)
                    if best_d_missing == 0:
                        print(f"    d={d}: needs {num_edges} edges (fixes all)")
                        break
                    else:
                        print(f"    d={d}: {num_edges} edges → {best_d_missing} missing")


if __name__ == '__main__':
    main()
