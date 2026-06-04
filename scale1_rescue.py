"""
Test the Scale-1 Rescue Lemma:

For every temporal K_n, every hub h, and every scale-1 backward pair
(v_{j+1}, v_j), does at least one compatible Route A or Route B relay
exist among the non-star edges?

Route A relay for (v_{j+1}, v_j): vertex v_a with a ≤ j,
  tree edge {v_{j+1}, v_a} with τ ≤ T_a.

Route B relay for (v_{j+1}, v_j): vertex v_a with a ≥ j+1,
  tree edge {v_a, v_j} with τ ≥ T_a.
  (a ≥ j+1 means a = j+1 or higher; but a = j+1 = source, so a ≥ j+2)

Actually a ≥ i = j+1, so a > j+1 means a ≥ j+2. With a = j+1 being
the source itself, Route B relay needs a ≥ j+2.

Route B relays: n-1-(j+1) = n-2-j vertices.
Route A relays: j vertices.
Total: j + (n-2-j) = n-2 relays.

For the extremes:
- j=1: Route A has 1 relay (v_1), Route B has n-3.
- j=n-2: Route A has n-2 relays, Route B has 0.
"""

import random
from collections import Counter

random.seed(42)


def test_scale1_lemma(n, timestamps, hub):
    """Check if every scale-1 backward pair has ≥1 compatible relay."""
    # Get star timestamps and ordering
    non_hub = [v for v in range(n) if v != hub]
    star_times = {v: timestamps[(min(hub, v), max(hub, v))] for v in non_hub}

    # Sort by star timestamp
    ordered = sorted(non_hub, key=lambda v: star_times[v])
    T = {v: star_times[v] for v in ordered}  # T[v] = star timestamp of v
    rank = {v: i for i, v in enumerate(ordered)}  # 0-indexed rank

    failures = []

    for j in range(len(ordered) - 1):
        # Scale-1 backward pair: (ordered[j+1], ordered[j])
        # Source = ordered[j+1] (higher star time), target = ordered[j]
        src = ordered[j + 1]
        tgt = ordered[j]

        has_rescue = False

        # Route A: src → v_a (tree) → h → tgt (star)
        # Need a with rank ≤ j, tree edge {src, a} with τ ≤ T[a], T[a] ≤ T[tgt]
        # rank(a) ≤ j means T[a] ≤ T[tgt] automatically
        for a_rank in range(j + 1):  # a_rank = 0, ..., j
            a = ordered[a_rank]
            e = (min(src, a), max(src, a))
            if e in timestamps:
                tau = timestamps[e]
                if tau <= T[a]:
                    has_rescue = True
                    break

        if has_rescue:
            continue

        # Route B: src → h → v_a (star) → tgt (tree)
        # Need a with rank ≥ j+1 (but a ≠ src, so rank ≥ j+2)
        # T[a] ≥ T[src], tree edge {a, tgt} with τ ≥ T[a]
        for a_rank in range(j + 2, len(ordered)):
            a = ordered[a_rank]
            e = (min(a, tgt), max(a, tgt))
            if e in timestamps:
                tau = timestamps[e]
                if tau >= T[a]:
                    has_rescue = True
                    break

        if not has_rescue:
            failures.append((j, src, tgt))

    return failures


def main():
    print("Scale-1 Rescue Lemma test")
    print("=" * 60)

    for n in [6, 8, 10, 12, 15, 20, 30]:
        m = n * (n - 1) // 2
        edges = [(i, j) for i in range(n) for j in range(i + 1, n)]

        if n <= 10:
            samples = 10000
        elif n <= 20:
            samples = 5000
        else:
            samples = 2000

        total_pairs_checked = 0
        total_failures = 0
        instances_with_failure = 0
        failure_positions = Counter()  # which j values fail?

        for trial in range(samples):
            ts_vals = list(range(1, m + 1))
            random.shuffle(ts_vals)
            timestamps = {e: t for e, t in zip(edges, ts_vals)}

            # Check all hubs
            worst_hub_failures = 0
            for hub in range(n):
                failures = test_scale1_lemma(n, timestamps, hub)
                total_pairs_checked += n - 2  # n-2 scale-1 pairs per hub
                total_failures += len(failures)
                worst_hub_failures = max(worst_hub_failures, len(failures))
                for j, src, tgt in failures:
                    failure_positions[j] += 1

            if worst_hub_failures > 0:
                instances_with_failure += 1

        fail_rate = 100 * total_failures / total_pairs_checked if total_pairs_checked > 0 else 0
        inst_rate = 100 * instances_with_failure / samples

        print(f"\nK_{n}: {samples} instances, {total_pairs_checked} pair-hub checks")
        print(f"  Scale-1 failures: {total_failures} ({fail_rate:.4f}%)")
        print(f"  Instances with any failure: {instances_with_failure} ({inst_rate:.2f}%)")

        if failure_positions:
            print(f"  Failure position distribution (rank j):")
            for j in sorted(failure_positions):
                print(f"    j={j}: {failure_positions[j]}")


if __name__ == '__main__':
    main()
