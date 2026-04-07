"""
What distinguishes working hubs from non-working hubs?

For each instance, compute many vertex metrics and see which ones
predict hub success. Focus on the "neither" failures to understand
what the two heuristics miss.
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
    tree_candidates = [i for i in range(m) if i not in star_idx]

    current = set(star_idx)

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
            covered = sum(bin(r).count('1') for r in tr)
            gain = covered - current_covered
            if gain > best_gain:
                best_gain = gain
                best_edge = idx
        if best_edge is None or best_gain <= 0:
            break
        current.add(best_edge)

    return current_reach() == target


def vertex_metrics(n, edges, timestamps, v):
    """Compute various metrics for vertex v."""
    edge_map = {}
    for i, (u, w) in enumerate(edges):
        edge_map[(u, w)] = timestamps[i]
        edge_map[(w, u)] = timestamps[i]

    # Timestamps of edges incident to v
    incident_times = sorted([edge_map[(v, u)] for u in range(n) if u != v])
    m = len(edges)

    # 1. Average timestamp rank of incident edges
    avg_time = sum(incident_times) / len(incident_times)

    # 2. Median timestamp
    med_time = statistics.median(incident_times)

    # 3. Spread (max - min) of incident timestamps
    spread = max(incident_times) - min(incident_times)

    # 4. Has the globally earliest edge?
    has_min = min(incident_times) == 1

    # 5. Has the globally latest edge?
    has_max = max(incident_times) == m

    # 6. Number of "forward" pairs: (a,b) where t(a,v) <= t(v,b)
    others = [u for u in range(n) if u != v]
    forward = 0
    for a in others:
        for b in others:
            if a != b and edge_map[(a, v)] <= edge_map[(v, b)]:
                forward += 1
    total_pairs = (n - 1) * (n - 2)

    # 7. Balance: how close to 50/50 is the forward/backward split
    balance = abs(forward - total_pairs / 2) / (total_pairs / 2)  # 0 = perfect balance

    # 8. Inversion count: how many pairs of incident edges are "out of order"
    # relative to the vertex ordering
    inversions = 0
    for i in range(len(incident_times)):
        for j in range(i + 1, len(incident_times)):
            if incident_times[i] > incident_times[j]:
                inversions += 1
    max_inv = len(incident_times) * (len(incident_times) - 1) // 2
    inv_ratio = inversions / max_inv if max_inv > 0 else 0

    # 9. Timestamp variance
    variance = statistics.variance(incident_times) if len(incident_times) > 1 else 0

    # 10. Rank among vertices by sum of incident timestamps
    all_sums = []
    for u in range(n):
        s = sum(edge_map[(u, w)] for w in range(n) if w != u)
        all_sums.append((s, u))
    all_sums.sort()
    rank = next(i for i, (_, u) in enumerate(all_sums) if u == v)
    norm_rank = rank / (n - 1)  # 0 = lowest sum, 1 = highest

    return {
        'avg_time': avg_time,
        'med_time': med_time,
        'spread': spread,
        'has_min': has_min,
        'has_max': has_max,
        'forward': forward,
        'balance': balance,
        'inv_ratio': inv_ratio,
        'variance': variance,
        'norm_rank': norm_rank,
    }


def run(n, num_samples=5000):
    edges = make_edges(n)
    m = len(edges)
    print(f"\nK_{n}: {n} vertices, {m} edges")
    print("=" * 60)

    # Collect metrics for winners vs losers
    winner_metrics = {k: [] for k in ['avg_time', 'med_time', 'spread', 'has_min',
                                        'has_max', 'forward', 'balance', 'inv_ratio',
                                        'variance', 'norm_rank']}
    loser_metrics = {k: [] for k in winner_metrics}

    winner_count = Counter()
    num_winners_dist = Counter()

    for _ in range(num_samples):
        ts = list(range(1, m + 1))
        random.shuffle(ts)

        winners = []
        for v in range(n):
            if star_tree_spans(n, edges, ts, v):
                winners.append(v)

        num_winners_dist[len(winners)] += 1

        for v in range(n):
            metrics = vertex_metrics(n, edges, ts, v)
            target = winner_metrics if v in winners else loser_metrics
            for k, val in metrics.items():
                target[k].append(val)

            if v in winners:
                winner_count[v] += 1

    print(f"\nNumber of working hubs per instance:")
    for k in sorted(num_winners_dist):
        print(f"  {k} hubs: {num_winners_dist[k]} ({num_winners_dist[k]/num_samples*100:.1f}%)")

    print(f"\nMetric comparison (winner avg vs loser avg):")
    print(f"{'metric':>15s}  {'winner':>10s}  {'loser':>10s}  {'delta':>10s}  {'separation':>10s}")
    print("-" * 60)
    for k in winner_metrics:
        if not winner_metrics[k] or not loser_metrics[k]:
            continue
        w_avg = sum(winner_metrics[k]) / len(winner_metrics[k])
        l_avg = sum(loser_metrics[k]) / len(loser_metrics[k])
        w_std = statistics.stdev(winner_metrics[k]) if len(winner_metrics[k]) > 1 else 0.001
        l_std = statistics.stdev(loser_metrics[k]) if len(loser_metrics[k]) > 1 else 0.001
        pooled_std = ((w_std**2 + l_std**2) / 2)**0.5
        separation = abs(w_avg - l_avg) / pooled_std if pooled_std > 0 else 0
        print(f"{k:>15s}  {w_avg:>10.3f}  {l_avg:>10.3f}  {w_avg - l_avg:>+10.3f}  {separation:>10.3f}")


def main():
    random.seed(42)
    for n in [5, 6, 7]:
        run(n, {5: 5000, 6: 2000, 7: 1000}.get(n, 1000))


if __name__ == "__main__":
    main()
