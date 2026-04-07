"""
Where exactly is the greedy gap?

For instances where greedy fails on ALL hubs:
1. Try exhaustive tree search for each hub
2. If exhaustive finds a solution, show which tree it picked
   vs what greedy picked — what went wrong?

Also: can we improve greedy with backtracking?
Try greedy with 1-step lookahead or 1-step backtrack.
"""

import random
import time
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


def check_spanner(n, edges, timestamps, hub, tree_edge_indices):
    """Check if star(hub) + given tree edges span G."""
    m = len(edges)
    timed = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in range(m)])
    target = compute_reachability(n, timed)

    star_idx = set(i for i, (u, v) in enumerate(edges) if u == hub or v == hub)
    used = star_idx | set(tree_edge_indices)
    sub = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in used])
    reach = compute_reachability(n, sub)
    return reach == target


def greedy_tree(n, edges, timestamps, hub):
    """Returns (ok, tree_edges_chosen)."""
    m = len(edges)
    timed = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in range(m)])
    target = compute_reachability(n, timed)
    star_idx = set(i for i, (u, v) in enumerate(edges) if u == hub or v == hub)
    current = set(star_idx)
    tree_candidates = [i for i in range(m) if i not in star_idx]
    tree_chosen = []

    def current_reach():
        sub = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in current])
        return compute_reachability(n, sub)

    for _ in range(n - 2):
        cr = current_reach()
        if cr == target:
            break
        current_covered = sum(bin(r).count('1') for r in cr)
        best_edge = None
        best_gain = -1
        for idx in tree_candidates:
            if idx in current:
                continue
            trial = current | {idx}
            sub = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in trial])
            tr = compute_reachability(n, sub)
            gain = sum(bin(r).count('1') for r in tr) - current_covered
            if gain > best_gain:
                best_gain = gain
                best_edge = idx
        if best_edge is None or best_gain <= 0:
            break
        current.add(best_edge)
        tree_chosen.append(best_edge)

    return current_reach() == target, tree_chosen


def exhaustive_tree(n, edges, timestamps, hub):
    """Try all possible n-2 edge subsets from non-star edges."""
    m = len(edges)
    timed = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in range(m)])
    target = compute_reachability(n, timed)
    star_idx = set(i for i, (u, v) in enumerate(edges) if u == hub or v == hub)
    tree_candidates = [i for i in range(m) if i not in star_idx]

    # Try all subsets of size n-2
    for subset in combinations(tree_candidates, n - 2):
        used = star_idx | set(subset)
        sub = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in used])
        reach = compute_reachability(n, sub)
        if reach == target:
            return True, list(subset)

    # Also try smaller subsets (maybe fewer than n-2 suffice)
    for size in range(1, n - 2):
        for subset in combinations(tree_candidates, size):
            used = star_idx | set(subset)
            sub = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in used])
            reach = compute_reachability(n, sub)
            if reach == target:
                return True, list(subset)

    return False, []


def greedy_with_backtrack(n, edges, timestamps, hub):
    """Greedy with 1-step backtrack: if greedy fails, try removing
    each chosen tree edge and replacing with a different one."""
    ok, tree_chosen = greedy_tree(n, edges, timestamps, hub)
    if ok:
        return True, tree_chosen

    m = len(edges)
    star_idx = set(i for i, (u, v) in enumerate(edges) if u == hub or v == hub)
    tree_candidates = [i for i in range(m) if i not in star_idx]

    # Try removing each greedy-chosen edge and replacing
    for remove_idx in range(len(tree_chosen)):
        remaining = [tree_chosen[j] for j in range(len(tree_chosen)) if j != remove_idx]
        # Try each candidate as replacement
        for replacement in tree_candidates:
            if replacement in remaining or replacement in star_idx:
                continue
            trial_tree = remaining + [replacement]
            if check_spanner(n, edges, timestamps, hub, trial_tree):
                return True, trial_tree

    return False, tree_chosen


