"""
Proving the Median Floor Conjecture: ∃ (h,v) with DZ degree ≤ 1.

Angle: direct construction.

Key observation: for triangle {h,v,w}, edge {v,w} is DZ iff σ({v,w})
is the median of three timestamps. Equivalently: exactly one of
σ({h,v}), σ({h,w}) is less than σ({v,w}).

For vertex v and hub h: DZ degree = #{w : exactly one of σ({h,v}), σ({h,w})
is less than σ({v,w})}.

Let S = σ({h,v}) (star time of v). For each w ≠ v,h:
  a = σ({h,w}), c = σ({v,w})
  DZ iff (S < c < a) or (a < c < S) iff c is between S and a.
  LIVE iff c < min(S,a) or c > max(S,a).

Strategy: choose h,v such that S = σ({h,v}) is extreme (very large or
very small). Then for most w, c is on the same side of S as a, making
the edge LIVE.

If S = max of all timestamps: S > a for all a. DZ iff a < c < S.
LIVE iff c < a (c below both) or c > S (impossible since S = max).
So LIVE iff c < a, i.e., σ({v,w}) < σ({h,w}).
DZ iff σ({h,w}) < σ({v,w}) < σ({h,v}).

DZ degree = #{w : σ({h,w}) < σ({v,w})}. This is the number of vertices w
where v's edge to w has a LARGER timestamp than h's edge to w.

For this to be ≤ 1: at most 1 vertex w has σ({v,w}) > σ({h,w}).
I.e., for almost all w: σ({v,w}) < σ({h,w}).
I.e., h "dominates" v in the edge-comparison tournament.

Does such a domination pair always exist? Not necessarily — this is
about the tournament structure of pairwise edge comparisons.

Let me test: for the edge {h,v} with the global max timestamp,
what is the DZ degree?
"""

import random
from collections import Counter

random.seed(42)


def compute_dz_for_max_edge(n, sigma):
    """Find the edge with global max timestamp. Use its endpoints as (h,v).
    Compute DZ degree of v for hub h."""
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
    ts = {e: t for e, t in zip(edges, sigma)}

    # Find global max edge
    max_edge = max(ts, key=ts.get)
    max_ts = ts[max_edge]
    h, v = max_edge  # h = hub, v = secondary hub

    # S = σ({h,v}) = max_ts
    S = max_ts

    # DZ degree of v for hub h:
    # For each w ≠ h,v: DZ iff σ({h,w}) < σ({v,w}) < S = max_ts
    # Since S is the global max, σ({v,w}) < S always. So DZ iff σ({h,w}) < σ({v,w}).
    non_hub = [w for w in range(n) if w != h]
    dz = 0
    for w in non_hub:
        if w == v:
            continue
        a = ts[(min(h, w), max(h, w))]  # σ({h,w})
        c = ts[(min(v, w), max(v, w))]  # σ({v,w})
        if a < c:  # DZ condition when S is max
            dz += 1

    return dz, h, v


def compute_dz_for_min_edge(n, sigma):
    """Use the edge with global min timestamp."""
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
    ts = {e: t for e, t in zip(edges, sigma)}

    min_edge = min(ts, key=ts.get)
    min_ts = ts[min_edge]
    h, v = min_edge

    # S = σ({h,v}) = min_ts = 1
    # DZ iff σ({v,w}) is between S and σ({h,w})
    # Since S = min, S < a for all a. DZ iff S < c < a, i.e., c < a.
    # LIVE iff c < S (impossible since S is min) or c > a.
    # So DZ iff σ({v,w}) < σ({h,w}). LIVE iff σ({v,w}) > σ({h,w}).
    non_hub = [w for w in range(n) if w != h]
    dz = 0
    for w in non_hub:
        if w == v:
            continue
        a = ts[(min(h, w), max(h, w))]
        c = ts[(min(v, w), max(v, w))]
        if c < a:  # DZ when S is min
            dz += 1

    return dz, h, v


