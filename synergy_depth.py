"""
Measure interaction depth between rescue edges.

Pairwise synergy: edges e1, e2 together cover pairs that neither covers alone.
Triple synergy: edges e1, e2, e3 together cover pairs that no PAIR covers.

If triple synergy = 0, the problem has pairwise-only interactions (2-SAT-like).
If triple synergy > 0, there are higher-order interactions (potentially NP-hard).
"""

import itertools
import numpy as np
from x3c_reduction import covering_hypergraph, temporal_reachable


def compute_coverage(M, forced, edges):
    """Compute which pairs are covered by forced ∪ edges."""
    k = M.shape[0]
    all_edges = forced | set(edges)
    covered = set()
    for s_side in ['A', 'B']:
        for s in range(k):
            for d_side in ['A', 'B']:
                for d in range(k):
                    if s_side == d_side and s == d:
                        continue
                    if temporal_reachable(M, all_edges, s_side, s, d_side, d):
                        covered.add((s_side, s, d_side, d))
    return covered


def measure_synergies(k, n_instances):
    """Measure pairwise and triple synergies across instances."""
    print(f"\n{'='*60}")
    print(f"SYNERGY DEPTH: k={k}, {n_instances} instances")
    print(f"{'='*60}")

    all_pairwise = []
    all_triple = []
    all_quad = []

    for seed in range(n_instances):
        rng = np.random.default_rng(seed)
        vals = rng.permutation(k * k)
        M = vals.reshape(k, k)

        forced, uncovered, rescue_map = covering_hypergraph(M)

        if not uncovered or not rescue_map:
            continue

        rescue_edges = list(rescue_map.keys())
        uncovered_set = set(uncovered)

        # Coverage of forced edges alone
        base_coverage = compute_coverage(M, forced, [])

        # Single-edge coverage (already in rescue_map, but recompute for consistency)
        single_cov = {}
        for e in rescue_edges:
            single_cov[e] = compute_coverage(M, forced, [e]) - base_coverage

        # Pairwise coverage and synergy
        pairwise_synergy_count = 0
        pairwise_synergy_total = 0
        pair_cov = {}

        for e1, e2 in itertools.combinations(rescue_edges, 2):
            pair = frozenset([e1, e2])
            cov = compute_coverage(M, forced, [e1, e2]) - base_coverage
            pair_cov[pair] = cov

            # Synergy = pairs covered by {e1,e2} but not by e1 alone or e2 alone
            synergy = cov - single_cov[e1] - single_cov[e2]
            # Wait, set subtraction doesn't work like that for unions
            # Synergy = cov - (single_cov[e1] | single_cov[e2])
            union_singles = single_cov[e1] | single_cov[e2]
            synergy = cov - union_singles

            if synergy:
                pairwise_synergy_count += 1
                pairwise_synergy_total += len(synergy)

        # Triple coverage and synergy
        triple_synergy_count = 0
        triple_synergy_total = 0

        if len(rescue_edges) <= 12:  # keep tractable
            for e1, e2, e3 in itertools.combinations(rescue_edges, 3):
                cov = compute_coverage(M, forced, [e1, e2, e3]) - base_coverage

                # Union of all pairwise coverages
                union_pairs = set()
                for pair in itertools.combinations([e1, e2, e3], 2):
                    union_pairs |= pair_cov[frozenset(pair)]

                # Triple synergy = covered by triple but not by any pair
                synergy = cov - union_pairs

                if synergy:
                    triple_synergy_count += 1
                    triple_synergy_total += len(synergy)

        n_pairs = len(list(itertools.combinations(rescue_edges, 2)))
        n_triples = len(list(itertools.combinations(rescue_edges, min(3, len(rescue_edges)))))

        all_pairwise.append((pairwise_synergy_count, n_pairs, pairwise_synergy_total))
        all_triple.append((triple_synergy_count, n_triples, triple_synergy_total))

        if seed < 5 or (pairwise_synergy_count > 0 and seed < 20):
            print(f"\n  seed={seed}: {len(rescue_edges)} rescue edges, "
                  f"{len(uncovered)} uncovered pairs")
            print(f"    Pairwise synergies: {pairwise_synergy_count}/{n_pairs} pairs, "
                  f"{pairwise_synergy_total} new pair-coverings")
            if len(rescue_edges) <= 12:
                print(f"    Triple synergies:   {triple_synergy_count}/{n_triples} triples, "
                      f"{triple_synergy_total} new triple-coverings")

    # Summary
    print(f"\n--- Summary (k={k}) ---")
    pw_rates = [c/n if n > 0 else 0 for c, n, _ in all_pairwise]
    tr_rates = [c/n if n > 0 else 0 for c, n, _ in all_triple]

    print(f"Pairwise synergy rate: {np.mean(pw_rates):.3f} "
          f"(min={min(pw_rates):.3f}, max={max(pw_rates):.3f})")
    if any(n > 0 for _, n, _ in all_triple):
        print(f"Triple synergy rate:   {np.mean(tr_rates):.3f} "
              f"(min={min(tr_rates):.3f}, max={max(tr_rates):.3f})")

    pw_total = sum(t for _, _, t in all_pairwise)
    tr_total = sum(t for _, _, t in all_triple)
    print(f"Total pairwise synergy coverings: {pw_total}")
    print(f"Total triple synergy coverings:   {tr_total}")

    if pw_total > 0:
        print(f"Triple/pairwise ratio: {tr_total/pw_total:.3f}")
    elif tr_total > 0:
        print(f"Triple synergy exists with zero pairwise!")


if __name__ == "__main__":
    measure_synergies(3, 100)
    measure_synergies(4, 50)
    measure_synergies(5, 20)
