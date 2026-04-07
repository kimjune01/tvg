"""
Inspect the structure of worst-case minimum spanners.
Find the worst-case labeling, compute the exact minimum spanner,
and show which edges are kept vs removed and WHY.
"""

import math
import random
from itertools import combinations


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


def find_minimum_spanner(n, edges, timestamps):
    """Return the actual edge indices of a minimum spanner."""
    m = len(edges)
    timed = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in range(m)])
    target = compute_reachability(n, timed)

    # Greedy upper bound
    included = list(range(m))
    for idx in sorted(range(m), key=lambda i: -timestamps[i]):
        candidate = [i for i in included if i != idx]
        sub_timed = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in candidate])
        if compute_reachability(n, sub_timed) == target:
            included = candidate
    greedy_size = len(included)

    # Exact search below greedy
    best_subset = included
    for size in range(n - 1, greedy_size):
        found = False
        for subset in combinations(range(m), size):
            sub_timed = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in subset])
            if compute_reachability(n, sub_timed) == target:
                best_subset = list(subset)
                found = True
                break
        if found:
            break

    return best_subset


def find_essential_edges(n, edges, timestamps):
    """Find edges that MUST be in every minimum spanner (removing breaks reachability)."""
    m = len(edges)
    timed = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in range(m)])
    target = compute_reachability(n, timed)

    essential = []
    for idx in range(m):
        remaining = [i for i in range(m) if i != idx]
        sub_timed = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in remaining])
        if compute_reachability(n, sub_timed) != target:
            essential.append(idx)
    return essential


def analyze_worst_case(n, num_search=5000):
    """Find worst case and analyze its spanner structure."""
    edges = make_edges(n)
    m = len(edges)

    print(f"\n{'='*60}")
    print(f"K_{n}: {n} vertices, {m} edges, {n*(n-1)} ordered pairs")
    print(f"{'='*60}")

    # Find worst-case labeling
    worst_size = 0
    worst_ts = None

    for _ in range(num_search):
        ts = list(range(1, m + 1))
        random.shuffle(ts)
        spanner = find_minimum_spanner(n, edges, ts)
        if len(spanner) > worst_size:
            worst_size = len(spanner)
            worst_ts = ts[:]

    print(f"\nWorst-case min spanner: {worst_size} edges (2n-3 = {2*n-3})")

    # Analyze the worst case
    ts = worst_ts
    spanner_idx = find_minimum_spanner(n, edges, ts)
    essential = find_essential_edges(n, edges, ts)

    print(f"Essential edges (in every spanner): {len(essential)}")
    print(f"Min spanner edges: {len(spanner_idx)}")
    print(f"Removable edges: {m - len(essential)}")

    # Show edges sorted by timestamp
    print(f"\nEdge labeling (sorted by time):")
    print(f"{'time':>5} {'edge':>8} {'in_spanner':>11} {'essential':>10}")
    print("-" * 40)
    by_time = sorted(range(m), key=lambda i: ts[i])
    for idx in by_time:
        u, v = edges[idx]
        in_sp = "YES" if idx in spanner_idx else "no"
        ess = "MUST" if idx in essential else ""
        print(f"{ts[idx]:>5} ({u},{v}){'':<3} {in_sp:>11} {ess:>10}")

    # Analyze spanner structure
    spanner_edges = [edges[i] for i in spanner_idx]
    spanner_times = [ts[i] for i in spanner_idx]

    # Degree distribution in spanner
    deg = [0] * n
    for u, v in spanner_edges:
        deg[u] += 1
        deg[v] += 1
    print(f"\nSpanner degree distribution: {deg}")
    print(f"Max degree: {max(deg)}, Min degree: {min(deg)}")

    # Check for hub structure (high-degree vertex)
    hub = deg.index(max(deg))
    print(f"Hub vertex: {hub} (degree {deg[hub]})")

    # Forward/backward analysis: which edges go "forward" vs "backward"?
    # Sort spanner edges by timestamp
    sorted_spanner = sorted(zip(spanner_times, spanner_edges))
    median_time = sorted_spanner[len(sorted_spanner)//2][0]

    early = [(t, e) for t, e in sorted_spanner if t <= median_time]
    late = [(t, e) for t, e in sorted_spanner if t > median_time]
    print(f"\nTemporal split (median time={median_time}):")
    print(f"  Early edges ({len(early)}): {[(t, e) for t, e in early]}")
    print(f"  Late edges ({len(late)}):  {[(t, e) for t, e in late]}")

    # Check: do early edges form a tree? Do late edges?
    def is_connected(edge_list, n):
        if not edge_list:
            return False
        adj = [[] for _ in range(n)]
        for _, (u, v) in edge_list:
            adj[u].append(v)
            adj[v].append(u)
        visited = set()
        stack = [edge_list[0][1][0]]
        while stack:
            v = stack.pop()
            if v in visited:
                continue
            visited.add(v)
            for w in adj[v]:
                if w not in visited:
                    stack.append(w)
        vertices_in_edges = set()
        for _, (u, v) in edge_list:
            vertices_in_edges.add(u)
            vertices_in_edges.add(v)
        return vertices_in_edges <= visited

    print(f"  Early connected: {is_connected(early, n)}")
    print(f"  Late connected: {is_connected(late, n)}")

    # Which pairs are covered by which edges?
    # For each edge in the spanner, which pairs REQUIRE this edge?
    print(f"\nEdge criticality (pairs that break if edge removed):")
    timed_full = sorted([(ts[i], edges[i][0], edges[i][1]) for i in spanner_idx])
    target = compute_reachability(n, timed_full)

    for idx in spanner_idx:
        remaining = [i for i in spanner_idx if i != idx]
        sub_timed = sorted([(ts[i], edges[i][0], edges[i][1]) for i in remaining])
        reach = compute_reachability(n, sub_timed)
        broken = []
        for src in range(n):
            diff = target[src] ^ reach[src]
            if diff:
                for dst in range(n):
                    if diff & (1 << dst):
                        broken.append((src, dst))
        u, v = edges[idx]
        if broken:
            print(f"  ({u},{v})@t={ts[idx]}: breaks {len(broken)} pairs: {broken[:5]}{'...' if len(broken)>5 else ''}")
        else:
            print(f"  ({u},{v})@t={ts[idx]}: removable (no pairs break)")


def main():
    random.seed(42)
    for n in [4, 5, 6]:
        analyze_worst_case(n, num_search=3000)


if __name__ == "__main__":
    main()
