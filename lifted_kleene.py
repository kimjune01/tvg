"""
Lifted temporal semiring and Kleene star for non-dismountable bicliques.

Praprotnik & Batagelj (2016): temporal quantities (sets of valid departure-arrival
pairs) form a semiring under union (⊕) and temporal composition (⊗). The Kleene
star A* = I ⊕ A ⊕ A² ⊕ ... computes all valid temporal journeys.

Key question: for non-dismountable bicliques, is A*[b_j1][b_j2] always non-empty
for connected column pairs? When the 2-hop relay M[i][j1] ≤ M[i][j2] fails for
all rows i, does a multi-hop relay always rescue connectivity?
"""

import random
from itertools import combinations


# ---------------------------------------------------------------------------
# Lifted temporal semiring
# ---------------------------------------------------------------------------

def pareto_prune(pairs):
    """Keep only Pareto-optimal (departure, arrival) pairs.
    Remove (d1, a1) if ∃ (d2, a2) with d2 ≥ d1 and a2 ≤ a1 (dominates).
    We want: latest possible departure, earliest possible arrival.
    Actually for journey composition we want: for each departure time,
    the earliest arrival; for each arrival time, the latest departure.
    Prune dominated pairs where another pair departs same-or-later AND
    arrives same-or-earlier.
    """
    if len(pairs) <= 1:
        return pairs
    pts = sorted(pairs)  # sort by departure asc, then arrival asc
    # Keep Pareto front: as departure increases, arrival should decrease
    # (otherwise the earlier-departing pair with same-or-earlier arrival dominates)
    result = []
    min_arrival = float('inf')
    for d, a in reversed(pts):  # scan from latest departure
        if a < min_arrival:
            result.append((d, a))
            min_arrival = a
    return set(result)


def semiring_add(A, B):
    """⊕ = union of journey pairs, then prune."""
    return pareto_prune(A | B)


def semiring_mul(A, B):
    """⊗ = temporal composition.
    {(d1, a2) | (d1, a1) ∈ A, (d2, a2) ∈ B, a1 ≤ d2}
    """
    if not A or not B:
        return set()
    # Sort B by departure for efficiency
    B_sorted = sorted(B)
    result = set()
    for d1, a1 in A:
        for d2, a2 in B_sorted:
            if a1 <= d2:
                result.add((d1, a2))
    return pareto_prune(result)


# ---------------------------------------------------------------------------
# Matrix operations over the semiring
# ---------------------------------------------------------------------------

def mat_add(X, Y, n):
    """Elementwise ⊕."""
    return [[semiring_add(X[i][j], Y[i][j]) for j in range(n)] for i in range(n)]


def mat_mul(X, Y, n):
    """Matrix multiplication over the semiring."""
    Z = [[set() for _ in range(n)] for _ in range(n)]
    for i in range(n):
        for j in range(n):
            acc = set()
            for m in range(n):
                acc = semiring_add(acc, semiring_mul(X[i][m], Y[m][j]))
            Z[i][j] = acc
    return Z


def mat_eq(X, Y, n):
    """Check if two matrices are equal."""
    for i in range(n):
        for j in range(n):
            if X[i][j] != Y[i][j]:
                return False
    return True


def kleene_star(A, n):
    """Compute A* = I ⊕ A ⊕ A² ⊕ A³ ⊕ ...
    Identity: I[v][v] = {(t,t) for all t that appear as timestamps}.
    Iterate until stable.
    """
    # Collect all timestamps
    all_times = set()
    for i in range(n):
        for j in range(n):
            for d, a in A[i][j]:
                all_times.add(d)
                all_times.add(a)
    all_times.add(0)

    # Identity matrix
    I = [[set() for _ in range(n)] for _ in range(n)]
    identity_elem = {(t, t) for t in all_times}
    for v in range(n):
        I[v][v] = identity_elem

    # S = I ⊕ A
    S = mat_add(I, A, n)
    power = [[set(A[i][j]) for j in range(n)] for i in range(n)]

    for iteration in range(2 * n):
        power = mat_mul(power, A, n)
        S_new = mat_add(S, power, n)
        if mat_eq(S_new, S, n):
            break
        S = S_new

    return S


# ---------------------------------------------------------------------------
# Biclique construction
# ---------------------------------------------------------------------------

def build_cross_matrix_sm(k):
    """SM(k) cross-edge timestamp matrix M[i][j].
    Edge (a_i, b_j) has label (j - i) mod k.
    Timestamps assigned by label value, then by i within each label.
    Internal V- edges get earliest timestamps, cross edges middle, V+ latest.
    Returns M, internal_minus, internal_plus dicts.
    """
    t = 1

    # V- internal edges: earliest timestamps
    internal_minus = {}
    for i1 in range(k):
        for i2 in range(i1 + 1, k):
            internal_minus[(i1, i2)] = t
            t += 1

    # Cross edges: middle timestamps, ordered by label
    M = [[0] * k for _ in range(k)]
    for label_val in range(k):
        for i in range(k):
            j = (i + label_val) % k
            M[i][j] = t
            t += 1

    # V+ internal edges: latest timestamps
    internal_plus = {}
    for j1 in range(k):
        for j2 in range(j1 + 1, k):
            internal_plus[(j1, j2)] = t
            t += 1

    return M, internal_minus, internal_plus


