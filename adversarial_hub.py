"""
Adversarial hub metric analysis.

For each k in {4,5,6,7}, generate random k-vertex temporal cliques.
For each instance:
  1. Find ALL valid hubs (brute force)
  2. For each of the 10 metrics from hub_fingerprint.py, check if the
     metric's "best" vertex is a valid hub
  3. Track fooling rates and find instances where ALL metrics fail simultaneously.

Goal: prove no single local metric works as a greedy hub selector.
"""

import random
import statistics
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


def star_tree_spans(n, edges, timestamps, hub):
    """Check if hub + greedy tree edges can span the temporal clique."""
    m = len(edges)
    timed = sorted([(timestamps[i], edges[i][0], edges[i][1]) for i in range(m)])
    target = compute_reachability(n, timed)

    star_idx = [i for i, (u, v) in enumerate(edges) if u == hub or v == hub]
    tree_candidates = [i for i in range(m) if i not in set(star_idx)]

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
    """Compute 10 metrics for vertex v. Returns dict of metric_name -> value."""
    edge_map = {}
    for i, (u, w) in enumerate(edges):
        edge_map[(u, w)] = timestamps[i]
        edge_map[(w, u)] = timestamps[i]

    incident_times = sorted([edge_map[(v, u)] for u in range(n) if u != v])
    m = len(edges)

    avg_time = sum(incident_times) / len(incident_times)
    med_time = statistics.median(incident_times)
    spread = max(incident_times) - min(incident_times)
    has_min = 1 if min(incident_times) == 1 else 0
    has_max = 1 if max(incident_times) == m else 0

    others = [u for u in range(n) if u != v]
    forward = 0
    for a in others:
        for b in others:
            if a != b and edge_map[(a, v)] <= edge_map[(v, b)]:
                forward += 1
    total_pairs = (n - 1) * (n - 2)
    balance = abs(forward - total_pairs / 2) / (total_pairs / 2) if total_pairs > 0 else 0

    inversions = 0
    for i in range(len(incident_times)):
        for j in range(i + 1, len(incident_times)):
            if incident_times[i] > incident_times[j]:
                inversions += 1
    max_inv = len(incident_times) * (len(incident_times) - 1) // 2
    inv_ratio = inversions / max_inv if max_inv > 0 else 0

    variance = statistics.variance(incident_times) if len(incident_times) > 1 else 0

    all_sums = []
    for u in range(n):
        s = sum(edge_map[(u, w)] for w in range(n) if w != u)
        all_sums.append((s, u))
    all_sums.sort()
    rank = next(i for i, (_, u) in enumerate(all_sums) if u == v)
    norm_rank = rank / (n - 1) if n > 1 else 0

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


# For each metric, define whether the "natural" best pick is argmax or argmin
# avg_time: middle is best? Try both. But "natural" for a hub = central = median rank
# We test BOTH argmax and argmin for each metric and report the better one.
METRIC_DIRECTIONS = {
    'avg_time': ['min', 'max'],       # low avg = early edges, high avg = late edges
    'med_time': ['min', 'max'],       # same
    'spread': ['max', 'min'],         # high spread = touches extremes
    'has_min': ['max'],               # 1 = has earliest edge
    'has_max': ['max'],               # 1 = has latest edge
    'forward': ['max', 'min'],        # max forward pairs = good relay
    'balance': ['min', 'max'],        # low balance = balanced
    'inv_ratio': ['min', 'max'],      # low inversions = ordered
    'variance': ['max', 'min'],       # high variance = spread
    'norm_rank': ['min', 'max'],      # low rank = low timestamp sum
}


def best_vertex_by_metric(metric_values, direction):
    """Given {vertex: value} dict and direction, return the 'best' vertex."""
    if direction == 'max':
        return max(metric_values, key=metric_values.get)
    else:
        return min(metric_values, key=metric_values.get)


