"""
Check LIVE floor at n=18,20,25: does max LIVE stay at n-3?
"""

import random

random.seed(42)


def max_live_best_pair(n, perm):
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
    ts = {e: t for e, t in zip(edges, perm)}
    best = 0
    for h in range(n):
        for v in range(n):
            if v == h:
                continue
            S = ts[(min(h, v), max(h, v))]
            live = 0
            for w in range(n):
                if w == h or w == v:
                    continue
                a = ts[(min(h, w), max(h, w))]
                c = ts[(min(v, w), max(v, w))]
                vals = sorted([S, a, c])
                if c != vals[1]:
                    live += 1
            best = max(best, live)
    return best


def main():
    for n in [15, 18, 20]:
        m = n * (n - 1) // 2

        # Random sampling: find min max_LIVE
        samples = 200 if n <= 18 else 100
        min_ml = n
        for trial in range(samples):
            perm = list(range(1, m + 1))
            random.shuffle(perm)
            ml = max_live_best_pair(n, perm)
            min_ml = min(min_ml, ml)

        # Adversarial hill-climbing
        perm = list(range(1, m + 1))
        random.shuffle(perm)
        best_score = max_live_best_pair(n, perm)
        steps = 3000 if n <= 18 else 1000
        for step in range(steps):
            i, j = random.sample(range(m), 2)
            c = list(perm)
            c[i], c[j] = c[j], c[i]
            s = max_live_best_pair(n, c)
            if s <= best_score:
                perm = c
                if s < best_score:
                    best_score = s

        print(f"K_{n}: random min max_LIVE={min_ml} ({samples} samples), "
              f"adversarial={best_score}, n-3={n-3}, n-2={n-2}")


if __name__ == '__main__':
    main()
