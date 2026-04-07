"""
Cycle-breaking hardness via the twist permutation.

The twist permutation σ = m⁺ ∘ (m⁻)⁻¹ maps column indices to column indices.
- m⁻[j] = argmin_i M[i][j]  (row with min in column j)
- m⁺[i] = argmax_j M[i][j]  (col with max in row i)
- (m⁻)⁻¹[i] = j such that m⁻[j] = i  (column whose min is in row i)
  Since m⁻ is a permutation (all-distinct matrix), this is well-defined.
- σ(j) = m⁺(m⁻⁻¹(... wait, let me be precise.

Actually: m⁻ : [k] → [k] maps columns to rows (m⁻[j] = row).
         m⁺ : [k] → [k] maps rows to columns (m⁺[i] = col).
         (m⁻)⁻¹ : [k] → [k] maps rows to columns (inverse of m⁻).

σ = m⁺ ∘ (m⁻)⁻¹ would map rows → columns → columns? No:
  (m⁻)⁻¹ maps rows to columns. Then m⁺ maps rows to columns.
  That doesn't compose.

Let me re-derive. m⁻ maps col→row. (m⁻)⁻¹ maps row→col.
m⁺ maps row→col.

To get col→col: σ(j) = m⁺(m⁻(j)).
  m⁻(j) = row i with min in col j.
  m⁺(i) = col with max in row i.
  σ(j) = "the column that has the max of the row that has the min of column j"

This is a permutation on [k] (columns).

Alternatively the worklog says σ = m⁺ ∘ (m⁻)⁻¹. If we read:
  (m⁻)⁻¹ : col → row (inverse of m⁻ : col → row would be row → col)

Hmm, let me just use σ(j) = m⁺(m⁻(j)) which maps col→row→col.
This IS a permutation since m⁻ is a bijection col→row and m⁺ is a
bijection row→col (in an extremally matched biclique).

Investigation: cycle structure of σ and its relationship to hub validity.
"""

import random
from collections import defaultdict
import sys

random.seed(42)


# ─── Matrix generation ───

def generate_sm_matrix(k):
    """SM(k): circulant matrix. M[i][j] = position of (i,j) in diagonal sweep."""
    M = [[0] * k for _ in range(k)]
    t = 1
    for d in range(k):
        for i in range(k):
            j = (i + d) % k
            M[i][j] = t
            t += 1
    return M


def generate_random_biclique(k):
    """Generate random k×k all-distinct biclique via topological sort
    respecting M⁻/M⁺ matchings."""
    for attempt in range(1000):
        m_minus = list(range(k))
        random.shuffle(m_minus)
        m_plus = list(range(k))
        random.shuffle(m_plus)

        # Build DAG: m⁻ edges are column-mins, m⁺ edges are row-maxes
        edge_idx = {(i, j): i * k + j for i in range(k) for j in range(k)}
        adj = [[] for _ in range(k * k)]
        in_degree = [0] * (k * k)

        for j in range(k):
            src = edge_idx[(m_minus[j], j)]
            for i in range(k):
                if i != m_minus[j]:
                    adj[src].append(edge_idx[(i, j)])
                    in_degree[edge_idx[(i, j)]] += 1

        for i in range(k):
            dst = edge_idx[(i, m_plus[i])]
            for jj in range(k):
                if jj != m_plus[i]:
                    adj[edge_idx[(i, jj)]].append(dst)
                    in_degree[dst] += 1

        queue = [i for i in range(k * k) if in_degree[i] == 0]
        order = []
        while queue:
            random.shuffle(queue)
            node = queue.pop()
            order.append(node)
            for nb in adj[node]:
                in_degree[nb] -= 1
                if in_degree[nb] == 0:
                    queue.append(nb)

        if len(order) != k * k:
            continue

        M = [[0] * k for _ in range(k)]
        for rank, node in enumerate(order):
            i, j = node // k, node % k
            M[i][j] = rank + 1
        return M, m_minus, m_plus

    return None, None, None


# ─── Core computations ───

