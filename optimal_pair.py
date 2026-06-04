"""
Find what characterizes (h,v) pairs with DZ = 0.

For DZ(h,v) = 0: every edge from v is LIVE. I.e., for every w:
σ({v,w}) is NOT between σ({h,v}) and σ({h,w}).

Equivalently: σ({v,w}) and σ({h,w}) are on the same side of S = σ({h,v}).

Let S = σ({h,v}). Then:
DZ = 0 iff for all w: (σ({v,w}) < S iff σ({h,w}) < S)
              OR     (σ({v,w}) > S iff σ({h,w}) > S)

This means: v's edges and h's edges have the same "sign pattern" relative
to their shared edge timestamp S.

Let L(v) = {w : σ({v,w}) < S} and R(v) = {w : σ({v,w}) > S}.
Let L(h) = {w : σ({h,w}) < S} and R(h) = {w : σ({h,w}) > S}.

DZ = 0 iff L(v) ⊇ L(h) and R(v) ⊇ R(h) (not quite — it's the symmetric condition).

Actually: DZ = 0 iff for each w ≠ h,v: [σ({v,w}) < S ↔ σ({h,w}) < S].

I.e., L(v) ∩ (V \ {h,v}) = L(h) ∩ (V \ {h,v}). The set of vertices
reachable "early" (before S) is the same for both h and v.

What determines this? S is the timestamp of edge {h,v}. Edges from h
and v to other vertices are separate. The condition is that their
"early/late" partitions (relative to S) agree.

This is like a "concordance" condition. How often does it hold?
"""

import random
from collections import Counter

random.seed(42)


def find_dz0_pairs(n, sigma):
    """Find all (h,v) pairs with DZ = 0."""
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
    ts = {e: t for e, t in zip(edges, sigma)}

    dz0_pairs = []
    for h in range(n):
        for v in range(n):
            if v == h:
                continue
            S = ts[(min(h, v), max(h, v))]
            dz = 0
            for w in range(n):
                if w == h or w == v:
                    continue
                a = ts[(min(h, w), max(h, w))]
                c = ts[(min(v, w), max(v, w))]
                if min(S, a) < c < max(S, a):
                    dz += 1
            if dz == 0:
                dz0_pairs.append((h, v, S))

    return dz0_pairs


def analyze_dz0(n, sigma, h, v, S):
    """Analyze the structure of a DZ=0 pair."""
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
    ts = {e: t for e, t in zip(edges, sigma)}

    # Partition vertices by early/late relative to S
    early_h = []  # σ({h,w}) < S
    late_h = []   # σ({h,w}) > S
    early_v = []  # σ({v,w}) < S
    late_v = []

    for w in range(n):
        if w == h or w == v:
            continue
        a = ts[(min(h, w), max(h, w))]
        c = ts[(min(v, w), max(v, w))]
        if a < S:
            early_h.append(w)
        else:
            late_h.append(w)
        if c < S:
            early_v.append(w)
        else:
            late_v.append(w)

    return {
        'S': S,
        'S_rank_among_h': sum(1 for w in range(n) if w != h and
                               ts[(min(h, w), max(h, w))] < S),
        'S_rank_among_v': sum(1 for w in range(n) if w != v and
                               ts[(min(v, w), max(v, w))] < S),
        'early_h': len(early_h),
        'late_h': len(late_h),
        'early_v': len(early_v),
        'late_v': len(late_v),
        'concordance': set(early_h) == set(early_v),
    }


def main():
    print("Optimal (h,v) pairs with DZ = 0")
    print("=" * 70)

    for n in [6, 8, 10]:
        m = n * (n - 1) // 2
        samples = 2000

        dz0_count = 0
        dz0_s_ranks_h = []  # where S falls among h's edges
        dz0_s_ranks_v = []
        total_pairs = 0
        concordance_count = 0

        for trial in range(samples):
            perm = list(range(1, m + 1))
            random.shuffle(perm)

            pairs = find_dz0_pairs(n, perm)
            dz0_count += len(pairs)
            total_pairs += n * (n - 1)

            for h, v, S in pairs[:5]:  # analyze up to 5 per instance
                info = analyze_dz0(n, perm, h, v, S)
                dz0_s_ranks_h.append(info['S_rank_among_h'])
                dz0_s_ranks_v.append(info['S_rank_among_v'])
                if info['concordance']:
                    concordance_count += 1

        avg_dz0_per_instance = dz0_count / samples
        print(f"\nK_{n}: {samples} instances")
        print(f"  DZ=0 pairs per instance: mean={avg_dz0_per_instance:.1f}")
        print(f"  DZ=0 pairs total: {dz0_count}/{total_pairs} "
              f"({100*dz0_count/total_pairs:.2f}%)")

        if dz0_s_ranks_h:
            # Where does S rank among h's edges?
            dist_h = Counter(dz0_s_ranks_h)
            dist_v = Counter(dz0_s_ranks_v)
            print(f"  S rank among h's edges (0=min, {n-2}=max):")
            for k in sorted(dist_h):
                print(f"    {k}: {dist_h[k]} ({100*dist_h[k]/len(dz0_s_ranks_h):.1f}%)")
            print(f"  S rank among v's edges:")
            for k in sorted(dist_v):
                print(f"    {k}: {dist_v[k]} ({100*dist_v[k]/len(dz0_s_ranks_v):.1f}%)")

    # Detailed examples
    print(f"\n\n{'='*70}")
    print("Detailed DZ=0 examples")
    print("=" * 70)

    n = 8
    m = n * (n - 1) // 2
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]

    for trial in range(10):
        perm = list(range(1, m + 1))
        random.shuffle(perm)
        ts = {e: t for e, t in zip(edges, perm)}
        pairs = find_dz0_pairs(n, perm)
        if not pairs:
            continue

        h, v, S = pairs[0]
        info = analyze_dz0(n, perm, h, v, S)

        print(f"\n  Trial {trial}: (h={h}, v={v}), S={S}")
        print(f"    S is rank {info['S_rank_among_h']} among h's edges, "
              f"rank {info['S_rank_among_v']} among v's edges")
        print(f"    Early/late h: {info['early_h']}/{info['late_h']}, "
              f"v: {info['early_v']}/{info['late_v']}")

        for w in range(n):
            if w == h or w == v:
                continue
            a = ts[(min(h, w), max(h, w))]
            c = ts[(min(v, w), max(v, w))]
            side_h = "<" if a < S else ">"
            side_v = "<" if c < S else ">"
            match = "✓" if (a < S) == (c < S) else "✗"
            print(f"      w={w}: h-edge={a:2d} {side_h} S={S}, "
                  f"v-edge={c:2d} {side_v} S={S}  {match}")
        break  # just one example


if __name__ == '__main__':
    main()
