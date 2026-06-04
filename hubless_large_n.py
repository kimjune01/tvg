"""
Hunt for hub-less instances at n≥8 with massive sampling.

Strategy: greedy is fast, use it as filter. For greedy failures,
run exhaustive tree search to confirm truly hub-less.

At n=8: C(21,6) = 54,264 per hub × 8 hubs = 434,112 total checks.
Feasible per instance, ~1 sec each.

At n=9: C(27,7) = 888,030 per hub × 9 hubs = 7,992,270. Slow (~30s).
Use randomized tree search as middle ground.
"""

import random
from itertools import combinations
import time

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


def check_spanner(n, timestamps, edge_set, target=None):
    if target is None:
        all_timed = sorted([(t, u, v) for (u, v), t in timestamps.items()])
        target = compute_reachability(n, all_timed)
    sub_timed = sorted([(timestamps[e], e[0], e[1]) for e in edge_set])
    return compute_reachability(n, sub_timed) == target


def greedy_star_tree(n, timestamps, hub, target):
    star = {(min(hub, v), max(hub, v)) for v in range(n) if v != hub}
    non_star = [e for e in timestamps if e not in star]
    current = set(star)

    for _ in range(n - 2):
        sub = sorted([(timestamps[e], e[0], e[1]) for e in current])
        cur_reach = compute_reachability(n, sub)
        if cur_reach == target:
            return True
        cur_count = len(cur_reach)
        best_e, best_g = None, -1
        for e in non_star:
            if e in current:
                continue
            trial = current | {e}
            sub = sorted([(timestamps[ee], ee[0], ee[1]) for ee in trial])
            g = len(compute_reachability(n, sub)) - cur_count
            if g > best_g:
                best_g = g
                best_e = e
        if best_e is None or best_g <= 0:
            break
        current.add(best_e)

    if len(current) > 2 * n - 3:
        return False
    sub = sorted([(timestamps[e], e[0], e[1]) for e in current])
    return compute_reachability(n, sub) == target


def exhaustive_star_tree(n, timestamps, hub, target):
    star = {(min(hub, v), max(hub, v)) for v in range(n) if v != hub}
    non_star = [e for e in timestamps if e not in star]
    for tree_edges in combinations(non_star, n - 2):
        if check_spanner(n, timestamps, star | set(tree_edges), target):
            return True
    return False


def random_tree_search(n, timestamps, hub, target, num_tries=10000):
    """Random tree search: sample random (n-2)-subsets of non-star edges."""
    star = {(min(hub, v), max(hub, v)) for v in range(n) if v != hub}
    non_star = [e for e in timestamps if e not in star]
    need = n - 2
    for _ in range(num_tries):
        sample = random.sample(non_star, need)
        if check_spanner(n, timestamps, star | set(sample), target):
            return True
    return False


def main():
    print("Hunting for hub-less instances at large n")
    print("=" * 70)

    configs = [
        # (n, samples, exhaustive_if_greedy_fails, random_tree_tries)
        (8,  100000, True,  0),
        (9,   50000, False, 50000),
        (10,  50000, False, 50000),
        (11,  30000, False, 50000),
        (12,  20000, False, 50000),
        (15,  10000, False, 50000),
        (20,   5000, False, 50000),
    ]

    for n, samples, do_exhaustive, rand_tries in configs:
        m = n * (n - 1) // 2
        edges_template = [(i, j) for i in range(n) for j in range(i + 1, n)]

        greedy_fails = 0
        truly_hubless = 0
        random_rescued = 0
        start = time.time()

        for trial in range(samples):
            ts_vals = list(range(1, m + 1))
            random.shuffle(ts_vals)
            timestamps = {e: t for e, t in zip(edges_template, ts_vals)}

            all_timed = sorted([(t, u, v) for (u, v), t in timestamps.items()])
            target = compute_reachability(n, all_timed)

            # Greedy check
            has_greedy = any(greedy_star_tree(n, timestamps, h, target)
                            for h in range(n))
            if has_greedy:
                continue

            greedy_fails += 1

            # Try to rescue
            rescued = False

            if do_exhaustive:
                for h in range(n):
                    if exhaustive_star_tree(n, timestamps, h, target):
                        rescued = True
                        break
            elif rand_tries > 0:
                for h in range(n):
                    if random_tree_search(n, timestamps, h, target,
                                          rand_tries // n):
                        rescued = True
                        random_rescued += 1
                        break

            if not rescued:
                truly_hubless += 1
                if truly_hubless <= 2:
                    print(f"  K_{n} CANDIDATE hub-less instance found! "
                          f"(trial {trial})")

            if (trial + 1) % (samples // 5) == 0:
                elapsed = time.time() - start
                rate = (trial + 1) / elapsed
                print(f"  K_{n}: {trial+1}/{samples} ({rate:.0f}/s), "
                      f"greedy_fails={greedy_fails}, hubless={truly_hubless}")

        elapsed = time.time() - start
        method = "exhaustive" if do_exhaustive else f"random({rand_tries})"
        print(f"\nK_{n} (n={n}, m={m}): {samples} samples in {elapsed:.1f}s")
        print(f"  Greedy failures: {greedy_fails} ({100*greedy_fails/samples:.4f}%)")
        print(f"  Truly hub-less ({method}): {truly_hubless}")
        if random_rescued:
            print(f"  Random tree rescued: {random_rescued}")
        print()


if __name__ == '__main__':
    main()
