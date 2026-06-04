"""
Can the adversary block ALL relays for a specific scale-1 pair?

For a fixed hub h and scale-1 pair at rank j:
- Route A relays: ranks 0..j-2, need τ_{src,a} > T_a for blocking
- Route B relays: ranks j+2..n-2, need τ_{a,tgt} < T_a for blocking

The adversary controls the full timestamp assignment. Can they make
ALL relays dead for some pair?

Strategy: hill-climb on timestamps to maximize the number of
scale-1 pairs with zero live relays.
"""

import random

random.seed(42)


def count_unrescued_pairs(n, perm, hub):
    """Count scale-1 pairs with zero live 3-hop relays for given hub."""
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
    timestamps = {e: t for e, t in zip(edges, perm)}

    non_hub = [v for v in range(n) if v != hub]
    star_times = {v: timestamps[(min(hub, v), max(hub, v))] for v in non_hub}
    ordered = sorted(non_hub, key=lambda v: star_times[v])
    T = [star_times[v] for v in ordered]

    unrescued = 0
    for j in range(len(ordered) - 1):
        src = ordered[j + 1]
        tgt = ordered[j]
        has_live = False

        # Route A: relay a with rank < j
        for a in range(j):
            va = ordered[a]
            e = (min(src, va), max(src, va))
            if timestamps[e] <= T[a]:
                has_live = True
                break

        if not has_live:
            # Route B: relay a with rank > j+1
            for a in range(j + 2, len(ordered)):
                va = ordered[a]
                e = (min(va, tgt), max(va, tgt))
                if timestamps[e] >= T[a]:
                    has_live = True
                    break

        if not has_live:
            unrescued += 1

    return unrescued


def total_unrescued(n, perm):
    """Total unrescued pairs across ALL hubs."""
    return sum(count_unrescued_pairs(n, perm, h) for h in range(n))


def max_unrescued_any_hub(n, perm):
    """Max unrescued pairs for the BEST hub (adversary's target)."""
    return min(count_unrescued_pairs(n, perm, h) for h in range(n))


def swap(perm):
    p = list(perm)
    i, j = random.sample(range(len(p)), 2)
    p[i], p[j] = p[j], p[i]
    return p


def main():
    print("Adversarial gap blocking")
    print("=" * 70)

    for n in [8, 10, 12, 15, 20]:
        m = n * (n - 1) // 2

        # Hill-climb to maximize unrescued pairs for the BEST hub
        # (= minimize the minimum over hubs)
        perm = list(range(1, m + 1))
        random.shuffle(perm)
        best_score = max_unrescued_any_hub(n, perm)
        best_perm = list(perm)

        steps = 20000 if n <= 12 else 10000

        for step in range(steps):
            candidate = swap(perm)
            score = max_unrescued_any_hub(n, candidate)
            if score >= best_score:
                perm = candidate
                if score > best_score:
                    best_score = score
                    best_perm = list(perm)

        # Also check: for the worst hub, how many unrescued?
        per_hub = [count_unrescued_pairs(n, best_perm, h) for h in range(n)]

        print(f"\nK_{n} (m={m}, budget={n-2}, {steps} hill-climb steps):")
        print(f"  Best adversarial: min-over-hubs unrescued = {best_score}")
        print(f"  Per-hub unrescued: {per_hub}")
        print(f"  Best hub has {min(per_hub)} unrescued scale-1 pairs "
              f"out of {n-2}")

        # Also: what fraction of total backward pairs are unrescued
        # (not just scale-1)?
        # Scale-1 is the hardest, so if those are 0, all pairs are rescued
        if min(per_hub) == 0:
            print(f"  ✓ Best hub has 0 unrescued scale-1 pairs")
        else:
            print(f"  ✗ Even best hub has {min(per_hub)} unrescued")

    # Detailed analysis for small n
    print(f"\n\n{'='*70}")
    print("Exhaustive: what's the WORST possible timestamp assignment?")
    print("=" * 70)

    for n in [6, 7]:
        m = n * (n - 1) // 2
        worst_best_hub = 0
        worst_perm = None

        # Extensive hill-climbing
        for restart in range(20):
            perm = list(range(1, m + 1))
            random.shuffle(perm)

            for step in range(50000):
                candidate = swap(perm)
                score = max_unrescued_any_hub(n, candidate)
                cur_score = max_unrescued_any_hub(n, perm)
                if score >= cur_score:
                    perm = candidate
                    if score > worst_best_hub:
                        worst_best_hub = score
                        worst_perm = list(perm)

        per_hub = [count_unrescued_pairs(n, worst_perm, h) for h in range(n)]
        print(f"\nK_{n}: worst found = {worst_best_hub} unrescued for best hub")
        print(f"  Per-hub: {per_hub}")


if __name__ == '__main__':
    main()
