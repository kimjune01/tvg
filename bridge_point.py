"""
Find the bridge point: the one edge where M⁻ reachability meets M⁺ reachability.

For each biclique:
1. Compute reachability using only M⁻ (early matching)
2. Compute reachability using only M⁺ (late matching)
3. Find the minimum set of edges needed to connect them
4. Is it always ONE edge? And where does it sit temporally?
"""

import random
from itertools import combinations
from collections import defaultdict


def compute_reachability(k, entries):
    """Reachability on V⁻ side through given matrix entries.
    entries = list of (i, j, t) where i=row, j=col, t=timestamp.
    aᵢ reaches aᵢ' iff ∃ chain of entries with non-decreasing timestamps
    alternating between same-column and same-row moves."""
    # Build journey graph: vertices are (side, index)
    # a_i = ('a', i), b_j = ('b', j)
    # Edge (a_i, b_j) at time t from entry M[i][j]=t
    n = 2 * k
    reached_by = [dict() for _ in range(n)]
    for v in range(n):
        reached_by[v][v] = 0

    timed = sorted(entries, key=lambda x: x[2])
    for i, j, t in timed:
        u = i       # a_i
        v = k + j   # b_j
        sources_u = {s: a for s, a in reached_by[u].items() if a <= t}
        sources_v = {s: a for s, a in reached_by[v].items() if a <= t}
        for s, a in sources_u.items():
            if s not in reached_by[v] or t < reached_by[v][s]:
                reached_by[v][s] = t
        for s, a in sources_v.items():
            if s not in reached_by[u] or t < reached_by[u][s]:
                reached_by[u][s] = t

    # Extract V⁻ to V⁻ reachability
    R_minus = [[False] * k for _ in range(k)]
    for i in range(k):
        for ip in range(k):
            R_minus[i][ip] = ip in reached_by[i] or i == ip

    # V⁺ to V⁺
    R_plus = [[False] * k for _ in range(k)]
    for j in range(k):
        for jp in range(k):
            R_plus[j][jp] = (k + jp) in reached_by[k + j] or j == jp

    # All pairs
    R_all = [[False] * n for _ in range(n)]
    for u in range(n):
        for v in range(n):
            R_all[u][v] = v in reached_by[u] or u == v

    return R_minus, R_plus, R_all


def generate_sm_matrix(k):
    offset = k * (k - 1) // 2
    M = [[0] * k for _ in range(k)]
    for d in range(k):
        for i in range(k):
            j = (i + d) % k
            M[i][j] = offset + d * k + i + 1
    return M


def random_biclique_matrix(k):
    offset = k * (k - 1) // 2
    vals = list(range(offset + 1, offset + k * k + 1))
    random.shuffle(vals)
    M = [[0] * k for _ in range(k)]
    idx = 0
    for i in range(k):
        for j in range(k):
            M[i][j] = vals[idx]; idx += 1
    return M


