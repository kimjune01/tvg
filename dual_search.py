"""
Dual search: try min(span) first, then max(span).
Also try: min(interleaving) then max(interleaving).
And: min(span) then max(max_run).

The algorithm exhausts both extremes. The proof is that one always works.
"""

import random
import statistics


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


def vertex_run_metrics(n, edges, timestamps, v):
    m = len(edges)
    ordered = sorted(range(m), key=lambda i: timestamps[i])
    involves_v = [(edges[i][0] == v or edges[i][1] == v) for i in ordered]

    # Span
    positions = [j for j, b in enumerate(involves_v) if b]
    span = positions[-1] - positions[0] + 1 if positions else 0

    # Interleaving
    foreign_in_span = span - len(positions) if span > 0 else 0
    interleaving = foreign_in_span / span if span > 0 else 0

    # Max run
    max_run = 0
    cur = 0
    for b in involves_v:
        if b:
            cur += 1
            max_run = max(max_run, cur)
        else:
            cur = 0

    # Max gap between consecutive v-edges
    gaps = [positions[i+1] - positions[i] - 1 for i in range(len(positions)-1)] if len(positions) > 1 else [0]
    max_gap = max(gaps) if gaps else 0

    return {
        'span': span,
        'interleaving': interleaving,
        'max_run': max_run,
        'max_gap': max_gap,
    }


def test_strategy(n, edges, num_samples, pick_first, pick_second, name):
    """Test a dual search: try pick_first, then pick_second."""
    success_1 = 0
    success_2_only = 0
    fail_both = 0

    for _ in range(num_samples):
        ts = list(range(1, len(edges) + 1))
        random.shuffle(ts)

        metrics = {}
        hub_ok = {}
        for v in range(n):
            metrics[v] = vertex_run_metrics(n, edges, ts, v)
            hub_ok[v] = star_tree_spans(n, edges, ts, v)

        v1 = pick_first(metrics)
        v2 = pick_second(metrics)

        if hub_ok[v1]:
            success_1 += 1
        elif hub_ok[v2]:
            success_2_only += 1
        else:
            fail_both += 1

    total = num_samples
    combined = success_1 + success_2_only
    print(f"  {name:>35s}: 1st={success_1/total*100:.1f}%  "
          f"2nd_only={success_2_only/total*100:.1f}%  "
          f"combined={combined/total*100:.1f}%  "
          f"fail={fail_both/total*100:.2f}%")
    return fail_both


def run(n, num_samples):
    edges = make_edges(n)
    m = len(edges)
    print(f"\nK_{n}: {n} vertices, {m} edges")
    print("=" * 70)

    strategies = [
        (lambda m: min(m, key=lambda v: m[v]['span']),
         lambda m: max(m, key=lambda v: m[v]['span']),
         "min_span → max_span"),

        (lambda m: min(m, key=lambda v: m[v]['interleaving']),
         lambda m: max(m, key=lambda v: m[v]['interleaving']),
         "min_interleave → max_interleave"),

        (lambda m: min(m, key=lambda v: m[v]['span']),
         lambda m: max(m, key=lambda v: m[v]['max_run']),
         "min_span → max_run"),

        (lambda m: min(m, key=lambda v: m[v]['max_gap']),
         lambda m: max(m, key=lambda v: m[v]['max_gap']),
         "min_gap → max_gap"),

        (lambda m: min(m, key=lambda v: m[v]['span']),
         lambda m: min(m, key=lambda v: m[v]['max_gap']),
         "min_span → min_gap"),

        # Opposite extremes of interleaving
        (lambda m: min(m, key=lambda v: m[v]['interleaving']),
         lambda m: max(m, key=lambda v: m[v]['max_run']),
         "min_interleave → max_run"),

        # Try ALL vertices sorted by span (what's the max attempts needed?)
        # Just test: min span, then 2nd-min, then 3rd-min...
    ]

    for pick1, pick2, name in strategies:
        test_strategy(n, edges, num_samples, pick1, pick2, name)

    # Also: exhaustive sorted order — how many attempts before success?
    print(f"\n  Exhaustive search (sorted by span, ascending):")
    attempt_hist = {}
    for _ in range(num_samples):
        ts = list(range(1, m + 1))
        random.shuffle(ts)
        metrics = {}
        for v in range(n):
            metrics[v] = vertex_run_metrics(n, edges, ts, v)
        order = sorted(range(n), key=lambda v: metrics[v]['span'])
        for attempt, v in enumerate(order, 1):
            if star_tree_spans(n, edges, ts, v):
                attempt_hist[attempt] = attempt_hist.get(attempt, 0) + 1
                break
        else:
            attempt_hist[n + 1] = attempt_hist.get(n + 1, 0) + 1  # all failed

    cumulative = 0
    for k in sorted(attempt_hist):
        cumulative += attempt_hist[k]
        pct = cumulative / num_samples * 100
        label = f"attempt {k}" if k <= n else "all fail"
        print(f"    {label}: {attempt_hist[k]:>5d} ({pct:.1f}% cumulative)")

    # Same but sorted by interleaving
    print(f"\n  Exhaustive search (sorted by interleaving, ascending):")
    attempt_hist2 = {}
    for _ in range(num_samples):
        ts = list(range(1, m + 1))
        random.shuffle(ts)
        metrics = {}
        for v in range(n):
            metrics[v] = vertex_run_metrics(n, edges, ts, v)
        order = sorted(range(n), key=lambda v: metrics[v]['interleaving'])
        for attempt, v in enumerate(order, 1):
            if star_tree_spans(n, edges, ts, v):
                attempt_hist2[attempt] = attempt_hist2.get(attempt, 0) + 1
                break
        else:
            attempt_hist2[n + 1] = attempt_hist2.get(n + 1, 0) + 1

    cumulative = 0
    for k in sorted(attempt_hist2):
        cumulative += attempt_hist2[k]
        pct = cumulative / num_samples * 100
        label = f"attempt {k}" if k <= n else "all fail"
        print(f"    {label}: {attempt_hist2[k]:>5d} ({pct:.1f}% cumulative)")


def main():
    random.seed(42)
    for n, samples in [(5, 10000), (6, 3000), (7, 1000), (8, 300)]:
        run(n, samples)


if __name__ == "__main__":
    main()
