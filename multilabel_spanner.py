"""
Does adding one more timestamp per edge make the spanner problem trivial?

Model: each edge of K_n has TWO timestamps. A journey uses edges with
non-decreasing timestamps, and can choose EITHER label per edge.

Question: what's the minimum spanner size?
- At k=1 labels: 2n-3 conjectured
- At k=2 labels: ? (this test)
- At k=∞ labels: n-1 (static spanning tree)

If k=2 is trivially O(n), we have an easy warm-up. If it's still 2n-3,
it's not easier.
"""

import random

random.seed(42)


def compute_reachability_multilabel(n, edges_with_labels):
    """edges_with_labels: list of (u, v, [t1, t2, ...]).
    A journey can use any label of each edge."""
    # Expand to single-label list: each label is a separate "edge event"
    expanded = []
    for u, v, labels in edges_with_labels:
        for t in labels:
            expanded.append((t, u, v))

    reached_by = [dict() for _ in range(n)]
    for i in range(n):
        reached_by[i][i] = 0
    for t, u, v in sorted(expanded):
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


def min_spanner_size(n, edges_with_labels):
    """Find the minimum spanner size by greedy from all hubs."""
    full_reach = compute_reachability_multilabel(n, edges_with_labels)
    best = n * n

    for hub in range(n):
        star_edges = set()
        for i, (u, v, labels) in enumerate(edges_with_labels):
            if u == hub or v == hub:
                star_edges.add(i)

        current = set(star_edges)
        remaining = [i for i in range(len(edges_with_labels))
                     if i not in current]

        while True:
            sub = [edges_with_labels[i] for i in current]
            cur_reach = compute_reachability_multilabel(n, sub)
            if cur_reach == full_reach:
                break
            cur_count = len(cur_reach)
            best_i, best_g = None, 0
            for i in remaining:
                if i in current:
                    continue
                sub_trial = [edges_with_labels[j] for j in current | {i}]
                g = len(compute_reachability_multilabel(n, sub_trial)) - cur_count
                if g > best_g:
                    best_g = g
                    best_i = i
            if best_i is None or best_g <= 0:
                break
            current.add(best_i)

        sub = [edges_with_labels[i] for i in current]
        if compute_reachability_multilabel(n, sub) == full_reach:
            if len(current) < best:
                best = len(current)

    return best


def main():
    print("Multi-label spanner size vs number of labels per edge")
    print("=" * 70)

    for n in range(4, 10):
        m = n * (n - 1) // 2
        budget_conjecture = 2 * n - 3

        print(f"\nn={n} (conjecture 2n-3={budget_conjecture}, n-1={n-1}):")

        for k_labels in [1, 2, 3, 5, 10]:
            samples = 30 if n <= 7 else 10
            total_tlabels = m * k_labels

            sizes = []
            for trial in range(samples):
                # Generate timestamps: m*k_labels distinct values
                all_ts = list(range(1, total_tlabels + 1))
                random.shuffle(all_ts)

                edges_with_labels = []
                idx = 0
                for i in range(n):
                    for j in range(i + 1, n):
                        labels = sorted(all_ts[idx:idx + k_labels])
                        edges_with_labels.append((i, j, labels))
                        idx += k_labels

                size = min_spanner_size(n, edges_with_labels)
                sizes.append(size)

            avg = sum(sizes) / len(sizes)
            mx = max(sizes)
            mn = min(sizes)
            print(f"  k={k_labels:3d} labels: mean={avg:.1f}, min={mn}, max={mx}")


if __name__ == '__main__':
    main()