def build_cross_matrix_random(k):
    """Random non-dismountable biclique.
    V- internal: timestamps 1..k(k-1)/2
    Cross: random permutation of next k^2 timestamps
    V+ internal: timestamps after cross
    Returns M, internal_minus, internal_plus dicts.
    """
    t = 1

    # V- internal edges
    internal_minus = {}
    pairs_minus = [(i1, i2) for i1 in range(k) for i2 in range(i1 + 1, k)]
    random.shuffle(pairs_minus)
    for (i1, i2) in pairs_minus:
        internal_minus[(i1, i2)] = t
        t += 1

    # Cross edges: random permutation
    cross_timestamps = list(range(t, t + k * k))
    random.shuffle(cross_timestamps)
    M = [[0] * k for _ in range(k)]
    idx = 0
    for i in range(k):
        for j in range(k):
            M[i][j] = cross_timestamps[idx]
            idx += 1
    t += k * k

    # V+ internal edges
    internal_plus = {}
    pairs_plus = [(j1, j2) for j1 in range(k) for j2 in range(j1 + 1, k)]
    random.shuffle(pairs_plus)
    for (j1, j2) in pairs_plus:
        internal_plus[(j1, j2)] = t
        t += 1

    return M, internal_minus, internal_plus


def build_adjacency_matrix(M, k, internal_minus=None, internal_plus=None):
    """Build 2k × 2k lifted temporal adjacency matrix from cross-edge matrix M.
    Vertices: a_0..a_{k-1} (indices 0..k-1), b_0..b_{k-1} (indices k..2k-1).
    A[a_i][b_j] = A[b_j][a_i] = {(M[i][j], M[i][j])}.
    internal_minus: dict of (i1,i2) -> timestamp for V- internal edges
    internal_plus: dict of (j1,j2) -> timestamp for V+ internal edges
    """
    n = 2 * k
    A = [[set() for _ in range(n)] for _ in range(n)]

    for i in range(k):
        for j in range(k):
            t = M[i][j]
            pair = {(t, t)}
            A[i][k + j] = pair        # a_i -> b_j
            A[k + j][i] = set(pair)    # b_j -> a_i

    if internal_minus:
        for (i1, i2), t in internal_minus.items():
            A[i1][i2] = semiring_add(A[i1][i2], {(t, t)})
            A[i2][i1] = semiring_add(A[i2][i1], {(t, t)})

    if internal_plus:
        for (j1, j2), t in internal_plus.items():
            A[k + j1][k + j2] = semiring_add(A[k + j1][k + j2], {(t, t)})
            A[k + j2][k + j1] = semiring_add(A[k + j2][k + j1], {(t, t)})

    return A, n


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def check_relay(M, k, star):
    """Check relay constraint for all b_j1 -> b_j2 column pairs.
    Returns (two_hop_ok, multi_hop_rescued, both_fail) counts.
    """
    n = 2 * k
    two_hop_ok = 0
    multi_hop_rescued = 0
    both_fail = 0

    for j1 in range(k):
        for j2 in range(k):
            if j1 == j2:
                continue

            # 2-hop check: ∃i with M[i][j1] ≤ M[i][j2]
            has_2hop = any(M[i][j1] <= M[i][j2] for i in range(k))

            # Kleene star check: A*[b_j1][b_j2] non-empty
            star_entry = star[k + j1][k + j2]
            has_path = len(star_entry) > 0

            if has_2hop:
                two_hop_ok += 1
            elif has_path:
                multi_hop_rescued += 1
            else:
                both_fail += 1

    return two_hop_ok, multi_hop_rescued, both_fail


def analyze_sm(k):
    """Analyze SM(k)."""
    M, im, ip = build_cross_matrix_sm(k)
    A, n = build_adjacency_matrix(M, k, im, ip)
    star = kleene_star(A, n)
    return check_relay(M, k, star)


def analyze_random(k, samples=1000):
    """Analyze random non-dismountable bicliques."""
    totals = [0, 0, 0]
    for s in range(samples):
        M, im, ip = build_cross_matrix_random(k)
        A, n = build_adjacency_matrix(M, k, im, ip)
        star = kleene_star(A, n)
        counts = check_relay(M, k, star)
        for i in range(3):
            totals[i] += counts[i]
        if (s + 1) % 200 == 0:
            print(f"  k={k}: {s+1}/{samples} samples done...", flush=True)
    return totals


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def analyze_random_cross_only(k, samples=1000):
    """Analyze random bicliques with cross edges ONLY (no internal edges)."""
    totals = [0, 0, 0]
    for s in range(samples):
        M, _, _ = build_cross_matrix_random(k)
        A, n = build_adjacency_matrix(M, k)  # no internal edges
        star = kleene_star(A, n)
        counts = check_relay(M, k, star)
        for i in range(3):
            totals[i] += counts[i]
    return totals


