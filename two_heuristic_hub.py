"""
Two-heuristic hub selection: spread + balanced.

Claim: two heuristics cover ALL temporal cliques.
- Heuristic A (spread): vertex with widest incident-timestamp range. Catches ~99.5%.
- Heuristic B (balanced): vertex closest to median rank. Catches the remainder.
- Together: 100% coverage.

The classification (extreme / balanced / in-between) is emergent.
"""

import random
import time
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


def max_spread_vertex(n, edges, timestamps):
    """Vertex with widest range of incident timestamps."""
    edge_map = {}
    for i, (u, v) in enumerate(edges):
        edge_map[(u, v)] = timestamps[i]
        edge_map[(v, u)] = timestamps[i]

    best_v, best_spread = 0, -1
    for v in range(n):
        times = [edge_map[(v, u)] for u in range(n) if u != v]
        spread = max(times) - min(times)
        if spread > best_spread:
            best_spread = spread
            best_v = v
    return best_v


def median_rank_vertex(n, edges, timestamps):
    """Vertex closest to median in average timestamp."""
    edge_map = {}
    for i, (u, v) in enumerate(edges):
        edge_map[(u, v)] = timestamps[i]
        edge_map[(v, u)] = timestamps[i]

    avgs = [(sum(edge_map[(v, u)] for u in range(n) if u != v) / (n - 1), v) for v in range(n)]
    avgs.sort()
    mid = len(avgs) // 2
    return avgs[mid][1]


def run(n, num_samples):
    edges = make_edges(n)
    m = len(edges)
    print(f"\nK_{n}: {n} vertices, {m} edges, 2n-3={2*n-3}")
    print("-" * 55)

    counts = {"same": 0, "both": 0, "spread_only": 0, "balanced_only": 0, "neither": 0}
    a_success = 0
    b_success = 0
    failures = []
    start = time.time()

    for trial in range(num_samples):
        ts = list(range(1, m + 1))
        random.shuffle(ts)

        hub_a = max_spread_vertex(n, edges, ts)
        hub_b = median_rank_vertex(n, edges, ts)

        ok_a = star_tree_spans(n, edges, ts, hub_a)
        ok_b = star_tree_spans(n, edges, ts, hub_b) if hub_b != hub_a else ok_a

        if ok_a:
            a_success += 1
        if ok_b:
            b_success += 1

        if hub_a == hub_b:
            counts["same"] += 1
            if not ok_a:
                failures.append(ts[:])
        elif ok_a and ok_b:
            counts["both"] += 1
        elif ok_a:
            counts["spread_only"] += 1
        elif ok_b:
            counts["balanced_only"] += 1
        else:
            counts["neither"] += 1
            failures.append(ts[:])

        if (trial + 1) % max(1, num_samples // 5) == 0:
            total = trial + 1
            elapsed = time.time() - start
            print(f"  {total:>6}/{num_samples}: "
                  f"A={a_success/total*100:.1f}% B={b_success/total*100:.1f}% "
                  f"A|B={(a_success + b_success - counts['both'] - counts['same'])/total*100:.1f}% "
                  f"fail={len(failures)/total*100:.2f}% ({elapsed:.1f}s)")

    total = sum(counts.values())
    print(f"\nResults K_{n}:")
    print(f"  Spread (A) alone:   {a_success/total*100:.2f}%")
    print(f"  Balanced (B) alone: {b_success/total*100:.2f}%")
    combined = total - len(failures)
    print(f"  A ∪ B:              {combined/total*100:.2f}%")
    print(f"  Breakdown:")
    for cat, c in counts.items():
        print(f"    {cat:15s}: {c:6d} ({c/total*100:5.1f}%)")
    print(f"  FAILURES: {len(failures)}/{total} ({len(failures)/total*100:.2f}%)")

    if failures:
        ts = failures[0]
        print(f"\n  First failure analysis:")
        edge_map = {}
        for i, (u, v) in enumerate(edges):
            edge_map[(u, v)] = ts[i]
            edge_map[(v, u)] = ts[i]
        for v in range(n):
            times = sorted([edge_map[(v, u)] for u in range(n) if u != v])
            spread = times[-1] - times[0]
            avg = sum(times) / len(times)
            ok = star_tree_spans(n, edges, ts, v)
            marker = ""
            if v == max_spread_vertex(n, edges, ts):
                marker += " <-A"
            if v == median_rank_vertex(n, edges, ts):
                marker += " <-B"
            print(f"    v={v}: spread={spread:2d} avg={avg:5.1f} {'OK' if ok else 'FAIL'}{marker}")

    return len(failures) == 0


def main():
    random.seed(42)
    print("Two-heuristic hub: A=max_spread, B=median_rank")
    print("=" * 55)

    for n, samples in [(4, 50000), (5, 20000), (6, 5000), (7, 2000), (8, 500)]:
        run(n, samples)


if __name__ == "__main__":
    main()
