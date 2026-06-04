"""
Test: does every-vertex-at-50%-forward ↔ truly hub-less?

Forward ratio = |{(a,b) : t(a,v) <= t(v,b)}| / |pairs|

For K_6 with 15 edges: each vertex has 5 incident edges.
Forward pairs = #{(a,b) : t(a,v) <= t(v,b)}, where a,b ≠ v, a ≠ b.
Total pairs = 4*5 = 20. Half = 10.

When t(a,v) = t(v,b) (same timestamp? no — all distinct). So strict:
t(a,v) <= t(v,b) with strict inequality since all timestamps distinct.
Actually: t(a,v) ≤ t(v,b) means t(a,v) < t(v,b) OR t(a,v) = t(v,b).
With distinct timestamps, equality only if a = b (same edge). So for a ≠ b,
it's always strict.

For vertex v with incident timestamps sorted as t₁ < t₂ < ... < t_{n-1}:
Forward count at v = #{(i,j) : i < j} among the 5 positions.
= C(5,2) = 10 = exactly half of 20.

WAIT. That's always true! For ANY vertex v in K_6 with distinct timestamps,
the forward count is ALWAYS C(n-1, 2) = (n-1)(n-2)/2.
Total directed pairs among n-1 neighbors = (n-1)(n-2).
Forward fraction = C(n-1,2) / (n-1)(n-2) = 1/2.

So the 50% forward ratio is a TAUTOLOGY for distinct timestamps!
It tells us nothing about hub-less-ness.

Let me verify this and look for the REAL distinguishing property.
"""

import random
from itertools import combinations

random.seed(42)


def compute_reachability(n, timed_edges):
    reached_by = [dict() for _ in range(n)]
    for i in range(n):
        reached_by[i][i] = 0
    for t, u, v in sorted(timed_edges):
        sources_u = {s: arr for s, arr in reached_by[u].items() if arr <= t}
        sources_v = {s: arr for s, arr in reached_by[v].items() if arr <= t}
        for s, arr in sources_u.items():
            if s not in reached_by[v] or t < reached_by[v][s]:
                reached_by[v][s] = t
        for s, arr in sources_v.items():
            if s not in reached_by[u] or t < reached_by[u][s]:
                reached_by[u][s] = t
    pairs = set()
    for v in range(n):
        for s in reached_by[v]:
            if s != v:
                pairs.add((s, v))
    return pairs


def forward_ratio(n, timestamps, v):
    forward = 0
    total = 0
    for a in range(n):
        if a == v:
            continue
        for b in range(n):
            if b == v or b == a:
                continue
            ta = timestamps[(min(a, v), max(a, v))]
            tb = timestamps[(min(v, b), max(v, b))]
            total += 1
            if ta <= tb:
                forward += 1
    return forward, total


def star_coverage(n, timestamps, hub):
    """How many pairs can hub route via 2-hop? (a→hub→b needs t(a,h) < t(h,b))"""
    covered = 0
    total = 0
    for a in range(n):
        if a == hub:
            continue
        for b in range(n):
            if b == hub or b == a:
                continue
            ta = timestamps[(min(a, hub), max(a, hub))]
            tb = timestamps[(min(hub, b), max(hub, b))]
            total += 1
            if ta < tb:  # strict for temporal journeys
                covered += 1
    return covered, total


def is_truly_hubless(n, timestamps):
    all_edges = list(timestamps.keys())
    for hub in range(n):
        star = {(min(hub, v), max(hub, v)) for v in range(n) if v != hub}
        non_star = [e for e in all_edges if e not in star]
        need = n - 2
        for tree_edges in combinations(non_star, need):
            all_timed = sorted([(t, u, v) for (u, v), t in timestamps.items()])
            target = compute_reachability(n, all_timed)
            sub = star | set(tree_edges)
            sub_timed = sorted([(timestamps[e], e[0], e[1]) for e in sub])
            if compute_reachability(n, sub_timed) == target:
                return False
    return True


