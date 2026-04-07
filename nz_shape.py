"""
N-shape vs Z-shape classification of temporal cliques.

Order vertices by average incident timestamp (v_1 earliest, v_n latest).
Look at the timestamp matrix M[v_i][v_j] in this ordering.

Z-shape: M[i][j] is small when |i-j| is large (extremes connected early).
         Correlation between |i-j| and M[i][j] is NEGATIVE.
N-shape: M[i][j] is small when |i-j| is small (neighbors connected early).
         Correlation between |i-j| and M[i][j] is POSITIVE.

The claim: Z-shaped instances need an extreme hub (min or max rank),
N-shaped instances need a middle hub. The shape determines which search.
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


def nz_score(n, edges, timestamps):
    """
    Compute the N/Z shape score.

    Order vertices by average incident timestamp.
    Score = correlation between vertex-distance |rank_i - rank_j|
    and timestamp M[i][j].

    Positive = N-shape (nearby vertices connected early)
    Negative = Z-shape (distant vertices connected early)
    """
    m = len(edges)
    edge_map = {}
    for i, (u, v) in enumerate(edges):
        edge_map[(u, v)] = timestamps[i]
        edge_map[(v, u)] = timestamps[i]

    # Order vertices by average timestamp
    avg_times = []
    for v in range(n):
        avg = sum(edge_map[(v, u)] for u in range(n) if u != v) / (n - 1)
        avg_times.append((avg, v))
    avg_times.sort()
    rank = {v: i for i, (_, v) in enumerate(avg_times)}

    # Compute correlation between |rank_i - rank_j| and M[i][j]
    distances = []
    times = []
    for i, (u, v) in enumerate(edges):
        d = abs(rank[u] - rank[v])
        distances.append(d)
        times.append(timestamps[i])

    # Pearson correlation
    n_edges = len(distances)
    mean_d = sum(distances) / n_edges
    mean_t = sum(times) / n_edges
    cov = sum((d - mean_d) * (t - mean_t) for d, t in zip(distances, times)) / n_edges
    std_d = (sum((d - mean_d)**2 for d in distances) / n_edges) ** 0.5
    std_t = (sum((t - mean_t)**2 for t in times) / n_edges) ** 0.5

    if std_d == 0 or std_t == 0:
        return 0.0

    return cov / (std_d * std_t)


def winner_rank_position(n, edges, timestamps):
    """Where do winning hubs sit in the vertex ordering?
    Returns normalized rank positions of all working hubs."""
    edge_map = {}
    for i, (u, v) in enumerate(edges):
        edge_map[(u, v)] = timestamps[i]
        edge_map[(v, u)] = timestamps[i]

    avg_times = []
    for v in range(n):
        avg = sum(edge_map[(v, u)] for u in range(n) if u != v) / (n - 1)
        avg_times.append((avg, v))
    avg_times.sort()
    rank = {v: i for i, (_, v) in enumerate(avg_times)}

    winners = []
    for v in range(n):
        if star_tree_spans(n, edges, timestamps, v):
            winners.append(rank[v] / (n - 1))  # normalized: 0=earliest, 1=latest

    return winners


def run(n, num_samples):
    edges = make_edges(n)
    m = len(edges)
    print(f"\nK_{n}: {n} vertices, {m} edges")
    print("=" * 70)

    # Bin instances by NZ score
    bins = {'strong_Z': [], 'mild_Z': [], 'neutral': [], 'mild_N': [], 'strong_N': []}

    def classify(score):
        if score < -0.3: return 'strong_Z'
        if score < -0.1: return 'mild_Z'
        if score < 0.1: return 'neutral'
        if score < 0.3: return 'mild_N'
        return 'strong_N'

    # For each instance: NZ score, winning hub positions, which search works
    all_data = []
    for _ in range(num_samples):
        ts = list(range(1, m + 1))
        random.shuffle(ts)

        score = nz_score(n, edges, ts)
        winner_ranks = winner_rank_position(n, edges, ts)
        cat = classify(score)
        bins[cat].append(winner_ranks)
        all_data.append((score, winner_ranks))

    # For each bin, show distribution of winning hub ranks
    print(f"\nWinning hub rank positions by NZ shape:")
    print(f"{'shape':>10s}  {'count':>6s}  {'avg_rank':>9s}  {'min_rank':>9s}  "
          f"{'max_rank':>9s}  {'prefer':>10s}")
    print("-" * 65)
    for cat in ['strong_Z', 'mild_Z', 'neutral', 'mild_N', 'strong_N']:
        data = bins[cat]
        if not data:
            print(f"{cat:>10s}  {'(none)':>6s}")
            continue
        all_ranks = [r for ranks in data for r in ranks]
        avg = sum(all_ranks) / len(all_ranks)
        mn = min(all_ranks)
        mx = max(all_ranks)

        # What fraction of winners are extreme (rank < 0.2 or > 0.8)?
        extreme = sum(1 for r in all_ranks if r < 0.2 or r > 0.8) / len(all_ranks)
        middle = sum(1 for r in all_ranks if 0.3 <= r <= 0.7) / len(all_ranks)
        prefer = "extreme" if extreme > middle else "middle" if middle > extreme else "mixed"

        print(f"{cat:>10s}  {len(data):>6d}  {avg:>9.3f}  {mn:>9.3f}  "
              f"{mx:>9.3f}  {prefer:>10s} (ext={extreme:.1%} mid={middle:.1%})")

    # Test the if-statement: NZ score determines search
    print(f"\nIf-statement test:")
    print(f"  Z-shaped (score < 0): pick extreme vertex (rank 0 or n-1)")
    print(f"  N-shaped (score > 0): pick middle vertex (rank n//2)")

    for threshold in [0.0, -0.1, -0.2, 0.1, 0.2]:
        success = 0
        for score, winner_ranks in all_data:
            if score < threshold:
                # Z-shaped: try extremes (rank 0.0 or 1.0)
                # Does extreme vertex work?
                target_ranks = [0.0, 1.0]
            else:
                # N-shaped: try middle
                target_ranks = [0.5] if n % 2 == 1 else [0.5 - 0.5/(n-1), 0.5 + 0.5/(n-1)]

            # Check if any winner is close to target
            for wr in winner_ranks:
                for tr in target_ranks:
                    if abs(wr - tr) <= 1.0 / (n - 1) + 0.01:
                        success += 1
                        break
                else:
                    continue
                break

        print(f"  threshold={threshold:+.1f}: {success}/{num_samples} "
              f"({success/num_samples*100:.1f}%)")

    # Scatter: NZ score vs winning hub rank (for visualization)
    print(f"\nNZ score vs winner rank (sampled):")
    print(f"  {'nz_score':>8s}  {'winner_ranks':>30s}")
    sample = sorted(all_data, key=lambda x: x[0])
    step = max(1, len(sample) // 20)
    for i in range(0, len(sample), step):
        score, ranks = sample[i]
        rank_str = ', '.join(f'{r:.2f}' for r in sorted(ranks))
        print(f"  {score:>+8.3f}  [{rank_str}]")


def main():
    random.seed(42)
    for n, samples in [(5, 10000), (6, 3000), (7, 1000), (8, 300)]:
        run(n, samples)


if __name__ == "__main__":
    main()
