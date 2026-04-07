"""Measure triple synergies at k=5 (removed the size-12 cap)."""

import itertools
import numpy as np
from x3c_reduction import covering_hypergraph, temporal_reachable


def compute_coverage(M, forced, edges):
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


k = 5
for seed in range(10):
    rng = np.random.default_rng(seed)
    vals = rng.permutation(k * k)
    M = vals.reshape(k, k)

    forced, uncovered, rescue_map = covering_hypergraph(M)
    if not uncovered or not rescue_map:
        continue

    rescue_edges = list(rescue_map.keys())
    base_coverage = compute_coverage(M, forced, [])

    single_cov = {}
    for e in rescue_edges:
        single_cov[e] = compute_coverage(M, forced, [e]) - base_coverage

    pair_cov = {}
    pw_syn = 0
    pw_total = 0
    for e1, e2 in itertools.combinations(rescue_edges, 2):
        pair = frozenset([e1, e2])
        cov = compute_coverage(M, forced, [e1, e2]) - base_coverage
        pair_cov[pair] = cov
        synergy = cov - (single_cov[e1] | single_cov[e2])
        if synergy:
            pw_syn += 1
            pw_total += len(synergy)

    tr_syn = 0
    tr_total = 0
    for e1, e2, e3 in itertools.combinations(rescue_edges, 3):
        cov = compute_coverage(M, forced, [e1, e2, e3]) - base_coverage
        union_pairs = set()
        for pair in itertools.combinations([e1, e2, e3], 2):
            union_pairs |= pair_cov[frozenset(pair)]
        synergy = cov - union_pairs
        if synergy:
            tr_syn += 1
            tr_total += len(synergy)

    n_pairs = len(list(itertools.combinations(rescue_edges, 2)))
    n_triples = len(list(itertools.combinations(rescue_edges, 3)))

    print(f"seed={seed}: {len(rescue_edges)} edges, {len(uncovered)} uncovered")
    print(f"  Pairwise: {pw_syn}/{n_pairs} synergies, {pw_total} coverings")
    print(f"  Triple:   {tr_syn}/{n_triples} synergies, {tr_total} coverings")
    ratio = tr_total / pw_total if pw_total > 0 else 0
    print(f"  Triple/pairwise ratio: {ratio:.3f}")
    print()