def get_matchings(M, k):
    """Compute m⁻ (column mins) and m⁺ (row maxes)."""
    m_minus = [0] * k
    m_plus = [0] * k
    for j in range(k):
        m_minus[j] = min(range(k), key=lambda i: M[i][j])
    for i in range(k):
        m_plus[i] = max(range(k), key=lambda j: M[i][j])
    return m_minus, m_plus


def twist_permutation(m_minus, m_plus, k):
    """σ(j) = m⁺(m⁻(j)): col → row → col."""
    sigma = [0] * k
    for j in range(k):
        row = m_minus[j]       # row with min in column j
        sigma[j] = m_plus[row]  # col with max in that row
    return sigma


def cycle_structure(sigma, k):
    """Return list of cycles. Each cycle is a list of elements."""
    visited = [False] * k
    cycles = []
    for start in range(k):
        if visited[start]:
            continue
        cycle = []
        j = start
        while not visited[j]:
            visited[j] = True
            cycle.append(j)
            j = sigma[j]
        cycles.append(cycle)
    return cycles


# ─── Temporal reachability ───

def compute_reachability_pairs(n, timed_edges):
    """All pairs reachable via temporal journeys (non-decreasing timestamps)."""
    reached_by = [dict() for _ in range(n)]
    for i in range(n):
        reached_by[i][i] = 0
    for t, u, v in sorted(timed_edges):
        for s, arr in list(reached_by[u].items()):
            if arr <= t and (s not in reached_by[v] or t < reached_by[v][s]):
                reached_by[v][s] = t
        for s, arr in list(reached_by[v].items()):
            if arr <= t and (s not in reached_by[u] or t < reached_by[u][s]):
                reached_by[u][s] = t
    pairs = set()
    for v in range(n):
        for s in reached_by[v]:
            if s != v:
                pairs.add((s, v))
    return pairs


def double_star_edges(M, k, h, c, m_minus, m_plus):
    """Build M⁻ ∪ M⁺ ∪ star(row h) ∪ star(col c)."""
    edges = set()
    for j in range(k):
        edges.add((m_minus[j], j))
    for i in range(k):
        edges.add((i, m_plus[i]))
    for j in range(k):
        edges.add((h, j))
    for i in range(k):
        edges.add((i, c))
    return edges


def check_spanner(k, M, spanner_edges):
    """Return number of missing pairs."""
    n = 2 * k
    full_timed = [(M[i][j], i, k + j) for i in range(k) for j in range(k)]
    full_pairs = compute_reachability_pairs(n, full_timed)
    span_timed = [(M[i][j], i, k + j) for i, j in spanner_edges]
    span_pairs = compute_reachability_pairs(n, span_timed)
    return len(full_pairs - span_pairs)


# ─── Hub validity relative to σ ───

def hub_in_which_cycles(h, sigma, cycles, m_minus_inv):
    """
    Given hub row h:
    - c = m⁺(h) is the hub column
    - The hub column c appears in some cycle of σ
    - The hub row h corresponds to column m⁻⁻¹(h) in σ's domain
    Return which cycle(s) the hub's column and the hub's "source column" belong to.
    """
    c_hub = None  # will be set by caller
    # m_minus_inv[h] = column j such that m_minus[j] = h
    source_col = m_minus_inv.get(h, None)
    return source_col


def analyze_hub_cycle_position(h, m_plus, m_minus, sigma, cycles, k):
    """Analyze where hub h sits relative to σ's cycle structure."""
    c = m_plus[h]  # hub column

    # Inverse of m_minus: row → column
    m_minus_inv = {}
    for j in range(k):
        m_minus_inv[m_minus[j]] = j

    source_col = m_minus_inv[h]  # column whose min-row is h

    # Which cycle contains c (the hub column)?
    col_to_cycle = {}
    for idx, cyc in enumerate(cycles):
        for elem in cyc:
            col_to_cycle[elem] = idx

    hub_col_cycle = col_to_cycle[c]
    source_col_cycle = col_to_cycle[source_col]

    # Is σ(source_col) = c? That would mean m⁺(m⁻(source_col)) = c
    # = m⁺(h) = c. Yes! σ(m⁻⁻¹(h)) = m⁺(h) = c.
    # So source_col → c is an edge in σ's functional graph.

    # Fixed point: σ(c) = c means m⁺(m⁻(c)) = c
    is_fixed = (sigma[c] == c)

    return {
        'hub_col': c,
        'source_col': source_col,
        'hub_col_cycle_idx': hub_col_cycle,
        'source_col_cycle_idx': source_col_cycle,
        'same_cycle': hub_col_cycle == source_col_cycle,
        'hub_col_cycle_len': len(cycles[hub_col_cycle]),
        'source_col_cycle_len': len(cycles[source_col_cycle]),
        'is_fixed_point': is_fixed,
        'sigma_of_source': sigma[source_col],  # should equal c
    }


