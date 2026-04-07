"""
Characterize the balanced-ness of vertex timestamp distributions.

For each vertex v, its incident timestamps form a sequence.
What shape predicts hub success?

Candidates:
- Gap uniformity: are gaps between consecutive timestamps even?
- Skewness: are timestamps bunched early or late?
- Entropy of gap distribution
- Quartile balance: how symmetric is the distribution?
- Position of median incident timestamp relative to global median
"""

import random
import math
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


def vertex_balance_metrics(n, edges, timestamps, v):
    """Compute balance metrics for vertex v's incident timestamps."""
    m = len(edges)
    edge_map = {}
    for i, (u, w) in enumerate(edges):
        edge_map[(u, w)] = timestamps[i]
        edge_map[(w, u)] = timestamps[i]

    times = sorted([edge_map[(v, u)] for u in range(n) if u != v])
    k = len(times)  # n-1
    global_median = (m + 1) / 2

    # 1. Spread
    spread = times[-1] - times[0]

    # 2. Normalized spread: spread / max_possible
    norm_spread = spread / (m - 1) if m > 1 else 0

    # 3. Gap uniformity: stdev of gaps / mean of gaps (CV)
    gaps = [times[i+1] - times[i] for i in range(k - 1)]
    mean_gap = sum(gaps) / len(gaps) if gaps else 1
    gap_cv = (statistics.stdev(gaps) / mean_gap) if len(gaps) > 1 and mean_gap > 0 else 0

    # 4. Max gap / mean gap ratio
    max_gap_ratio = max(gaps) / mean_gap if gaps and mean_gap > 0 else 0

    # 5. Skewness: (mean - median) / stdev
    med = statistics.median(times)
    std = statistics.stdev(times) if k > 1 else 0.001
    skewness = (sum(times)/k - med) / std if std > 0 else 0

    # 6. Median position relative to global median
    med_offset = abs(med - global_median) / global_median

    # 7. Quartile balance: Q3-median vs median-Q1
    q1_idx = k // 4
    q3_idx = 3 * k // 4
    q1 = times[q1_idx]
    q3 = times[q3_idx]
    upper = q3 - med
    lower = med - q1
    quartile_asymmetry = abs(upper - lower) / (upper + lower) if (upper + lower) > 0 else 0

    # 8. Concentration: what fraction of incident timestamps fall
    #    in the middle third of the global range?
    lo = m / 3
    hi = 2 * m / 3
    mid_count = sum(1 for t in times if lo <= t <= hi)
    concentration = mid_count / k

    # 9. Extremal: does v own the global min or max timestamp?
    has_extreme = 1 if (times[0] == 1 or times[-1] == m) else 0

    # 10. Pair-composability: for how many non-hub pairs (a,b) does
    #     there exist any c != v such that t(a,v) <= t(v,c) and t(c,?) works?
    #     Simplified: count pairs where star routing works (t(a,v) <= t(v,b))
    others = [u for u in range(n) if u != v]
    star_pairs = 0
    for a in others:
        for b in others:
            if a != b and edge_map[(a, v)] <= edge_map[(v, b)]:
                star_pairs += 1
    total_pairs = (n-1) * (n-2)
    star_coverage = star_pairs / total_pairs

    return {
        'spread': spread,
        'norm_spread': norm_spread,
        'gap_cv': gap_cv,
        'max_gap_ratio': max_gap_ratio,
        'skewness': skewness,
        'med_offset': med_offset,
        'q_asymmetry': quartile_asymmetry,
        'concentration': concentration,
        'has_extreme': has_extreme,
        'star_coverage': star_coverage,
    }


def run(n, num_samples):
    edges = make_edges(n)
    m = len(edges)
    print(f"\nK_{n}: {n} vertices, {m} edges")
    print("=" * 70)

    metrics_names = ['spread', 'norm_spread', 'gap_cv', 'max_gap_ratio',
                     'skewness', 'med_offset', 'q_asymmetry', 'concentration',
                     'has_extreme', 'star_coverage']

    winner_data = {k: [] for k in metrics_names}
    loser_data = {k: [] for k in metrics_names}

    for _ in range(num_samples):
        ts = list(range(1, m + 1))
        random.shuffle(ts)

        for v in range(n):
            ok = star_tree_spans(n, edges, ts, v)
            metrics = vertex_balance_metrics(n, edges, ts, v)
            target = winner_data if ok else loser_data
            for k in metrics_names:
                target[k].append(metrics[k])

    print(f"\n{'metric':>15s}  {'winner':>8s}  {'loser':>8s}  {'delta':>8s}  {'effect_d':>8s}")
    print("-" * 55)
    for k in metrics_names:
        if not winner_data[k] or not loser_data[k]:
            continue
        w = sum(winner_data[k]) / len(winner_data[k])
        l = sum(loser_data[k]) / len(loser_data[k])
        ws = statistics.stdev(winner_data[k]) if len(winner_data[k]) > 1 else 0.001
        ls = statistics.stdev(loser_data[k]) if len(loser_data[k]) > 1 else 0.001
        pooled = ((ws**2 + ls**2) / 2) ** 0.5
        d = abs(w - l) / pooled if pooled > 0 else 0
        print(f"{k:>15s}  {w:>8.3f}  {l:>8.3f}  {w-l:>+8.3f}  {d:>8.3f}")

    # Also: which single metric best predicts hub success?
    # For each metric, what's the accuracy of "pick the vertex that maximizes/minimizes it"?
    print(f"\nBest-single-vertex prediction accuracy:")
    for k in metrics_names:
        correct_max = 0
        correct_min = 0
        total = 0
        for _ in range(min(num_samples, 2000)):
            ts = list(range(1, m + 1))
            random.shuffle(ts)

            scores = []
            for v in range(n):
                ok = star_tree_spans(n, edges, ts, v)
                metrics = vertex_balance_metrics(n, edges, ts, v)
                scores.append((metrics[k], v, ok))

            total += 1
            # Pick vertex with max metric value
            scores_sorted = sorted(scores, key=lambda x: -x[0])
            if scores_sorted[0][2]:
                correct_max += 1
            # Pick vertex with min metric value
            scores_sorted = sorted(scores, key=lambda x: x[0])
            if scores_sorted[0][2]:
                correct_min += 1

        print(f"  {k:>15s}: max={correct_max/total*100:.1f}% min={correct_min/total*100:.1f}%")


def main():
    random.seed(42)
    for n, samples in [(5, 3000), (6, 1500), (7, 500)]:
        run(n, samples)


if __name__ == "__main__":
    main()
