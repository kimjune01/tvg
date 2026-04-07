"""
Extract the exact constraint structure of minimum temporal spanner.

For each uncovered pair (i→i'), the constraint is:
  ∨_j [edges (i,j) AND (i',j) present] where M[i][j] < M[i'][j]

Some of these edges are forced (in M⁻ ∪ M⁺), simplifying the constraint.
If both forced: pair auto-covered. If one forced: constraint is a simple
disjunction over the non-forced edge. If neither forced: constraint is
OR of (x_{i,j} ∧ x_{i',j}) — a 2-CNF clause.

Classify: what fraction of constraints are each type? Does the structure
map to vertex cover, 2-SAT, or something else?
"""

import itertools
import numpy as np
from x3c_reduction import temporal_reachable


def extract_constraints(M):
    """Extract the exact 2-hop constraint structure."""
    k = M.shape[0]

    # Compute forced edges
    m_minus = set()
    m_plus = set()
    for j in range(k):
        min_i = int(np.argmin(M[:, j]))
        m_minus.add((min_i, j))
    for i in range(k):
        max_j = int(np.argmax(M[i, :]))
        m_plus.add((i, max_j))
    forced = m_minus | m_plus

    # For each A→A pair, find 2-hop witnesses
    # Pair (i→i'): column j works if M[i][j] < M[i'][j]
    constraints = []  # list of (pair, witnesses)
    # witness types: 'auto' (both forced), 'single' (one forced edge needed),
    #                'double' (both non-forced)

    for i in range(k):
        for i2 in range(k):
            if i == i2:
                continue

            # Check if already reachable via forced edges (might have longer paths)
            if temporal_reachable(M, forced, 'A', i, 'A', i2):
                continue

            witnesses = []
            for j in range(k):
                if M[i][j] < M[i2][j]:  # valid 2-hop direction
                    e1 = (i, j)
                    e2 = (i2, j)
                    e1_forced = e1 in forced
                    e2_forced = e2 in forced

                    if e1_forced and e2_forced:
                        witnesses.append(('auto', j, None))
                    elif e1_forced:
                        witnesses.append(('single', j, e2))
                    elif e2_forced:
                        witnesses.append(('single', j, e1))
                    else:
                        witnesses.append(('double', j, (e1, e2)))

            # If any witness is 'auto', pair is covered by forced alone
            # (but we already checked reachability above, so auto shouldn't appear
            #  ... unless 2-hop works but we missed it because we check full reachability)
            auto = [w for w in witnesses if w[0] == 'auto']
            if auto:
                continue  # shouldn't happen since we checked reachability

            constraints.append(('A', i, i2, witnesses))

    # B→B pairs: row i works if M[i][j] < M[i][j2]
    for j in range(k):
        for j2 in range(k):
            if j == j2:
                continue

            if temporal_reachable(M, forced, 'B', j, 'B', j2):
                continue

            witnesses = []
            for i in range(k):
                if M[i][j] < M[i][j2]:  # valid 2-hop: b_j → a_i → b_{j2}
                    e1 = (i, j)
                    e2 = (i, j2)
                    e1_forced = e1 in forced
                    e2_forced = e2 in forced

                    if e1_forced and e2_forced:
                        witnesses.append(('auto', i, None))
                    elif e1_forced:
                        witnesses.append(('single', i, e2))
                    elif e2_forced:
                        witnesses.append(('single', i, e1))
                    else:
                        witnesses.append(('double', i, (e1, e2)))

            auto = [w for w in witnesses if w[0] == 'auto']
            if auto:
                continue

            constraints.append(('B', j, j2, witnesses))

    # A→B and B→A pairs: direct 1-hop
    for i in range(k):
        for j in range(k):
            # A→B: edge (i,j) directly
            if not temporal_reachable(M, forced, 'A', i, 'B', j):
                e = (i, j)
                if e in forced:
                    pass  # shouldn't happen
                else:
                    constraints.append(('AB', i, j, [('single', None, e)]))

            # B→A: need some path b_j → a_i
            if not temporal_reachable(M, forced, 'B', j, 'A', i):
                # 2-hop: b_j → a_{i'} → b_{j'} → a_i (complex)
                # or: direct if there's an edge with right timing
                # For simplicity, just note it's uncovered
                witnesses = []
                # 2-hop through another B vertex: b_j → a_{i'} → b_{j'} then...
                # This gets complex. Just flag it.
                constraints.append(('BA', j, i, witnesses))

    return forced, constraints


def classify_constraints(constraints):
    """Classify constraint types."""
    stats = {
        'pure_single': 0,      # all witnesses are 'single' (= disjunction)
        'has_double': 0,        # at least one 'double' witness (= OR of ANDs)
        'only_double': 0,       # all witnesses are 'double' (hardest)
        'no_witness': 0,        # no 2-hop witnesses (needs longer journey)
        'total': len(constraints),
    }

    single_edge_vars = set()  # edges that appear in single-type witnesses
    double_edge_vars = set()  # edges that appear in double-type witnesses

    for pair_type, idx1, idx2, witnesses in constraints:
        if not witnesses:
            stats['no_witness'] += 1
            continue

        types = set(w[0] for w in witnesses)

        if types == {'single'}:
            stats['pure_single'] += 1
            for _, _, e in witnesses:
                single_edge_vars.add(e)
        elif 'double' in types:
            if types == {'double'}:
                stats['only_double'] += 1
            else:
                stats['has_double'] += 1
            for w in witnesses:
                if w[0] == 'single':
                    single_edge_vars.add(w[2])
                elif w[0] == 'double':
                    double_edge_vars.add(w[2][0])
                    double_edge_vars.add(w[2][1])

    return stats, single_edge_vars, double_edge_vars