def run(n, num_samples):
    edges = make_edges(n)
    m = len(edges)
    print(f"\nK_{n}: {n} vertices, {m} edges")
    print("=" * 70)

    greedy_instance_ok = 0
    backtrack_instance_ok = 0
    exhaust_instance_ok = 0
    greedy_vertex_ok = 0
    backtrack_vertex_ok = 0
    exhaust_vertex_ok = 0
    total_v = 0

    greedy_fail_instances = []
    start = time.time()

    for trial in range(num_samples):
        ts = list(range(1, m + 1))
        random.shuffle(ts)

        g_any = False
        b_any = False
        e_any = False

        for v in range(n):
            total_v += 1
            g_ok, g_tree = greedy_tree(n, edges, ts, v)
            if g_ok:
                greedy_vertex_ok += 1
                backtrack_vertex_ok += 1
                exhaust_vertex_ok += 1
                g_any = True
                b_any = True
                e_any = True
            else:
                b_ok, b_tree = greedy_with_backtrack(n, edges, ts, v)
                if b_ok:
                    backtrack_vertex_ok += 1
                    b_any = True
                    exhaust_vertex_ok += 1
                    e_any = True
                else:
                    e_ok, e_tree = exhaustive_tree(n, edges, ts, v)
                    if e_ok:
                        exhaust_vertex_ok += 1
                        e_any = True

        if g_any:
            greedy_instance_ok += 1
        if b_any:
            backtrack_instance_ok += 1
        if e_any:
            exhaust_instance_ok += 1

        if not g_any:
            greedy_fail_instances.append(ts[:])

        if (trial + 1) % max(1, num_samples // 5) == 0:
            elapsed = time.time() - start
            print(f"  {trial+1}/{num_samples}: greedy={greedy_instance_ok} "
                  f"backtrack={backtrack_instance_ok} exhaust={exhaust_instance_ok} "
                  f"({elapsed:.1f}s)")

    total = num_samples
    print(f"\nInstance-level success (≥1 hub works):")
    print(f"  greedy:    {greedy_instance_ok}/{total} ({greedy_instance_ok/total*100:.2f}%)")
    print(f"  backtrack: {backtrack_instance_ok}/{total} ({backtrack_instance_ok/total*100:.2f}%)")
    print(f"  exhaust:   {exhaust_instance_ok}/{total} ({exhaust_instance_ok/total*100:.2f}%)")

    print(f"\nVertex-level success:")
    print(f"  greedy:    {greedy_vertex_ok}/{total_v} ({greedy_vertex_ok/total_v*100:.2f}%)")
    print(f"  backtrack: {backtrack_vertex_ok}/{total_v} ({backtrack_vertex_ok/total_v*100:.2f}%)")
    print(f"  exhaust:   {exhaust_vertex_ok}/{total_v} ({exhaust_vertex_ok/total_v*100:.2f}%)")

    backtrack_gain = backtrack_vertex_ok - greedy_vertex_ok
    exhaust_gain = exhaust_vertex_ok - backtrack_vertex_ok
    print(f"\n  Backtrack recovers: {backtrack_gain} vertices ({backtrack_gain/total_v*100:.2f}%)")
    print(f"  Exhaustive recovers beyond backtrack: {exhaust_gain} vertices ({exhaust_gain/total_v*100:.2f}%)")

    # Analyze greedy fail instances
    if greedy_fail_instances and len(greedy_fail_instances) <= 5:
        print(f"\nGreedy-fail instance analysis:")
        for idx, ts in enumerate(greedy_fail_instances[:3]):
            print(f"\n  Instance {idx+1}:")
            for v in range(n):
                g_ok, g_tree = greedy_tree(n, edges, ts, v)
                b_ok, b_tree = greedy_with_backtrack(n, edges, ts, v)
                e_ok, e_tree = exhaustive_tree(n, edges, ts, v)
                status = "greedy" if g_ok else ("backtrack" if b_ok else ("exhaust" if e_ok else "NONE"))
                tree = g_tree if g_ok else (b_tree if b_ok else (e_tree if e_ok else []))
                tree_edges = [f"({edges[i][0]},{edges[i][1]})@{ts[i]}" for i in tree]
                print(f"    hub={v}: {status:>10s}  tree={tree_edges}")


def main():
    random.seed(42)
    for n, samples in [(5, 5000), (6, 1000)]:
        run(n, samples)


if __name__ == "__main__":
    main()
