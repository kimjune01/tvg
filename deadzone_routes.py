"""
Dead-zone routing: when ALL non-star edges are in dead zones,
what routes exist?

Key insight: with τ_{ab} ∈ (T_a, T_b), 3-hop relays are impossible.
Routes must use multi-hop tree paths or star-tree combinations.

Test: construct adversarial dead-zone assignments and check
what the star+tree spanner actually uses.

Also: does the full temporal graph (with dead-zone edges) remain
temporally connected? If yes, what's the minimum spanner size?
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


def make_deadzone_assignment(n, hub):
    """Construct a timestamp assignment where ALL non-star edges
    are in their dead zones.

    Strategy: choose evenly spaced star timestamps, then assign
    non-star timestamps to dead zones."""
    m = n * (n - 1) // 2
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]

    non_hub = [v for v in range(n) if v != hub]
    # Star edges sorted by non-hub vertex
    star_edges = [(min(hub, v), max(hub, v)) for v in non_hub]

    # Choose star timestamps: evenly spaced
    step = m // n
    star_ts = {e: (i + 1) * step for i, e in enumerate(star_edges)}

    # Non-star edges
    non_star_edges = [e for e in edges if e not in star_edges]
    # Sort non-hub vertices by star timestamp
    ordered = sorted(non_hub, key=lambda v: star_ts[(min(hub, v), max(hub, v))])
    rank = {v: i for i, v in enumerate(ordered)}
    T = [star_ts[(min(hub, v), max(hub, v))] for v in ordered]

    # Assign non-star timestamps: each τ_{ab} in (T_a, T_b)
    # where a = min rank, b = max rank
    non_star_ts = {}
    used = set(star_ts.values())
    all_ts = set(range(1, m + 1))
    available = sorted(all_ts - used)

    # For each non-star edge, find a value in its dead zone
    # Sort edges by dead zone width (smallest first = hardest to fill)
    non_star_with_zones = []
    for e in non_star_edges:
        u, v = e
        if u == hub or v == hub:
            continue
        ru, rv = rank[u], rank[v]
        lo, hi = min(ru, rv), max(ru, rv)
        zone_lo, zone_hi = T[lo], T[hi]
        non_star_with_zones.append((e, zone_lo, zone_hi))

    # Sort by zone width (ascending)
    non_star_with_zones.sort(key=lambda x: x[2] - x[1])

    available_set = set(available)
    for e, zone_lo, zone_hi in non_star_with_zones:
        # Find a value in (zone_lo, zone_hi)
        found = False
        for t in available:
            if zone_lo < t < zone_hi and t in available_set:
                non_star_ts[e] = t
                available_set.remove(t)
                found = True
                break
        if not found:
            # Can't find dead-zone value — assign any available
            for t in available:
                if t in available_set:
                    non_star_ts[e] = t
                    available_set.remove(t)
                    break

    # Combine
    timestamps = {}
    timestamps.update(star_ts)
    timestamps.update(non_star_ts)
    return timestamps, ordered, T


def check_deadzone_compliance(n, timestamps, hub, ordered, T):
    """Check what fraction of non-star edges are in dead zones."""
    rank = {v: i for i, v in enumerate(ordered)}
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
    star_edges = {(min(hub, v), max(hub, v)) for v in range(n) if v != hub}

    in_dz = 0
    not_in_dz = 0
    for e in edges:
        if e in star_edges:
            continue
        u, v = e
        if u == hub or v == hub:
            continue
        ru, rv = rank[u], rank[v]
        lo, hi = min(ru, rv), max(ru, rv)
        tau = timestamps[e]
        if T[lo] < tau < T[hi]:
            in_dz += 1
        else:
            not_in_dz += 1

    return in_dz, not_in_dz


def interactive_greedy(n, timestamps, hub):
    """Interactive greedy star+tree."""
    edges = list(timestamps.keys())
    all_timed = sorted([(t, u, v) for (u, v), t in timestamps.items()])
    target = compute_reachability(n, all_timed)

    star = {(min(hub, v), max(hub, v)) for v in range(n) if v != hub}
    non_star = [e for e in edges if e not in star]
    current = set(star)
    count = 0

    while True:
        sub = sorted([(timestamps[e], e[0], e[1]) for e in current])
        cur_reach = compute_reachability(n, sub)
        if cur_reach == target:
            return count, True
        cur_count = len(cur_reach)
        best_e, best_g = None, 0
        for e in non_star:
            if e in current:
                continue
            trial = current | {e}
            sub2 = sorted([(timestamps[ee], ee[0], ee[1]) for ee in trial])
            g = len(compute_reachability(n, sub2)) - cur_count
            if g > best_g:
                best_g = g
                best_e = e
        if best_e is None or best_g <= 0:
            return count, False
        current.add(best_e)
        count += 1
        if count > 3 * n:
            return count, False

    return count, cur_reach == target


def main():
    print("Dead-zone routing analysis")
    print("=" * 70)

    for n in [6, 8, 10, 12]:
        m = n * (n - 1) // 2
        hub = 0
        budget = n - 2

        print(f"\nK_{n} (m={m}, budget={budget}):")

        # Build dead-zone assignment
        timestamps, ordered, T = make_deadzone_assignment(n, hub)
        in_dz, not_in_dz = check_deadzone_compliance(n, timestamps, hub, ordered, T)
        total_ns = in_dz + not_in_dz

        print(f"  Dead zone compliance: {in_dz}/{total_ns} "
              f"({100*in_dz/total_ns:.1f}%)")
        print(f"  Star timestamps: {T}")

        # Check temporal connectivity of full graph
        all_timed = sorted([(t, u, v) for (u, v), t in timestamps.items()])
        full_reach = compute_reachability(n, all_timed)
        expected = n * (n - 1)
        print(f"  Full reachability: {len(full_reach)}/{expected}")

        # Try interactive greedy for each hub
        print(f"  Interactive greedy cover:")
        for h in range(min(n, 5)):
            count, ok = interactive_greedy(n, timestamps, h)
            marker = "✓" if ok and count <= n - 2 else "✗"
            print(f"    hub={h}: {count} tree edges {'(OK)' if ok else '(FAIL)'} "
                  f"{marker}")

        # Try multiple dead-zone assignments
        print(f"\n  Testing {10} different dead-zone assignments:")
        for trial in range(10):
            # Randomize star timestamp positions
            all_vals = list(range(1, m + 1))
            random.shuffle(all_vals)
            star_vals = sorted(all_vals[:n-1])

            star_edges = [(min(hub, v), max(hub, v))
                          for v in range(n) if v != hub]
            non_hub_sorted = sorted(range(1, n), key=lambda v: v)  # arbitrary
            star_ts = {e: star_vals[i]
                       for i, e in enumerate(star_edges)}

            # Order non-hub by star timestamp
            ordered2 = sorted(range(1, n),
                              key=lambda v: star_ts[(min(0, v), max(0, v))])
            T2 = [star_ts[(min(0, v), max(0, v))] for v in ordered2]
            rank2 = {v: i for i, v in enumerate(ordered2)}

            # Assign non-star timestamps to dead zones
            remaining_vals = sorted(set(all_vals) - set(star_vals))
            non_star_edges2 = [(i, j) for i in range(n) for j in range(i+1, n)
                               if (i, j) not in set(star_edges)]

            # Build (edge, zone) pairs
            edge_zones = []
            for e in non_star_edges2:
                u, v = e
                if u == 0 or v == 0:
                    uu = u if u != 0 else v
                    # This shouldn't happen, star edges filtered
                    continue
                ru, rv = rank2[u], rank2[v]
                lo, hi = min(ru, rv), max(ru, rv)
                edge_zones.append((e, T2[lo], T2[hi]))

            edge_zones.sort(key=lambda x: x[2] - x[1])

            ts2 = dict(star_ts)
            avail = set(remaining_vals)
            dz_count = 0
            for e, zlo, zhi in edge_zones:
                found = False
                for t in sorted(avail):
                    if zlo < t < zhi:
                        ts2[e] = t
                        avail.remove(t)
                        dz_count += 1
                        found = True
                        break
                if not found:
                    # Assign any available
                    t = min(avail)
                    ts2[e] = t
                    avail.remove(t)

            # Check greedy for hub 0
            count, ok = interactive_greedy(n, ts2, 0)
            best_count = count
            best_hub = 0

            for h in range(1, n):
                c, o = interactive_greedy(n, ts2, h)
                if o and c < best_count:
                    best_count = c
                    best_hub = h

            dz_frac = dz_count / len(non_star_edges2)
            in_budget = "✓" if best_count <= budget else "✗"
            print(f"    Trial {trial}: DZ={100*dz_frac:.0f}%, "
                  f"best hub={best_hub}, cover={best_count} {in_budget}")


if __name__ == '__main__':
    main()
