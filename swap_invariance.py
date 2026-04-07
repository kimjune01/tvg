"""
Swap invariance: does swapping two adjacent timestamps ever break
the spanner property?

Start from any labeling that has a valid hub+tree. Swap two adjacent
timestamps (values t and t+1). Check: does a valid hub+tree still exist?

If swap invariance holds, then by induction from the identity permutation
(where everything works trivially), every permutation has a valid spanner.

Also test: non-adjacent swaps (any two timestamps).
"""

import random
from itertools import combinations


def make_edges(n):
    return [(i, j) for i in range(n) for j in range(i + 1, n)]


def compute_reachability(n, timed_edges):
    reached_by = [dict() for _ in range(n)]
    for i in range(n):
        reached_by[i][i] = 0
    for t, u, v in timed_edges:
        sources_u = {s: arr for s, arr in reached_by[u].items() if arr <= t}
        sources_v = {s: arr for s, arr in reached_by[v].items() if arr <= t}
        for s, arr in sources_u.items():
            if s not in reached_by[v] or t < reached_by[v][s]:
                reached_by[v][s] = t
        for s, arr in sources_v.items():
            if s not in reached_by[u] or t < reached_by[u][s]:
                reached_by[u][s] = t
    reach = [0] * n
    for v in range(n):
        for s in reached_by[v]:
            if s != v:
                reach[s] |= (1 << v)
    return reach


def exhaustive_any_hub(n, edges, timestamps):
    """Does ANY hub have a valid tree? (exhaustive)"""
    m = len(edges)
    timed = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in range(m)])
    target = compute_reachability(n, timed)

    for hub in range(n):
        star_idx = set(i for i, (u, v) in enumerate(edges) if u == hub or v == hub)
        tree_candidates = [i for i in range(m) if i not in star_idx]
        for subset in combinations(tree_candidates, n - 2):
            used = star_idx | set(subset)
            sub = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in used])
            if compute_reachability(n, sub) == target:
                return True
    return False


def count_valid_hubs_greedy(n, edges, timestamps):
    """Count hubs where greedy tree works."""
    m = len(edges)
    timed = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in range(m)])
    target = compute_reachability(n, timed)
    count = 0

    for hub in range(n):
        star_idx = set(i for i, (u, v) in enumerate(edges) if u == hub or v == hub)
        current = set(star_idx)
        tree_candidates = [i for i in range(m) if i not in star_idx]

        for _ in range(n - 2):
            sub = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in current])
            cr = compute_reachability(n, sub)
            if cr == target:
                break
            current_covered = sum(bin(r).count('1') for r in cr)
            best_edge = None
            best_gain = -1
            for idx in tree_candidates:
                if idx in current:
                    continue
                trial = current | {idx}
                sub2 = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in trial])
                tr = compute_reachability(n, sub2)
                gain = sum(bin(r).count('1') for r in tr) - current_covered
                if gain > best_gain:
                    best_gain = gain
                    best_edge = idx
            if best_edge is None or best_gain <= 0:
                break
            current.add(best_edge)

        sub = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in current])
        if compute_reachability(n, sub) == target:
            count += 1

    return count


def run(n, num_samples):
    edges = make_edges(n)
    m = len(edges)
    print(f"\nK_{n}: {n} vertices, {m} edges")
    print("=" * 60)

    adj_swap_breaks = 0
    adj_swap_total = 0
    any_swap_breaks = 0
    any_swap_total = 0

    # Track: does swapping ever REDUCE the number of valid hubs to 0?
    adj_kills_all = 0
    any_kills_all = 0

    # Track greedy hub count change
    adj_greedy_worse = 0
    adj_greedy_better = 0
    adj_greedy_same = 0

    for trial in range(num_samples):
        ts = list(range(1, m + 1))
        random.shuffle(ts)

        # Baseline: count greedy hubs
        base_hubs = count_valid_hubs_greedy(n, edges, ts)

        # Adjacent swaps: swap values t and t+1
        for t_val in range(1, m):
            # Find which edges have timestamps t_val and t_val+1
            idx_a = ts.index(t_val)
            idx_b = ts.index(t_val + 1)

            # Swap
            ts_new = ts[:]
            ts_new[idx_a], ts_new[idx_b] = ts_new[idx_b], ts_new[idx_a]

            new_hubs = count_valid_hubs_greedy(n, edges, ts_new)
            adj_swap_total += 1

            if new_hubs < base_hubs:
                adj_greedy_worse += 1
            elif new_hubs > base_hubs:
                adj_greedy_better += 1
            else:
                adj_greedy_same += 1

            if new_hubs == 0:
                # Check exhaustive
                if not exhaustive_any_hub(n, edges, ts_new):
                    adj_kills_all += 1
                    adj_swap_breaks += 1

        # A few random non-adjacent swaps
        for _ in range(5):
            i, j = random.sample(range(m), 2)
            ts_new = ts[:]
            ts_new[i], ts_new[j] = ts_new[j], ts_new[i]

            new_hubs = count_valid_hubs_greedy(n, edges, ts_new)
            any_swap_total += 1
            if new_hubs == 0:
                if not exhaustive_any_hub(n, edges, ts_new):
                    any_kills_all += 1
                    any_swap_breaks += 1

        if (trial + 1) % max(1, num_samples // 5) == 0:
            print(f"  {trial+1}/{num_samples}: adj_worse={adj_greedy_worse} "
                  f"adj_kills_all={adj_kills_all}")

    print(f"\nAdjacent swaps ({adj_swap_total} total):")
    print(f"  Greedy worse: {adj_greedy_worse} ({adj_greedy_worse/adj_swap_total*100:.2f}%)")
    print(f"  Greedy better: {adj_greedy_better} ({adj_greedy_better/adj_swap_total*100:.2f}%)")
    print(f"  Greedy same: {adj_greedy_same} ({adj_greedy_same/adj_swap_total*100:.2f}%)")
    print(f"  Kills ALL hubs (exhaustive): {adj_kills_all}")

    print(f"\nRandom swaps ({any_swap_total} total):")
    print(f"  Kills ALL hubs (exhaustive): {any_kills_all}")


def main():
    random.seed(42)
    for n, samples in [(4, 5000), (5, 2000), (6, 500)]:
        run(n, samples)


if __name__ == "__main__":
    main()