# ─── FVS connection ───

def build_sigma_digraph(sigma, k):
    """Build directed graph from σ: edge j → σ(j) for all j."""
    adj = defaultdict(list)
    for j in range(k):
        adj[j].append(sigma[j])
    return adj


def is_feedback_vertex(sigma, k, removed_set):
    """Check if removing `removed_set` from σ's functional graph breaks all cycles."""
    remaining = [j for j in range(k) if j not in removed_set]
    visited = set()
    for start in remaining:
        if start in visited:
            continue
        path = set()
        j = start
        while j not in visited and j not in path and j not in removed_set:
            path.add(j)
            j = sigma[j]
        if j in path:
            # Found a cycle
            return False
        visited.update(path)
    return True


# ─── Main experiments ───

def experiment_1_cycle_structure_stats():
    """For various k, generate random bicliques and analyze σ's cycle structure."""
    print("=" * 70)
    print("EXPERIMENT 1: Cycle structure statistics of σ")
    print("=" * 70)

    ks = [3, 4, 5, 6, 7, 8, 10, 12, 15]
    n_samples = 1000

    print(f"\n{'k':>3} | {'avg_cycles':>10} | {'avg_max_cyc':>11} | {'avg_fixed':>9} | "
          f"{'frac_identity':>13} | {'frac_1cyc':>9}")
    print("-" * 75)

    all_data = {}

    for k in ks:
        cycle_counts = []
        max_cycle_lens = []
        fixed_point_counts = []
        identity_count = 0
        single_cycle_count = 0

        generated = 0
        attempts = 0
        while generated < n_samples and attempts < n_samples * 20:
            attempts += 1
            result = generate_random_biclique(k)
            if result[0] is None:
                continue
            M, m_minus, m_plus = result
            generated += 1

            sigma = twist_permutation(m_minus, m_plus, k)
            cycles = cycle_structure(sigma, k)

            n_cycles = len(cycles)
            max_len = max(len(c) for c in cycles)
            n_fixed = sum(1 for c in cycles if len(c) == 1)

            cycle_counts.append(n_cycles)
            max_cycle_lens.append(max_len)
            fixed_point_counts.append(n_fixed)

            if n_cycles == k:  # identity permutation
                identity_count += 1
            if n_cycles == 1:  # single k-cycle
                single_cycle_count += 1

        if generated == 0:
            print(f"{k:>3} | {'FAIL':>10}")
            continue

        avg_c = sum(cycle_counts) / generated
        avg_m = sum(max_cycle_lens) / generated
        avg_f = sum(fixed_point_counts) / generated

        all_data[k] = {
            'cycle_counts': cycle_counts,
            'max_cycle_lens': max_cycle_lens,
            'fixed_point_counts': fixed_point_counts,
            'generated': generated,
        }

        print(f"{k:>3} | {avg_c:>10.2f} | {avg_m:>11.2f} | {avg_f:>9.2f} | "
              f"{identity_count/generated:>13.3f} | {single_cycle_count/generated:>9.3f}")

    return all_data


