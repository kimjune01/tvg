"""
deep_metrics.py

Test new metric ideas for predicting whether a vertex v works as a hub
in a temporal spanner (star(v) + tree spans the temporal clique).

For each metric, picks the vertex with max (or min) value and checks
if it's a working hub. Reports accuracy and Cohen's d effect size.

Metrics tested:
1. Inversion density
2. Transitivity score
3. Max anti-chain length
4. Complementary edge density
5. Eigenvalue-like (coverage matrix rank / trace / sum of squares)
6. Vertex centrality in temporal ordering (signed coverage)
7. Gap structure (max gap, gap variance, large gap count)
8. Composite metrics
"""

import random
import statistics
import math


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

    def current_reach():
        sub = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in current])
        return compute_reachability(n, sub)

    tree_candidates = [i for i in range(m) if i not in star_idx]

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


def build_edge_map(n, edges, timestamps):
    edge_map = {}
    for i, (u, v) in enumerate(edges):
        edge_map[(u, v)] = timestamps[i]
        edge_map[(v, u)] = timestamps[i]
    return edge_map


def compute_all_metrics(n, edges, timestamps):
    """Compute all metrics for every vertex. Returns dict of metric_name -> list of n values."""
    m = len(edges)
    edge_map = build_edge_map(n, edges, timestamps)
    all_ts = list(range(1, m + 1))
    ts_range = max(all_ts) - min(all_ts)
    mean_ts = sum(all_ts) / len(all_ts)

    results = {name: [] for name in [
        # Metric 1: Inversion density
        'inversion_density',
        # Metric 2: Transitivity score
        'transitivity_score',
        # Metric 3: Max anti-chain length
        'max_antichain',
        # Metric 4: Complementary edge density
        'comp_edge_density',
        # Metric 5a: Coverage matrix rank (approximate via row distinct)
        'cov_rank',
        # Metric 5b: Coverage matrix trace (= n-1, constant — skip)
        # Metric 5c: Coverage matrix sum of squares
        'cov_sum_sq',
        # Metric 6: Signed coverage (temporal centrality)
        'signed_coverage',
        # Metric 7a: Max gap
        'max_gap',
        # Metric 7b: Gap coefficient of variation
        'gap_cv',
        # Metric 7c: Large gap count (> 2x mean gap)
        'large_gap_count',
        # Metric 8a: Composite: signed_coverage / (1 + gap_cv)
        'composite_sc_gap',
        # Metric 8b: Composite: transitivity / (1 + inversion_density)
        'composite_trans_inv',
        # Reference metrics (spread + concentration) for comparison
        'spread',
        'concentration',
    ]}

    for v in range(n):
        others = [u for u in range(n) if u != v]
        incident = {u: edge_map[(v, u)] for u in others}
        inc_sorted = sorted(others, key=lambda u: incident[u])
        inc_times = [incident[u] for u in inc_sorted]

        # --- Metric 1: Inversion density ---
        # Count pairs (a, b) where t(a,v) > t(v,b) — star can't route a->v->b
        # i.e., can't forward: arrival a->v is AFTER departure v->b
        # (since edge timestamps are symmetric: t(a,v) == t(v,a))
        blocked = 0
        total_ordered = 0
        for a in others:
            for b in others:
                if a == b:
                    continue
                total_ordered += 1
                if edge_map[(a, v)] > edge_map[(v, b)]:
                    blocked += 1
        inversion_density = blocked / total_ordered if total_ordered > 0 else 0

        # --- Metric 2: Transitivity score ---
        # Count triples (a, b, c) where t(a,v) <= t(v,b) AND t(b,v) <= t(v,c)
        trans_count = 0
        total_triples = 0
        for i, a in enumerate(others):
            for j, b in enumerate(others):
                if a == b:
                    continue
                for c in others:
                    if c == a or c == b:
                        continue
                    total_triples += 1
                    if edge_map[(a, v)] <= edge_map[(v, b)] and edge_map[(b, v)] <= edge_map[(v, c)]:
                        trans_count += 1
        transitivity_score = trans_count / total_triples if total_triples > 0 else 0

        # --- Metric 3: Max anti-chain length ---
        # Vertices ordered by t(v, u). Anti-chain: longest set pairwise unreachable through star.
        # Two vertices a, b are "incompatible via star" if neither t(a,v)<=t(v,b) nor t(b,v)<=t(v,a).
        # Since t(a,v) == t(v,a) (undirected edges), this means t(a,v) != t(b,v) is not the issue —
        # incompatibility means the star can't route a->b (t(a,v) > t(v,b)) AND can't route b->a
        # (t(b,v) > t(v,a)).
        incompatible = [[False] * len(others) for _ in range(len(others))]
        for i, a in enumerate(others):
            for j, b in enumerate(others):
                if i == j:
                    continue
                ab_blocked = edge_map[(a, v)] > edge_map[(v, b)]
                ba_blocked = edge_map[(b, v)] > edge_map[(v, a)]
                if ab_blocked and ba_blocked:
                    incompatible[i][j] = True

        # Find max independent set in incompatibility graph (= max clique in complement)
        # For small n this is feasible by brute force
        k = len(others)
        max_antichain = 1
        for mask in range(1, 1 << k):
            bits = [i for i in range(k) if mask & (1 << i)]
            is_antichain = all(
                incompatible[bits[x]][bits[y]]
                for x in range(len(bits))
                for y in range(x + 1, len(bits))
            )
            if is_antichain and len(bits) > max_antichain:
                max_antichain = len(bits)

        # --- Metric 4: Complementary edge density ---
        # Among pairs (a,b) NOT covered by star(v), what fraction have timestamps
        # in the "middle" of the range (between 25th and 75th percentile)?
        all_ts_sorted = sorted(timestamps)
        q1 = all_ts_sorted[len(all_ts_sorted) // 4]
        q3 = all_ts_sorted[3 * len(all_ts_sorted) // 4]

        non_star_edges = [(u, w) for (u, w) in edges if u != v and w != v]
        comp_middle = 0
        for (u, w) in non_star_edges:
            t_uw = edge_map[(u, w)]
            if q1 <= t_uw <= q3:
                comp_middle += 1
        comp_edge_density = comp_middle / len(non_star_edges) if non_star_edges else 0

        # --- Metric 5: Coverage matrix ---
        # C[a][b] = 1 if star(v) covers a->b (i.e., t(a,v) <= t(v,b))
        k = len(others)
        C = [[0] * k for _ in range(k)]
        for i, a in enumerate(others):
            for j, b in enumerate(others):
                if i != j and edge_map[(a, v)] <= edge_map[(v, b)]:
                    C[i][j] = 1

        # Rank: approximate by number of distinct rows
        row_strs = [tuple(C[i]) for i in range(k)]
        cov_rank = len(set(row_strs))

        # Sum of squares
        cov_sum_sq = sum(C[i][j] ** 2 for i in range(k) for j in range(k))

        # --- Metric 6: Signed coverage ---
        # For each non-hub pair (a,b): +1 if t(a,v) <= t(v,b), else -1
        signed = 0
        count_pairs = 0
        for a in others:
            for b in others:
                if a != b:
                    count_pairs += 1
                    if edge_map[(a, v)] <= edge_map[(v, b)]:
                        signed += 1
                    else:
                        signed -= 1
        signed_coverage = signed / count_pairs if count_pairs > 0 else 0

        # --- Metric 7: Gap structure ---
        gaps = [inc_times[i + 1] - inc_times[i] for i in range(len(inc_times) - 1)]
        if gaps:
            max_gap = max(gaps)
            mean_gap = sum(gaps) / len(gaps)
            if mean_gap > 0:
                gap_std = statistics.stdev(gaps) if len(gaps) > 1 else 0
                gap_cv = gap_std / mean_gap
            else:
                gap_cv = 0
            large_gap_count = sum(1 for g in gaps if g > 2 * mean_gap)
        else:
            max_gap = 0
            gap_cv = 0
            large_gap_count = 0

        # --- Reference metrics ---
        spread = max(inc_times) - min(inc_times)
        # Concentration: how tightly clustered around the center of [1, m]
        mid = (m + 1) / 2
        concentration = sum(abs(t - mid) for t in inc_times) / len(inc_times)

        # --- Metric 8: Composites ---
        composite_sc_gap = signed_coverage / (1 + gap_cv)
        composite_trans_inv = transitivity_score / (1 + inversion_density)

        results['inversion_density'].append(inversion_density)
        results['transitivity_score'].append(transitivity_score)
        results['max_antichain'].append(max_antichain)
        results['comp_edge_density'].append(comp_edge_density)
        results['cov_rank'].append(cov_rank)
        results['cov_sum_sq'].append(cov_sum_sq)
        results['signed_coverage'].append(signed_coverage)
        results['max_gap'].append(max_gap)
        results['gap_cv'].append(gap_cv)
        results['large_gap_count'].append(large_gap_count)
        results['composite_sc_gap'].append(composite_sc_gap)
        results['composite_trans_inv'].append(composite_trans_inv)
        results['spread'].append(spread)
        results['concentration'].append(concentration)

    return results


def cohen_d(group1, group2):
    if len(group1) < 2 or len(group2) < 2:
        return 0.0
    m1 = sum(group1) / len(group1)
    m2 = sum(group2) / len(group2)
    s1 = statistics.stdev(group1)
    s2 = statistics.stdev(group2)
    n1, n2 = len(group1), len(group2)
    pooled = math.sqrt(((n1 - 1) * s1 ** 2 + (n2 - 1) * s2 ** 2) / (n1 + n2 - 2))
    return abs(m1 - m2) / pooled if pooled > 0 else 0.0


def run(n, num_samples):
    edges = make_edges(n)
    m = len(edges)
    print(f"\n{'='*70}")
    print(f"K_{n}: {n} vertices, {m} edges, {num_samples} samples")
    print(f"{'='*70}")

    metric_names = [
        'inversion_density', 'transitivity_score', 'max_antichain',
        'comp_edge_density', 'cov_rank', 'cov_sum_sq',
        'signed_coverage', 'max_gap', 'gap_cv', 'large_gap_count',
        'composite_sc_gap', 'composite_trans_inv',
        'spread', 'concentration',
    ]

    # For each metric: track accuracy when selecting argmax vs argmin
    max_correct = {name: 0 for name in metric_names}
    min_correct = {name: 0 for name in metric_names}

    # For Cohen's d: collect metric values for winning vs non-winning vertices
    winner_vals = {name: [] for name in metric_names}
    loser_vals = {name: [] for name in metric_names}

    for sample_idx in range(num_samples):
        ts = list(range(1, m + 1))
        random.shuffle(ts)

        # Determine which vertices are working hubs
        working = []
        for v in range(n):
            if star_tree_spans(n, edges, ts, v):
                working.append(v)

        if not working:
            continue  # skip degenerate cases (shouldn't happen for small n)

        # Compute all metrics for all vertices
        metrics = compute_all_metrics(n, edges, ts)

        # For each metric, test max and min selection
        # Tie-break randomly to avoid vertex-0 bias
        for name in metric_names:
            vals = metrics[name]
            shuffled = list(range(n))
            random.shuffle(shuffled)
            argmax_v = max(shuffled, key=lambda v: vals[v])
            argmin_v = min(shuffled, key=lambda v: vals[v])

            if argmax_v in working:
                max_correct[name] += 1
            if argmin_v in working:
                min_correct[name] += 1

            # Collect winner/loser metric values
            for v in range(n):
                if v in working:
                    winner_vals[name].append(vals[v])
                else:
                    loser_vals[name].append(vals[v])

        if (sample_idx + 1) % max(1, num_samples // 4) == 0:
            print(f"  Progress: {sample_idx + 1}/{num_samples}")

    total = num_samples
    print(f"\n{'metric':<22}  {'max_acc':>7}  {'min_acc':>7}  {'best':>5}  {'cohen_d':>8}  {'direction':>10}")
    print("-" * 70)

    rows = []
    for name in metric_names:
        max_acc = max_correct[name] / total
        min_acc = min_correct[name] / total
        best_acc = max(max_acc, min_acc)
        best_dir = "max" if max_acc >= min_acc else "min"
        d = cohen_d(winner_vals[name], loser_vals[name])

        # Direction of effect: do winners have higher or lower values?
        w_mean = sum(winner_vals[name]) / len(winner_vals[name]) if winner_vals[name] else 0
        l_mean = sum(loser_vals[name]) / len(loser_vals[name]) if loser_vals[name] else 0
        effect_dir = "higher" if w_mean > l_mean else "lower"

        rows.append((name, max_acc, min_acc, best_acc, best_dir, d, effect_dir))

    # Sort by best accuracy descending
    rows.sort(key=lambda r: r[3], reverse=True)

    for (name, max_acc, min_acc, best_acc, best_dir, d, effect_dir) in rows:
        print(f"{name:<22}  {max_acc:>6.1%}  {min_acc:>6.1%}  {best_dir:>5}  {d:>8.3f}  {effect_dir:>10}")

    print()
    print(f"Top 3 metrics by best accuracy:")
    for i, (name, max_acc, min_acc, best_acc, best_dir, d, effect_dir) in enumerate(rows[:3]):
        print(f"  {i+1}. {name} ({best_dir}) -> {best_acc:.1%}  [Cohen's d = {d:.3f}, winners are {effect_dir}]")


def main():
    random.seed(42)
    print("Deep metric search for temporal hub prediction")
    print("Testing new metrics: inversion density, transitivity, anti-chain,")
    print("complementary density, coverage matrix, signed coverage, gap structure, composites")

    configs = [
        (5, 10000),
        (6, 3000),
        (7, 1000),
    ]

    for n, num_samples in configs:
        run(n, num_samples)


if __name__ == "__main__":
    main()
