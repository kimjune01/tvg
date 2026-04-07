"""
Inductive tree construction analysis.

Build the tree one edge at a time. At step k, we have k vertices
in the tree (plus the hub). Adding vertex w via edge (w, c) creates
k new tree paths: w→c→...→v for each v already in tree.

Question: at each step, does there always exist a candidate edge (w, c)
that covers all new pairs involving w?

"Cover" means: for each new pair (w, v) or (v, w) that is a reverse pair
(star can't handle), the tree path + star composition provides a valid
temporal journey.

Track: how many candidates work at each step? Does it ever drop to 0?
"""

import random
from itertools import combinations
from collections import defaultdict


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


def hub_max_run(n, edges, timestamps, hub):
    m = len(edges)
    ordered = sorted(range(m), key=lambda i: timestamps[i])
    involves_hub = [(edges[i][0] == hub or edges[i][1] == hub) for i in ordered]
    max_run = 0
    cur = 0
    for b in involves_hub:
        if b:
            cur += 1
            max_run = max(max_run, cur)
        else:
            cur = 0
    return max_run


def build_tree_inductively(n, edges, timestamps, hub):
    """Build tree greedily, one vertex at a time.
    At each step, try all possible edges to add the next vertex.
    Pick the one that covers the most new pairs.

    Returns: list of (step, edge_idx, vertex_added, num_candidates,
             new_pairs_covered, new_pairs_total)
    """
    m = len(edges)
    edge_map = {}
    for i, (u, v) in enumerate(edges):
        edge_map[(u, v)] = timestamps[i]
        edge_map[(v, u)] = timestamps[i]

    timed_all = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in range(m)])
    target = compute_reachability(n, timed_all)

    star_idx = set(i for i, (u, v) in enumerate(edges) if u == hub or v == hub)
    others = set(v for v in range(n) if v != hub)

    # Start: just the star
    in_tree = set()  # vertices in the tree (subset of others)
    tree_edges = set()
    current_edges = set(star_idx)

    def current_reach():
        sub = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in current_edges])
        return compute_reachability(n, sub)

    log = []

    for step in range(n - 2):
        not_in_tree = others - in_tree
        if not not_in_tree:
            break

        cr = current_reach()
        current_covered = sum(bin(r).count('1') for r in cr)

        best_edge = None
        best_gain = -1
        best_vertex = None
        num_candidates = 0

        for w in not_in_tree:
            for c in (in_tree if in_tree else others - {w}):
                # Find edge index for (w, c)
                idx = None
                for i, (u, v) in enumerate(edges):
                    if (u == w and v == c) or (u == c and v == w):
                        idx = i
                        break
                if idx is None or idx in star_idx:
                    continue

                trial = current_edges | {idx}
                sub = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in trial])
                tr = compute_reachability(n, sub)
                gain = sum(bin(r).count('1') for r in tr) - current_covered

                if gain > 0:
                    num_candidates += 1

                if gain > best_gain:
                    best_gain = gain
                    best_edge = idx
                    best_vertex = w

        if best_edge is None:
            # No improvement possible — try any edge
            for w in not_in_tree:
                for i, (u, v) in enumerate(edges):
                    if i in star_idx or i in current_edges:
                        continue
                    if (u == w and v in in_tree) or (v == w and u in in_tree):
                        best_edge = i
                        best_vertex = w
                        break
                    if not in_tree and ((u == w and v in others) or (v == w and u in others)):
                        best_edge = i
                        best_vertex = w
                if best_edge:
                    break

        if best_edge is None:
            break

        # How many new pairs does this create?
        new_pairs_total = len(in_tree) if in_tree else 0  # undirected pairs with w
        new_pairs_total *= 2  # directed

        current_edges.add(best_edge)
        in_tree.add(best_vertex)
        tree_edges.add(best_edge)

        log.append({
            'step': step + 1,
            'vertex': best_vertex,
            'edge': edges[best_edge],
            'time': timestamps[best_edge],
            'gain': best_gain,
            'candidates': num_candidates,
            'tree_size': len(in_tree),
        })

    final = current_reach()
    ok = final == target

    return ok, log


def run(n, num_samples):
    edges = make_edges(n)
    m = len(edges)
    print(f"\nK_{n}: {n} vertices, {m} edges, tree needs {n-2} edges")
    print("=" * 70)

    # Per step: min/avg/max candidates, min/avg/max gain
    step_stats = defaultdict(lambda: {
        'candidates': [], 'gains': [], 'count': 0
    })
    successes = 0
    failures = 0

    by_run = defaultdict(lambda: {'ok': 0, 'fail': 0})

    for trial in range(num_samples):
        ts = list(range(1, m + 1))
        random.shuffle(ts)

        # Try each vertex as hub
        best_ok = False
        best_hub = None
        best_log = None

        for hub in range(n):
            ok, log = build_tree_inductively(n, edges, ts, hub)
            if ok:
                best_ok = True
                best_hub = hub
                best_log = log
                break

        mr = hub_max_run(n, edges, ts, best_hub) if best_hub is not None else 0

        if best_ok:
            successes += 1
            by_run[mr]['ok'] += 1
            for entry in best_log:
                s = entry['step']
                step_stats[s]['candidates'].append(entry['candidates'])
                step_stats[s]['gains'].append(entry['gain'])
                step_stats[s]['count'] += 1
        else:
            failures += 1
            by_run[mr]['fail'] += 1

    total = successes + failures
    print(f"\nSuccess: {successes}/{total} ({successes/total*100:.1f}%)")

    print(f"\nPer-step statistics:")
    print(f"{'step':>5s}  {'count':>6s}  {'min_cand':>9s}  {'avg_cand':>9s}  "
          f"{'max_cand':>9s}  {'min_gain':>9s}  {'avg_gain':>9s}")
    print("-" * 60)
    for step in sorted(step_stats):
        s = step_stats[step]
        cands = s['candidates']
        gains = s['gains']
        print(f"{step:>5d}  {s['count']:>6d}  {min(cands):>9d}  "
              f"{sum(cands)/len(cands):>9.1f}  {max(cands):>9d}  "
              f"{min(gains):>9d}  {sum(gains)/len(gains):>9.1f}")

    print(f"\nBy max-run:")
    for mr in sorted(by_run):
        d = by_run[mr]
        t = d['ok'] + d['fail']
        print(f"  run={mr}: {d['ok']}/{t} ({d['ok']/t*100:.1f}%)")


def main():
    random.seed(42)
    for n, samples in [(5, 5000), (6, 2000), (7, 500), (8, 200)]:
        run(n, samples)


if __name__ == "__main__":
    main()