def experiment_2_hub_validity_vs_cycles():
    """For each instance, check which hubs are valid and correlate with σ structure."""
    print("\n" + "=" * 70)
    print("EXPERIMENT 2: Hub validity vs cycle structure")
    print("=" * 70)

    # Smaller k values due to reachability computation cost
    ks = [3, 4, 5, 6, 7]
    n_samples = 200  # fewer samples since reachability is expensive

    for k in ks:
        print(f"\n--- k = {k} ---")

        # Track correlations
        results_by_ncycles = defaultdict(lambda: {'total_hubs': 0, 'valid_hubs': 0, 'instances': 0})
        results_by_maxcyc = defaultdict(lambda: {'total_hubs': 0, 'valid_hubs': 0, 'instances': 0})

        # Per-hub properties
        valid_in_longest = 0
        valid_not_in_longest = 0
        valid_is_fixed = 0
        valid_not_fixed = 0
        total_valid = 0
        total_hubs_checked = 0

        # Cycle position tracking
        valid_hub_cycle_len_sum = 0
        invalid_hub_cycle_len_sum = 0
        valid_count = 0
        invalid_count = 0

        # Per-instance: do all valid hubs come from same cycle?
        all_from_one_cycle = 0
        instances_with_valid = 0

        generated = 0
        attempts = 0
        while generated < n_samples and attempts < n_samples * 20:
            attempts += 1
            result = generate_random_biclique(k)
            if result[0] is None:
                continue
            M, m_minus, m_plus = result
            generated += 1

            sigma = twist_permutation(m_minus, m_plus, k)
            cycles = cycle_structure(sigma, k)
            n_cycles = len(cycles)
            max_cyc_len = max(len(c) for c in cycles)

            # Build col → cycle mapping
            col_to_cycle_idx = {}
            for idx, cyc in enumerate(cycles):
                for elem in cyc:
                    col_to_cycle_idx[elem] = idx

            # Find the longest cycle (first one if tie)
            longest_cycle_idx = max(range(len(cycles)), key=lambda i: len(cycles[i]))
            longest_cycle_set = set(cycles[longest_cycle_idx])

            # m⁻ inverse
            m_minus_inv = {}
            for j in range(k):
                m_minus_inv[m_minus[j]] = j

            valid_hub_indices = []
            valid_hub_cycle_indices = set()

            for h in range(k):
                c = m_plus[h]
                edges = double_star_edges(M, k, h, c, m_minus, m_plus)
                missing = check_spanner(k, M, edges)

                total_hubs_checked += 1
                source_col = m_minus_inv[h]
                hub_col = c

                # Which cycle is the hub column in?
                hub_cycle_idx = col_to_cycle_idx[hub_col]
                hub_cycle_len = len(cycles[hub_cycle_idx])

                is_valid = (missing == 0)

                if is_valid:
                    total_valid += 1
                    valid_hub_indices.append(h)
                    valid_hub_cycle_indices.add(hub_cycle_idx)
                    valid_hub_cycle_len_sum += hub_cycle_len
                    valid_count += 1

                    if hub_col in longest_cycle_set:
                        valid_in_longest += 1
                    else:
                        valid_not_in_longest += 1

                    if sigma[hub_col] == hub_col:
                        valid_is_fixed += 1
                    else:
                        valid_not_fixed += 1
                else:
                    invalid_hub_cycle_len_sum += hub_cycle_len
                    invalid_count += 1

            results_by_ncycles[n_cycles]['total_hubs'] += k
            results_by_ncycles[n_cycles]['valid_hubs'] += len(valid_hub_indices)
            results_by_ncycles[n_cycles]['instances'] += 1

            results_by_maxcyc[max_cyc_len]['total_hubs'] += k
            results_by_maxcyc[max_cyc_len]['valid_hubs'] += len(valid_hub_indices)
            results_by_maxcyc[max_cyc_len]['instances'] += 1

            if valid_hub_indices:
                instances_with_valid += 1
                if len(valid_hub_cycle_indices) == 1:
                    all_from_one_cycle += 1

        print(f"  Generated: {generated}")
        print(f"  Total valid hubs: {total_valid}/{total_hubs_checked} "
              f"({100*total_valid/max(total_hubs_checked,1):.1f}%)")

        if valid_count > 0:
            print(f"\n  Hub-in-longest-cycle:")
            print(f"    Valid hubs in longest cycle: {valid_in_longest}/{total_valid}")
            print(f"    Valid hubs NOT in longest:   {valid_not_in_longest}/{total_valid}")

            print(f"\n  Hub-is-fixed-point of σ:")
            print(f"    Valid hubs that are fixed:   {valid_is_fixed}/{total_valid}")
            print(f"    Valid hubs not fixed:        {valid_not_fixed}/{total_valid}")

            avg_valid_cyc = valid_hub_cycle_len_sum / valid_count
            avg_invalid_cyc = invalid_hub_cycle_len_sum / max(invalid_count, 1)
            print(f"\n  Avg cycle length of hub column:")
            print(f"    Valid hubs:   {avg_valid_cyc:.2f}")
            print(f"    Invalid hubs: {avg_invalid_cyc:.2f}")

        if instances_with_valid > 0:
            print(f"\n  All valid hubs from single cycle: "
                  f"{all_from_one_cycle}/{instances_with_valid} "
                  f"({100*all_from_one_cycle/instances_with_valid:.1f}%)")

        print(f"\n  Validity rate by number of cycles in σ:")
        for nc in sorted(results_by_ncycles.keys()):
            d = results_by_ncycles[nc]
            rate = d['valid_hubs'] / max(d['total_hubs'], 1)
            avg_valid_per = d['valid_hubs'] / max(d['instances'], 1)
            print(f"    {nc} cycles: {rate:.3f} valid rate, "
                  f"{avg_valid_per:.1f} avg valid/instance, "
                  f"({d['instances']} instances)")

        print(f"\n  Validity rate by max cycle length:")
        for mc in sorted(results_by_maxcyc.keys()):
            d = results_by_maxcyc[mc]
            rate = d['valid_hubs'] / max(d['total_hubs'], 1)
            avg_valid_per = d['valid_hubs'] / max(d['instances'], 1)
            print(f"    max_cyc={mc}: {rate:.3f} valid rate, "
                  f"{avg_valid_per:.1f} avg valid/instance, "
                  f"({d['instances']} instances)")


