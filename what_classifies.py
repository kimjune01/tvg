"""
What property GUARANTEES a hub works?

For each vertex in each instance, compute every metric we have.
Then: find the property (or combination) that perfectly separates
working hubs from failing hubs.

If no single property works, find the minimal set that does.
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


def exhaustive_hub_works(n, edges, timestamps, hub):
    m = len(edges)
    timed = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in range(m)])
    target = compute_reachability(n, timed)
    star_idx = set(i for i, (u, v) in enumerate(edges) if u == hub or v == hub)
    tree_candidates = [i for i in range(m) if i not in star_idx]
    for subset in combinations(tree_candidates, n - 2):
        used = star_idx | set(subset)
        sub = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in used])
        if compute_reachability(n, sub) == target:
            return True
    return False


def all_vertex_metrics(n, edges, timestamps, v):
    m = len(edges)
    edge_map = {}
    for i, (u, w) in enumerate(edges):
        edge_map[(u, w)] = timestamps[i]
        edge_map[(w, u)] = timestamps[i]

    times = sorted([edge_map[(v, u)] for u in range(n) if u != v])
    k = len(times)

    # Max run
    ordered = sorted(range(m), key=lambda i: timestamps[i])
    involves_v = [(edges[i][0] == v or edges[i][1] == v) for i in ordered]
    max_run = cur = 0
    for b in involves_v:
        if b: cur += 1; max_run = max(max_run, cur)
        else: cur = 0

    # Span
    positions = [j for j, b in enumerate(involves_v) if b]
    span = positions[-1] - positions[0] + 1

    # Spread
    spread = times[-1] - times[0]

    # Gaps
    gaps = [times[i+1] - times[i] for i in range(k-1)]
    max_gap = max(gaps) if gaps else 0

    # How many reverse pairs does this hub create?
    others = [u for u in range(n) if u != v]
    reverse_count = 0
    for a in others:
        for b in others:
            if a != b and edge_map[(a, v)] > edge_map[(v, b)]:
                reverse_count += 1
    total_directed = (n-1) * (n-2)

    # Interleaving
    foreign_in_span = span - k
    interleaving = foreign_in_span / span if span > 0 else 0

    # Number of non-hub edges with timestamps INSIDE the star range
    star_min, star_max = times[0], times[-1]
    non_hub_inside = 0
    non_hub_total = 0
    for i in range(m):
        u, w = edges[i]
        if u != v and w != v:
            non_hub_total += 1
            if star_min <= timestamps[i] <= star_max:
                non_hub_inside += 1
    non_hub_inside_frac = non_hub_inside / non_hub_total if non_hub_total > 0 else 0

    # Composition potential: for how many pairs (a,b) where star fails,
    # does there exist c where t(a,v) ≤ t(v,c) AND t(c,v) ≤ t(v,b)?
    # (This is steep-in or steep-out availability)
    steep_available = 0
    for a in others:
        for b in others:
            if a != b and edge_map[(a, v)] > edge_map[(v, b)]:
                # Reverse pair. Check steep-in: ∃c with t(a,v) ≤ t(v,c)?
                has_steep_in = any(
                    edge_map[(v, c)] >= edge_map[(a, v)]
                    for c in others if c != a and c != b
                )
                # Check steep-out: ∃c with t(c,v) ≤ t(v,b)?
                has_steep_out = any(
                    edge_map[(c, v)] <= edge_map[(v, b)]
                    for c in others if c != a and c != b
                )
                if has_steep_in or has_steep_out:
                    steep_available += 1

    steep_frac = steep_available / reverse_count if reverse_count > 0 else 1.0

    return {
        'max_run': max_run,
        'span': span,
        'spread': spread,
        'max_gap': max_gap,
        'interleaving': interleaving,
        'reverse_count': reverse_count,
        'reverse_frac': reverse_count / total_directed,
        'non_hub_inside_frac': non_hub_inside_frac,
        'steep_frac': steep_frac,
    }


def run(n, num_samples):
    edges = make_edges(n)
    m = len(edges)
    print(f"\nK_{n}: {n} vertices, {m} edges")
    print("=" * 70)

    # Collect all (metrics, ok) pairs
    data = []

    for trial in range(num_samples):
        ts = list(range(1, m + 1))
        random.shuffle(ts)

        for v in range(n):
            ok = exhaustive_hub_works(n, edges, ts, v)
            metrics = all_vertex_metrics(n, edges, ts, v)
            data.append((metrics, ok))

        if (trial + 1) % max(1, num_samples // 5) == 0:
            print(f"  {trial+1}/{num_samples}")

    # For each metric, find the threshold that best separates ok/fail
    metric_names = list(data[0][0].keys())
    ok_data = [d for d in data if d[1]]
    fail_data = [d for d in data if not d[1]]

    print(f"\nTotal: {len(ok_data)} working, {len(fail_data)} failing")

    print(f"\nPer-metric: can any threshold perfectly separate?")
    print(f"{'metric':>25s}  {'best_thresh':>12s}  {'FP':>5s}  {'FN':>5s}  "
          f"{'accuracy':>9s}  {'direction':>10s}")
    print("-" * 75)

    for name in metric_names:
        ok_vals = sorted(set(d[0][name] for d in ok_data))
        fail_vals = sorted(set(d[0][name] for d in fail_data))

        # Try thresholds: pick vertex if metric ≤ threshold (min direction)
        best_acc = 0
        best_thresh = 0
        best_fp = 0
        best_fn = 0
        best_dir = 'min'

        all_vals = sorted(set(d[0][name] for d in data))
        for thresh in all_vals:
            # Direction: ok if metric ≤ thresh
            tp = sum(1 for d in ok_data if d[0][name] <= thresh)
            fp = sum(1 for d in fail_data if d[0][name] <= thresh)
            fn = sum(1 for d in ok_data if d[0][name] > thresh)
            tn = sum(1 for d in fail_data if d[0][name] > thresh)
            acc = (tp + tn) / len(data)
            if acc > best_acc:
                best_acc = acc
                best_thresh = thresh
                best_fp = fp
                best_fn = fn
                best_dir = 'min'

            # Direction: ok if metric ≥ thresh
            tp2 = sum(1 for d in ok_data if d[0][name] >= thresh)
            fp2 = sum(1 for d in fail_data if d[0][name] >= thresh)
            fn2 = sum(1 for d in ok_data if d[0][name] < thresh)
            tn2 = sum(1 for d in fail_data if d[0][name] < thresh)
            acc2 = (tp2 + tn2) / len(data)
            if acc2 > best_acc:
                best_acc = acc2
                best_thresh = thresh
                best_fp = fp2
                best_fn = fn2
                best_dir = 'max'

        print(f"{name:>25s}  {best_thresh:>12.3f}  {best_fp:>5d}  {best_fn:>5d}  "
              f"{best_acc:>9.4f}  {best_dir:>10s}")

    # Check: is steep_frac = 1.0 a guarantee?
    steep_perfect = sum(1 for d in data if d[0]['steep_frac'] == 1.0 and d[1])
    steep_perfect_fail = sum(1 for d in data if d[0]['steep_frac'] == 1.0 and not d[1])
    steep_imperfect_ok = sum(1 for d in data if d[0]['steep_frac'] < 1.0 and d[1])
    steep_imperfect_fail = sum(1 for d in data if d[0]['steep_frac'] < 1.0 and not d[1])

    print(f"\nSteep availability analysis:")
    print(f"  steep_frac=1.0: {steep_perfect} ok, {steep_perfect_fail} fail")
    print(f"  steep_frac<1.0: {steep_imperfect_ok} ok, {steep_imperfect_fail} fail")

    # Reverse fraction analysis
    print(f"\nReverse fraction distribution:")
    for d_list, label in [(ok_data, 'working'), (fail_data, 'failing')]:
        vals = [d[0]['reverse_frac'] for d in d_list]
        if vals:
            print(f"  {label}: min={min(vals):.3f} avg={sum(vals)/len(vals):.3f} max={max(vals):.3f}")


def main():
    random.seed(42)
    for n, samples in [(5, 2000), (6, 300)]:
        run(n, samples)


if __name__ == "__main__":
    main()
