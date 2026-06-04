"""
LIVE/DZ framework on non-dismountable bicliques.

Structure: k rows (A-side), k columns (B-side). k² cross edges with
timestamps M[i][j]. Matchings M⁻[j] = argmin_i M[i][j] (column mins)
and M⁺[i] = argmax_j M[i][j] (row maxes).

Target: spanner of size ≤ 4k-3 = 2n-3 where n = 2k.

In the K_n framework: "hub" was a vertex. In K_{k,k}: what's the analog?
A "hub row" a_h connects to all k columns. Star(a_h) = k edges.
Budget = 4k-3 - k = 3k-3 more edges.

Alternatively: pick hub row a_h AND hub column b_c.
Star(a_h) = k edges (a_h to all B).
Star(b_c) = k edges (b_c to all A).
Overlap: edge (a_h, b_c) counted once.
Total: 2k-1 edges. Budget = 4k-3 - (2k-1) = 2k-2 more edges.

The LIVE/DZ framework: for a cross edge (a_i, b_j) with timestamp M[i][j]:
- Relative to hub row a_h: "star times" are M[h][j'] for columns j'
- Edge (a_i, b_j) is LIVE if M[i][j] is NOT the median of
  {M[h][j], M[h][j'], M[i][j]} for some relevant triple

Actually the biclique structure is different from K_n. Let me think about
what "hub" means here and apply the framework correctly.

In K_{k,k}: we want to span all pairs. Types of pairs:
- A-B pairs (a_i, b_j): direct cross edges
- A-A pairs (a_i, a_{i'}): need path through B-side
- B-B pairs (b_j, b_{j'}): need path through A-side

A single hub row a_h: star = {(a_h, b_j) : j=1..k}. These k edges
route B-B pairs via b_j → a_h → b_{j'} and provide A-B routing via
a_i → ... → a_h → b_j.

For A-A pair (a_i, a_{i'}): need journey a_i → b_j → a_{i'} for some j.
This requires cross edges (a_i, b_j) and (a_{i'}, b_j) with
M[i][j] ≤ M[i'][j] (same column j, nondecreasing).

So column j "relays" the pair (a_i, a_{i'}) if M[i][j] ≤ M[i'][j].

This is the biclique analog of the three-timestamp framework!
For A-A pair (a_i, a_{i'}): column j relays it iff M[i][j] < M[i'][j].
The "DZ" condition would be... different.

Let me build the framework and test it.
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


def generate_biclique(k):
    """Generate random extremally matched k×k biclique."""
    M = [[0]*k for _ in range(k)]
    # Random permutation for timestamp assignment
    vals = list(range(1, k*k+1))
    random.shuffle(vals)
    idx = 0
    for i in range(k):
        for j in range(k):
            M[i][j] = vals[idx]
            idx += 1
    return M


def biclique_to_timed_edges(M, k):
    """Convert k×k matrix to timed edges. Rows = 0..k-1, cols = k..2k-1."""
    edges = []
    for i in range(k):
        for j in range(k):
            edges.append((M[i][j], i, k+j))
    return edges


def column_relay_analysis(M, k):
    """For each A-A pair (i, i'), which columns relay them?
    Column j relays (i→i') if M[i][j] ≤ M[i'][j] (2-hop via column j).
    """
    relays = {}
    for i in range(k):
        for ip in range(k):
            if i == ip:
                continue
            relay_cols = []
            for j in range(k):
                if M[i][j] <= M[ip][j]:
                    relay_cols.append(j)
            relays[(i, ip)] = relay_cols
    return relays


def row_relay_analysis(M, k):
    """For each B-B pair (j, j'), which rows relay them?
    Row i relays (j→j') if M[i][j] ≤ M[i][j'] (2-hop via row i).
    """
    relays = {}
    for j in range(k):
        for jp in range(k):
            if j == jp:
                continue
            relay_rows = []
            for i in range(k):
                if M[i][j] <= M[i][jp]:
                    relay_rows.append(i)
            relays[(j, jp)] = relay_rows
    return relays


def hub_row_spanner(M, k, hub_row):
    """Build spanner: star(hub_row) + greedy tree edges.
    star = {(hub_row, b_j) : j=0..k-1} = k edges.
    Need to add edges to cover A-A pairs and remaining A-B pairs.
    Budget: 4k-3 - k = 3k-3 more edges.
    """
    n = 2*k
    all_timed = biclique_to_timed_edges(M, k)
    target = compute_reachability(n, sorted(all_timed))

    # Star edges
    star = {(hub_row, j) for j in range(k)}
    current_edges = set(star)

    budget = 4*k - 3 - k  # 3k-3

    for step in range(budget):
        cur_timed = sorted([(M[i][j], i, k+j) for i, j in current_edges])
        cur_reach = compute_reachability(n, cur_timed)
        if cur_reach == target:
            return len(current_edges), True

        cur_count = len(cur_reach)
        best_e, best_g = None, 0
        for i in range(k):
            for j in range(k):
                if (i, j) in current_edges:
                    continue
                trial = current_edges | {(i, j)}
                trial_timed = sorted([(M[ii][jj], ii, k+jj) for ii, jj in trial])
                g = len(compute_reachability(n, trial_timed)) - cur_count
                if g > best_g:
                    best_g = g
                    best_e = (i, j)

        if best_e is None or best_g <= 0:
            break
        current_edges.add(best_e)

    cur_timed = sorted([(M[i][j], i, k+j) for i, j in current_edges])
    final = compute_reachability(n, cur_timed)
    return len(current_edges), final == target


def main():
    print("LIVE/DZ framework on bicliques")
    print("=" * 70)

    for k in range(3, 9):
        n = 2*k
        budget = 4*k - 3
        samples = 500 if k <= 6 else 100

        # Column relay analysis
        relay_counts = []
        min_relay_per_pair = []

        # Hub row spanner
        hub_sizes = []
        hub_success = 0

        for trial in range(samples):
            M = generate_biclique(k)

            # Column relays for A-A pairs
            col_relays = column_relay_analysis(M, k)
            min_relay = min(len(v) for v in col_relays.values())
            avg_relay = sum(len(v) for v in col_relays.values()) / len(col_relays)
            relay_counts.append(avg_relay)
            min_relay_per_pair.append(min_relay)

            # Try hub row spanner (best hub row)
            best_size = 999
            best_ok = False
            for h in range(k):
                size, ok = hub_row_spanner(M, k, h)
                if ok and size < best_size:
                    best_size = size
                    best_ok = ok

            if best_ok:
                hub_sizes.append(best_size)
                if best_size <= budget:
                    hub_success += 1

        avg_relay_count = sum(relay_counts) / len(relay_counts)
        avg_min = sum(min_relay_per_pair) / len(min_relay_per_pair)
        min_min = min(min_relay_per_pair)

        print(f"\nK_{{{k},{k}}} (n={n}, budget={budget}):")
        print(f"  Column relays per A-A pair: mean={avg_relay_count:.1f}, "
              f"min_per_instance mean={avg_min:.1f}, worst={min_min}")
        if hub_sizes:
            avg_size = sum(hub_sizes) / len(hub_sizes)
            print(f"  Hub row spanner: mean size={avg_size:.1f}, "
                  f"within budget={hub_success}/{samples} "
                  f"({100*hub_success/samples:.1f}%)")
        else:
            print(f"  Hub row spanner: no valid hub found")


if __name__ == '__main__':
    main()
