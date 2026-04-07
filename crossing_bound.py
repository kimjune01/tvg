"""
Prove: for k >= C, every dominated pair has a crossing intermediate.

A dominated pair (i, i') is bridge-less iff every intermediate row is
either dominated by i or dominates i' (never crosses).

If row i has values v_0 > v_1 > ... > v_{k-1} (sorted descending),
the MINIMUM value in row i is v_{k-1}. For i to dominate i', we need
v_{k-1} > max(row i') in the corresponding column... no, domination is
pointwise, not by extremes.

Key insight: if i dominates i', consider the SUM of row i vs row i'.
sum(row i) > sum(row i') since M[i][j] > M[i'][j] for all j.
The difference is at least k (since each column differs by at least 1).

For bridge-less: every intermediate is either dominated by i (sum < sum_i)
or dominates i' (sum > sum_i'). The intermediate sums partition into
"large" (>= sum_i') and "small" (<= sum_i)... wait, that's backwards.

Actually dominated by i means sum(i'') < sum(i) (not necessarily, pointwise
doesn't imply sum ordering). Let me think differently.

Approach: for bridge-less, define A = {i'': dominates i'} and B = {i'': dominated by i}.
Every intermediate is in A, B, or both (A ∩ B = between).

The row sums of A members must each exceed sum(i') (not exactly, but each
A member has M[i''][j] > M[i'][j] for all j, so sum(i'') > sum(i')).
Similarly sum of B members < sum(i).

Count: k-2 intermediate rows, each in A ∪ B. Total sum of all rows =
k² * (k²+1) / 2 (since values are 1..k²). Constrained by the partition.

Let's compute: for the bridge-less case, what's the maximum k?
"""

import random
from math import comb


def analyze_bridge_less_constraints(k):
    """
    For a k×k matrix with values {1,...,k²}:
    Row i dominates row i': M[i][j] > M[i'][j] for all j.
    Bridge-less: every other row either dominated by i or dominates i'.

    What are the constraints on the value distribution?
    """
    total_sum = k * k * (k * k + 1) // 2  # sum of 1..k²

    print(f"\nk={k}: {k}×{k} matrix, values 1..{k*k}")
    print(f"  Total sum of all entries: {total_sum}")
    print(f"  Average row sum: {total_sum / k}")

    # For domination: row i has M[i][j] > M[i'][j] for all j.
    # Minimum possible sum of row i: if M[i][j] - M[i'][j] = 1 for all j,
    # then sum(i) - sum(i') = k.
    # Maximum sum of dominated row: total_sum/k - k/2 or so.

    # For bridge-less with all intermediates dominated by i:
    # Row i dominates ALL other k-1 rows.
    # This means: in every column, row i has the maximum value.
    # But there are k values per column, and the max can only be in one row.
    # So row i has the column-max in every column.
    # Column max values: the top value in each column.
    # If row i gets the max of every column, what are those values?

    # In a k×k matrix with values 1..k², the column maximums are k values.
    # For row i to have the max in every column: row i = (max_col_0, ..., max_col_{k-1})
    # The column maximums must sum to at most total_sum / ... no specific constraint
    # except they're k distinct values from {1,...,k²}.

    # The minimum possible set of column maximums: if columns are arranged
    # so that the max of each column is as small as possible.
    # Column j has k values. The max is the largest. To minimize the max,
    # assign the k smallest remaining values to this column.
    # But values are shared across columns (each value appears exactly once).

    # Actually, the k column maximums are k distinct values. They must each
    # be the largest value in their respective column. The OTHER k-1 values
    # in each column must be less than the column max.

    # If row i has column max in every column, then row i's values are
    # c_0, c_1, ..., c_{k-1} where c_j > M[i''][j] for all other i'' and all j.
    # This means row i's values are the k column-wise maximums.

    # The minimum possible value of min(c_0,...,c_{k-1}):
    # The k column maxes must be chosen from {1,...,k²} such that each c_j
    # is larger than the other k-1 values in its column.
    # The other k-1 values in column j are any k-1 values less than c_j.

    # For all intermediates to be dominated by i: c_j > M[i''][j] for all i'', j.
    # This is exactly: c_j = max of column j.

    # Can this happen? Yes — if row i gets the max of every column.
    # What's the minimum sum of such a row?
    # The k column maxes must be distinct and each must have k-1 smaller
    # values available in its column. The absolute minimum: if we put
    # values k, 2k, 3k, ..., k² as the column maxes (one per column),
    # each column gets values {ik-k+1,...,ik}. Then column maxes sum to
    # k + 2k + ... + k² = k(k+1)/2 * k = k²(k+1)/2.
    # But this is a very specific arrangement.

    # More generally: the column maxes are k values from {1..k²}.
    # The minimum column max (across all columns) is at least k
    # (since it must be larger than k-1 other values in its column,
    # and the smallest possible set of k-1 values below it is {1,...,k-1}).

    # For bridge-less with split intermediates (some in A, some in B):
    # A members dominate i'. B members are dominated by i. No crosser.
    # This constrains the column orderings of A and B relative to i, i'.

    # Key constraint: the k values in each column must accommodate:
    # - Row i: above all B members in this column
    # - Row i': below all A members in this column
    # - A members: above i' in this column
    # - B members: below i in this column

    # In each column, the ordering is:
    # [B members] < [row i'] < [A members] < [row i]
    #             OR
    # [B members] < [row i'] < [row i] < [A members]
    # but i dominates i', so M[i][j] > M[i'][j]. And A members dominate i',
    # so they're above i'. And B members are below i.

    # Wait — A members dominate i' means M[a][j] > M[i'][j] for all j.
    # B members dominated by i means M[i][j] > M[b][j] for all j.
    # An A member could be below i: M[a][j] could be between M[i'][j] and M[i][j].
    # A B member could be above i': M[b][j] could be between M[i'][j] and M[i][j].

    # The constraint is just: no row is BOTH above i somewhere AND below i' somewhere.

    # For the column: we have k values assigned to k rows.
    # Row i gets value v_i, row i' gets value v_i' < v_i.
    # A members get values > v_i' (in every column).
    # B members get values < v_i (in every column).
    # No row gets a value > v_i in this column AND < v_i' in another column.

    pass


