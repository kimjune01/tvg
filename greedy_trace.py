"""
Trace what the interactive greedy selects as tree edges
in a dead-zone assignment. What routes rescue backward pairs?

Key question: do the selected tree edges form a specific structure
(path? star? balanced tree?) and what journey types rescue pairs?
"""

import random

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


def make_maxdz_assignment(n, hub):
    """Maximize dead-zone edges."""
    m = n * (n - 1) // 2
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]

    non_hub = sorted([v for v in range(n) if v != hub])
    star_edges = [(min(hub, v), max(hub, v)) for v in non_hub]

    # Random star timestamps
    all_vals = list(range(1, m + 1))
    random.shuffle(all_vals)
    star_vals = sorted(all_vals[:n - 1])

    star_ts = {}
    for i, e in enumerate(star_edges):
        star_ts[e] = star_vals[i]

    ordered = sorted(non_hub, key=lambda v: star_ts[(min(hub, v), max(hub, v))])
    rank = {v: i for i, v in enumerate(ordered)}
    T = [star_ts[(min(hub, v), max(hub, v))] for v in ordered]

    # Assign non-star to dead zones
    non_star_edges = [e for e in edges if e not in set(star_edges)]
    remaining = sorted(set(all_vals) - set(star_vals))

    edge_zones = []
    for e in non_star_edges:
        u, v = e
        ru, rv = rank.get(u), rank.get(v)
        if ru is None or rv is None:
            continue
        lo, hi = min(ru, rv), max(ru, rv)
        edge_zones.append((e, T[lo], T[hi], lo, hi))

    edge_zones.sort(key=lambda x: x[2] - x[1])

    ts = dict(star_ts)
    avail = set(remaining)
    for e, zlo, zhi, lo, hi in edge_zones:
        found = False
        for t in sorted(avail):
            if zlo < t < zhi:
                ts[e] = t
                avail.remove(t)
                found = True
                break
        if not found:
            t = min(avail)
            ts[e] = t
            avail.remove(t)

    return ts, ordered, T, rank


def greedy_with_trace(n, timestamps, hub, ordered, T, rank):
    """Greedy star+tree with detailed trace of what each edge rescues."""
    edges = list(timestamps.keys())
    all_timed = sorted([(t, u, v) for (u, v), t in timestamps.items()])
    target = compute_reachability(n, all_timed)

    star = {(min(hub, v), max(hub, v)) for v in range(n) if v != hub}
    non_star = [e for e in edges if e not in star]
    current = set(star)

    trace = []
    step = 0

    while step < 3 * n:
        sub = sorted([(timestamps[e], e[0], e[1]) for e in current])
        cur_reach = compute_reachability(n, sub)
        if cur_reach == target:
            break

        missing = target - cur_reach
        cur_count = len(cur_reach)

        best_e, best_g, best_new = None, 0, set()
        for e in non_star:
            if e in current:
                continue
            trial = current | {e}
            sub2 = sorted([(timestamps[ee], ee[0], ee[1]) for ee in trial])
            tr = compute_reachability(n, sub2)
            new_pairs = tr - cur_reach
            g = len(new_pairs)
            if g > best_g:
                best_g = g
                best_e = e
                best_new = new_pairs

        if best_e is None or best_g <= 0:
            break

        # Analyze the selected edge
        u, v = best_e
        ru = rank.get(u, -1)
        rv = rank.get(v, -1)
        tau = timestamps[best_e]

        # Is it in dead zone?
        if ru >= 0 and rv >= 0:
            lo, hi = min(ru, rv), max(ru, rv)
            in_dz = T[lo] < tau < T[hi]
        else:
            in_dz = False

        trace.append({
            'step': step,
            'edge': best_e,
            'ranks': (ru, rv),
            'tau': tau,
            'in_dz': in_dz,
            'gain': best_g,
            'new_pairs': best_new,
        })

        current.add(best_e)
        step += 1

    return step, cur_reach == target, trace


def main():
    print("Greedy trace on dead-zone assignments")
    print("=" * 70)

    for n in [8, 10, 12]:
        m = n * (n - 1) // 2
        hub = 0
        budget = n - 2

        # Find a good hub for a dead-zone assignment
        ts, ordered, T, rank = make_maxdz_assignment(n, hub)

        # Try all hubs, find the best
        best_hub = None
        best_count = 999
        for h in range(n):
            # Recompute ordering for this hub
            non_hub_h = [v for v in range(n) if v != h]
            star_h = {(min(h, v), max(h, v)) for v in non_hub_h}
            star_times_h = {v: ts[(min(h, v), max(h, v))] for v in non_hub_h}
            ordered_h = sorted(non_hub_h, key=lambda v: star_times_h[v])
            T_h = [star_times_h[v] for v in ordered_h]
            rank_h = {v: i for i, v in enumerate(ordered_h)}

            count, ok, _ = greedy_with_trace(n, ts, h, ordered_h, T_h, rank_h)
            if ok and count < best_count:
                best_count = count
                best_hub = h

        if best_hub is None:
            print(f"\nK_{n}: no hub found!")
            continue

        # Detailed trace for best hub
        h = best_hub
        non_hub_h = [v for v in range(n) if v != h]
        star_times_h = {v: ts[(min(h, v), max(h, v))] for v in non_hub_h}
        ordered_h = sorted(non_hub_h, key=lambda v: star_times_h[v])
        T_h = [star_times_h[v] for v in ordered_h]
        rank_h = {v: i for i, v in enumerate(ordered_h)}

        count, ok, trace = greedy_with_trace(n, ts, h, ordered_h, T_h, rank_h)

        print(f"\nK_{n} (budget={budget}), best hub={h}, cover={count}")
        print(f"  Star order: {ordered_h}")
        print(f"  Star times: {T_h}")
        print(f"\n  Greedy trace:")

        dz_count = 0
        for step in trace:
            e = step['edge']
            ru, rv = step['ranks']
            dz = "DZ" if step['in_dz'] else "LIVE"
            # Classify rescued pairs
            backward_rescued = []
            forward_rescued = []
            for s, t in step['new_pairs']:
                rs = rank_h.get(s, -1)
                rt = rank_h.get(t, -1)
                if rs > rt and rs >= 0 and rt >= 0:
                    backward_rescued.append((rs, rt))
                elif rs >= 0 and rt >= 0:
                    forward_rescued.append((rs, rt))

            if step['in_dz']:
                dz_count += 1

            print(f"    Step {step['step']}: edge {e} (ranks {ru},{rv}), "
                  f"τ={step['tau']}, {dz}, gain={step['gain']}")
            if backward_rescued:
                # Show scale of rescued backward pairs
                scales = [s - t for s, t in backward_rescued]
                print(f"      Backward rescued: {len(backward_rescued)} pairs, "
                      f"scales {sorted(set(scales))}")
            if forward_rescued:
                print(f"      Forward rescued: {len(forward_rescued)} pairs")

        print(f"\n  Summary: {dz_count}/{count} tree edges are dead-zone")

        # Tree structure: what does the selected tree look like?
        tree_edges = [step['edge'] for step in trace]
        degrees = {}
        for u, v in tree_edges:
            degrees[u] = degrees.get(u, 0) + 1
            degrees[v] = degrees.get(v, 0) + 1

        print(f"  Tree edge ranks: {[(step['ranks']) for step in trace]}")
        print(f"  Vertex degrees in tree: {dict(sorted(degrees.items()))}")


if __name__ == '__main__':
    main()