def analyze_instances(k, n_instances):
    """Analyze constraint structure across instances."""
    print(f"\n{'='*60}")
    print(f"CONSTRAINT STRUCTURE: k={k}")
    print(f"{'='*60}")

    all_stats = []
    for seed in range(n_instances):
        rng = np.random.default_rng(seed)
        vals = rng.permutation(k * k)
        M = vals.reshape(k, k)

        forced, constraints = extract_constraints(M)
        stats, single_vars, double_vars = classify_constraints(constraints)
        all_stats.append(stats)

        if seed < 5:
            print(f"\n  seed={seed}: {len(forced)} forced, {stats['total']} constraints")
            print(f"    pure_single (disjunction): {stats['pure_single']}")
            print(f"    has_double (OR of ANDs):    {stats['has_double']}")
            print(f"    only_double (hard):         {stats['only_double']}")
            print(f"    no_witness (needs >2 hop):  {stats['no_witness']}")
            print(f"    single vars: {len(single_vars)}, double vars: {len(double_vars)}")

    # Aggregate
    print(f"\n--- Aggregate (k={k}, {n_instances} instances) ---")
    for key in ['total', 'pure_single', 'has_double', 'only_double', 'no_witness']:
        vals = [s[key] for s in all_stats]
        print(f"  {key}: mean={np.mean(vals):.1f}, min={min(vals)}, max={max(vals)}")

    # What fraction of constraints are "hard" (only_double)?
    hard_fracs = [s['only_double'] / s['total'] if s['total'] > 0 else 0
                  for s in all_stats]
    print(f"  fraction only_double: mean={np.mean(hard_fracs):.3f}")

    # What fraction need >2 hops?
    long_fracs = [s['no_witness'] / s['total'] if s['total'] > 0 else 0
                  for s in all_stats]
    print(f"  fraction no_witness: mean={np.mean(long_fracs):.3f}")


def check_2sat_reducibility(k, seed):
    """Check if the constraint structure for one instance is 2-SAT-like.

    A constraint is 2-SAT-like if each pair constraint can be expressed
    as implications between at most 2 boolean variables.

    'single' constraints: x_e (one variable) — trivially 2-SAT.
    'double' constraints: x_{e1} ∧ x_{e2} — this is NOT a clause,
    it's a conjunction. OR of conjunctions is not 2-SAT.

    But if every 'double' constraint shares a variable with another,
    we might get polynomial structure through variable elimination.
    """
    rng = np.random.default_rng(seed)
    vals = rng.permutation(k * k)
    M = vals.reshape(k, k)

    forced, constraints = extract_constraints(M)

    print(f"\n  Detailed constraint analysis (k={k}, seed={seed}):")

    # Build variable occurrence map
    var_to_constraints = {}
    for ci, (pair_type, idx1, idx2, witnesses) in enumerate(constraints):
        for w in witnesses:
            if w[0] == 'single':
                e = w[2]
                var_to_constraints.setdefault(e, []).append(ci)
            elif w[0] == 'double':
                e1, e2 = w[2]
                var_to_constraints.setdefault(e1, []).append(ci)
                var_to_constraints.setdefault(e2, []).append(ci)

    print(f"  Variables (non-forced edges): {len(var_to_constraints)}")
    print(f"  Constraints: {len(constraints)}")

    # Variable degree distribution
    degrees = [len(cs) for cs in var_to_constraints.values()]
    if degrees:
        print(f"  Variable degree: min={min(degrees)}, max={max(degrees)}, "
              f"mean={np.mean(degrees):.1f}")

    # Check: how many variables appear in ONLY 'double' constraints
    # vs mixed or only 'single'?
    double_only_vars = 0
    mixed_vars = 0
    single_only_vars = 0

    for var, cis in var_to_constraints.items():
        in_single = False
        in_double = False
        for ci in cis:
            _, _, _, witnesses = constraints[ci]
            for w in witnesses:
                if w[0] == 'single' and w[2] == var:
                    in_single = True
                elif w[0] == 'double' and var in w[2]:
                    in_double = True
        if in_single and in_double:
            mixed_vars += 1
        elif in_single:
            single_only_vars += 1
        elif in_double:
            double_only_vars += 1

    print(f"  Vars in single only: {single_only_vars}")
    print(f"  Vars in double only: {double_only_vars}")
    print(f"  Vars in both: {mixed_vars}")


if __name__ == "__main__":
    analyze_instances(3, 200)
    analyze_instances(4, 100)
    analyze_instances(5, 50)

    print(f"\n{'='*60}")
    print("DETAILED VARIABLE ANALYSIS")
    print(f"{'='*60}")
    check_2sat_reducibility(4, 0)
    check_2sat_reducibility(4, 3)
    check_2sat_reducibility(5, 0)