def count_bridge_less_exact(k):
    """For small k, enumerate all k×k matrices and count bridge-less pairs."""
    if k > 3:
        print(f"  k={k} too large for exact enumeration")
        return

    from itertools import permutations

    # Generate all k×k latin-rectangle-like matrices with values 1..k²
    # Actually, we need arbitrary placement of 1..k² into a k×k grid.
    # That's (k²)! / ... too many. Use random sampling instead.
    pass


def structural_analysis():
    """
    Analyze WHY bridge-less vanishes at k >= 7.

    For bridge-less (i, i') with |A|=a, |B|=b, a+b = k-2:
    - Row i must be > all B members in EVERY column: k values per column,
      row i is above b+1 values (b members + row i').
    - Row i' must be < all A members in EVERY column: row i' is below a+1
      values (a members + row i).

    In each column, the ordering has:
    [b B-members, row i'] all below [a A-members, row i]

    That's (b+1) values below (a+1) values. Total k values in the column.
    b+1+a+1 = k. So it's a clean partition: bottom b+1, top a+1.

    The values 1..k² distributed into k columns of k values each.
    In each column, the bottom b+1 values go to B∪{i'}, top a+1 to A∪{i}.

    Constraint: row i must get one of the top a+1 values in EVERY column.
    Row i gets k values, one per column, each from the top a+1 of that column.
    Similarly, row i' gets k values, each from the bottom b+1 of that column.

    The question: can we assign k² distinct values to a k×k grid such that
    row i always gets a top-(a+1) value and row i' always gets a bottom-(b+1)
    value in each column?

    This is a constraint satisfaction problem. For large k, the constraints
    become unsatisfiable because:
    - Row i needs k values, each from the top a+1 of its column.
    - The top a+1 of each column = the (a+1) largest values assigned to that column.
    - Row i's values must all be "large" in their columns, but with k² distinct
      values, row i can't hog all the large values in every column simultaneously.
    """
    print("\nStructural analysis: when does bridge-less become impossible?")
    print("=" * 60)

    for k in range(3, 12):
        # For bridge-less with a A-members and b B-members, a+b = k-2:
        # Row i gets top-(a+1) in every column.
        # Row i's k values must each be in the top (a+1)/k fraction of its column.
        # The "easiest" case: a = k-2, b = 0 (all intermediates dominate i').
        # Then row i gets top-(k-1) in every column = row i is NOT the minimum
        # of any column. Very easy.

        # The hardest case for the dominator: a = 0, b = k-2 (all dominated by i).
        # Row i must be the MAXIMUM of every column. row i' must be the minimum
        # of every column. And all intermediates are between them.
        # Wait no — B dominated by i means row i > intermediates. But intermediates
        # could be above or below row i'. For all B: dominated by i but dominating i'.
        # That means they're between i and i'. Which is the "between" zone.

        # Hmm, let me reconsider. For bridge-less:
        # A = {i'': dominates i', never above i in any col}
        #   = {i'': M[i''][j] > M[i'][j] for all j, and M[i''][j] < M[i][j] for all j}
        #   = between rows (dominated by i AND dominating i')
        # B = {i'': dominated by i, never below i' in any col}
        #   = same as A! Because dominated by i = M[i''][j] < M[i][j] for all j,
        #     and never below i' = M[i''][j] > M[i'][j] for all j.

        # WAIT. Let me re-derive. Bridge-less means A_cross ∩ B_cross = ∅ where:
        # A_cross = {i'': ∃j with M[i''][j] >= M[i][j]} (above i somewhere)
        # B_cross = {i'': ∃j with M[i''][j] <= M[i'][j]} (below i' somewhere)

        # Not in A_cross: M[i''][j] < M[i][j] for all j (dominated by i)
        # Not in B_cross: M[i''][j] > M[i'][j] for all j (dominates i')

        # Bridge-less = A_cross ∩ B_cross = ∅.
        # So every i'' is in at most one of {A_cross, B_cross}.

        # Partition of intermediates:
        # P = not in A_cross, not in B_cross = dominated by i AND dominates i' = BETWEEN
        # Q = in A_cross, not in B_cross = above i somewhere, never below i' = ABOVE
        # R = not in A_cross, in B_cross = below i' somewhere, never above i = BELOW
        # (A_cross ∩ B_cross = ∅, so no fourth category)

        # P: between rows (M[i'][j] < M[i''][j] < M[i][j] for all j)
        # Q: above i in some col, but M[i''][j] > M[i'][j] for all j (dominates i')
        # R: below i' in some col, but M[i''][j] < M[i][j] for all j (dominated by i)

        # For each column j, the k values are distributed as:
        # R members: some may be below M[i'][j]
        # row i': value M[i'][j]
        # P members: between M[i'][j] and M[i][j]
        # row i: value M[i][j]
        # Q members: some may be above M[i][j]

        # Q members dominate i' but may be above i in some columns.
        # In column j: Q member values are > M[i'][j], and SOME are > M[i][j].
        # R members dominated by i but may be below i' in some columns.
        # In column j: R member values are < M[i][j], and SOME are < M[i'][j].

        # The constraint is per-row, not per-column. A Q-row must have ALL values
        # > M[i'][j] (for each j), but in at least one column, its value > M[i][j].

        # For counting: let p = |P|, q = |Q|, r = |R|, p+q+r = k-2.

        # In each column j, the gap g_j = M[i][j] - M[i'][j] - 1 is the number
        # of integer values strictly between M[i'][j] and M[i][j].
        # P rows each need one value from this gap in every column.
        # So p ≤ g_j for all j. Hence p ≤ min_j(g_j).

        # The total of all gaps: sum_j g_j = sum_j (M[i][j] - M[i'][j] - 1)
        # = sum(row_i) - sum(row_i') - k.

        # For bridge-less, p ≤ min_j(g_j). If min_j(g_j) = 0, then p = 0
        # (no between rows). This happens when M[i][j] = M[i'][j] + 1 for some j.

        # With p = 0 (empirically the common case):
        # All intermediates are Q or R. q + r = k-2.
        # Q rows: above i in some col, dominate i'.
        # R rows: below i' in some col, dominated by i.

        # Each Q row contributes at least one value > M[i][j] to some column.
        # Each R row contributes at least one value < M[i'][j] to some column.

        # Total values above row i across all columns: each column has a+1 values
        # above M[i'][j] where a+1 is... this is getting complicated.

        # Let me just count: how many values in {1..k²} are above M[i][j] in column j?
        # That's k - rank(i, j) where rank is the position of M[i][j] in column j.
        # For i to be the top value in column j, 0 values above.
        # For Q rows to have values above M[i][j] in column j, there must be
        # values > M[i][j] available in that column.

        # The total number of "above i" slots across all columns:
        # sum_j (k - 1 - position_of_i_in_col_j)... but this depends on the arrangement.

        # Minimum above-i slots: if row i is the column max in every column, then
        # 0 above-i slots. Then Q = 0 (no row can be above i). All intermediates are R.
        # R rows are dominated by i, and below i' somewhere. r = k-2.

        # For this to be bridge-less: all R rows dominated by i AND below i' somewhere.
        # But bridge-less requires R rows to NEVER be above i (which is guaranteed since
        # they're dominated by i) and in B_cross (below i' somewhere, which is given).
        # And A_cross ∩ B_cross = ∅ requires no row in both. Since Q = 0, this is trivially
        # satisfied.

        # So: bridge-less with Q=0, R=k-2 means row i is column-max in every column,
        # and every intermediate is dominated by i. Some intermediates are also below i'
        # in some columns.

        # Can row i be column-max in every column?
        # Row i has k values. Column max means it's the largest of k values in that column.
        # The k column-maxes are among the k largest values in the matrix? No — they're
        # the largest per column, which depends on arrangement.

        # Minimum sum for row i to be column-max everywhere:
        # In each column, row i's value must be larger than all other k-1 values.
        # If column j has values sorted as v_1 < v_2 < ... < v_k, then row i gets v_k.
        # The sum of column maxes is minimized when columns have similar ranges.
        # E.g., columns = {1,..,k}, {k+1,...,2k}, ..., {(k-1)k+1,...,k²}.
        # Then column maxes = k, 2k, 3k, ..., k². Sum = k·k(k+1)/2 = k²(k+1)/2.

        min_sum_i_all_max = sum(j * k for j in range(1, k + 1))
        avg_row = k * (k * k + 1) // 2 // k

        # Is this achievable? Row i = {k, 2k, 3k, ..., k²}.
        # Other rows fill in the gaps. Row i' must be below i everywhere,
        # i.e., M[i'][j] < M[i][j] = j*k. So M[i'][j] ∈ {(j-1)*k+1,...,j*k-1}.
        # Row i' takes one value from each block, below the block max.
        # This is always possible.

        # So bridge-less is constructible for any k. But is it consistent
        # with ALL constraints simultaneously?

        # Actually wait — we showed bridge-less pairs DON'T EXIST for k >= 7
        # empirically. So something prevents it. What?

        # The issue might be that bridge-less constrains not just the dominator
        # and dominated rows, but ALL OTHER rows simultaneously. Having every
        # intermediate dominated by i means i is column-max everywhere, which
        # forces the other rows to have small values, constraining i' to also
        # be small. But then other intermediates might not dominate i'.

        # Let me check: for k=7, is it possible to have row i as column-max
        # in all 7 columns, AND have all 5 intermediates dominated by i,
        # AND have row i' dominated by i, AND have no crossing?

        ts = k * k * (k * k + 1) // 2
        print(f"\n  k={k}: min sum for all-column-max row = {min_sum_i_all_max}, "
              f"avg row sum = {ts // k}")

    # The issue: when row i is column-max everywhere, it takes the k largest
    # per-column values. The remaining (k-1)k values are distributed among
    # k-1 rows. For ALL of these to be dominated by i: true by construction
    # (i is column max). For i' to be below i in every column: also true
    # (everyone is below i). So bridge-less pair (i, any other row) with
    # Q=0 is trivially constructible.

    # BUT: the reachability rank isn't about ONE pair — it's about ALL pairs
    # simultaneously. Maybe bridge-less for one pair forces crossings elsewhere.

    # Hmm, but the empirical search was for individual pairs, and it found
    # ZERO bridge-less pairs at k >= 7. So even individual pairs can't be
    # bridge-less at k >= 7. My reasoning above must be wrong.

    # Let me re-examine: row i has column-max in every column. Row i' is
    # some other row. Is the pair (i, i') bridge-less?
    # Every intermediate is dominated by i (Q = 0, since no row is above i anywhere).
    # So every intermediate is either R (below i' somewhere) or P (between).
    # For bridge-less: A_cross ∩ B_cross = ∅.
    # A_cross = rows above i somewhere = ∅ (since i is column-max).
    # So A_cross ∩ B_cross = ∅ trivially. Bridge-less!

    # But wait — this contradicts the empirical finding. Let me check if such
    # a matrix can exist at k=7 and have no crossing.

    print("\n\nDirect construction test: row 0 = column maxes")
    for k in [5, 6, 7, 8]:
        # Construct: row 0 gets the max of each column block
        M = [[0]*k for _ in range(k)]
        # Column j gets values {(j)*k - k + 1, ..., j*k} = {jk-k+1,...,jk}
        # Wait, let me use blocks: col 0 gets {1,...,k}, col 1 gets {k+1,...,2k}, etc.
        for j in range(k):
            col_vals = list(range(j * k + 1, (j + 1) * k + 1))
            # Row 0 gets the max
            M[0][j] = col_vals[-1]  # = (j+1)*k
            # Other rows get the rest in some order
            remaining = col_vals[:-1]
            random.shuffle(remaining)
            for r_idx, r in enumerate(range(1, k)):
                M[r][j] = remaining[r_idx]

        # Check: is row 0 column-max in every column?
        assert all(M[0][j] == max(M[r][j] for r in range(k)) for j in range(k))

        # Row 0 dominates all other rows (since it's column-max everywhere).
        # Pick row 1 as i'. Is (0, 1) bridge-less?
        # A_cross for row 0 = ∅ (nothing above row 0).
        # So bridge-less trivially. But check crossing anyway:
        for ip in range(1, k):
            has_crossing = False
            for ipp in range(1, k):
                if ipp == ip:
                    continue
                above_0 = any(M[ipp][j] >= M[0][j] for j in range(k))
                below_ip = any(M[ipp][j] <= M[ip][j] for j in range(k))
                if above_0 and below_ip:
                    has_crossing = True
                    break
            if not has_crossing:
                print(f"  k={k}: pair (0, {ip}) is bridge-less in constructed matrix")
                break
        else:
            print(f"  k={k}: all pairs (0, x) have crossings in constructed matrix")


structural_analysis()
