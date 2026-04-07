"""
Anatomy of hub failures.

When star(v) + greedy tree fails, exactly which pairs are uncovered?
What's the structure of those pairs relative to v's timestamp ordering?

Also: when ALL vertices fail as hub, what does the instance look like?
(This should never happen — ≥2 hubs always exist. But let's verify and
understand the hardest instances where only 2 hubs work.)
"""

import random
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


def star_tree_spans_detail(n, edges, timestamps, hub):
    """Returns (ok, uncovered_pairs, edges_used)."""
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

    final = current_reach()
    uncovered = []
    for src in range(n):
        diff = target[src] ^ final[src]
        for dst in range(n):
            if diff & (1 << dst):
                uncovered.append((src, dst))
    return final == target, uncovered, current


def run(n, num_samples):
    edges = make_edges(n)
    m = len(edges)
    edge_map_template = {}
    for i, (u, v) in enumerate(edges):
        edge_map_template[(u, v)] = i
        edge_map_template[(v, u)] = i

    print(f"\nK_{n}: {n} vertices, {m} edges")
    print("=" * 70)

    num_winners_dist = Counter()
    hardest_instances = []  # (num_winners, ts, winner_list)

    # When a hub fails, where do uncovered pairs sit?
    # Relative to v's timestamp ordering of neighbors
    uncov_position_counts = Counter()  # (rank_a, rank_b) relative to hub
    total_uncov = 0

    # When exactly 2 hubs work, what's special about them?
    two_winner_data = []

    for trial in range(num_samples):
        ts = list(range(1, m + 1))
        random.shuffle(ts)

        edge_map = {}
        for i, (u, v) in enumerate(edges):
            edge_map[(u, v)] = ts[i]
            edge_map[(v, u)] = ts[i]

        results = {}
        winners = []
        for v in range(n):
            ok, uncov, used = star_tree_spans_detail(n, edges, ts, v)
            results[v] = (ok, uncov)
            if ok:
                winners.append(v)

            if not ok:
                # Rank non-hub vertices by t(v, u)
                others = sorted([u for u in range(n) if u != v],
                                key=lambda u: edge_map[(v, u)])
                rank = {u: i for i, u in enumerate(others)}
                for (a, b) in uncov:
                    if a != v and b != v:
                        ra = rank[a] / (n - 2) if n > 2 else 0
                        rb = rank[b] / (n - 2) if n > 2 else 0
                        # Bin into thirds: early(0), mid(1), late(2)
                        ba = 0 if ra < 0.33 else (2 if ra > 0.67 else 1)
                        bb = 0 if rb < 0.33 else (2 if rb > 0.67 else 1)
                        uncov_position_counts[(ba, bb)] += 1
                        total_uncov += 1

        num_winners_dist[len(winners)] += 1

        if len(winners) <= 3:
            hardest_instances.append((len(winners), ts[:], winners[:]))

        if len(winners) == 2:
            # Analyze the two winners
            w0, w1 = winners
            # Relative positions
            avg_times = []
            for v in range(n):
                avg = sum(edge_map[(v, u)] for u in range(n) if u != v) / (n - 1)
                avg_times.append((avg, v))
            avg_times.sort()
            rank = {v: i for i, (_, v) in enumerate(avg_times)}
            two_winner_data.append((rank[w0] / (n-1), rank[w1] / (n-1)))

    print(f"\nNumber of working hubs per instance:")
    for k in sorted(num_winners_dist):
        print(f"  {k} hubs: {num_winners_dist[k]:6d} ({num_winners_dist[k]/num_samples*100:.1f}%)")

    print(f"\nUncovered pair positions (relative to hub's timestamp ordering):")
    print(f"  Bins: 0=early, 1=mid, 2=late (in hub's ordering of neighbors)")
    print(f"  {'(src,dst)':>10s}  {'count':>6s}  {'pct':>6s}")
    labels = {0: 'early', 1: 'mid', 2: 'late'}
    for (ba, bb) in sorted(uncov_position_counts.keys()):
        c = uncov_position_counts[(ba, bb)]
        print(f"  ({labels[ba]:>5s},{labels[bb]:>5s})  {c:>6d}  {c/total_uncov*100:>5.1f}%")

    if two_winner_data:
        print(f"\nTwo-winner instances ({len(two_winner_data)} cases):")
        print(f"  Winner rank positions (0=earliest avg timestamp, 1=latest):")
        # Distribution of winner ranks
        all_ranks = [r for pair in two_winner_data for r in pair]
        rank_bins = Counter()
        for r in all_ranks:
            b = round(r * (n-1)) / (n-1)  # snap to grid
            rank_bins[b] += 1
        for b in sorted(rank_bins):
            bar = '#' * (rank_bins[b] * 40 // max(rank_bins.values()))
            print(f"    rank {b:.2f}: {rank_bins[b]:>4d} {bar}")

        # Gap between the two winners
        gaps = [abs(r1 - r0) for r0, r1 in two_winner_data]
        print(f"  Gap between two winners: avg={sum(gaps)/len(gaps):.3f}, "
              f"min={min(gaps):.3f}, max={max(gaps):.3f}")

        # Are they adjacent, opposite, or random?
        adj = sum(1 for g in gaps if g <= 1.0/(n-1) + 0.01)
        opp = sum(1 for g in gaps if g >= 0.6)
        print(f"  Adjacent (gap≤1 step): {adj} ({adj/len(gaps)*100:.0f}%)")
        print(f"  Opposite (gap≥0.6): {opp} ({opp/len(gaps)*100:.0f}%)")

    if hardest_instances:
        # Show a few hardest instances
        hardest_instances.sort(key=lambda x: x[0])
        print(f"\nHardest instance (fewest winners):")
        nw, ts, winners = hardest_instances[0]
        print(f"  {nw} working hubs: {winners}")
        edge_map = {}
        for i, (u, v) in enumerate(edges):
            edge_map[(u, v)] = ts[i]
            edge_map[(v, u)] = ts[i]

        # Show timestamp matrix
        print(f"  Timestamp matrix:")
        header = "     " + "".join(f"{j:>4d}" for j in range(n))
        print(f"  {header}")
        for i in range(n):
            row = f"  {i:>3d}:"
            for j in range(n):
                if i == j:
                    row += "   ."
                else:
                    row += f"{edge_map[(i,j)]:>4d}"
            marker = " <-- HUB" if i in winners else ""
            print(f"  {row}{marker}")


def main():
    random.seed(42)
    for n, samples in [(5, 20000), (6, 5000), (7, 2000), (8, 500)]:
        run(n, samples)


if __name__ == "__main__":
    main()
