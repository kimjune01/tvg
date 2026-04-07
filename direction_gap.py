"""
Check whether the directionality argument closes the gap.

For a connected column pair (j1, j2): if uniformly ordered (j1 > j2 in all rows),
route j2 -> j1 and relay is free. But does graph reachability work in that direction
for ALL source-target pairs?

The 2-hop route j2->j1 from i to i' needs:
  rank_j1(i') >= rank_j2(i)

The 2-hop route j1->j2 from i to i' needs:
  rank_j2(i') >= rank_j1(i)

Both fail iff: rank_j1(i') < rank_j2(i) AND rank_j2(i') < rank_j1(i)
= i has high ranks, i' has low ranks.

Question: for connected pairs, does this ever happen? And if so,
do multi-hop routes (4-hop, 6-hop via alternating columns) rescue?
"""

import random
from itertools import combinations


def is_connected_pair(M, k, j1, j2):
    """Check if (j1, j2) is a connected column pair.
    Connected = no proper subset S that is a downset for both columns.
    A downset for column j: if i' in S and M[i][j] <= M[i'][j], then i in S.
    Equivalently: the set of rows reachable by going "up" in both columns
    from any starting row eventually covers everything.
    """
    # Build reachability: i -> i' if M[i][j] <= M[i'][j] for j in {j1, j2}
    # Check if the undirected reachability graph is connected
    adj = [set() for _ in range(k)]
    for i in range(k):
        for ip in range(k):
            if i == ip:
                continue
            # i can reach ip via j1 or j2
            if M[i][j1] <= M[ip][j1] or M[i][j2] <= M[ip][j2]:
                adj[i].add(ip)
                adj[ip].add(i)

    # BFS from 0
    visited = set([0])
    queue = [0]
    while queue:
        v = queue.pop(0)
        for w in adj[v]:
            if w not in visited:
                visited.add(w)
                queue.append(w)
    return len(visited) == k


def check_direction_gap(M, k, j1, j2):
    """For connected pair (j1, j2), check if 2-hop routing works
    in at least one direction for all source-target pairs.

    Returns (all_2hop_ok, failed_pairs, uniform_order)
    """
    # Check if uniformly ordered
    j1_gt_j2 = all(M[i][j1] > M[i][j2] for i in range(k))
    j2_gt_j1 = all(M[i][j2] > M[i][j1] for i in range(k))
    mixed = not j1_gt_j2 and not j2_gt_j1

    # Compute ranks in each column
    col_j1 = [(M[i][j1], i) for i in range(k)]
    col_j2 = [(M[i][j2], i) for i in range(k)]
    col_j1.sort()
    col_j2.sort()
    rank_j1 = [0] * k
    rank_j2 = [0] * k
    for r, (_, i) in enumerate(col_j1):
        rank_j1[i] = r
    for r, (_, i) in enumerate(col_j2):
        rank_j2[i] = r

    failed_pairs = []
    for i in range(k):
        for ip in range(k):
            if i == ip:
                continue
            # Route j2 -> j1: works iff rank_j1(i') >= rank_j2(i)
            route_21 = rank_j1[ip] >= rank_j2[i]
            # Route j1 -> j2: works iff rank_j2(i') >= rank_j1(i)
            route_12 = rank_j2[ip] >= rank_j1[i]

            if not route_21 and not route_12:
                failed_pairs.append((i, ip))

    uniform = "j1>j2" if j1_gt_j2 else ("j2>j1" if j2_gt_j1 else "mixed")
    return len(failed_pairs) == 0, failed_pairs, uniform