def find_failure_example(k):
    """Find and diagnose a specific failure for random cross-only biclique."""
    for attempt in range(10000):
        M, im, ip = build_cross_matrix_random(k)
        A, n = build_adjacency_matrix(M, k, im, ip)
        star = kleene_star(A, n)
        for j1 in range(k):
            for j2 in range(k):
                if j1 == j2:
                    continue
                has_2hop = any(M[i][j1] <= M[i][j2] for i in range(k))
                has_path = len(star[k + j1][k + j2]) > 0
                if not has_2hop and not has_path:
                    return M, im, ip, j1, j2, star
    return None


if __name__ == "__main__":
    print("=" * 70)
    print("LIFTED TEMPORAL SEMIRING — KLEENE STAR RELAY ANALYSIS")
    print("=" * 70)

    # SM(k) analysis with full graph (internal edges included)
    print("\n--- SM(k) shifted matching bicliques (FULL GRAPH) ---\n")
    print(f"{'k':>3}  {'pairs':>6}  {'2-hop OK':>8}  {'multi-hop rescue':>16}  {'FAIL':>6}")
    print("-" * 50)
    for k in range(3, 8):
        total_pairs = k * (k - 1)
        two_hop, multi_hop, fail = analyze_sm(k)
        print(f"{k:>3}  {total_pairs:>6}  {two_hop:>8}  {multi_hop:>16}  {fail:>6}")
        if fail > 0:
            print(f"  *** CONJECTURE FAILS for SM({k})! ***")
    print()

    # Random biclique analysis WITH internal edges
    print("--- Random bicliques WITH internal edges (1000 samples) ---\n")
    print(f"{'k':>3}  {'samples':>8}  {'total pairs':>12}  {'2-hop OK':>8}  "
          f"{'multi-hop':>10}  {'FAIL':>6}")
    print("-" * 60)
    for k in range(3, 6):
        samples = 1000
        total_pairs_per = k * (k - 1)
        two_hop, multi_hop, fail = analyze_random(k, samples)
        total_pairs = total_pairs_per * samples
        print(f"{k:>3}  {samples:>8}  {total_pairs:>12}  {two_hop:>8}  "
              f"{multi_hop:>10}  {fail:>6}")
        if fail > 0:
            print(f"  *** CONJECTURE FAILS for random k={k}! ***")
            print(f"      {fail}/{total_pairs} pairs had no temporal path")
    print()

    # Random biclique analysis CROSS-ONLY (for comparison)
    print("--- Random bicliques CROSS EDGES ONLY (200 samples) ---\n")
    print(f"{'k':>3}  {'samples':>8}  {'total pairs':>12}  {'2-hop OK':>8}  "
          f"{'multi-hop':>10}  {'FAIL':>6}")
    print("-" * 60)
    for k in range(3, 6):
        samples = 200
        total_pairs_per = k * (k - 1)
        two_hop, multi_hop, fail = analyze_random_cross_only(k, samples)
        total_pairs = total_pairs_per * samples
        print(f"{k:>3}  {samples:>8}  {total_pairs:>12}  {two_hop:>8}  "
              f"{multi_hop:>10}  {fail:>6}")
        if fail > 0:
            print(f"      {fail}/{total_pairs} pairs had no temporal path (cross-only)")
    print()

    # Diagnose a failure
    print("--- Diagnosing a failure case (k=3, with internal edges) ---\n")
    result = find_failure_example(3)
    if result:
        M, im, ip, j1, j2, star = result
        k = 3
        print(f"Cross-edge matrix M[i][j]:")
        for i in range(k):
            print(f"  row {i}: {M[i]}")
        print(f"\nV- internal edges: {im}")
        print(f"V+ internal edges: {ip}")
        print(f"\nFailing pair: b_{j1} -> b_{j2}")
        print(f"  2-hop relays M[i][{j1}] vs M[i][{j2}]:")
        for i in range(k):
            direction = "<=" if M[i][j1] <= M[i][j2] else ">"
            print(f"    row {i}: M[{i}][{j1}]={M[i][j1]} {direction} M[{i}][{j2}]={M[i][j2]}")
        print(f"  Kleene star entry: {star[k + j1][k + j2]}")
        print(f"  (empty = no temporal journey exists)")
    else:
        print("No failure found in 10000 attempts! Conjecture may hold with internal edges.")

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("If FAIL=0 with internal edges: the Kleene star closure always provides")
    print("multi-hop relays when direct 2-hop relays are unavailable, but ONLY")
    print("when internal edges (within V- and V+) are present.")
    print("=" * 70)
