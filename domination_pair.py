"""
Find (h,v) where h dominates v: σ({h,w}) > σ({v,w}) for most w.

If S = σ({h,v}) = max timestamp: DZ = #{w : σ({h,w}) < σ({v,w})}.
Domination means DZ is small.

But we don't need the max-edge pair. We just need SOME (h,v) where
DZ is small. The domination ordering of vertices (by total edge
timestamp sum) might identify the best pair.

Also: try picking S to be the MEDIAN of v's edges. This minimizes
the dead zone widths.
"""

import random

random.seed(42)


def compute_dz(n, ts, h, v):
    S = ts[(min(h, v), max(h, v))]
    dz = 0
    for w in range(n):
        if w == h or w == v:
            continue
        a = ts[(min(h, w), max(h, w))]
        c = ts[(min(v, w), max(v, w))]
        if min(S, a) < c < max(S, a):
            dz += 1
    return dz


def main():
    print("Domination-based pair selection")
    print("=" * 70)

    for n in [8, 10, 12, 15, 20]:
        m = n * (n - 1) // 2
        edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
        samples = 2000 if n <= 12 else 500

        # Strategy 1: max/min edge (complementarity)
        s1_dz = []
        # Strategy 2: vertex with max edge-sum vs min edge-sum
        s2_dz = []
        # Strategy 3: min DZ over all pairs (oracle)
        s3_dz = []
        # Strategy 4: for each pair, pick orientation with smaller DZ
        s4_dz = []
        # Strategy 5: vertex with max edge-sum as h, try all v
        s5_dz = []

        for trial in range(samples):
            perm = list(range(1, m + 1))
            random.shuffle(perm)
            ts = {e: t for e, t in zip(edges, perm)}

            # Edge sums per vertex
            edge_sums = {}
            for v in range(n):
                edge_sums[v] = sum(ts[(min(v, w), max(v, w))]
                                   for w in range(n) if w != v)
            sorted_verts = sorted(range(n), key=lambda v: edge_sums[v])
            v_min_sum = sorted_verts[0]
            v_max_sum = sorted_verts[-1]

            # Strategy 1: max edge pair
            max_edge = max(ts, key=ts.get)
            h1, v1 = max_edge
            dz_hv = compute_dz(n, ts, h1, v1)
            dz_vh = compute_dz(n, ts, v1, h1)
            s1_dz.append(min(dz_hv, dz_vh))

            # Strategy 2: max-sum hub, min-sum vertex
            dz2 = compute_dz(n, ts, v_max_sum, v_min_sum)
            dz2r = compute_dz(n, ts, v_min_sum, v_max_sum)
            s2_dz.append(min(dz2, dz2r))

            # Strategy 3: true minimum (oracle) — expensive
            if n <= 12:
                min_dz = n
                for h in range(n):
                    for v in range(n):
                        if v == h:
                            continue
                        dz = compute_dz(n, ts, h, v)
                        min_dz = min(min_dz, dz)
                s3_dz.append(min_dz)

            # Strategy 4: for all pairs, best orientation
            best_s4 = n
            for h in range(n):
                for v in range(h + 1, n):
                    dz1 = compute_dz(n, ts, h, v)
                    dz2 = compute_dz(n, ts, v, h)
                    best_s4 = min(best_s4, dz1, dz2)
            s4_dz.append(best_s4)

            # Strategy 5: max-sum hub, try all v
            h5 = v_max_sum
            best_dz5 = n
            for v in range(n):
                if v == h5:
                    continue
                dz = compute_dz(n, ts, h5, v)
                best_dz5 = min(best_dz5, dz)
            s5_dz.append(best_dz5)

        print(f"\nK_{n} (budget={n-2}):")
        print(f"  S1 (max-edge, best orient): "
              f"mean={sum(s1_dz)/len(s1_dz):.1f}, "
              f"max={max(s1_dz)}")
        print(f"  S2 (max-sum h, min-sum v): "
              f"mean={sum(s2_dz)/len(s2_dz):.1f}, "
              f"max={max(s2_dz)}")
        if s3_dz:
            print(f"  S3 (oracle min DZ): "
                  f"mean={sum(s3_dz)/len(s3_dz):.1f}, "
                  f"max={max(s3_dz)}")
        print(f"  S4 (all pairs, best orient): "
              f"mean={sum(s4_dz)/len(s4_dz):.1f}, "
              f"max={max(s4_dz)}")
        print(f"  S5 (max-sum hub, best v): "
              f"mean={sum(s5_dz)/len(s5_dz):.1f}, "
              f"max={max(s5_dz)}")


if __name__ == '__main__':
    main()
