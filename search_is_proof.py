"""
Search-as-proof experiment.

The algorithm tries hub candidates in order. The proof is that it always
finds one. Two search strategies:

Strategy 1: Try vertex with max spread.
Strategy 2: When max-spread fails, what structural constraint does that
            impose on the matrix? Use that constraint to identify the
            guaranteed fallback.

Key question: what does "max-spread vertex fails" tell us about M?
"""

import random
import time
from collections import Counter


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


def star_tree_spans(n, edges, timestamps, hub):
    """Check if star(hub) + greedy_tree spans G. Returns (ok, uncovered_pairs)."""
    m = len(edges)
    timed = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in range(m)])
    target = compute_reachability(n, timed)

    star_idx = [i for i, (u, v) in enumerate(edges) if u == hub or v == hub]
    current = set(star_idx)
    tree_candidates = [i for i in range(m) if i not in star_idx]

    def current_reach():
        sub = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in current])
        return compute_reachability(n, sub)

    for _ in range(n - 2):
        cr = current_reach()
        if cr == target:
            break
        current_covered = sum(bin(r).count('1') for r in cr)
        best_edge = None
        best_gain = -1
        for idx in tree_candidates:
            if idx in current:
                continue
            trial = current | {idx}
            sub = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in trial])
            tr = compute_reachability(n, sub)
            gain = sum(bin(r).count('1') for r in tr) - current_covered
            if gain > best_gain:
                best_gain = gain
                best_edge = idx
        if best_edge is None or best_gain <= 0:
            break
        current.add(best_edge)

    final = current_reach()
    # Find uncovered pairs
    uncovered = []
    for src in range(n):
        diff = target[src] ^ final[src]
        for dst in range(n):
            if diff & (1 << dst):
                uncovered.append((src, dst))
    return final == target, uncovered


def vertex_profile(n, edges, timestamps, v):
    """Detailed profile of vertex v as potential hub."""
    edge_map = {}
    for i, (u, w) in enumerate(edges):
        edge_map[(u, w)] = timestamps[i]
        edge_map[(w, u)] = timestamps[i]

    times = [edge_map[(v, u)] for u in range(n) if u != v]
    times_sorted = sorted(times)
    spread = times_sorted[-1] - times_sorted[0]
    avg = sum(times) / len(times)

    # Forward pairs: (a,b) where t(a,v) <= t(v,b)
    others = [u for u in range(n) if u != v]
    forward = 0
    backward = 0
    for a in others:
        for b in others:
            if a != b:
                if edge_map[(a, v)] <= edge_map[(v, b)]:
                    forward += 1
                else:
                    backward += 1

    # Composability: for how many pairs (a,b) does there exist c≠v in others
    # such that t(a,v) <= t(v,c) and c can reach b via non-v edges?
    # (This is the 3-hop composition budget)

    return {
        'spread': spread,
        'avg': avg,
        'forward': forward,
        'backward': backward,
        'balance': forward / (forward + backward) if (forward + backward) > 0 else 0.5,
        'min_t': times_sorted[0],
        'max_t': times_sorted[-1],
    }


def analyze_failure_structure(n, edges, ts):
    """When a vertex fails as hub, what pairs does it fail on?"""
    m = len(edges)
    edge_map = {}
    for i, (u, v) in enumerate(edges):
        edge_map[(u, v)] = ts[i]
        edge_map[(v, u)] = ts[i]

    results = {}
    for v in range(n):
        ok, uncovered = star_tree_spans(n, edges, ts, v)
        profile = vertex_profile(n, edges, ts, v)
        results[v] = {
            'ok': ok,
            'uncovered': uncovered,
            'profile': profile,
        }
    return results


def search_order_experiment(n, num_samples=5000):
    """Try different search orders. Which order minimizes worst-case attempts?"""
    edges = make_edges(n)
    m = len(edges)
    print(f"\nK_{n}: {n} vertices, {m} edges")
    print("=" * 60)

    # Track: for each ordering strategy, how many attempts before success?
    strategies = {
        'max_spread': lambda profiles: sorted(profiles.keys(),
            key=lambda v: -profiles[v]['profile']['spread']),
        'min_spread': lambda profiles: sorted(profiles.keys(),
            key=lambda v: profiles[v]['profile']['spread']),
        'most_balanced': lambda profiles: sorted(profiles.keys(),
            key=lambda v: abs(profiles[v]['profile']['balance'] - 0.5)),
        'least_balanced': lambda profiles: sorted(profiles.keys(),
            key=lambda v: -abs(profiles[v]['profile']['balance'] - 0.5)),
        'max_spread_then_balanced': lambda profiles: sorted(profiles.keys(),
            key=lambda v: (-profiles[v]['profile']['spread'],
                           abs(profiles[v]['profile']['balance'] - 0.5))),
        'balanced_then_spread': lambda profiles: sorted(profiles.keys(),
            key=lambda v: (abs(profiles[v]['profile']['balance'] - 0.5),
                           -profiles[v]['profile']['spread'])),
    }

    attempt_counts = {s: [] for s in strategies}
    first_two_success = {s: 0 for s in strategies}

    for _ in range(num_samples):
        ts = list(range(1, m + 1))
        random.shuffle(ts)

        profiles = analyze_failure_structure(n, edges, ts)

        for sname, order_fn in strategies.items():
            order = order_fn(profiles)
            attempts = 0
            for v in order:
                attempts += 1
                if profiles[v]['ok']:
                    break
            attempt_counts[sname].append(attempts)
            if attempts <= 2:
                first_two_success[sname] += 1

    print(f"\nSearch strategy comparison ({num_samples} samples):")
    print(f"{'strategy':>30s}  {'avg_attempts':>12s}  {'max':>4s}  {'≤2 tries':>10s}")
    print("-" * 65)
    for sname in strategies:
        counts = attempt_counts[sname]
        avg = sum(counts) / len(counts)
        mx = max(counts)
        p2 = first_two_success[sname] / num_samples * 100
        print(f"{sname:>30s}  {avg:>12.2f}  {mx:>4d}  {p2:>9.1f}%")

    # Deeper look: when does first candidate fail?
    # What's special about instances where attempt > 1?
    print(f"\nWhen max_spread first candidate fails:")
    fail_balance = []
    fail_spread = []
    ok_balance = []
    ok_spread = []

    for _ in range(min(num_samples, 2000)):
        ts = list(range(1, m + 1))
        random.shuffle(ts)
        profiles = analyze_failure_structure(n, edges, ts)
        order = strategies['max_spread'](profiles)
        first_v = order[0]
        if profiles[first_v]['ok']:
            ok_balance.append(profiles[first_v]['profile']['balance'])
            ok_spread.append(profiles[first_v]['profile']['spread'])
        else:
            fail_balance.append(profiles[first_v]['profile']['balance'])
            fail_spread.append(profiles[first_v]['profile']['spread'])

    if fail_balance and ok_balance:
        print(f"  Failing hubs: avg balance={sum(fail_balance)/len(fail_balance):.3f}, "
              f"avg spread={sum(fail_spread)/len(fail_spread):.1f}")
        print(f"  Working hubs: avg balance={sum(ok_balance)/len(ok_balance):.3f}, "
              f"avg spread={sum(ok_spread)/len(ok_spread):.1f}")


def main():
    random.seed(42)
    print("Search-as-proof: which ordering finds a hub fastest?")

    for n, samples in [(5, 10000), (6, 5000), (7, 2000), (8, 500)]:
        search_order_experiment(n, samples)


if __name__ == "__main__":
    main()
