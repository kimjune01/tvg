"""
If-statement hub selection.

Define balance metric b(v) = concentration of incident timestamps in middle third.
Compute B = max_v b(v) for the instance.

If B >= threshold: pick argmax_v b(v) as hub.
If B < threshold:  pick argmin_v spread(v) as hub.

Find the threshold range where both sides work at 100%.
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


def concentration(n, edges, timestamps, v):
    m = len(edges)
    edge_map = {}
    for i, (u, w) in enumerate(edges):
        edge_map[(u, w)] = timestamps[i]
        edge_map[(w, u)] = timestamps[i]
    times = [edge_map[(v, u)] for u in range(n) if u != v]
    lo = m / 3
    hi = 2 * m / 3
    return sum(1 for t in times if lo <= t <= hi) / len(times)


def spread(n, edges, timestamps, v):
    edge_map = {}
    for i, (u, w) in enumerate(edges):
        edge_map[(u, w)] = timestamps[i]
        edge_map[(w, u)] = timestamps[i]
    times = [edge_map[(v, u)] for u in range(n) if u != v]
    return max(times) - min(times)


def run(n, num_samples):
    edges = make_edges(n)
    m = len(edges)
    print(f"\nK_{n}: {n} vertices, {m} edges")
    print("=" * 70)

    # Sweep thresholds
    thresholds = [i / 20 for i in range(1, 15)]

    # Precompute all instances
    instances = []
    for _ in range(num_samples):
        ts = list(range(1, m + 1))
        random.shuffle(ts)

        # Compute per-vertex metrics
        vertex_data = []
        for v in range(n):
            c = concentration(n, edges, ts, v)
            s = spread(n, edges, ts, v)
            ok = star_tree_spans(n, edges, ts, v)
            vertex_data.append((v, c, s, ok))

        max_conc = max(c for _, c, _, _ in vertex_data)
        hub_conc = max(vertex_data, key=lambda x: x[1])  # max concentration vertex
        hub_spread = min(vertex_data, key=lambda x: x[2])  # min spread vertex

        instances.append((ts, vertex_data, max_conc, hub_conc, hub_spread))

    print(f"\n{'threshold':>10s}  {'balanced%':>10s}  {'extreme%':>10s}  "
          f"{'bal_ok%':>8s}  {'ext_ok%':>8s}  {'combined%':>10s}  {'overlap%':>9s}")
    print("-" * 75)

    for tau in thresholds:
        bal_count = 0
        ext_count = 0
        bal_ok = 0
        ext_ok = 0
        combined_ok = 0

        for ts, vdata, max_conc, hub_conc, hub_spread in instances:
            if max_conc >= tau:
                # Balanced case: use max-concentration vertex
                bal_count += 1
                if hub_conc[3]:  # ok field
                    bal_ok += 1
                    combined_ok += 1
                else:
                    # Fallback: does min-spread also work here?
                    if hub_spread[3]:
                        combined_ok += 1
            else:
                # Extreme case: use min-spread vertex
                ext_count += 1
                if hub_spread[3]:
                    ext_ok += 1
                    combined_ok += 1
                else:
                    # Fallback: does max-conc also work here?
                    if hub_conc[3]:
                        combined_ok += 1

        total = num_samples
        bal_pct = bal_count / total * 100
        ext_pct = ext_count / total * 100
        bal_ok_pct = bal_ok / bal_count * 100 if bal_count > 0 else 0
        ext_ok_pct = ext_ok / ext_count * 100 if ext_count > 0 else 0
        combined_pct = combined_ok / total * 100

        # Overlap: instances where BOTH heuristics work
        overlap = sum(1 for _, vdata, _, hc, hs in instances if hc[3] and hs[3])
        overlap_pct = overlap / total * 100

        print(f"{tau:>10.2f}  {bal_pct:>10.1f}  {ext_pct:>10.1f}  "
              f"{bal_ok_pct:>8.1f}  {ext_ok_pct:>8.1f}  {combined_pct:>10.1f}  {overlap_pct:>9.1f}")

    # Now: for the best threshold, show the failure cases
    best_tau = None
    best_combined = 0
    for tau in thresholds:
        combined_ok = 0
        for ts, vdata, max_conc, hub_conc, hub_spread in instances:
            if max_conc >= tau:
                if hub_conc[3] or hub_spread[3]:
                    combined_ok += 1
            else:
                if hub_spread[3] or hub_conc[3]:
                    combined_ok += 1
        if combined_ok > best_combined:
            best_combined = combined_ok
            best_tau = tau

    fail_count = num_samples - best_combined
    print(f"\nBest threshold: {best_tau:.2f}")
    print(f"Combined success: {best_combined}/{num_samples} ({best_combined/num_samples*100:.2f}%)")
    print(f"Failures: {fail_count}")

    if fail_count > 0 and fail_count <= 10:
        print(f"\nFailure details:")
        for ts, vdata, max_conc, hub_conc, hub_spread in instances:
            if max_conc >= best_tau:
                if hub_conc[3] or hub_spread[3]:
                    continue
            else:
                if hub_spread[3] or hub_conc[3]:
                    continue
            print(f"  max_conc={max_conc:.3f}, hub_conc=v{hub_conc[0]}({'OK' if hub_conc[3] else 'FAIL'}), "
                  f"hub_spread=v{hub_spread[0]}({'OK' if hub_spread[3] else 'FAIL'})")
            for v, c, s, ok in vdata:
                print(f"    v={v}: conc={c:.3f} spread={s:2d} {'OK' if ok else 'FAIL'}")


def main():
    random.seed(42)
    print("If-statement hub: threshold on max concentration")
    print("Balanced (high conc) -> max-conc vertex")
    print("Extreme (low conc) -> min-spread vertex")

    for n, samples in [(4, 20000), (5, 10000), (6, 3000), (7, 1000), (8, 300)]:
        run(n, samples)


if __name__ == "__main__":
    main()
