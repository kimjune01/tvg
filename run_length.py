"""
Run-length analysis for hub selection.

A "run" for vertex v: count consecutive timestamps in the global
edge ordering where v is an endpoint.

max_run(v) = longest consecutive streak of v's edges in timestamp order.

If edges are ordered by time: e1, e2, ..., em
Run for v = maximal contiguous block where v ∈ e_i for all i in block.

Balanced vertex: long max-run (edges bunched together in time)
Extreme vertex: short max-run (edges spread out, interleaved)

Hypothesis: max_run predicts hub success.
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


def run_metrics(n, edges, timestamps, v):
    """Compute run-length metrics for vertex v."""
    m = len(edges)
    # Order edges by timestamp
    ordered = sorted(range(m), key=lambda i: timestamps[i])

    # Which edges involve v?
    involves_v = [1 if (edges[i][0] == v or edges[i][1] == v) else 0 for i in ordered]

    # Max run: longest consecutive 1s
    max_run = 0
    current_run = 0
    for bit in involves_v:
        if bit:
            current_run += 1
            max_run = max(max_run, current_run)
        else:
            current_run = 0

    # Total runs: number of contiguous blocks of 1s
    num_runs = 0
    in_run = False
    for bit in involves_v:
        if bit and not in_run:
            num_runs += 1
            in_run = True
        elif not bit:
            in_run = False

    # Run lengths list
    run_lengths = []
    current_run = 0
    for bit in involves_v:
        if bit:
            current_run += 1
        else:
            if current_run > 0:
                run_lengths.append(current_run)
            current_run = 0
    if current_run > 0:
        run_lengths.append(current_run)

    avg_run = sum(run_lengths) / len(run_lengths) if run_lengths else 0

    # Gap lengths (consecutive 0s between runs)
    gap_lengths = []
    current_gap = 0
    in_gap = False
    started = False
    for bit in involves_v:
        if bit:
            if in_gap and started:
                gap_lengths.append(current_gap)
            current_gap = 0
            in_gap = False
            started = True
        else:
            if started:
                current_gap += 1
                in_gap = True
    max_gap = max(gap_lengths) if gap_lengths else 0
    avg_gap = sum(gap_lengths) / len(gap_lengths) if gap_lengths else 0

    # Degree: number of edges involving v
    degree = sum(involves_v)  # always n-1

    # Coverage density: degree / m (fraction of edges involving v)
    density = degree / m

    # Interleaving: how many OTHER vertices' edges appear between
    # v's first and last edge? (lower = more bunched)
    first_pos = involves_v.index(1)
    last_pos = len(involves_v) - 1 - involves_v[::-1].index(1)
    span = last_pos - first_pos + 1
    foreign_in_span = span - degree
    interleaving = foreign_in_span / span if span > 0 else 0

    return {
        'max_run': max_run,
        'num_runs': num_runs,
        'avg_run': avg_run,
        'max_gap': max_gap,
        'avg_gap': avg_gap,
        'interleaving': interleaving,
        'span': span,
    }


def run(n, num_samples):
    edges = make_edges(n)
    m = len(edges)
    print(f"\nK_{n}: {n} vertices, {m} edges, degree={n-1}")
    print("=" * 70)

    metrics_names = ['max_run', 'num_runs', 'avg_run', 'max_gap', 'avg_gap',
                     'interleaving', 'span']

    winner_data = {k: [] for k in metrics_names}
    loser_data = {k: [] for k in metrics_names}

    for _ in range(num_samples):
        ts = list(range(1, m + 1))
        random.shuffle(ts)

        for v in range(n):
            ok = star_tree_spans(n, edges, ts, v)
            metrics = run_metrics(n, edges, ts, v)
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

    # Prediction accuracy
    print(f"\nPrediction accuracy (pick vertex by metric):")
    for k in metrics_names:
        correct_max = 0
        correct_min = 0
        total = 0
        for _ in range(min(num_samples, 3000)):
            ts = list(range(1, m + 1))
            random.shuffle(ts)
            scores = []
            for v in range(n):
                ok = star_tree_spans(n, edges, ts, v)
                metrics = run_metrics(n, edges, ts, v)
                scores.append((metrics[k], v, ok))
            total += 1
            if sorted(scores, key=lambda x: -x[0])[0][2]:
                correct_max += 1
            if sorted(scores, key=lambda x: x[0])[0][2]:
                correct_min += 1
        print(f"  {k:>15s}: max={correct_max/total*100:.1f}%  min={correct_min/total*100:.1f}%")

    # Combined: max_run as primary, interleaving as secondary
    print(f"\nCombined metric test (max_run + interleaving):")
    correct = 0
    total_test = 0
    for _ in range(min(num_samples, 3000)):
        ts = list(range(1, m + 1))
        random.shuffle(ts)
        scores = []
        for v in range(n):
            ok = star_tree_spans(n, edges, ts, v)
            metrics = run_metrics(n, edges, ts, v)
            # Low max_run + low interleaving = compact, uninterleaved
            scores.append((-metrics['max_run'], metrics['interleaving'], v, ok))
        total_test += 1
        # Sort by combined: min max_run first, then min interleaving
        best = sorted(scores)[0]
        if best[3]:
            correct += 1
    print(f"  min(max_run, interleaving): {correct/total_test*100:.1f}%")

    # And: min span
    correct2 = 0
    for _ in range(min(num_samples, 3000)):
        ts = list(range(1, m + 1))
        random.shuffle(ts)
        scores = []
        for v in range(n):
            ok = star_tree_spans(n, edges, ts, v)
            metrics = run_metrics(n, edges, ts, v)
            scores.append((metrics['span'], v, ok))
        # Min span
        if sorted(scores)[0][2]:
            correct2 += 1
    print(f"  min(span): {correct2/min(num_samples, 3000)*100:.1f}%")


def main():
    random.seed(42)
    for n, samples in [(5, 5000), (6, 2000), (7, 700)]:
        run(n, samples)


if __name__ == "__main__":
    main()
