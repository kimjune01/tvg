"""
Dijkstra-style monotone sweep for temporal spanner construction.

Process edges in timestamp order. An edge is "essential" if it's the
first to achieve some temporal reachability that no earlier edge provides.

Questions:
1. How many edges does a single sweep select?
2. Does it match 2n-3?
3. If it overshoots, how many edges need to be "unselected" (backtracking)?
4. What's the structure of the essential edge set?

Also: reverse sweep (latest-first) and compare.
"""

import random
from itertools import combinations


def make_temporal_clique(n):
    """Random temporal K_n: n(n-1)/2 edges, timestamps = random permutation."""
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
    m = len(edges)
    timestamps = list(range(1, m + 1))
    random.shuffle(timestamps)
    return edges, timestamps


def make_sm_clique(k):
    """SM(k) temporal clique on n=2k vertices."""
    n = 2 * k
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
    m = len(edges)
    ts = [0] * m
    eidx = {}
    for i, (u, v) in enumerate(edges):
        eidx[(u, v)] = i
        eidx[(v, u)] = i

    t = 1
    # V- internal
    for i in range(k):
        for j in range(i + 1, k):
            ts[eidx[(i, j)]] = t
            t += 1
    # Cross edges by diagonal
    for d in range(k):
        for i in range(k):
            j = (i + d) % k
            ts[eidx[(min(i, k + j), max(i, k + j))]] = t
            t += 1
    # V+ internal
    for i in range(k):
        for j in range(i + 1, k):
            ts[eidx[(k + i, k + j)]] = t
            t += 1

    return edges, ts


def compute_full_reachability(n, edges, timestamps):
    """Full temporal reachability via sweep."""
    timed = sorted(zip(timestamps, edges))
    # reach[v] = set of vertices that can reach v (with arrival time)
    # Actually: reach_from[s] = {v: earliest_arrival}
    reach = [{i: 0} for i in range(n)]  # each vertex reaches itself at time 0

    for t, (u, v) in timed:
        # edge {u,v} at time t
        # Anyone who reached u by time t can now reach v at time t (and vice versa)
        new_for_v = {}
        new_for_u = {}

        for s, arr in reach[u].items():
            if arr <= t:
                if s not in reach[v] or t < reach[v][s]:
                    new_for_v[s] = t

        for s, arr in reach[v].items():
            if arr <= t:
                if s not in reach[u] or t < reach[u][s]:
                    new_for_u[s] = t

        for s, arr in new_for_v.items():
            reach[v][s] = arr
        for s, arr in new_for_u.items():
            reach[u][s] = arr

    # Convert to reachability matrix
    R = [[False] * n for _ in range(n)]
    for v in range(n):
        for s in reach[v]:
            R[s][v] = True
    return R


def dijkstra_sweep_forward(n, edges, timestamps):
    """Process edges earliest-first. Include edge only if it achieves
    NEW reachability not already covered by earlier edges.
    Returns: list of selected edge indices, reachability after sweep.
    """
    timed = sorted(enumerate(zip(timestamps, edges)), key=lambda x: x[1][0])
    # timed[i] = (original_idx, (timestamp, (u, v)))

    reach = [{i: 0} for i in range(n)]
    selected = []

    for orig_idx, (t, (u, v)) in timed:
        # Check what new reachability this edge would provide
        new_for_v = {}
        new_for_u = {}

        for s, arr in reach[u].items():
            if arr <= t:
                if s not in reach[v] or t < reach[v][s]:
                    new_for_v[s] = t

        for s, arr in reach[v].items():
            if arr <= t:
                if s not in reach[u] or t < reach[u][s]:
                    new_for_u[s] = t

        if new_for_v or new_for_u:
            selected.append(orig_idx)
            for s, arr in new_for_v.items():
                reach[v][s] = arr
            for s, arr in new_for_u.items():
                reach[u][s] = arr

    return selected, reach


def dijkstra_sweep_reverse(n, edges, timestamps):
    """Process edges latest-first. Include edge only if it achieves
    NEW reachability. Reachability computed in reverse: who can be
    reached FROM each vertex via temporally valid journeys ending
    with this edge or later.

    Actually, for a fair comparison: just do the same forward sweep
    but process in reverse timestamp order and see what happens.
    The semantics change: later edges first means we're building
    reachability from the "future" backward.
    """
    # Reverse temporal reachability: process latest-first
    # Edge at time t: can connect v->u if someone departs from v at time >= t
    # and arrives at u at time t. Then from u, earlier edges can extend.
    # This is "latest departure" reachability.

    timed = sorted(enumerate(zip(timestamps, edges)), key=lambda x: -x[1][0])

    reach = [{i: float('inf')} for i in range(n)]  # latest departure = inf (always available)
    selected = []

    for orig_idx, (t, (u, v)) in timed:
        new_for_v = {}
        new_for_u = {}

        # In reverse: edge at time t. From u side: can depart at time t.
        # Anyone reachable from u with departure >= t can now be reached from v
        # by departing v at time t.
        for d, latest_dep in reach[u].items():
            if latest_dep >= t:  # can reach d from u departing at or after t
                if d not in reach[v] or t > reach[v][d]:
                    new_for_v[d] = t

        for d, latest_dep in reach[v].items():
            if latest_dep >= t:
                if d not in reach[u] or t > reach[u][d]:
                    new_for_u[d] = t

        if new_for_v or new_for_u:
            selected.append(orig_idx)
            for d, dep in new_for_v.items():
                reach[v][d] = dep
            for d, dep in new_for_u.items():
                reach[u][d] = dep

    return selected, reach