def experiment_3_fvs_connection():
    """Check if valid hubs form a feedback vertex set of some σ-derived graph."""
    print("\n" + "=" * 70)
    print("EXPERIMENT 3: FVS connection")
    print("=" * 70)

    ks = [3, 4, 5, 6, 7]
    n_samples = 200

    for k in ks:
        print(f"\n--- k = {k} ---")

        fvs_match = 0
        fvs_subset = 0  # valid hubs ⊆ FVS
        fvs_superset = 0  # FVS ⊆ valid hubs
        total = 0

        # Track: is valid hub set exactly = one element from each cycle?
        transversal_match = 0

        generated = 0
        attempts = 0
        while generated < n_samples and attempts < n_samples * 20:
            attempts += 1
            result = generate_random_biclique(k)
            if result[0] is None:
                continue
            M, m_minus, m_plus = result
            generated += 1

            sigma = twist_permutation(m_minus, m_plus, k)
            cycles = cycle_structure(sigma, k)

            m_minus_inv = {}
            for j in range(k):
                m_minus_inv[m_minus[j]] = j

            # Find valid hubs
            valid_hubs = set()
            for h in range(k):
                c = m_plus[h]
                edges = double_star_edges(M, k, h, c, m_minus, m_plus)
                missing = check_spanner(k, M, edges)
                if missing == 0:
                    valid_hubs.add(h)

            if not valid_hubs:
                continue
            total += 1

            # Convert valid hubs to column indices via m⁺
            valid_hub_cols = {m_plus[h] for h in valid_hubs}

            # Check FVS: do valid hub columns form a FVS of σ?
            is_fvs = is_feedback_vertex(sigma, k, valid_hub_cols)

            # Check: is each valid hub column a FVS by itself?
            each_is_fvs = all(
                is_feedback_vertex(sigma, k, {c}) for c in valid_hub_cols
            )

            # Check: does each valid hub column hit every cycle?
            # (single element FVS = hits all cycles = transversal of cycle partition)
            col_to_cycle = {}
            for idx, cyc in enumerate(cycles):
                for elem in cyc:
                    col_to_cycle[elem] = idx

            # For each valid hub, check if its column hits every cycle
            # (a single vertex can only be in one cycle, so it can't hit all cycles
            # unless there's only one cycle or the vertex is special)

            # Actually: "breaking all cycles" for a single hub means:
            # the double star provides temporal shortcuts that bypass every cycle.
            # This is NOT the same as FVS (removing vertex from graph).
            # Let me think about what "breaks" means operationally...

            # Alternative: build a "conflict graph" where vertices are pairs (i,i')
            # and check if the hub's star covers all conflicts.
            # The conflict is: pair (a_i, a_{i'}) needs a journey, and the
            # forced edges (M⁻ ∪ M⁺) alone don't provide one.

            # For now, just check the FVS property
            if is_fvs:
                fvs_match += 1

            # Check if valid hub cols (as a set) contain a transversal
            cycles_hit = {col_to_cycle[c] for c in valid_hub_cols}
            if cycles_hit == set(range(len(cycles))):
                transversal_match += 1

            # Check if source_col is in same cycle as hub_col for valid hubs
            # source_col = m⁻⁻¹(h), hub_col = m⁺(h)
            # We know σ(source_col) = hub_col, so they're always in the same cycle!

        print(f"  Instances with valid hubs: {total}")
        if total > 0:
            print(f"  Valid hub cols form FVS of σ: {fvs_match}/{total} "
                  f"({100*fvs_match/total:.1f}%)")
            print(f"  Valid hub cols hit all cycles: {transversal_match}/{total} "
                  f"({100*transversal_match/total:.1f}%)")


