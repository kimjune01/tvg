"""
Is max LIVE degree ≥ n-3 a theorem?

For each triangle {h,v,w}, edge {v,w} is LIVE for hub h iff
σ({v,w}) is NOT the median of (σ({h,v}), σ({h,w}), σ({v,w})).

P(LIVE) = 2/3 by the three-timestamp symmetry (approximately).

For vertex v with hub h: DZ degree = #{w : σ({v,w}) is median of triple}.
Expected DZ degree ≈ (n-2)/3. We want min DZ degree ≤ 1 (max LIVE ≥ n-3).

Test adversarially for larger n.
"""

import random

random.seed(42)


def max_live_best_hub(n, perm):
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
    ts = {e: t for e, t in zip(edges, perm)}

    best = 0
    for hub in range(n):
        non_hub = [v for v in range(n) if v != hub]
        for v in non_hub:
            live = 0
            sv = ts[(min(hub, v), max(hub, v))]
            for w in non_hub:
                if w == v:
                    continue
                sw = ts[(min(hub, w), max(hub, w))]
                cvw = ts[(min(v, w), max(v, w))]
                # LIVE iff cvw is NOT median of (sv, sw, cvw)
                vals = sorted([sv, sw, cvw])
                if cvw != vals[1]:  # not the median
                    live += 1
            best = max(best, live)
    return best


def main():
    print("Is max LIVE degree ≥ n-3 always?")
    print("=" * 60)

    for n in [6, 8, 10, 12, 15]:
        m = n * (n - 1) // 2

        # Adversarial hill-climb to minimize max LIVE degree
        perm = list(range(1, m + 1))
        random.shuffle(perm)
        best_score = max_live_best_hub(n, perm)

        steps = 20000 if n <= 10 else 5000
        for step in range(steps):
            i, j = random.sample(range(m), 2)
            candidate = list(perm)
            candidate[i], candidate[j] = candidate[j], candidate[i]
            score = max_live_best_hub(n, candidate)
            if score <= best_score:
                perm = candidate
                if score < best_score:
                    best_score = score

        floor = n - 3
        status = "✓" if best_score >= floor else "✗"
        print(f"  K_{n}: adversarial min max_LIVE = {best_score}, "
              f"n-3 = {floor}, n-2 = {n-2} {status}")

    # Also: theoretical check — does the three-timestamp argument
    # guarantee a vertex with ≤ 1 DZ edge?
    print(f"\n\nTheoretical check: triangle median counting")
    print("=" * 60)

    for n in [6, 8, 10, 12]:
        m = n * (n - 1) // 2

        # For each σ, for each (h,v) pair, count DZ degree of v
        min_dz_found = n
        samples = 5000

        for trial in range(samples):
            perm = list(range(1, m + 1))
            random.shuffle(perm)
            edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
            ts = {e: t for e, t in zip(edges, perm)}

            for hub in range(n):
                non_hub = [v for v in range(n) if v != hub]
                for v in non_hub:
                    dz = 0
                    sv = ts[(min(hub, v), max(hub, v))]
                    for w in non_hub:
                        if w == v:
                            continue
                        sw = ts[(min(hub, w), max(hub, w))]
                        cvw = ts[(min(v, w), max(v, w))]
                        vals = sorted([sv, sw, cvw])
                        if cvw == vals[1]:
                            dz += 1
                    min_dz_found = min(min_dz_found, dz)

            if min_dz_found == 0:
                break

        print(f"  K_{n}: minimum DZ degree found = {min_dz_found} "
              f"({samples} random σ)")
        if min_dz_found <= 1:
            print(f"    → max LIVE ≥ {n-2-min_dz_found} = n-{2+min_dz_found}")


if __name__ == '__main__':
    main()
