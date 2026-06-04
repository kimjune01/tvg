"""
Two-hub construction on K_n temporal cliques.

Star+tree works 99.8% of instances (single hub). For the 0.2% hub-less
instances: does a pair of hubs always work?

Double star: star(h1) ∪ star(h2) = 2(n-1) - 1 = 2n-3 edges (exactly at budget).
Routes: u→h1→v, u→h2→v (2-hop), or u→h1→h2→v, u→h2→h1→v (3-hop).

Test: exhaustive for small n, sampling for larger n.
"""

import random
from itertools import combinations

random.seed(42)


def compute_reachability(n, timed_edges):
    """Compute all reachable pairs via non-decreasing timestamp journeys."""
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


def make_timed_edges(n, timestamps):
    """Build timed edge list for K_n from timestamp dict."""
    return [(t, u, v) for (u, v), t in timestamps.items()]


def star_tree_check(n, timestamps, hub):
    """Check if star(hub) + best greedy tree is a valid spanner."""
    all_edges = make_timed_edges(n, timestamps)
    target = compute_reachability(n, sorted(all_edges))

    # Star edges
    star = {(min(hub, v), max(hub, v)) for v in range(n) if v != hub}

    # Greedy tree: add edges one at a time, pick best improvement
    non_star = [(u, v) for u, v in timestamps if (u, v) not in star]
    current = set(star)

    for _ in range(n - 2):
        sub_timed = sorted([(timestamps[e], e[0], e[1]) for e in current])
        cur_reach = compute_reachability(n, sub_timed)
        if cur_reach == target:
            break

        cur_count = len(cur_reach)
        best_edge = None
        best_gain = -1
        for e in non_star:
            if e in current:
                continue
            trial = current | {e}
            sub = sorted([(timestamps[ee], ee[0], ee[1]) for ee in trial])
            tr = compute_reachability(n, sub)
            gain = len(tr) - cur_count
            if gain > best_gain:
                best_gain = gain
                best_edge = e
        if best_edge is None or best_gain <= 0:
            break
        current.add(best_edge)

    if len(current) > 2 * n - 3:
        return False  # over budget

    sub_timed = sorted([(timestamps[e], e[0], e[1]) for e in current])
    final = compute_reachability(n, sub_timed)
    return final == target


def double_star_check(n, timestamps, h1, h2):
    """Check if star(h1) ∪ star(h2) is a valid spanner. Exactly 2n-3 edges."""
    all_edges = make_timed_edges(n, timestamps)
    target = compute_reachability(n, sorted(all_edges))

    # Double star edges
    ds_edges = set()
    for v in range(n):
        if v != h1:
            ds_edges.add((min(h1, v), max(h1, v)))
        if v != h2:
            ds_edges.add((min(h2, v), max(h2, v)))

    assert len(ds_edges) == 2 * n - 3, f"Expected {2*n-3}, got {len(ds_edges)}"

    sub_timed = sorted([(timestamps[e], e[0], e[1]) for e in ds_edges])
    span_reach = compute_reachability(n, sub_timed)
    missing = target - span_reach
    return len(missing) == 0, missing


def random_temporal_clique(n):
    """Generate random temporal K_n with distinct timestamps."""
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
    m = len(edges)
    ts = list(range(1, m + 1))
    random.shuffle(ts)
    return {e: t for e, t in zip(edges, ts)}


def find_hubless_instances(n, num_samples):
    """Find instances where no single hub works with star+tree."""
    hubless = []
    for _ in range(num_samples):
        timestamps = random_temporal_clique(n)
        has_hub = False
        for h in range(n):
            if star_tree_check(n, timestamps, h):
                has_hub = True
                break
        if not has_hub:
            hubless.append(timestamps)
    return hubless


def main():
    print("Two-hub construction on K_n temporal cliques")
    print("=" * 60)

    for n in range(5, 13):
        m = n * (n - 1) // 2
        # Scale samples: exhaustive is impossible, but need enough to find hub-less
        if n <= 8:
            samples = 10000
        elif n <= 10:
            samples = 5000
        else:
            samples = 2000

        print(f"\nK_{n}: {n} vertices, {m} edges, 2n-3={2*n-3}")
        print(f"  Searching {samples} instances for hub-less cases...")

        hubless_count = 0
        two_hub_fixes = 0
        two_hub_fails = 0
        total_checked = 0

        for trial in range(samples):
            timestamps = random_temporal_clique(n)
            total_checked += 1

            # Check all single hubs
            has_hub = False
            for h in range(n):
                if star_tree_check(n, timestamps, h):
                    has_hub = True
                    break

            if has_hub:
                continue

            hubless_count += 1

            # Try all pairs of hubs
            found_pair = False
            for h1, h2 in combinations(range(n), 2):
                ok, missing = double_star_check(n, timestamps, h1, h2)
                if ok:
                    found_pair = True
                    if hubless_count <= 3:
                        print(f"    Hub-less instance #{hubless_count}: "
                              f"fixed by double star ({h1},{h2})")
                    break

            if found_pair:
                two_hub_fixes += 1
            else:
                two_hub_fails += 1
                if two_hub_fails <= 3:
                    print(f"    *** TWO-HUB FAILURE #{two_hub_fails} ***")
                    # Show which pairs come closest
                    best_missing = None
                    for h1, h2 in combinations(range(n), 2):
                        ok, missing = double_star_check(n, timestamps, h1, h2)
                        if best_missing is None or len(missing) < len(best_missing):
                            best_missing = missing
                            best_pair = (h1, h2)
                    print(f"      Best pair {best_pair}: {len(best_missing)} missing")

        hubless_pct = 100 * hubless_count / total_checked if total_checked > 0 else 0
        print(f"  Hub-less: {hubless_count}/{total_checked} ({hubless_pct:.1f}%)")
        if hubless_count > 0:
            fix_pct = 100 * two_hub_fixes / hubless_count
            print(f"  Two-hub fixes: {two_hub_fixes}/{hubless_count} ({fix_pct:.1f}%)")
            if two_hub_fails > 0:
                print(f"  *** TWO-HUB FAILURES: {two_hub_fails} ***")
        else:
            print(f"  (all instances have a single hub)")


if __name__ == '__main__':
    main()
