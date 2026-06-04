"""
Verify hub-less instances: does greedy tree miss valid trees?

For small n, try ALL (n-2)-subsets of non-star edges as the tree component.
If any works, the instance isn't truly hub-less — greedy just failed.
"""

import random
from itertools import combinations

random.seed(42)


def compute_reachability(n, timed_edges):
    reached_by = [dict() for _ in range(n)]
    for i in range(n):
        reached_by[i][i] = 0
    for t, u, v in sorted(timed_edges):
        sources_u = {s: arr for s, arr in reached_by[u].items() if arr <= t}
        sources_v = {s: arr for s, arr in reached_by[v].items() if arr <= t}
        for s, arr in sources_u.items():
            if s not in reached_by[v] or t < reached_by[v][s]:
                reached_by[v][s] = t
        for s, arr in sources_v.items():
            if s not in reached_by[u] or t < reached_by[u][s]:
                reached_by[u][s] = t
    pairs = set()
    for v in range(n):
        for s in reached_by[v]:
            if s != v:
                pairs.add((s, v))
    return pairs


def check_spanner(n, timestamps, edges):
    """Check if edge set is a valid temporal spanner."""
    all_timed = sorted([(t, u, v) for (u, v), t in timestamps.items()])
    target = compute_reachability(n, all_timed)
    sub_timed = sorted([(timestamps[e], e[0], e[1]) for e in edges])
    span_reach = compute_reachability(n, sub_timed)
    return span_reach == target


def star_exhaustive_check(n, timestamps, hub):
    """Try ALL possible (n-2)-subsets of non-star edges with star(hub)."""
    star = {(min(hub, v), max(hub, v)) for v in range(n) if v != hub}
    non_star = [e for e in timestamps if e not in star]
    need = n - 2  # tree edges needed

    for tree_edges in combinations(non_star, need):
        edges = star | set(tree_edges)
        if check_spanner(n, timestamps, edges):
            return True, set(tree_edges)
    return False, None


def main():
    print("Verifying hub-less instances: greedy vs exhaustive tree search")
    print("=" * 60)

    for n in [5, 6, 7]:
        m = n * (n - 1) // 2
        samples = {5: 50000, 6: 20000, 7: 5000}[n]
        greedy_hubless = 0
        true_hubless = 0
        greedy_rescued = 0
        total = 0

        print(f"\nK_{n}: checking {samples} instances...")

        for trial in range(samples):
            edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
            ts_vals = list(range(1, m + 1))
            random.shuffle(ts_vals)
            timestamps = {e: t for e, t in zip(edges, ts_vals)}
            total += 1

            # Quick greedy check for all hubs
            has_greedy_hub = False
            for h in range(n):
                star = {(min(h, v), max(h, v)) for v in range(n) if v != h}
                non_star = [e for e in timestamps if e not in star]

                # Greedy tree
                current = set(star)
                all_timed = sorted([(t, u, v) for (u, v), t in timestamps.items()])
                target = compute_reachability(n, all_timed)

                for _ in range(n - 2):
                    sub_timed = sorted([(timestamps[e], e[0], e[1]) for e in current])
                    cur_reach = compute_reachability(n, sub_timed)
                    if cur_reach == target:
                        break
                    cur_count = len(cur_reach)
                    best_e, best_g = None, -1
                    for e in non_star:
                        if e in current:
                            continue
                        trial_edges = current | {e}
                        sub = sorted([(timestamps[ee], ee[0], ee[1]) for ee in trial_edges])
                        tr = compute_reachability(n, sub)
                        g = len(tr) - cur_count
                        if g > best_g:
                            best_g = g
                            best_e = e
                    if best_e is None or best_g <= 0:
                        break
                    current.add(best_e)

                if len(current) <= 2 * n - 3:
                    sub_timed = sorted([(timestamps[e], e[0], e[1]) for e in current])
                    if compute_reachability(n, sub_timed) == target:
                        has_greedy_hub = True
                        break

            if has_greedy_hub:
                continue

            greedy_hubless += 1

            # Exhaustive: try all hubs with all possible trees
            truly_hubless = True
            for h in range(n):
                ok, tree = star_exhaustive_check(n, timestamps, h)
                if ok:
                    truly_hubless = False
                    greedy_rescued += 1
                    if greedy_rescued <= 5:
                        print(f"    Greedy missed: hub={h} works with tree={tree}")
                    break

            if truly_hubless:
                true_hubless += 1

        print(f"  Total: {total}")
        print(f"  Greedy hub-less: {greedy_hubless} ({100*greedy_hubless/total:.2f}%)")
        print(f"  Greedy missed (exhaustive finds hub): {greedy_rescued}")
        print(f"  Truly hub-less: {true_hubless} ({100*true_hubless/total:.2f}%)")


if __name__ == '__main__':
    main()