def experiment_4_single_hub_fvs():
    """For each individual valid hub, check if its column alone is a FVS
    (i.e., removing it breaks all cycles of σ). Since σ is a permutation,
    a single vertex can only be in one cycle. So single-vertex FVS only
    works when σ has exactly one cycle."""
    print("\n" + "=" * 70)
    print("EXPERIMENT 4: Single hub as FVS — and what 'cycle breaking' really means")
    print("=" * 70)

    ks = [3, 4, 5, 6, 7]
    n_samples = 200

    for k in ks:
        print(f"\n--- k = {k} ---")

        # Track relationship between valid hubs and σ structure
        cases = {
            'valid_and_single_cycle': 0,
            'valid_and_multi_cycle': 0,
            'valid_hub_in_longest': 0,
            'valid_hub_not_in_longest': 0,
        }

        # Deeper: for multi-cycle σ, what makes a hub valid?
        multi_cycle_analysis = []

        generated = 0
        attempts = 0
        while generated < n_samples and attempts < n_samples * 20:
            attempts += 1
            result = generate_random_biclique(k)
            if result[0] is None:
                continue
            M, m_minus, m_plus = result
            generated += 1

            sigma = twist_permutation(m_minus, m_plus, k)
            cycles = cycle_structure(sigma, k)
            n_cycles = len(cycles)

            longest_idx = max(range(len(cycles)), key=lambda i: len(cycles[i]))
            longest_set = set(cycles[longest_idx])

            for h in range(k):
                c = m_plus[h]
                edges = double_star_edges(M, k, h, c, m_minus, m_plus)
                missing = check_spanner(k, M, edges)

                if missing == 0:
                    if n_cycles == 1:
                        cases['valid_and_single_cycle'] += 1
                    else:
                        cases['valid_and_multi_cycle'] += 1
                        # Record details for analysis
                        col_to_cycle = {}
                        for idx, cyc in enumerate(cycles):
                            for elem in cyc:
                                col_to_cycle[elem] = idx
                        multi_cycle_analysis.append({
                            'k': k,
                            'n_cycles': n_cycles,
                            'cycle_lens': sorted([len(c) for c in cycles], reverse=True),
                            'hub_col': c,
                            'hub_col_cycle_len': len(cycles[col_to_cycle[c]]),
                        })

                    if c in longest_set:
                        cases['valid_hub_in_longest'] += 1
                    else:
                        cases['valid_hub_not_in_longest'] += 1

        print(f"  Valid hubs in single-cycle σ:  {cases['valid_and_single_cycle']}")
        print(f"  Valid hubs in multi-cycle σ:   {cases['valid_and_multi_cycle']}")
        print(f"  Valid hubs in longest cycle:   {cases['valid_hub_in_longest']}")
        print(f"  Valid hubs NOT in longest:     {cases['valid_hub_not_in_longest']}")

        if multi_cycle_analysis:
            # Summarize: cycle length of valid hub's column vs σ structure
            by_ncyc = defaultdict(list)
            for entry in multi_cycle_analysis:
                by_ncyc[entry['n_cycles']].append(entry['hub_col_cycle_len'])
            print(f"\n  Multi-cycle instances — hub column's cycle length:")
            for nc in sorted(by_ncyc.keys()):
                lens = by_ncyc[nc]
                avg = sum(lens) / len(lens)
                print(f"    σ has {nc} cycles: avg hub-col cycle len = {avg:.2f} "
                      f"(n={len(lens)})")