def analyze_bridge(k, M):
    """Find the bridge: minimum edges connecting M⁻ and M⁺ reachability."""
    # M⁻ entries: row minimum for each row (earliest cross edge per V⁺ vertex)
    m_minus = []
    for i in range(k):
        j_min = min(range(k), key=lambda j: M[i][j])
        m_minus.append((i, j_min, M[i][j_min]))

    # M⁺ entries: column maximum for each column (latest cross edge per V⁻ vertex)
    m_plus = []
    for j in range(k):
        i_max = max(range(k), key=lambda i: M[i][j])
        m_plus.append((i_max, j, M[i_max][j]))

    # All entries
    all_entries = [(i, j, M[i][j]) for i in range(k) for j in range(k)]

    # Full reachability
    _, _, R_full = compute_reachability(k, all_entries)

    # M⁻ ∪ M⁺ reachability
    base_entries = list(set(m_minus + m_plus))
    _, _, R_base = compute_reachability(k, base_entries)

    # Missing pairs
    n = 2 * k
    missing = []
    for u in range(n):
        for v in range(n):
            if R_full[u][v] and not R_base[u][v]:
                missing.append((u, v))

    if not missing:
        return {
            'bridges_needed': 0,
            'base_size': len(base_entries),
            'missing': 0,
        }

    # Find minimum bridge set: try adding ONE entry at a time
    # Which single entry covers the most missing pairs?
    remaining = [(i, j, M[i][j]) for i, j, t in all_entries
                 if (i, j, t) not in set(base_entries)]

    bridges = []
    current_entries = list(base_entries)
    current_missing = missing[:]

    while current_missing:
        best_entry = None
        best_covered = 0

        for entry in remaining:
            if entry in current_entries:
                continue
            trial = current_entries + [entry]
            _, _, R_trial = compute_reachability(k, trial)
            covered = sum(1 for u, v in current_missing if R_trial[u][v])
            if covered > best_covered:
                best_covered = covered
                best_entry = entry

        if best_entry is None or best_covered == 0:
            break

        bridges.append(best_entry)
        current_entries.append(best_entry)
        remaining = [e for e in remaining if e != best_entry]
        _, _, R_new = compute_reachability(k, current_entries)
        current_missing = [(u, v) for u, v in current_missing if not R_new[u][v]]

    # Temporal position of bridges
    all_times = sorted(M[i][j] for i in range(k) for j in range(k))
    median_time = all_times[len(all_times) // 2]
    m_minus_max_time = max(t for _, _, t in m_minus)
    m_plus_min_time = min(t for _, _, t in m_plus)

    return {
        'bridges_needed': len(bridges),
        'bridges': bridges,
        'base_size': len(base_entries),
        'missing_before': len(missing),
        'missing_after': len(current_missing),
        'm_minus_max_t': m_minus_max_time,
        'm_plus_min_t': m_plus_min_time,
        'bridge_times': [t for _, _, t in bridges],
        'gap': (m_plus_min_time - m_minus_max_time) if m_plus_min_time > m_minus_max_time else 0,
        'bridges_in_gap': sum(1 for _, _, t in bridges
                             if m_minus_max_time <= t <= m_plus_min_time),
    }


def run():
    random.seed(42)

    print("SHIFTED MATCHING: bridge analysis")
    print("=" * 60)
    for k in range(3, 9):
        M = generate_sm_matrix(k)
        result = analyze_bridge(k, M)
        print(f"\nSM({k}):")
        print(f"  M⁻∪M⁺ base: {result['base_size']} entries")
        print(f"  Missing pairs: {result['missing_before']}")
        print(f"  Bridges needed: {result['bridges_needed']}")
        if result['bridges_needed'] > 0:
            print(f"  M⁻ max time: {result['m_minus_max_t']}")
            print(f"  M⁺ min time: {result['m_plus_min_t']}")
            print(f"  Gap: {result['gap']}")
            print(f"  Bridge times: {result['bridge_times']}")
            print(f"  Bridges in gap: {result['bridges_in_gap']}")
            for i, j, t in result['bridges']:
                print(f"    M[{i}][{j}] = {t}")

    print(f"\n{'='*60}")
    print("RANDOM BICLIQUES: bridge analysis")
    print("=" * 60)
    for k in range(3, 8):
        bridge_counts = []
        gap_hits = []
        samples = 300 if k <= 5 else 100
        for _ in range(samples):
            M = random_biclique_matrix(k)
            result = analyze_bridge(k, M)
            bridge_counts.append(result['bridges_needed'])
            if result['bridges_needed'] > 0:
                gap_hits.append(result['bridges_in_gap'])

        avg = sum(bridge_counts) / len(bridge_counts)
        print(f"\n  k={k}: bridges needed: min={min(bridge_counts)} "
              f"avg={avg:.1f} max={max(bridge_counts)}")
        if gap_hits:
            avg_gap = sum(gap_hits) / len(gap_hits)
            print(f"    Bridges in M⁻/M⁺ gap: avg={avg_gap:.1f}")


if __name__ == "__main__":
    run()
