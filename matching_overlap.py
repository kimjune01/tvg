"""
Check: do M⁻ and M⁺ always share at least one edge?

M⁻(j) = argmin_i M[i][j]  (earliest row per column)
M⁺(i) = argmax_j M[i][j]  (latest column per row)

M⁻ edge: (m_minus(j), j)
M⁺ edge: (i, m_plus(i))

Shared edge: m_minus(j₀) = i₀ AND m_plus(i₀) = j₀
"""

import random


def generate_extremal_biclique(k, seed=None):
    if seed is not None:
        random.seed(seed)
    vals = list(range(1, k * k + 1))
    random.shuffle(vals)
    M = [[0] * k for _ in range(k)]
    idx = 0
    for i in range(k):
        for j in range(k):
            M[i][j] = vals[idx]
            idx += 1
    return M


def compute_matchings(M, k):
    # M⁻(j) = argmin_i M[i][j]
    m_minus = [min(range(k), key=lambda i: M[i][j]) for j in range(k)]
    # M⁺(i) = argmax_j M[i][j]
    m_plus = [max(range(k), key=lambda j: M[i][j]) for i in range(k)]
    return m_minus, m_plus


def matching_overlap(m_minus, m_plus, k):
    # M⁻ edges: {(m_minus[j], j) for j in range(k)}
    # M⁺ edges: {(i, m_plus[i]) for i in range(k)}
    minus_edges = {(m_minus[j], j) for j in range(k)}
    plus_edges = {(i, m_plus[i]) for i in range(k)}
    return minus_edges & plus_edges


def main():
    random.seed(42)

    print("M⁻ ∩ M⁺ OVERLAP CHECK")
    print("=" * 60)

    for k in range(3, 10):
        samples = {3: 10000, 4: 5000, 5: 2000, 6: 1000,
                   7: 500, 8: 200, 9: 100}[k]
        overlaps = []
        zero_overlap = 0

        for s in range(samples):
            M = generate_extremal_biclique(k, seed=42 + s)
            m_minus, m_plus = compute_matchings(M, k)
            shared = matching_overlap(m_minus, m_plus, k)
            overlaps.append(len(shared))
            if len(shared) == 0:
                zero_overlap += 1

        avg = sum(overlaps) / len(overlaps)
        min_o = min(overlaps)
        max_o = max(overlaps)

        print(f"k={k} ({samples} samples):")
        print(f"  |M⁻ ∩ M⁺|: min={min_o}, avg={avg:.2f}, max={max_o}")
        print(f"  Zero overlap: {zero_overlap}/{samples} "
              f"({100*zero_overlap/samples:.1f}%)")

        from collections import Counter
        dist = Counter(overlaps)
        print(f"  Distribution: {dict(sorted(dist.items()))}")
        print()


if __name__ == "__main__":
    main()