def run(n, num_samples):
    edges = make_edges(n)
    m = len(edges)
    print(f"\n{'='*70}")
    print(f"K_{n}: {n} vertices, {m} edges, {num_samples} samples")
    print(f"{'='*70}")

    # For each metric+direction combo, track: how often its pick is a valid hub
    metric_dir_combos = []
    for metric, dirs in METRIC_DIRECTIONS.items():
        for d in dirs:
            metric_dir_combos.append((metric, d))

    success_count = {combo: 0 for combo in metric_dir_combos}
    total_with_valid_hub = 0
    all_fail_count = 0  # instances where EVERY metric's best pick fails
    no_hub_count = 0    # instances where NO vertex is a valid hub

    # Track the "best direction" per metric (we'll report the better one)
    for sample_idx in range(num_samples):
        ts = list(range(1, m + 1))
        random.shuffle(ts)

        # Find all valid hubs
        valid_hubs = set()
        for v in range(n):
            if star_tree_spans(n, edges, ts, v):
                valid_hubs.add(v)

        if not valid_hubs:
            no_hub_count += 1
            continue

        total_with_valid_hub += 1

        # Compute metrics for all vertices
        all_metrics = {}
        for v in range(n):
            all_metrics[v] = vertex_metrics(n, edges, ts, v)

        # For each metric+direction, check if best pick is valid
        any_combo_works = False
        for combo in metric_dir_combos:
            metric, direction = combo
            metric_vals = {v: all_metrics[v][metric] for v in range(n)}
            pick = best_vertex_by_metric(metric_vals, direction)
            if pick in valid_hubs:
                success_count[combo] += 1
                any_combo_works = True

        if not any_combo_works:
            all_fail_count += 1
            if all_fail_count <= 3:
                print(f"\n  ALL-FAIL instance #{all_fail_count} (sample {sample_idx}):")
                print(f"    Valid hubs: {sorted(valid_hubs)}")
                for combo in metric_dir_combos:
                    metric, direction = combo
                    metric_vals = {v: all_metrics[v][metric] for v in range(n)}
                    pick = best_vertex_by_metric(metric_vals, direction)
                    print(f"    {metric:>12s} ({direction:>3s}) -> vertex {pick} "
                          f"(value={all_metrics[pick][metric]:.3f})")

        if (sample_idx + 1) % max(1, num_samples // 5) == 0:
            print(f"  ... {sample_idx + 1}/{num_samples} done")

    # Report
    print(f"\nInstances with NO valid hub: {no_hub_count}/{num_samples} "
          f"({100*no_hub_count/num_samples:.1f}%)")
    print(f"Instances with >= 1 valid hub: {total_with_valid_hub}/{num_samples}")

    if total_with_valid_hub == 0:
        print("  No valid hub instances to analyze.")
        return

    print(f"\nInstances where ALL metrics' picks fail simultaneously: "
          f"{all_fail_count}/{total_with_valid_hub} "
          f"({100*all_fail_count/total_with_valid_hub:.1f}%)")

    print(f"\n{'Metric':<15s} {'Dir':>4s} {'Success':>8s} {'Total':>7s} "
          f"{'Success%':>9s} {'Fool%':>7s}")
    print("-" * 55)

    # Group by metric, report best direction
    for metric in METRIC_DIRECTIONS:
        best_rate = -1
        best_combo = None
        for d in METRIC_DIRECTIONS[metric]:
            combo = (metric, d)
            rate = success_count[combo] / total_with_valid_hub if total_with_valid_hub > 0 else 0
            if rate > best_rate:
                best_rate = rate
                best_combo = combo

        for d in METRIC_DIRECTIONS[metric]:
            combo = (metric, d)
            succ = success_count[combo]
            rate = succ / total_with_valid_hub if total_with_valid_hub > 0 else 0
            fool = 1 - rate
            marker = " <-- best" if combo == best_combo else ""
            print(f"{metric:<15s} {d:>4s} {succ:>8d} {total_with_valid_hub:>7d} "
                  f"{100*rate:>8.1f}% {100*fool:>6.1f}%{marker}")

    # Summary: best achievable per metric
    print(f"\nSummary — best success rate per metric:")
    print(f"{'Metric':<15s} {'Best Dir':>8s} {'Success%':>9s} {'Fool%':>7s}")
    print("-" * 42)
    for metric in METRIC_DIRECTIONS:
        best_rate = -1
        best_dir = None
        for d in METRIC_DIRECTIONS[metric]:
            combo = (metric, d)
            rate = success_count[combo] / total_with_valid_hub if total_with_valid_hub > 0 else 0
            if rate > best_rate:
                best_rate = rate
                best_dir = d
        fool = 1 - best_rate
        print(f"{metric:<15s} {best_dir:>8s} {100*best_rate:>8.1f}% {100*fool:>6.1f}%")


def main():
    random.seed(42)
    configs = {
        4: 10000,
        5: 5000,
        6: 1000,
        7: 200,  # star_tree_spans is expensive at n=7
    }
    for n, samples in sorted(configs.items()):
        run(n, samples)

    print("\n" + "=" * 70)
    print("CONCLUSION")
    print("=" * 70)
    print("If all metrics have fool rate > 30% and 'all-fail' instances exist,")
    print("no single local metric works as a greedy hub selector.")
    print("If any metric has success rate > 90%, it's a viable greedy criterion.")


if __name__ == "__main__":
    main()