def experiment_5_many_short_cycles():
    """When σ has many short cycles (hardest case per Casteigts), how many valid hubs?"""
    print("\n" + "=" * 70)
    print("EXPERIMENT 5: Many short cycles — hardest case")
    print("=" * 70)

    ks = [4, 5, 6, 7, 8]
    n_samples = 500

    for k in ks:
        print(f"\n--- k = {k} ---")

        # Bin by number of cycles
        by_ncycles = defaultdict(lambda: {'valid_per_instance': [], 'count': 0})

        generated = 0
        attempts = 0
        while generated < n_samples and attempts < n_samples * 20:
            attempts += 1
            result = generate_random_biclique(k)
            if result[0] is None:
                continue
            M, m_minus, m_plus = result
            generated += 1

            sigma = twist_permutation(m_minus, m_plus, k)
            cycles = cycle_structure(sigma, k)
            n_cycles = len(cycles)

            n_valid = 0
            for h in range(k):
                c = m_plus[h]
                edges = double_star_edges(M, k, h, c, m_minus, m_plus)
                missing = check_spanner(k, M, edges)
                if missing == 0:
                    n_valid += 1

            by_ncycles[n_cycles]['valid_per_instance'].append(n_valid)
            by_ncycles[n_cycles]['count'] += 1

        print(f"  Generated: {generated}")
        print(f"\n  {'n_cycles':>8} | {'instances':>9} | {'avg_valid':>9} | "
              f"{'min_valid':>9} | {'zero_valid':>10} | {'frac':>6}")
        print("  " + "-" * 65)

        for nc in sorted(by_ncycles.keys()):
            d = by_ncycles[nc]
            vals = d['valid_per_instance']
            avg = sum(vals) / len(vals)
            mn = min(vals)
            zeros = sum(1 for v in vals if v == 0)
            frac = d['count'] / generated
            print(f"  {nc:>8} | {d['count']:>9} | {avg:>9.2f} | "
                  f"{mn:>9} | {zeros:>10} | {frac:>6.3f}")


def experiment_6_sm_twist():
    """Analyze σ for SM(k) specifically — the structured case."""
    print("\n" + "=" * 70)
    print("EXPERIMENT 6: SM(k) twist permutation")
    print("=" * 70)

    for k in range(3, 16):
        M = generate_sm_matrix(k)
        m_minus, m_plus = get_matchings(M, k)
        sigma = twist_permutation(m_minus, m_plus, k)
        cycles = cycle_structure(sigma, k)

        cycle_lens = sorted([len(c) for c in cycles], reverse=True)

        # Check which hubs are valid (only for small k)
        valid_hubs = []
        if k <= 10:
            for h in range(k):
                c = m_plus[h]
                edges = double_star_edges(M, k, h, c, m_minus, m_plus)
                missing = check_spanner(k, M, edges)
                if missing == 0:
                    valid_hubs.append(h)

        print(f"  SM({k:>2}): σ = {sigma}, cycles = {cycle_lens}, "
              f"valid hubs = {valid_hubs if k <= 10 else '(skipped)'}")


