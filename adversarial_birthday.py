"""
Adversarial test: find the timestamp assignment that MINIMIZES
P(random hub valid) = fraction of hubs within budget.

If the adversarial minimum P is still bounded away from 0,
the birthday bound holds worst-case.

Strategy: for small n, try structured timestamp assignments
(identity, reverse, circulant, etc.) and also use gradient-free
optimization to minimize P.
"""

import random
from itertools import permutations

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


def interactive_greedy_cover(n, timestamps, hub, target):
    star = {(min(hub, v), max(hub, v)) for v in range(n) if v != hub}
    non_star = [e for e in timestamps if e not in star]
    current = set(star)
    count = 0
    while count < len(non_star):
        sub = sorted([(timestamps[e], e[0], e[1]) for e in current])
        cur_reach = compute_reachability(n, sub)
        if cur_reach == target:
            return count, True
        cur_count = len(cur_reach)
        best_e, best_g = None, 0
        for e in non_star:
            if e in current:
                continue
            trial = current | {e}
            sub2 = sorted([(timestamps[ee], ee[0], ee[1]) for ee in trial])
            g = len(compute_reachability(n, sub2)) - cur_count
            if g > best_g:
                best_g = g
                best_e = e
        if best_e is None or best_g <= 0:
            return count, False
        current.add(best_e)
        count += 1
    sub = sorted([(timestamps[e], e[0], e[1]) for e in current])
    return count, compute_reachability(n, sub) == target


def count_valid_hubs(n, timestamps):
    """Count hubs where greedy cover ≤ budget."""
    edges = list(timestamps.keys())
    m = len(edges)
    all_timed = sorted([(t, u, v) for (u, v), t in timestamps.items()])
    target = compute_reachability(n, all_timed)
    budget = n - 2
    valid = 0
    sizes = []
    for h in range(n):
        size, ok = interactive_greedy_cover(n, timestamps, h, target)
        if ok and size <= budget:
            valid += 1
        sizes.append(size if ok else 999)
    return valid, sizes


def make_timestamps(n, perm):
    """From a permutation of {1..m}, build timestamps."""
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
    return {e: t for e, t in zip(edges, perm)}


def swap_mutation(perm):
    """Swap two random elements."""
    p = list(perm)
    i, j = random.sample(range(len(p)), 2)
    p[i], p[j] = p[j], p[i]
    return p


def main():
    print("Adversarial birthday bound: minimize P(random hub valid)")
    print("=" * 70)

    for n in [6, 7, 8]:
        m = n * (n - 1) // 2
        budget = n - 2
        print(f"\nK_{n} (m={m}, budget={budget})")
        print("-" * 50)

        # 1. Structured instances
        print("\n  Structured instances:")

        # Identity ordering
        perm_id = list(range(1, m + 1))
        ts = make_timestamps(n, perm_id)
        valid, sizes = count_valid_hubs(n, ts)
        print(f"    Identity: {valid}/{n} valid hubs, sizes={sizes}")

        # Reverse
        perm_rev = list(range(m, 0, -1))
        ts = make_timestamps(n, perm_rev)
        valid, sizes = count_valid_hubs(n, ts)
        print(f"    Reverse: {valid}/{n} valid hubs, sizes={sizes}")

        # Random best/worst from sampling
        print(f"\n  Random sampling (10000 instances):")
        min_valid = n + 1
        max_valid = -1
        valid_dist = [0] * (n + 1)

        for trial in range(10000):
            perm = list(range(1, m + 1))
            random.shuffle(perm)
            ts = make_timestamps(n, perm)
            valid, _ = count_valid_hubs(n, ts)
            valid_dist[valid] += 1
            min_valid = min(min_valid, valid)
            max_valid = max(max_valid, valid)

        print(f"    Min valid hubs: {min_valid}")
        print(f"    Max valid hubs: {max_valid}")
        print(f"    Distribution:")
        for v in range(n + 1):
            if valid_dist[v] > 0:
                print(f"      {v} valid: {valid_dist[v]} "
                      f"({100*valid_dist[v]/10000:.2f}%)")

        # 2. Hill-climbing to minimize valid hub count
        print(f"\n  Hill-climbing (minimize valid hubs):")
        best_perm = list(range(1, m + 1))
        random.shuffle(best_perm)
        ts = make_timestamps(n, best_perm)
        best_valid, _ = count_valid_hubs(n, ts)

        for step in range(5000):
            candidate = swap_mutation(best_perm)
            ts = make_timestamps(n, candidate)
            valid, _ = count_valid_hubs(n, ts)
            if valid <= best_valid:
                best_perm = candidate
                best_valid = valid
                if valid == 0:
                    print(f"    Step {step}: FOUND ZERO VALID HUBS!")
                    ts = make_timestamps(n, best_perm)
                    _, sizes = count_valid_hubs(n, ts)
                    print(f"    Sizes: {sizes}")
                    break

        print(f"    Best found: {best_valid} valid hubs")
        if best_valid > 0:
            ts = make_timestamps(n, best_perm)
            _, sizes = count_valid_hubs(n, ts)
            print(f"    Sizes: {sizes}")
            p = best_valid / n
            print(f"    Adversarial P = {p:.3f}")
            print(f"    Birthday P(none) = (1-{p:.3f})^{n} = {(1-p)**n:.6f}")


if __name__ == '__main__':
    main()
