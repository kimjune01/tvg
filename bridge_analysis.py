"""
What do the non-essential edges in SM(k) spanners do?

Essential: 2k edges (diagonals 0 and k-1 = M- and M+).
Bridge edges: the ~k extra edges from middle diagonals.

Questions:
1. Which diagonal do bridge edges come from?
2. What pairs do they cover that M- ∪ M+ can't?
3. Is there a pattern to which bridge edges are chosen?
4. What's the reachability structure of M- ∪ M+ alone?
"""

import random
from itertools import combinations
from collections import defaultdict, Counter


def make_edges(n):
    return [(i, j) for i in range(n) for j in range(i + 1, n)]


def compute_reachability(n, timed_edges):
    reached_by = [dict() for _ in range(n)]
    for i in range(n):
        reached_by[i][i] = 0
    for t, u, v in timed_edges:
        sources_u = {s: arr for s, arr in reached_by[u].items() if arr <= t}
        sources_v = {s: arr for s, arr in reached_by[v].items() if arr <= t}
        for s, arr in sources_u.items():
            if s not in reached_by[v] or t < reached_by[v][s]:
                reached_by[v][s] = t
        for s, arr in sources_v.items():
            if s not in reached_by[u] or t < reached_by[u][s]:
                reached_by[u][s] = t
    reach = [0] * n
    for v in range(n):
        for s in reached_by[v]:
            if s != v:
                reach[s] |= (1 << v)
    return reach


def generate_sm(k):
    n = 2 * k
    edges = make_edges(n)
    m = len(edges)
    eidx = {}
    for i, (u, v) in enumerate(edges):
        eidx[(u, v)] = i; eidx[(v, u)] = i

    ts = [0] * m
    t = 1
    for i in range(k):
        for j in range(i + 1, k):
            ts[eidx[(i, j)]] = t; t += 1
    for d in range(k):
        for i in range(k):
            j = (i + d) % k
            idx = eidx[(min(i, k+j), max(i, k+j))]
            if ts[idx] == 0:
                ts[idx] = t; t += 1
    for i in range(k):
        for j in range(i + 1, k):
            ts[eidx[(k+i, k+j)]] = t; t += 1

    return n, edges, ts, eidx


def find_best_spanner(n, edges, ts, num_trials=100):
    m = len(edges)
    timed_all = sorted([(ts[i], edges[i][0], edges[i][1]) for i in range(m)])
    target = compute_reachability(n, timed_all)

    best = list(range(m))
    for _ in range(num_trials):
        order = list(range(m))
        random.shuffle(order)
        included = list(range(m))
        for idx in order:
            if idx not in included:
                continue
            candidate = [i for i in included if i != idx]
            sub = sorted([(ts[i], edges[i][0], edges[i][1]) for i in candidate])
            if compute_reachability(n, sub) == target:
                included = candidate
        if len(included) < len(best):
            best = included
    return best


def uncovered_pairs(n, edges, ts, subset_idx):
    """Which ordered pairs are NOT reachable through subset?"""
    m = len(edges)
    timed_all = sorted([(ts[i], edges[i][0], edges[i][1]) for i in range(m)])
    target = compute_reachability(n, timed_all)
    sub = sorted([(ts[i], edges[i][0], edges[i][1]) for i in subset_idx])
    reach = compute_reachability(n, sub)

    missing = []
    for src in range(n):
        diff = target[src] ^ reach[src]
        for dst in range(n):
            if diff & (1 << dst):
                missing.append((src, dst))
    return missing


def run():
    random.seed(42)

    for k in [4, 5, 6, 7]:
        n, edges, ts, eidx = generate_sm(k)
        m = len(edges)
        print(f"\nSM({k}): n={n}, m={m}")
        print("=" * 70)

        # Essential edges (diag 0 and k-1)
        essential = []
        for d in [0, k - 1]:
            for i in range(k):
                j = (i + d) % k
                essential.append(eidx[(min(i, k+j), max(i, k+j))])

        # What does M- ∪ M+ cover?
        missing_base = uncovered_pairs(n, edges, ts, essential)
        total_pairs = n * (n - 1)
        covered_base = total_pairs - len(missing_base)
        print(f"\n  M- ∪ M+ ({len(essential)} edges):")
        print(f"    Covers: {covered_base}/{total_pairs} pairs ({covered_base/total_pairs*100:.1f}%)")
        print(f"    Missing: {len(missing_base)} pairs")

        # Classify missing pairs
        missing_types = Counter()
        for (src, dst) in missing_base:
            src_side = 'a' if src < k else 'b'
            dst_side = 'a' if dst < k else 'b'
            missing_types[f"{src_side}→{dst_side}"] += 1
        print(f"    Missing by type: {dict(missing_types)}")

        # Find best spanner
        best = find_best_spanner(n, edges, ts, num_trials=100)
        bridge = [i for i in best if i not in essential]
        print(f"\n  Best spanner: {len(best)} edges ({len(essential)} essential + {len(bridge)} bridge)")

        # Analyze bridge edges
        bridge_diags = Counter()
        print(f"    Bridge edges:")
        for i in sorted(bridge, key=lambda x: ts[x]):
            u, v = edges[i]
            a_node = u if u < k else v
            b_node = (v if v >= k else u) - k
            d = (b_node - a_node) % k
            bridge_diags[d] += 1
            print(f"      (a{a_node}, b{b_node}) diag={d} @ t={ts[i]}")

        print(f"    Bridge diagonal distribution: {dict(sorted(bridge_diags.items()))}")

        # What does each bridge edge contribute?
        print(f"\n    Per-bridge-edge contribution:")
        current = set(essential)
        for i in sorted(bridge, key=lambda x: ts[x]):
            before = uncovered_pairs(n, edges, ts, list(current))
            current.add(i)
            after = uncovered_pairs(n, edges, ts, list(current))
            newly_covered = len(before) - len(after)
            u, v = edges[i]
            a_node = u if u < k else v
            b_node = (v if v >= k else u) - k
            d = (b_node - a_node) % k

            # Which specific pairs does this edge cover?
            covered_pairs = [(s, t) for (s, t) in before if (s, t) not in after]
            pair_types = Counter()
            for (s, t) in covered_pairs[:20]:
                ss = f"a{s}" if s < k else f"b{s-k}"
                tt = f"a{t}" if t < k else f"b{t-k}"
                pair_types[f"{ss}→{tt}"] += 1

            print(f"      (a{a_node},b{b_node}) d={d} t={ts[i]}: "
                  f"+{newly_covered} pairs, e.g. {dict(list(pair_types.items())[:5])}")

        # Verify: essential + bridge covers everything?
        final_missing = uncovered_pairs(n, edges, ts, best)
        print(f"\n    Final missing: {len(final_missing)}")


if __name__ == "__main__":
    run()