def compute_all_dz(n, sigma):
    """Compute DZ degree for ALL (h,v) pairs. Return min."""
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
    ts = {e: t for e, t in zip(edges, sigma)}

    min_dz = n
    best_pair = None
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
            if dz < min_dz:
                min_dz = dz
                best_pair = (h, v)

    return min_dz, best_pair


def main():
    print("Median Floor Conjecture: direct construction via extreme edges")
    print("=" * 70)

    for n in [6, 8, 10, 12, 15, 20]:
        m = n * (n - 1) // 2
        samples = 5000 if n <= 10 else 1000

        max_edge_dz = []
        min_edge_dz = []
        true_min_dz = [] if n <= 12 else None

        for trial in range(samples):
            perm = list(range(1, m + 1))
            random.shuffle(perm)

            dz_max, _, _ = compute_dz_for_max_edge(n, perm)
            dz_min, _, _ = compute_dz_for_min_edge(n, perm)
            max_edge_dz.append(dz_max)
            min_edge_dz.append(dz_min)

            if true_min_dz is not None:
                tdz, _ = compute_all_dz(n, perm)
                true_min_dz.append(tdz)

        # The DZ from max-edge and min-edge are COMPLEMENTARY:
        # For max edge: DZ = #{w : σ({h,w}) < σ({v,w})}
        # For min edge: DZ = #{w : σ({v,w}) < σ({h,w})}
        # These sum to n-2 for the SAME pair. But max/min edge give
        # DIFFERENT pairs, so no direct complement.

        # Best of max and min:
        best_dz = [min(a, b) for a, b in zip(max_edge_dz, min_edge_dz)]

        budget = n - 2
        print(f"\nK_{n} (n-2={budget}, n-3={n-3}):")
        print(f"  Max-edge DZ: mean={sum(max_edge_dz)/len(max_edge_dz):.1f}, "
              f"min={min(max_edge_dz)}, max={max(max_edge_dz)}")
        print(f"  Min-edge DZ: mean={sum(min_edge_dz)/len(min_edge_dz):.1f}, "
              f"min={min(min_edge_dz)}, max={max(min_edge_dz)}")
        print(f"  Best of two: mean={sum(best_dz)/len(best_dz):.1f}, "
              f"min={min(best_dz)}, max={max(best_dz)}")

        if true_min_dz:
            print(f"  True min DZ: mean={sum(true_min_dz)/len(true_min_dz):.1f}, "
                  f"min={min(true_min_dz)}, max={max(true_min_dz)}")

        # Distribution of max-edge DZ
        dist = Counter(max_edge_dz)
        print(f"  Max-edge DZ distribution:")
        for k in sorted(dist):
            print(f"    {k:3d}: {dist[k]:5d} ({100*dist[k]/samples:.1f}%)")

    # Part 2: what determines the max-edge DZ degree?
    # DZ = #{w : σ({h,w}) < σ({v,w})} where {h,v} has the max timestamp.
    # This is the number of "wins" of v over h in pairwise edge comparisons.
    # If h "dominates" v (h has larger edge to most vertices), DZ is small.
    print(f"\n\n{'='*70}")
    print("Analysis: what makes max-edge DZ small?")
    print("=" * 70)

    n = 10
    m = n * (n - 1) // 2
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]

    for trial in range(5):
        perm = list(range(1, m + 1))
        random.shuffle(perm)
        ts = {e: t for e, t in zip(edges, perm)}

        dz, h, v = compute_dz_for_max_edge(n, perm)
        S = ts[(min(h, v), max(h, v))]

        print(f"\n  Trial {trial}: max edge ({h},{v}), τ={S}, DZ={dz}")

        # Show the comparison for each w
        for w in range(n):
            if w == h or w == v:
                continue
            a = ts[(min(h, w), max(h, w))]
            c = ts[(min(v, w), max(v, w))]
            status = "DZ" if a < c else "LIVE"
            print(f"    w={w}: σ(h,w)={a:3d}, σ(v,w)={c:3d} → {status}")


if __name__ == '__main__':
    main()