def main():
    print("Forward ratio analysis")
    print("=" * 60)

    # First: verify forward ratio is always 50%
    n = 6
    m = 15
    print(f"\nK_{n}: checking if forward ratio is always 50%...")
    all_exact = True
    for trial in range(1000):
        edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
        ts_vals = list(range(1, m + 1))
        random.shuffle(ts_vals)
        timestamps = {e: t for e, t in zip(edges, ts_vals)}
        for v in range(n):
            fwd, tot = forward_ratio(n, timestamps, v)
            if fwd != tot // 2:
                all_exact = False
                print(f"  Counter-example: v={v}, fwd={fwd}, total={tot}")
                break
        if not all_exact:
            break
    if all_exact:
        print("  Confirmed: forward ratio = 50% for ALL instances (tautology)")

    # The real question: what distinguishes hub-less instances?
    # Star coverage: how many pairs does the BEST hub cover via 2-hop?
    print(f"\nStar 2-hop coverage: hub-less vs normal instances")
    print("-" * 60)

    normal_coverages = []
    hubless_coverages = []

    for trial in range(50000):
        edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
        ts_vals = list(range(1, m + 1))
        random.shuffle(ts_vals)
        timestamps = {e: t for e, t in zip(edges, ts_vals)}

        # Best hub coverage
        best_cov = 0
        for v in range(n):
            cov, tot = star_coverage(n, timestamps, v)
            best_cov = max(best_cov, cov)

        hubless = is_truly_hubless(n, timestamps)
        if hubless:
            hubless_coverages.append(best_cov)
        else:
            normal_coverages.append(best_cov)

    print(f"  Normal instances: {len(normal_coverages)}")
    if normal_coverages:
        print(f"    Best hub coverage: mean={sum(normal_coverages)/len(normal_coverages):.1f}, "
              f"min={min(normal_coverages)}, max={max(normal_coverages)}")

    print(f"  Hub-less instances: {len(hubless_coverages)}")
    if hubless_coverages:
        print(f"    Best hub coverage: mean={sum(hubless_coverages)/len(hubless_coverages):.1f}, "
              f"min={min(hubless_coverages)}, max={max(hubless_coverages)}")

    # Distribution of best hub coverage
    from collections import Counter
    print(f"\n  Coverage distribution (normal):")
    normal_dist = Counter(normal_coverages)
    for k in sorted(normal_dist):
        pct = 100 * normal_dist[k] / len(normal_coverages)
        print(f"    {k:3d}: {normal_dist[k]:6d} ({pct:.2f}%)")

    if hubless_coverages:
        print(f"\n  Coverage distribution (hub-less):")
        hubless_dist = Counter(hubless_coverages)
        for k in sorted(hubless_dist):
            pct = 100 * hubless_dist[k] / len(hubless_coverages)
            print(f"    {k:3d}: {hubless_dist[k]:6d} ({pct:.2f}%)")

    # What about tree edges — which non-star edges are critical?
    print(f"\n\nStructural analysis of hub-less instances:")
    print("-" * 60)

    random.seed(42)
    hubless_found = 0
    for trial in range(200000):
        edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
        ts_vals = list(range(1, m + 1))
        random.shuffle(ts_vals)
        timestamps = {e: t for e, t in zip(edges, ts_vals)}

        if not is_truly_hubless(n, timestamps):
            continue

        hubless_found += 1
        if hubless_found > 5:
            break

        print(f"\n  Hub-less instance #{hubless_found}:")
        # For each hub, what's the minimum # of missing pairs?
        all_timed = sorted([(t, u, v) for (u, v), t in timestamps.items()])
        target = compute_reachability(n, all_timed)

        for hub in range(n):
            star = {(min(hub, v), max(hub, v)) for v in range(n) if v != hub}
            star_timed = sorted([(timestamps[e], e[0], e[1]) for e in star])
            star_reach = compute_reachability(n, star_timed)
            star_missing = len(target - star_reach)

            # With best single tree edge
            non_star = [e for e in timestamps if e not in star]
            best_rescue = star_missing
            for e in non_star:
                trial_edges = star | {e}
                sub = sorted([(timestamps[ee], ee[0], ee[1]) for ee in trial_edges])
                tr = compute_reachability(n, sub)
                rescue = len(target - tr)
                best_rescue = min(best_rescue, rescue)

            cov, tot = star_coverage(n, timestamps, hub)
            print(f"    hub={hub}: 2-hop coverage={cov}/{tot}, "
                  f"star-only missing={star_missing}, "
                  f"star+1 best={best_rescue}")


if __name__ == '__main__':
    main()