def check_multihop_rescue(M, k, j1, j2, failed_pairs):
    """For pairs that fail 2-hop in both directions, check if multi-hop
    (4-hop, 6-hop) through alternating columns rescues them.

    A 4-hop route i -> i1 -> i' uses:
    j2 -> j1 -> j2 -> j1 (or any alternation)

    Actually, multi-hop means: i ->_j2 i1 ->_j1 i2 ->_j2 i3 ->_j1 i'
    with relay constraints at each switch.
    """
    # Build full directed reachability using BFS on (row, last_column_used)
    # State: (current_row, last_column_used, arrival_time)
    # But we're just checking existence, not timestamps.

    # For the non-temporal version (relay always satisfied in one direction):
    # If j1 > j2 uniformly, relay j2->j1 is always free.
    # Multi-hop: i ->_j2 i1 ->_j1 i2 ->_j2 i3 ->_j1 i'
    # Each transition is: going "up" in the column used.
    # relay at i1: j2 <= j1 (free)
    # relay at i2: j1 <= j2 (FAILS if j1 > j2)
    # relay at i3: j2 <= j1 (free)

    # Wait: multi-hop alternation means some relays go j1->j2 and others j2->j1.
    # If j1 > j2 uniformly, only j2->j1 relays are free.
    # So we can only use routes that always switch j2->j1, never j1->j2.
    # That means: column sequence must be j2, j1, j2, j1, ...
    # (never j1 followed by j2)
    # This means at each relay point, we switch from j2 to j1 (free)
    # then from j1 to j2 (FAILS!)

    # Hmm, this means multi-hop doesn't help for uniformly ordered pairs!
    # The 4-hop route j2, j1, j2, j1 requires relay at position 2: j1 -> j2 (fails!)

    # Unless we go all j2->j1 without going back: 2-hop is j2, j1.
    # 4-hop would need j2, j1, jX, jY but jX must follow j1 temporally.
    # If j1 > j2, after arriving via j1 at some row, the only valid next column
    # is j1 again (j2 would need j1 <= j2 which fails) or some other column.
    # But we only have two relay columns!

    # SO: for uniformly ordered (j1, j2) with j1 > j2:
    # Only valid column sequence is: j2, j1 (2-hop). Cannot extend further.
    # Multi-hop does NOT rescue.

    rescued = []
    not_rescued = []

    # Check via BFS with column state
    # Directed edges: i ->_j i' iff M[i][j] <= M[i'][j]
    # Valid transitions: after arriving via j2, can switch to j1 (j2 <= j1, free)
    #                   after arriving via j1, can switch to j2 (j1 <= j2, FAILS)
    #                   after arriving via j1, can stay on j1 (no switch needed)
    #                   after arriving via j2, can stay on j2 (no switch needed)

    j1_gt_j2 = all(M[i][j1] > M[i][j2] for i in range(k))

    for (i, ip) in failed_pairs:
        # BFS: state = (row, last_column)
        # Start: (i, None) - haven't used a column yet
        # Can choose first column freely

        visited = set()
        queue = []

        # Start by going up in j1
        for i2 in range(k):
            if M[i][j1] <= M[i2][j1]:
                state = (i2, j1)
                if state not in visited:
                    visited.add(state)
                    queue.append(state)
        # Start by going up in j2
        for i2 in range(k):
            if M[i][j2] <= M[i2][j2]:
                state = (i2, j2)
                if state not in visited:
                    visited.add(state)
                    queue.append(state)

        while queue:
            row, last_col = queue.pop(0)

            if row == ip:
                break

            # Try continuing with same column
            for i2 in range(k):
                if M[row][last_col] <= M[i2][last_col]:
                    state = (i2, last_col)
                    if state not in visited:
                        visited.add(state)
                        queue.append(state)

            # Try switching column (check relay)
            other_col = j2 if last_col == j1 else j1
            if M[row][last_col] <= M[row][other_col]:  # relay check
                for i2 in range(k):
                    if M[row][other_col] <= M[i2][other_col]:
                        state = (i2, other_col)
                        if state not in visited:
                            visited.add(state)
                            queue.append(state)

        if any(r == ip for r, _ in visited):
            rescued.append((i, ip))
        else:
            not_rescued.append((i, ip))

    return rescued, not_rescued


def main():
    random.seed(42)

    print("DIRECTION GAP ANALYSIS")
    print("=" * 70)

    for k in range(3, 8):
        samples = {3: 5000, 4: 2000, 5: 1000, 6: 500, 7: 200}[k]

        total_connected_pairs = 0
        total_uniform_pairs = 0
        total_2hop_fail = 0
        total_multihop_rescued = 0
        total_multihop_fail = 0

        for s in range(samples):
            # Random k x k matrix with distinct entries
            vals = random.sample(range(1, k*k + 1), k*k)
            M = [[0]*k for _ in range(k)]
            idx = 0
            for i in range(k):
                for j in range(k):
                    M[i][j] = vals[idx]
                    idx += 1

            # Check all column pairs
            for j1 in range(k):
                for j2 in range(j1+1, k):
                    if not is_connected_pair(M, k, j1, j2):
                        continue
                    total_connected_pairs += 1

                    ok, failed, uniform = check_direction_gap(M, k, j1, j2)

                    if uniform != "mixed":
                        total_uniform_pairs += 1

                    if not ok:
                        total_2hop_fail += len(failed)
                        rescued, not_rescued = check_multihop_rescue(
                            M, k, j1, j2, failed)
                        total_multihop_rescued += len(rescued)
                        total_multihop_fail += len(not_rescued)

            if (s+1) % max(1, samples//5) == 0:
                print(f"  k={k}: {s+1}/{samples}...", flush=True)

        print(f"\nk={k} ({samples} samples):")
        print(f"  Connected pairs found: {total_connected_pairs}")
        print(f"  Uniform pairs: {total_uniform_pairs} "
              f"({100*total_uniform_pairs/max(1,total_connected_pairs):.1f}%)")
        print(f"  2-hop direction failures: {total_2hop_fail}")
        print(f"  Multi-hop rescued: {total_multihop_rescued}")
        print(f"  Multi-hop STILL FAILED: {total_multihop_fail}")
        print()


if __name__ == "__main__":
    main()