def greedy_deletion(n, edges, timestamps):
    """Standard greedy: try removing each edge (latest first), keep if
    reachability unchanged. Returns selected edge indices."""
    m = len(edges)
    target = compute_full_reachability(n, edges, timestamps)
    included = set(range(m))

    # Remove latest edges first
    for idx in sorted(range(m), key=lambda i: -timestamps[i]):
        trial = included - {idx}
        sub_edges = [(edges[i][0], edges[i][1]) for i in trial]
        sub_ts = [timestamps[i] for i in trial]
        if compute_full_reachability(n, sub_edges, sub_ts) == target:
            included = trial

    return sorted(included)


def classify_edges(edges, timestamps, selected, k):
    """Classify selected edges as V-, cross, V+."""
    counts = {'V-': 0, 'cross': 0, 'V+': 0}
    for idx in selected:
        u, v = edges[idx]
        if u < k and v < k:
            counts['V-'] += 1
        elif u >= k and v >= k:
            counts['V+'] += 1
        else:
            counts['cross'] += 1
    return counts


def main():
    random.seed(42)

    print("DIJKSTRA SWEEP SPANNER CONSTRUCTION")
    print("=" * 70)

    # SM(k) tests
    print("\n--- SM(k) ---\n")
    print(f"{'k':>3} {'n':>3} {'2n-3':>5} {'fwd':>5} {'rev':>5} {'greedy':>7} "
          f"{'fwd_type':>20} {'rev_type':>20}")
    print("-" * 85)

    for k in range(3, 8):
        n = 2 * k
        edges, ts = make_sm_clique(k)

        fwd_sel, _ = dijkstra_sweep_forward(n, edges, ts)
        rev_sel, _ = dijkstra_sweep_reverse(n, edges, ts)

        if n <= 12:
            greedy_sel = greedy_deletion(n, edges, ts)
            greedy_ct = len(greedy_sel)
        else:
            greedy_ct = -1

        fwd_cls = classify_edges(edges, ts, fwd_sel, k)
        rev_cls = classify_edges(edges, ts, rev_sel, k)

        fwd_type = f"{fwd_cls['V-']}/{fwd_cls['cross']}/{fwd_cls['V+']}"
        rev_type = f"{rev_cls['V-']}/{rev_cls['cross']}/{rev_cls['V+']}"

        print(f"{k:>3} {n:>3} {2*n-3:>5} {len(fwd_sel):>5} {len(rev_sel):>5} "
              f"{greedy_ct:>7} {fwd_type:>20} {rev_type:>20}")

    # Random temporal cliques
    print("\n--- Random temporal cliques ---\n")
    print(f"{'n':>3} {'2n-3':>5} {'fwd_avg':>8} {'fwd_max':>8} {'rev_avg':>8} "
          f"{'rev_max':>8} {'greedy_avg':>10}")
    print("-" * 65)

    for n in [6, 8, 10, 12]:
        samples = {6: 1000, 8: 500, 10: 200, 12: 100}[n]
        fwd_sizes = []
        rev_sizes = []
        greedy_sizes = []

        for _ in range(samples):
            edges, ts = make_temporal_clique(n)
            fwd_sel, _ = dijkstra_sweep_forward(n, edges, ts)
            rev_sel, _ = dijkstra_sweep_reverse(n, edges, ts)

            fwd_sizes.append(len(fwd_sel))
            rev_sizes.append(len(rev_sel))

            if n <= 10:
                greedy_sel = greedy_deletion(n, edges, ts)
                greedy_sizes.append(len(greedy_sel))

        g_avg = f"{sum(greedy_sizes)/len(greedy_sizes):.1f}" if greedy_sizes else "—"
        print(f"{n:>3} {2*n-3:>5} {sum(fwd_sizes)/len(fwd_sizes):>8.1f} "
              f"{max(fwd_sizes):>8} {sum(rev_sizes)/len(rev_sizes):>8.1f} "
              f"{max(rev_sizes):>8} {g_avg:>10}")

    # Backtracking analysis: how many edges does forward sweep select
    # that greedy would NOT select?
    print("\n--- Backtracking: forward sweep vs greedy ---\n")
    print(f"{'n':>3} {'samples':>8} {'fwd_only':>10} {'greedy_only':>12} "
          f"{'overlap':>8} {'backtrack_depth':>16}")
    print("-" * 65)

    for n in [6, 8, 10]:
        samples = {6: 500, 8: 200, 10: 100}[n]
        fwd_only_total = 0
        greedy_only_total = 0
        overlap_total = 0
        max_backtrack = 0

        for _ in range(samples):
            edges, ts = make_temporal_clique(n)
            fwd_sel, _ = dijkstra_sweep_forward(n, edges, ts)
            greedy_sel = greedy_deletion(n, edges, ts)

            fwd_set = set(fwd_sel)
            greedy_set = set(greedy_sel)

            fwd_only = len(fwd_set - greedy_set)
            greedy_only = len(greedy_set - fwd_set)
            overlap = len(fwd_set & greedy_set)

            fwd_only_total += fwd_only
            greedy_only_total += greedy_only
            overlap_total += overlap

            # "Backtracking depth": how many swaps needed to go from
            # forward sweep to greedy? = max(fwd_only, greedy_only)
            bt = max(fwd_only, greedy_only)
            if bt > max_backtrack:
                max_backtrack = bt

        print(f"{n:>3} {samples:>8} {fwd_only_total/samples:>10.1f} "
              f"{greedy_only_total/samples:>12.1f} {overlap_total/samples:>8.1f} "
              f"{max_backtrack:>16}")


if __name__ == "__main__":
    main()
