"""
Shape of the temporal clique: how are edges distributed across time?

For each vertex v, its incident edges occupy positions in [1..m].
The SHAPE of the clique is how uniformly vs clustered these positions are
across all vertices.

Uniform: every vertex's edges are spread across the full range.
Concentrated: some vertices have edges bunched early, others late.

Key metric: for each vertex, compute the centroid (avg timestamp) of its
incident edges. Then measure the SPREAD of centroids across vertices.

Wide centroid spread = concentrated shape (early vs late vertices exist)
Narrow centroid spread = uniform shape (all vertices similar)

The claim: concentrated shapes need extreme hubs, uniform shapes need
any hub (easy), and the proof covers both.
"""

import random
import statistics
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

    return current_reach() == target


def instance_shape(n, edges, timestamps):
    """Characterize the global shape of the temporal clique."""
    m = len(edges)
    edge_map = {}
    for i, (u, v) in enumerate(edges):
        edge_map[(u, v)] = timestamps[i]
        edge_map[(v, u)] = timestamps[i]

    # Centroid per vertex
    centroids = []
    for v in range(n):
        times = [edge_map[(v, u)] for u in range(n) if u != v]
        centroids.append(sum(times) / len(times))

    # Centroid spread (normalized by m)
    centroid_spread = (max(centroids) - min(centroids)) / m

    # Centroid stdev (normalized)
    centroid_std = statistics.stdev(centroids) / m if n > 1 else 0

    # Per-vertex spread
    spreads = []
    for v in range(n):
        times = [edge_map[(v, u)] for u in range(n) if u != v]
        spreads.append((max(times) - min(times)) / m)

    avg_spread = sum(spreads) / len(spreads)
    spread_variance = statistics.variance(spreads) if len(spreads) > 1 else 0

    # Correlation between vertex centroid and vertex spread
    # (do early vertices have narrow or wide spread?)
    if len(centroids) > 2:
        mean_c = sum(centroids) / len(centroids)
        mean_s = sum(spreads) / len(spreads)
        cov = sum((c - mean_c) * (s - mean_s) for c, s in zip(centroids, spreads)) / len(centroids)
        std_c = statistics.stdev(centroids)
        std_s = statistics.stdev(spreads)
        centroid_spread_corr = cov / (std_c * std_s) if std_c > 0 and std_s > 0 else 0
    else:
        centroid_spread_corr = 0

    return {
        'centroid_spread': centroid_spread,
        'centroid_std': centroid_std,
        'avg_vertex_spread': avg_spread,
        'spread_variance': spread_variance,
        'centroid_spread_corr': centroid_spread_corr,
    }


def run(n, num_samples):
    edges = make_edges(n)
    m = len(edges)
    print(f"\nK_{n}: {n} vertices, {m} edges")
    print("=" * 70)

    # Collect: shape metrics vs number of working hubs and vs which hub works
    shape_data = []

    for _ in range(num_samples):
        ts = list(range(1, m + 1))
        random.shuffle(ts)

        shape = instance_shape(n, edges, ts)
        winners = [v for v in range(n) if star_tree_spans(n, edges, ts, v)]
        num_winners = len(winners)

        # Winner positions
        edge_map = {}
        for i, (u, v) in enumerate(edges):
            edge_map[(u, v)] = ts[i]
            edge_map[(v, u)] = ts[i]
        centroids = []
        for v in range(n):
            times = [edge_map[(v, u)] for u in range(n) if u != v]
            centroids.append(sum(times) / len(times))
        ranked = sorted(range(n), key=lambda v: centroids[v])
        rank = {v: i for i, v in enumerate(ranked)}

        # Does extreme hub (rank 0 or n-1) work?
        extreme_works = rank[ranked[0]] in [rank[w] for w in winners] or \
                        rank[ranked[-1]] in [rank[w] for w in winners]
        # More precisely:
        extreme_works = ranked[0] in winners or ranked[-1] in winners

        # Does middle hub work?
        mid = ranked[n // 2]
        middle_works = mid in winners

        shape_data.append({
            **shape,
            'num_winners': num_winners,
            'extreme_works': extreme_works,
            'middle_works': middle_works,
        })

    # Bin by centroid_spread
    shape_data.sort(key=lambda d: d['centroid_spread'])
    bin_size = len(shape_data) // 5

    print(f"\nBinned by centroid spread (uniform → concentrated):")
    print(f"{'bin':>5s}  {'c_spread':>9s}  {'avg_win':>8s}  {'ext_ok%':>8s}  {'mid_ok%':>8s}  {'either%':>8s}")
    print("-" * 55)
    for i in range(5):
        chunk = shape_data[i * bin_size : (i + 1) * bin_size]
        avg_cs = sum(d['centroid_spread'] for d in chunk) / len(chunk)
        avg_win = sum(d['num_winners'] for d in chunk) / len(chunk)
        ext_ok = sum(1 for d in chunk if d['extreme_works']) / len(chunk) * 100
        mid_ok = sum(1 for d in chunk if d['middle_works']) / len(chunk) * 100
        either = sum(1 for d in chunk if d['extreme_works'] or d['middle_works']) / len(chunk) * 100
        label = ['most uniform', 'uniform', 'mixed', 'concentrated', 'most concentrated'][i]
        print(f"{label:>16s}  {avg_cs:>9.3f}  {avg_win:>8.1f}  {ext_ok:>8.1f}  {mid_ok:>8.1f}  {either:>8.1f}")

    # Correlation between shape metrics and num_winners
    print(f"\nCorrelation: shape metric vs num_winners")
    for metric in ['centroid_spread', 'centroid_std', 'avg_vertex_spread', 'spread_variance']:
        vals = [d[metric] for d in shape_data]
        wins = [d['num_winners'] for d in shape_data]
        mean_v = sum(vals) / len(vals)
        mean_w = sum(wins) / len(wins)
        cov = sum((v - mean_v) * (w - mean_w) for v, w in zip(vals, wins)) / len(vals)
        std_v = statistics.stdev(vals)
        std_w = statistics.stdev(wins)
        corr = cov / (std_v * std_w) if std_v > 0 and std_w > 0 else 0
        print(f"  {metric:>25s}: r = {corr:+.3f}")

    # The if-statement: centroid_spread threshold
    print(f"\nIf-statement: concentrated → extreme hub, uniform → middle hub")
    best_acc = 0
    best_tau = 0
    for pct in range(10, 91, 5):
        tau = shape_data[len(shape_data) * pct // 100]['centroid_spread']
        success = 0
        for d in shape_data:
            if d['centroid_spread'] >= tau:
                if d['extreme_works']:
                    success += 1
            else:
                if d['middle_works']:
                    success += 1
        acc = success / len(shape_data) * 100
        if acc > best_acc:
            best_acc = acc
            best_tau = tau
    # Also try: always extreme, always middle, always either
    always_ext = sum(1 for d in shape_data if d['extreme_works']) / len(shape_data) * 100
    always_mid = sum(1 for d in shape_data if d['middle_works']) / len(shape_data) * 100
    always_either = sum(1 for d in shape_data if d['extreme_works'] or d['middle_works']) / len(shape_data) * 100

    print(f"  Best threshold: centroid_spread={best_tau:.3f}, accuracy={best_acc:.1f}%")
    print(f"  Always extreme: {always_ext:.1f}%")
    print(f"  Always middle:  {always_mid:.1f}%")
    print(f"  Either (union): {always_either:.1f}%")


def main():
    random.seed(42)
    for n, samples in [(5, 10000), (6, 3000), (7, 1000), (8, 300)]:
        run(n, samples)


if __name__ == "__main__":
    main()