def experiment_7_decision_problem():
    """
    Formal analysis: is "find h that breaks all cycles" reducible to FVS?

    Key insight: σ is a PERMUTATION, so its functional graph is a union of
    disjoint cycles. FVS on a union of disjoint cycles is trivial (pick one
    vertex from each cycle). The question is whether the TEMPORAL constraint
    makes it harder.

    The temporal constraint: hub (h, c=m⁺(h)) must produce a valid spanner.
    This depends on M's VALUES, not just σ's structure.

    So the decision problem is: given σ AND M, find h such that
    double_star(h, m⁺(h)) is a valid spanner.

    This is NOT pure FVS — it's FVS-with-side-constraints from M.
    """
    print("\n" + "=" * 70)
    print("EXPERIMENT 7: Decision problem structure")
    print("=" * 70)

    print("\n  Theoretical analysis:")
    print("  σ = permutation on [k] → functional graph = disjoint cycles")
    print("  FVS on disjoint cycles: O(k) — pick one vertex per cycle")
    print("  But hub validity depends on M's values, not just σ's structure")
    print()
    print("  The real decision problem:")
    print("  INPUT: k×k all-distinct matrix M")
    print("  QUESTION: ∃ row h such that M⁻ ∪ M⁺ ∪ star(h) ∪ star(m⁺(h))")
    print("            is a temporal spanner?")
    print()
    print("  This is NOT FVS. It's a feasibility problem over M's values.")
    print("  The cycle structure of σ constrains WHICH hubs CAN work,")
    print("  but the values of M determine which ones ACTUALLY work.")

    # Empirical: for instances where σ is the same permutation,
    # do different M matrices yield different valid hub sets?
    print("\n  Testing: same σ, different M → different valid hubs?")

    k = 5
    n_samples = 500
    sigma_to_results = defaultdict(list)

    generated = 0
    attempts = 0
    while generated < n_samples and attempts < n_samples * 20:
        attempts += 1
        result = generate_random_biclique(k)
        if result[0] is None:
            continue
        M, m_minus, m_plus = result
        generated += 1

        sigma = twist_permutation(m_minus, m_plus, k)
        sigma_key = tuple(sigma)

        valid_hubs = set()
        for h in range(k):
            c = m_plus[h]
            edges = double_star_edges(M, k, h, c, m_minus, m_plus)
            missing = check_spanner(k, M, edges)
            if missing == 0:
                valid_hubs.add(h)

        sigma_to_results[sigma_key].append(frozenset(valid_hubs))

    # Find σ values that appear multiple times
    multi_sigma = {s: results for s, results in sigma_to_results.items()
                   if len(results) >= 3}

    print(f"\n  k={k}, {generated} instances, {len(sigma_to_results)} distinct σ values")
    print(f"  σ values with ≥3 instances: {len(multi_sigma)}")

    differ_count = 0
    same_count = 0
    for sig, results in multi_sigma.items():
        if len(set(results)) > 1:
            differ_count += 1
        else:
            same_count += 1

    print(f"  Same σ, same valid hubs:     {same_count}")
    print(f"  Same σ, DIFFERENT valid hubs: {differ_count}")

    if differ_count > 0:
        print("\n  ==> σ alone does NOT determine valid hubs. M's values matter.")
        print("  ==> The problem is NOT purely combinatorial over σ.")
    else:
        print("\n  ==> σ appears to determine valid hubs (surprising!)")
        print("  ==> But sample size may be too small to confirm.")

    # Show some examples
    print(f"\n  Examples (same σ, different valid hubs):")
    shown = 0
    for sig, results in sorted(multi_sigma.items()):
        if len(set(results)) > 1 and shown < 5:
            print(f"    σ = {list(sig)}: valid_hubs = {[sorted(r) for r in set(results)]}")
            shown += 1


if __name__ == '__main__':
    experiment_6_sm_twist()
    data = experiment_1_cycle_structure_stats()
    experiment_2_hub_validity_vs_cycles()
    experiment_3_fvs_connection()
    experiment_4_single_hub_fvs()
    experiment_5_many_short_cycles()
    experiment_7_decision_problem()
