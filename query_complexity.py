"""
Query complexity lower bound for hub certification in temporal bicliques.

H2: How many entries of the k×k timestamp matrix M must an algorithm
read before it can certify a valid hub for the double-star construction?

Two experiments:
1. Adaptive query simulation: try several query orderings, measure how
   many entries are needed before ANY hub can be certified.
2. Minimum certificate size: for each valid hub, what is the smallest
   set of entries that proves it works?

The double-star construction picks hub row h, hub col c (with m⁺(h)=c),
builds M⁻ ∪ M⁺ ∪ star(h) ∪ star(c). This is a valid spanner iff
every ordered pair is temporally reachable through this edge set.

A hub (h,c) is valid when the 3-hop chains work for all pairs:
  Forward:  a_i → b_c → a_h → b_j  needs M[i][c] < M[h][c] < M[h][j]
  Reverse:  b_j → a_h → b_c → a_i  needs M[h][j] < M[h][c] < M[i][c]
Plus the M⁻/M⁺ matchings route the remaining pairs.

Key question: does certificate size grow as Θ(k) or Θ(k²)?
"""

import random
from itertools import combinations
from collections import defaultdict
import time

random.seed(42)


# ─── Matrix generation ───────────────────────────────────────────────

def generate_sm_matrix(k):
    """Standard monotone matrix SM(k): diagonal-first ordering."""
    M = [[0] * k for _ in range(k)]
    t = 1
    for d in range(k):
        for i in range(k):
            j = (i + d) % k
            M[i][j] = t
            t += 1
    return M


def generate_random_biclique(k):
    """Random k×k biclique with all-distinct timestamps respecting
    M⁻ and M⁺ constraints (topological sort of ordering DAG)."""
    for _ in range(1000):
        m_minus = list(range(k))
        random.shuffle(m_minus)
        m_plus = list(range(k))
        random.shuffle(m_plus)

        # Build ordering DAG on k² entries
        edge_idx = {(i, j): i * k + j for i in range(k) for j in range(k)}
        adj = [[] for _ in range(k * k)]
        in_degree = [0] * (k * k)

        # M⁻[j] = m_minus[j] means M[m_minus[j]][j] < M[i][j] for all i != m_minus[j]
        for j in range(k):
            src = edge_idx[(m_minus[j], j)]
            for i in range(k):
                if i != m_minus[j]:
                    adj[src].append(edge_idx[(i, j)])
                    in_degree[edge_idx[(i, j)]] += 1

        # M⁺[i] = m_plus[i] means M[i][m_plus[i]] > M[i][j] for all j != m_plus[i]
        for i in range(k):
            dst = edge_idx[(i, m_plus[i])]
            for jj in range(k):
                if jj != m_plus[i]:
                    adj[edge_idx[(i, jj)]].append(dst)
                    in_degree[dst] += 1

        # Topological sort with randomized tie-breaking
        queue = [i for i in range(k * k) if in_degree[i] == 0]
        order = []
        while queue:
            random.shuffle(queue)
            node = queue.pop()
            order.append(node)
            for nb in adj[node]:
                in_degree[nb] -= 1
                if in_degree[nb] == 0:
                    queue.append(nb)

        if len(order) != k * k:
            continue

        M = [[0] * k for _ in range(k)]
        for rank, node in enumerate(order):
            i, j = node // k, node % k
            M[i][j] = rank + 1
        return M, m_minus, m_plus
    return None


# ─── Reachability check ──────────────────────────────────────────────

def compute_reachability_pairs(n, timed_edges):
    """All-pairs temporal reachability via forward sweep."""
    reached_by = [dict() for _ in range(n)]
    for i in range(n):
        reached_by[i][i] = 0
    for t, u, v in sorted(timed_edges):
        for s, arr in list(reached_by[u].items()):
            if arr <= t and (s not in reached_by[v] or t < reached_by[v][s]):
                reached_by[v][s] = t
        for s, arr in list(reached_by[v].items()):
            if arr <= t and (s not in reached_by[u] or t < reached_by[u][s]):
                reached_by[u][s] = t
    pairs = set()
    for v in range(n):
        for s in reached_by[v]:
            if s != v:
                pairs.add((s, v))
    return pairs


def is_valid_spanner(M, k, edges):
    """Check if edge set is a valid temporal spanner."""
    n = 2 * k
    full_timed = [(M[i][j], i, k + j) for i in range(k) for j in range(k)]
    full_pairs = compute_reachability_pairs(n, full_timed)
    span_timed = [(M[i][j], i, k + j) for i, j in edges]
    span_pairs = compute_reachability_pairs(n, span_timed)
    return full_pairs == span_pairs


def double_star_edges(k, m_minus, m_plus, h, c):
    """Build M⁻ ∪ M⁺ ∪ star(h) ∪ star(c)."""
    edges = set()
    for j in range(k):
        edges.add((m_minus[j], j))
    for i in range(k):
        edges.add((i, m_plus[i]))
    for j in range(k):
        edges.add((h, j))
    for i in range(k):
        edges.add((i, c))
    return edges


def get_matchings(M, k):
    m_minus = [min(range(k), key=lambda i: M[i][j]) for j in range(k)]
    m_plus = [max(range(k), key=lambda j: M[i][j]) for i in range(k)]
    return m_minus, m_plus


def find_valid_hubs(M, k):
    """Return list of (h, c) pairs that produce valid double-star spanners."""
    m_minus, m_plus = get_matchings(M, k)
    valid = []
    for h in range(k):
        c = m_plus[h]
        edges = double_star_edges(k, m_minus, m_plus, h, c)
        if is_valid_spanner(M, k, edges):
            valid.append((h, c))
    return valid, m_minus, m_plus


# ─── Experiment 1: Minimum certificate size ──────────────────────────

def hub_certificate_entries(M, k, h, c, m_minus, m_plus):
    """Find the minimum set of M entries needed to certify hub (h,c).

    To certify that (h,c) is a valid hub, we need to verify:
    1. m⁻ identities: for each column j, M[m⁻(j)][j] is min in column j
       → need all k entries in each column = k² entries (to confirm min)
       BUT we only need enough to confirm the argmin.
    2. m⁺ identities: for each row i, M[i][m⁺(i)] is max in row i
       → same issue
    3. Forward chain: M[i][c] < M[h][c] < M[h][j] for all i≠h, j≠c
    4. Reverse chain: M[h][j] < M[h][c] < M[i][c] for all j≠c, i≠h

    The NECESSARY entries for conditions 3+4 are:
    - M[h][c] (the pivot)
    - M[i][c] for all i (column c entries)
    - M[h][j] for all j (row h entries)
    That's 2k-1 entries for the chain conditions alone.

    For M⁻ verification: to certify m⁻(j) = r, we need M[r][j] and
    at least enough other entries in column j to prove r is the argmin.
    In the worst case, we need ALL k entries in column j.

    For M⁺ verification: similarly for rows.

    Let's compute the minimum certificate more carefully by tracking
    which entries are ESSENTIAL (removing any one breaks the proof).
    """

    # Approach: start with all k² entries, then try removing each one.
    # An entry is dispensable if we can still certify the hub without it.
    # Use greedy removal to find a small certificate.

    all_entries = [(i, j) for i in range(k) for j in range(k)]

    def can_certify_hub(known_entries, M, k, h, c):
        """Given a subset of revealed entries, can we certify (h,c)?

        We can certify if:
        1. We can determine m⁻(j) for all j from known entries
        2. We can determine m⁺(i) for all i from known entries
        3. All chain conditions are verifiable from known entries
        """
        known_set = set(known_entries)
        known_vals = {(i, j): M[i][j] for i, j in known_entries}

        # Check 1: Can we certify m⁻(j) for each column j?
        for j in range(k):
            col_entries = [(i, j) for i in range(k) if (i, j) in known_set]
            if not col_entries:
                return False
            min_i = min(col_entries, key=lambda e: M[e[0]][e[1]])[0]
            # We know min_i has the smallest value among KNOWN entries.
            # But there might be unknown entries that are smaller.
            unknown_in_col = [i for i in range(k) if (i, j) not in known_set]
            if unknown_in_col:
                # Can't certify m⁻(j) — unknown entries might be smaller
                # UNLESS min_i == m_minus[j] and we can prove it
                # Actually: we CAN'T certify without seeing all entries
                # in the column, unless we have other information.
                # Conservative: require all column entries known.
                return False

        # Check 2: Can we certify m⁺(i) for each row i?
        for i in range(k):
            row_entries = [(i, j) for j in range(k) if (i, j) in known_set]
            if not row_entries:
                return False
            unknown_in_row = [j for j in range(k) if (i, j) not in known_set]
            if unknown_in_row:
                return False

        # Check 3: Chain conditions (all entries known at this point)
        # Forward: M[i][c] < M[h][c] < M[h][j] for all i≠h, j≠c
        for i in range(k):
            if i == h:
                continue
            if M[i][c] >= M[h][c]:
                return False  # chain fails — hub is actually invalid
        for j in range(k):
            if j == c:
                continue
            if M[h][j] <= M[h][c]:
                return False

        # Reverse: M[h][j] < M[h][c] < M[i][c] for all j≠c, i≠h
        # Wait — forward and reverse can't both hold simultaneously
        # unless M[h][c] is BOTH > all M[i][c] for i≠h AND < all M[i][c].
        # That's contradictory! Let me re-examine...
        #
        # Actually, the double-star routes DIFFERENT pairs through
        # different chains. Forward chain: a_i → b_c → a_h → b_j
        # covers (a_i → b_j). Reverse: b_j → a_h → b_c → a_i
        # covers (b_j → a_i). But M⁻ and M⁺ edges handle SOME pairs.
        # The chain conditions need not hold universally — only for
        # pairs not already covered by M⁻/M⁺.
        #
        # This makes the certificate MORE complex, not less.
        # For now, just check if it IS a valid spanner (full reachability).

        return True

    # Actually let's do this differently. The question is about the
    # information-theoretic certificate. Let's measure it empirically:
    # what is the minimum number of entries such that the revealed partial
    # matrix is ONLY consistent with matrices where (h,c) is a valid hub?

    # Simpler approach: greedy removal from full knowledge.
    # Start with all k² entries. Remove entries one at a time (random order).
    # After each removal, check: can we still PROVE the hub is valid?
    # "Prove" = every completion of unknown entries consistent with
    # the known entries still has (h,c) as a valid hub.
    #
    # This is expensive (exponential in unknowns). For small k, feasible.
    # For larger k, use the conservative check above.

    # For the conservative model: require all entries in row h, column c,
    # plus enough to certify m⁻ and m⁺.
    # Certificate = star(h) ∪ star(c) ∪ (entries needed for m⁻/m⁺)

    # Let's count the NECESSARY entries:
    star_h = {(h, j) for j in range(k)}           # k entries
    star_c = {(i, c) for i in range(k)}            # k entries
    matching_entries = set()

    # For m⁻(j): need to certify argmin. Need all entries in column j
    # (or at least enough to prove the minimum).
    # Conservative: all entries in each column.
    for j in range(k):
        for i in range(k):
            matching_entries.add((i, j))

    # That's k² = ALL entries. So the conservative certificate is k².
    # But that's trivially true and unhelpful.

    # Better: use the STRUCTURAL certificate.
    # What does the certifier actually need to verify?
    # 1. That m⁻(j) = claimed value for each j
    # 2. That m⁺(i) = claimed value for each i
    # 3. That the chain conditions hold
    #
    # For (1): to certify m⁻(j) = r, need M[r][j] < M[i][j] for all i≠r.
    #   That requires k entries in column j.
    # For (2): similarly k entries per row.
    # For (3): chain conditions on star(h) and star(c) — 2k-1 entries.
    #
    # But (1) already requires all k² entries (k entries × k columns).
    # So the m⁻ certificate alone is k².
    #
    # HOWEVER: do we really need to certify ALL of m⁻?
    # The double star only uses m⁻ edges for routing. If we already
    # know the chain conditions, maybe not all m⁻ edges matter?

    # Let's take a different approach: compute the actual minimum
    # certificate by greedy removal. For each entry NOT in the
    # certificate, check if removing it allows an adversarial
    # completion that invalidates the hub.

    # For small k (3,4,5), this is feasible via brute force.
    return None  # placeholder — real implementation below


def minimum_certificate_greedy(M, k, h, c, m_minus, m_plus):
    """Greedy removal: start with all entries, remove dispensable ones.

    An entry (i,j) is dispensable if EVERY completion of the matrix
    consistent with the remaining known entries still has (h,c) as
    a valid double-star hub.

    For tractability, we use a sufficient condition:
    an entry is NECESSARY if it participates in proving either:
    - an m⁻ identity (column minimum)
    - an m⁺ identity (row maximum)
    - a chain inequality for the hub
    """
    all_entries = [(i, j) for i in range(k) for j in range(k)]

    # Identify structurally necessary entries
    necessary = set()

    # Chain conditions require star(h) and star(c)
    for j in range(k):
        necessary.add((h, j))
    for i in range(k):
        necessary.add((i, c))

    # m⁻ certification: for each column j, need to verify m⁻(j)
    # We need M[m⁻(j)][j] and at least one comparison partner.
    # Actually need all k entries to prove argmin. But if we already
    # have star(h) and star(c), some entries are already in necessary.

    # m⁺ certification: same for rows.

    # Let's count: star(h) has k entries, star(c) has k entries,
    # overlap at (h,c). So |star(h) ∪ star(c)| = 2k-1.

    # For m⁻(j): the entries in column j are (0,j),(1,j),...,(k-1,j).
    # star(c) gives us column c entirely. For j≠c, we have (h,j) from star(h).
    # We still need the other k-1 entries in column j to certify m⁻(j).

    # For m⁺(i): row i entries are (i,0),(i,1),...,(i,k-1).
    # star(h) gives us row h entirely. For i≠h, we have (i,c) from star(c).
    # We still need k-1 entries in row i to certify m⁺(i).

    # So total needed for m⁻ certification:
    # Column c: already have all k (from star(c)) ✓
    # Column j≠c: have (h,j), need k-1 more = all remaining. Total per col: k.
    # → (k-1) columns × k entries = k(k-1), plus column c = k. Total = k².

    # This analysis shows k² is necessary under the conservative model.
    # But IS it truly necessary? Maybe we can certify with less if we
    # use cross-column information...

    # Let's just measure empirically. Try removing entries and check
    # if the hub is still certifiable.

    # Define "certifiable with partial info":
    # Given revealed entries R, hub (h,c) is certifiable if for EVERY
    # matrix M' consistent with R (same values at revealed positions,
    # all distinct, any values at unrevealed positions), the double-star
    # construction with (h,c) is a valid spanner of M'.

    # This is the information-theoretic certificate. Computing it exactly
    # requires checking all consistent completions — exponential.
    # For small k, we can sample completions instead.

    # Simpler proxy: compute the STRUCTURAL certificate.
    # Count entries needed for:
    # (a) star(h) ∪ star(c): 2k-1
    # (b) m⁻ certification: need all entries in each column
    # (c) m⁺ certification: need all entries in each row

    # Return the structural breakdown
    star_entries = set()
    for j in range(k):
        star_entries.add((h, j))
    for i in range(k):
        star_entries.add((i, c))

    return len(star_entries), 2 * k - 1


# ─── Experiment 1 (revised): Adaptive query simulation ───────────────

def can_certify_any_hub(revealed, M, k):
    """Given a set of revealed entries, can we certify ANY hub?

    Conservative check: a hub (h,c) is certifiable if:
    1. ALL entries in row h are revealed (to certify m⁺(h) and chains)
    2. ALL entries in column c are revealed (to certify m⁻(c) and chains)
    3. m⁺(h) = c is verified from row h entries
    4. For EVERY column j≠c: ALL entries in column j are revealed
       (to certify m⁻(j))
    5. For EVERY row i≠h: ALL entries in row i are revealed
       (to certify m⁺(i))
    6. The chain conditions hold

    Under this model, certification requires ALL k² entries.
    This is too conservative — it proves a trivial k² lower bound.

    Weaker model: "certify relative to known matchings."
    Assume m⁻ and m⁺ are given for free (they come from reading 2k entries
    that are forced anyway — the extremal edges). Then the hub question is:
    given m⁻, m⁺, and partial knowledge of M, can we certify (h,c)?

    The chain conditions for hub (h,c) require:
    - M[h][c] known (pivot value)
    - M[i][c] known for all i (to check M[i][c] < M[h][c] for i with
      certain properties, or M[i][c] > M[h][c] for the reverse chain)
    - M[h][j] known for all j (to check M[h][j] > M[h][c] etc.)
    That's 2k-1 entries for the chain conditions alone.

    But the chain conditions aren't the whole story. The double-star
    is valid iff ALL pairs are reachable. Some pairs route through
    M⁻/M⁺ edges, not through the hub chains. Whether those routes
    work depends on the full matrix structure, not just the hub's
    star entries.

    The most honest measurement: simulate the full spanner check.
    """
    revealed_set = set(revealed)

    # Check each candidate hub
    m_minus = [None] * k
    m_plus = [None] * k

    # Can we determine m⁻ from revealed entries?
    for j in range(k):
        col_entries = [(i, M[i][j]) for i in range(k) if (i, j) in revealed_set]
        if len(col_entries) < k:
            # Not all entries in column j revealed — can't certify m⁻(j)
            # unless the current min is below any possible unrevealed value.
            # But we don't know the range of unrevealed values in general.
            m_minus[j] = None
        else:
            m_minus[j] = min(col_entries, key=lambda x: x[1])[0]

    for i in range(k):
        row_entries = [(j, M[i][j]) for j in range(k) if (i, j) in revealed_set]
        if len(row_entries) < k:
            m_plus[i] = None
        else:
            m_plus[i] = max(row_entries, key=lambda x: x[1])[0]

    if None in m_minus or None in m_plus:
        return False, None

    # We know m⁻ and m⁺. Now check each hub candidate.
    for h in range(k):
        c = m_plus[h]
        # Check if all entries needed for the spanner check are revealed
        # The double star uses star(h), star(c), m⁻ edges, m⁺ edges.
        ds_edges = set()
        for j in range(k):
            ds_edges.add((m_minus[j], j))
        for i in range(k):
            ds_edges.add((i, m_plus[i]))
        for j in range(k):
            ds_edges.add((h, j))
        for i in range(k):
            ds_edges.add((i, c))

        # Need all these entries revealed to do reachability check
        if not ds_edges.issubset(revealed_set):
            continue

        # Full reachability check on the double-star
        if is_valid_spanner(M, k, ds_edges):
            return True, (h, c)

    return False, None


def can_certify_any_hub_relaxed(revealed, M, k):
    """Relaxed model: m⁻ and m⁺ given for free.

    Only count queries needed BEYOND the matchings.
    Certification requires:
    - star(h) entries revealed (for chain conditions)
    - star(c) entries revealed
    - Full spanner validity (reachability)
    """
    revealed_set = set(revealed)

    # m⁻ and m⁺ are free
    m_minus = [min(range(k), key=lambda i: M[i][j]) for j in range(k)]
    m_plus = [max(range(k), key=lambda j: M[i][j]) for i in range(k)]

    for h in range(k):
        c = m_plus[h]
        # Do we have star(h) ∪ star(c)?
        star_known = True
        for j in range(k):
            if (h, j) not in revealed_set:
                star_known = False
                break
        if not star_known:
            continue
        for i in range(k):
            if (i, c) not in revealed_set:
                star_known = False
                break
        if not star_known:
            continue

        # We know the hub's stars. Check spanner validity.
        ds_edges = set()
        for j in range(k):
            ds_edges.add((m_minus[j], j))
        for i in range(k):
            ds_edges.add((i, m_plus[i]))
        for j in range(k):
            ds_edges.add((h, j))
        for i in range(k):
            ds_edges.add((i, c))

        # For reachability check, we need timestamps of all ds_edges
        if not ds_edges.issubset(revealed_set):
            continue

        if is_valid_spanner(M, k, ds_edges):
            return True, (h, c)

    return False, None


def simulate_queries(M, k, query_order, model='conservative'):
    """Simulate adaptive queries in given order, return # needed."""
    certify_fn = (can_certify_any_hub if model == 'conservative'
                  else can_certify_any_hub_relaxed)
    revealed = []
    for idx, (i, j) in enumerate(query_order):
        revealed.append((i, j))
        found, hub = certify_fn(revealed, M, k)
        if found:
            return idx + 1, hub
    return len(query_order), None


def generate_query_orders(k):
    """Generate different query strategies."""
    all_entries = [(i, j) for i in range(k) for j in range(k)]

    # Random
    rand_order = list(all_entries)
    random.shuffle(rand_order)

    # Row-first: read row 0 fully, then row 1, etc.
    row_first = []
    for i in range(k):
        for j in range(k):
            row_first.append((i, j))

    # Column-first: read column 0 fully, then column 1, etc.
    col_first = []
    for j in range(k):
        for i in range(k):
            col_first.append((i, j))

    # Diagonal-first: main diagonal, then off-diagonals
    diag_first = []
    for d in range(k):
        for i in range(k):
            j = (i + d) % k
            diag_first.append((i, j))

    # Star-first: pick a candidate hub, read its star first
    # Read row 0, then column 0, then remaining
    star_first = []
    seen = set()
    for j in range(k):
        star_first.append((0, j))
        seen.add((0, j))
    for i in range(k):
        if (i, 0) not in seen:
            star_first.append((i, 0))
            seen.add((i, 0))
    for i, j in all_entries:
        if (i, j) not in seen:
            star_first.append((i, j))

    return {
        'random': rand_order,
        'row_first': row_first,
        'col_first': col_first,
        'diag_first': diag_first,
        'star_first': star_first,
    }


# ─── Experiment 2: True minimum certificate via greedy removal ───────

def minimum_certificate_by_removal(M, k, h, c, m_minus, m_plus):
    """Find minimum certificate by greedy removal from full matrix.

    Start with all k² entries. Shuffle order. Try removing each;
    if the remaining entries still certify the hub, remove it.

    "Still certify" means: given only the remaining entries,
    we can prove (h,c) is a valid hub. Conservative model:
    need to verify m⁻, m⁺, and chain conditions from revealed entries.

    For small k, we can check this by sampling adversarial completions.
    For now, use the structural check: all entries needed for m⁻/m⁺
    certification and chain conditions must be present.
    """
    all_entries = [(i, j) for i in range(k) for j in range(k)]
    certificate = set(all_entries)

    # Entries that are structurally necessary:
    # - star(h): needed for chain conditions
    # - star(c): needed for chain conditions
    # - For each column j: entries needed to prove m⁻(j)
    #   = all entries in column j (to verify argmin)
    # - For each row i: entries needed to prove m⁺(i)
    #   = all entries in row i (to verify argmax)
    #
    # Under this model, ALL k² entries are necessary.
    # This is the "naive" lower bound.

    # Better model: what if we get to assume the VALUES are all-distinct
    # integers from a known set? Then we can use ordering information.
    # E.g., if we know M[i][j] = 5 and M[i'][j] = 3 for the only two
    # unrevealed entries in column j, we can deduce the argmin.

    # For the information-theoretic model: we know that M uses a
    # permutation of {1,...,k²}. Revealed entries constrain the
    # unrevealed ones. The certificate is the set of entries such that
    # NO consistent completion of the unrevealed entries can invalidate
    # the hub.

    # Let's implement this properly for small k via brute force.
    # For k=3 (9 entries), we can enumerate completions.
    # For k=4 (16 entries), with ~8 unrevealed entries, 8! = 40320.
    # Feasible up to ~10 unrevealed.

    return len(certificate)  # placeholder


def check_all_completions(revealed_entries, revealed_vals, k, h, c, all_vals):
    """Check if (h,c) is a valid hub under ALL consistent completions.

    revealed_entries: list of (i,j) positions
    revealed_vals: dict (i,j) -> value
    k: matrix size
    h, c: hub row and column
    all_vals: set of all possible values {1,...,k²}

    Returns True if (h,c) is valid for every consistent completion.
    """
    unrevealed = [(i, j) for i in range(k) for j in range(k)
                  if (i, j) not in revealed_vals]
    remaining_vals = sorted(all_vals - set(revealed_vals.values()))

    if not unrevealed:
        # All entries known — just check directly
        M = [[0] * k for _ in range(k)]
        for (i, j), v in revealed_vals.items():
            M[i][j] = v
        m_minus = [min(range(k), key=lambda ii: M[ii][j]) for j in range(k)]
        m_plus = [max(range(k), key=lambda jj: M[i][jj]) for i in range(k)]
        if m_plus[h] != c:
            return False
        edges = double_star_edges(k, m_minus, m_plus, h, c)
        return is_valid_spanner(M, k, edges)

    if len(unrevealed) > 10:
        return None  # too many to enumerate

    from itertools import permutations
    for perm in permutations(remaining_vals):
        M = [[0] * k for _ in range(k)]
        for (i, j), v in revealed_vals.items():
            M[i][j] = v
        for idx, (i, j) in enumerate(unrevealed):
            M[i][j] = perm[idx]

        m_minus = [min(range(k), key=lambda ii: M[ii][j]) for j in range(k)]
        m_plus = [max(range(k), key=lambda jj: M[i][jj]) for i in range(k)]

        if m_plus[h] != c:
            return False  # some completion doesn't even have m⁺(h)=c

        edges = double_star_edges(k, m_minus, m_plus, h, c)
        if not is_valid_spanner(M, k, edges):
            return False

    return True


def find_minimum_certificate(M, k, h, c):
    """Find minimum certificate for hub (h,c) by greedy removal."""
    all_vals = set(M[i][j] for i in range(k) for j in range(k))
    all_entries = [(i, j) for i in range(k) for j in range(k)]
    revealed = dict()
    for i, j in all_entries:
        revealed[(i, j)] = M[i][j]

    # Try removing entries in random order
    removable = list(all_entries)
    random.shuffle(removable)

    for entry in removable:
        trial = dict(revealed)
        del trial[entry]

        result = check_all_completions(
            list(trial.keys()), trial, k, h, c, all_vals)

        if result is True:
            revealed = trial  # entry is dispensable

    return len(revealed)


# ─── Experiment 3: Spanner-validity certificate ──────────────────────

def find_validity_certificate(M, k, h, c, m_minus, m_plus):
    """What entries are needed to verify the spanner is VALID?

    The double-star edge set is determined by m⁻, m⁺, h, c.
    But to check that the spanner preserves all temporal reachability,
    we need the TIMESTAMPS of those edges (to run the reachability check).

    The edges in the double star are:
    - M⁻ edges: (m⁻(j), j) for each j
    - M⁺ edges: (i, m⁺(i)) for each i
    - star(h): (h, j) for each j
    - star(c): (i, c) for each i

    These overlap. The union has at most 4k-4 entries (at most 4 overlaps).
    Let's count exact needed entries.
    """
    edges = double_star_edges(k, m_minus, m_plus, h, c)
    return len(edges)


# ─── Main experiments ─────────────────────────────────────────────────

def experiment_1_query_simulation():
    """Experiment 1: How many queries until hub certification?"""
    print("=" * 70)
    print("EXPERIMENT 1: Adaptive Query Simulation")
    print("=" * 70)
    print()
    print("Model: conservative (must certify m⁻, m⁺, and validity from")
    print("revealed entries alone; no free information)")
    print()

    for k in range(3, 8):
        n_sq = k * k
        samples = min(50, max(5, 200 // k))
        results_by_strategy = defaultdict(list)

        for trial in range(samples):
            if k <= 5:
                result = generate_random_biclique(k)
            else:
                result = generate_random_biclique(k)
            if result is None:
                continue
            M, m_minus, m_plus = result

            # Check if any valid hub exists
            valid_hubs, _, _ = find_valid_hubs(M, k)
            if not valid_hubs:
                continue  # skip if no valid hub

            orders = generate_query_orders(k)
            for strategy, order in orders.items():
                nq, hub = simulate_queries(M, k, order, model='conservative')
                results_by_strategy[strategy].append(nq / n_sq)

        if not results_by_strategy:
            print(f"k={k}: no valid instances found")
            continue

        print(f"k={k} (k²={n_sq}): fraction of k² entries needed for certification")
        for strategy in ['random', 'row_first', 'col_first', 'diag_first', 'star_first']:
            vals = results_by_strategy[strategy]
            if vals:
                avg = sum(vals) / len(vals)
                mn = min(vals)
                mx = max(vals)
                print(f"  {strategy:12s}: avg={avg:.3f}, min={mn:.3f}, max={mx:.3f}")
        print()


def experiment_2_minimum_certificate():
    """Experiment 2: Minimum certificate size for hub verification."""
    print("=" * 70)
    print("EXPERIMENT 2: Minimum Certificate Size (greedy removal)")
    print("=" * 70)
    print()
    print("For each valid hub, find the smallest set of entries that")
    print("certifies it under ALL consistent matrix completions.")
    print()

    for k in range(3, 6):  # k≥6 too expensive for brute-force
        n_sq = k * k
        samples = min(30, max(5, 100 // k))
        certs = []
        hub_count = 0

        for trial in range(samples):
            result = generate_random_biclique(k)
            if result is None:
                continue
            M, m_minus, m_plus = result

            valid_hubs, _, _ = find_valid_hubs(M, k)
            if not valid_hubs:
                continue

            for h, c in valid_hubs[:2]:  # check up to 2 hubs per matrix
                cert_size = find_minimum_certificate(M, k, h, c)
                certs.append(cert_size)
                hub_count += 1

        if not certs:
            print(f"k={k}: no valid hubs found")
            continue

        avg_cert = sum(certs) / len(certs)
        min_cert = min(certs)
        max_cert = max(certs)
        print(f"k={k} (k²={n_sq}):")
        print(f"  hubs tested: {hub_count}")
        print(f"  certificate size: avg={avg_cert:.1f}, min={min_cert}, max={max_cert}")
        print(f"  fraction of k²:   avg={avg_cert/n_sq:.3f}, min={min_cert/n_sq:.3f}, max={max_cert/n_sq:.3f}")
        print(f"  ratio to k:       avg={avg_cert/k:.2f}, min={min_cert/k:.2f}, max={max_cert/k:.2f}")
        print()


def experiment_3_spanner_edge_certificate():
    """Experiment 3: How many entries define the spanner's edge set?

    This measures the structural certificate: the entries in the
    double-star edge set. If you know m⁻, m⁺, h, c, how many
    timestamps do you need to verify the spanner is valid?
    """
    print("=" * 70)
    print("EXPERIMENT 3: Spanner Edge Certificate Size")
    print("=" * 70)
    print()
    print("# entries in double_star_edges(h,c) = entries whose timestamps")
    print("are needed to verify temporal reachability of the spanner.")
    print()

    for k in range(3, 11):
        n_sq = k * k
        samples = min(100, max(10, 500 // k))
        edge_counts = []
        valid_hub_fracs = []

        for trial in range(samples):
            result = generate_random_biclique(k)
            if result is None:
                continue
            M, m_minus, m_plus = result

            valid_hubs, mm, mp = find_valid_hubs(M, k)
            if not valid_hubs:
                valid_hub_fracs.append(0)
                continue

            valid_hub_fracs.append(len(valid_hubs) / k)

            for h, c in valid_hubs[:1]:
                edges = double_star_edges(k, mm, mp, h, c)
                edge_counts.append(len(edges))

        if not edge_counts:
            print(f"k={k}: no valid hubs")
            continue

        avg_edges = sum(edge_counts) / len(edge_counts)
        avg_frac = sum(valid_hub_fracs) / len(valid_hub_fracs)
        print(f"k={k:2d} (k²={n_sq:3d}): "
              f"ds_edges={avg_edges:.1f} ({avg_edges/n_sq:.3f} of k²), "
              f"= {avg_edges/k:.2f}k, "
              f"valid_hub_frac={avg_frac:.2f}")


def experiment_4_what_must_be_read():
    """Experiment 4: Among entries NOT in the double-star, which are needed?

    The double-star edge set has ~4k-4 entries (star(h) + star(c) + m⁻ + m⁺).
    But to CERTIFY the hub, we might need entries OUTSIDE the star
    (to verify m⁻/m⁺ identities).

    For each column j: m⁻(j) = argmin_i M[i][j]. To certify this,
    we need to see enough entries in column j to prove no other entry
    is smaller. The star only gives us (h,j) in that column. If h ≠ m⁻(j),
    we need additional entries.

    Question: how many NON-star entries are needed for m⁻/m⁺ certification?
    """
    print("=" * 70)
    print("EXPERIMENT 4: Entries Beyond the Double Star")
    print("=" * 70)
    print()
    print("For each valid hub (h,c), the double-star edge set has ~4k-4 entries.")
    print("How many ADDITIONAL entries (outside star(h) ∪ star(c)) are needed")
    print("to certify m⁻ and m⁺?")
    print()

    for k in range(3, 11):
        samples = min(100, max(10, 500 // k))
        extra_counts = []

        for trial in range(samples):
            result = generate_random_biclique(k)
            if result is None:
                continue
            M, m_minus, m_plus = result

            valid_hubs, mm, mp = find_valid_hubs(M, k)
            if not valid_hubs:
                continue

            for h, c in valid_hubs[:1]:
                # Entries in star(h) ∪ star(c)
                star = set()
                for j in range(k):
                    star.add((h, j))
                for i in range(k):
                    star.add((i, c))

                # Entries needed for m⁻ certification (outside star)
                extra = set()
                for j in range(k):
                    # To certify m⁻(j) = mm[j], need ALL entries in col j
                    # that aren't already in the star.
                    for i in range(k):
                        if (i, j) not in star:
                            extra.add((i, j))

                # But wait: m⁺ certification too
                for i in range(k):
                    for j in range(k):
                        if (i, j) not in star:
                            extra.add((i, j))

                # extra = all entries not in star = k² - (2k-1)
                # This is ALWAYS k² - 2k + 1 = (k-1)². Trivially Θ(k²).
                #
                # The interesting question is whether we can AVOID reading
                # all these entries by using the ordering structure.

                extra_counts.append(len(extra))

        if not extra_counts:
            print(f"k={k}: no valid hubs")
            continue

        avg = sum(extra_counts) / len(extra_counts)
        print(f"k={k:2d}: entries outside star = {avg:.0f} = (k-1)² = {(k-1)**2}")


def experiment_5_adversarial_distinguishing():
    """Experiment 5: Adversarial distinguishing.

    Core question: given partial matrix knowledge, can an adversary
    present two completions — one where hub h works, one where it doesn't?

    For each hub h and each subset of entries of size s, check if there
    exist two completions that AGREE on the revealed entries but DISAGREE
    on whether h is a valid hub.

    If such pairs exist for all subsets of size < f(k), then f(k) queries
    are NECESSARY (information-theoretic lower bound).

    For small k, check by enumeration.
    """
    print("=" * 70)
    print("EXPERIMENT 5: Adversarial Distinguishing Pairs")
    print("=" * 70)
    print()
    print("For each k: among all k×k matrices with valid hub h, what is")
    print("the minimum # of entries that DISTINGUISH 'h works' from 'h fails'?")
    print()

    for k in [3, 4]:
        n_sq = k * k
        # Generate many matrices, some with valid hubs, some without
        with_hub = []
        without_hub = []

        for trial in range(200):
            result = generate_random_biclique(k)
            if result is None:
                continue
            M, m_minus, m_plus = result

            valid_hubs, _, _ = find_valid_hubs(M, k)
            flat = tuple(M[i][j] for i in range(k) for j in range(k))
            if valid_hubs:
                with_hub.append((M, valid_hubs, flat))
            else:
                without_hub.append((M, flat))

        print(f"k={k}: {len(with_hub)} matrices with valid hub, "
              f"{len(without_hub)} without")

        if not with_hub or not without_hub:
            print("  Need both types for distinguishing test — skip")
            continue

        # For each matrix with a valid hub: find the minimum number of entries
        # that, when revealed, are inconsistent with ALL hub-less matrices.
        # This is the information-theoretic certificate.
        #
        # Approximation: for each pair (M_yes, M_no), find the minimum
        # number of positions where they differ. The certificate must
        # include at least one entry from each differing pair.

        # Actually, let's measure something simpler:
        # For a matrix M with valid hub h=0, how many entries must be
        # revealed so that no matrix M' agreeing on revealed entries
        # has h=0 as an INVALID hub?

        # This is expensive. Let's just report the fraction of matrices
        # that have valid hubs.
        print(f"  Valid hub rate: {len(with_hub)}/{len(with_hub)+len(without_hub)} "
              f"= {len(with_hub)/(len(with_hub)+len(without_hub)):.2f}")

        # More useful: for each hub-valid matrix, how many entries can
        # be changed (one at a time) before the hub becomes invalid?
        fragility = []
        M_yes, hubs, _ = with_hub[0]
        h, c = hubs[0]
        m_minus_y = [min(range(k), key=lambda i: M_yes[i][j]) for j in range(k)]
        m_plus_y = [max(range(k), key=lambda j: M_yes[i][j]) for i in range(k)]

        # Count how many single-entry changes break the hub
        breaks = 0
        total_swaps = 0
        for i1 in range(k):
            for j1 in range(k):
                for i2 in range(k):
                    for j2 in range(k):
                        if (i1, j1) >= (i2, j2):
                            continue
                        # Swap M[i1][j1] and M[i2][j2]
                        M_test = [row[:] for row in M_yes]
                        M_test[i1][j1], M_test[i2][j2] = M_test[i2][j2], M_test[i1][j1]
                        # Check if hub still valid
                        mm = [min(range(k), key=lambda i: M_test[i][j]) for j in range(k)]
                        mp = [max(range(k), key=lambda j: M_test[i][j]) for i in range(k)]
                        if mp[h] != c:
                            breaks += 1
                        else:
                            edges = double_star_edges(k, mm, mp, h, c)
                            if not is_valid_spanner(M_test, k, edges):
                                breaks += 1
                        total_swaps += 1

        print(f"  Fragility of hub h={h},c={c} in first matrix:")
        print(f"    {breaks}/{total_swaps} swaps break the hub "
              f"({100*breaks/total_swaps:.1f}%)")
        print()


def experiment_6_certificate_scaling():
    """Experiment 6: Certificate scaling — the key measurement.

    For k=3,4,5: compute exact minimum certificate via greedy removal
    with adversarial completion checking. Report certificate/k and
    certificate/k² to determine Θ(k) vs Θ(k²) scaling.
    """
    print("=" * 70)
    print("EXPERIMENT 6: Certificate Scaling (Key Measurement)")
    print("=" * 70)
    print()
    print("Minimum certificate = smallest set of entries such that")
    print("ALL consistent completions agree the hub is valid.")
    print()

    results = {}
    for k in range(3, 6):
        n_sq = k * k
        samples = 20 if k <= 4 else 10
        certs = []

        t0 = time.time()
        for trial in range(samples):
            result = generate_random_biclique(k)
            if result is None:
                continue
            M, m_minus, m_plus = result

            valid_hubs, _, _ = find_valid_hubs(M, k)
            if not valid_hubs:
                continue

            h, c = valid_hubs[0]
            cert_size = find_minimum_certificate(M, k, h, c)
            certs.append(cert_size)

            if time.time() - t0 > 120:  # 2 min timeout per k
                print(f"  k={k}: timeout after {len(certs)} samples")
                break

        if not certs:
            print(f"k={k}: no data")
            continue

        avg = sum(certs) / len(certs)
        mn, mx = min(certs), max(certs)
        results[k] = avg

        print(f"k={k} (k²={n_sq}):")
        print(f"  samples: {len(certs)}")
        print(f"  certificate size: avg={avg:.1f}, min={mn}, max={mx}")
        print(f"  cert/k  = {avg/k:.2f}  (Θ(k) ⟹ constant)")
        print(f"  cert/k² = {avg/n_sq:.3f}  (Θ(k²) ⟹ constant)")
        print()

    # Scaling analysis
    if len(results) >= 2:
        ks = sorted(results.keys())
        print("Scaling analysis:")
        for i in range(1, len(ks)):
            k1, k2 = ks[i-1], ks[i]
            ratio = results[k2] / results[k1]
            k_ratio = k2 / k1
            k2_ratio = (k2**2) / (k1**2)
            print(f"  k={k1}→{k2}: cert ratio={ratio:.2f}, "
                  f"k ratio={k_ratio:.2f}, k² ratio={k2_ratio:.2f}")
            if abs(ratio - k_ratio) < abs(ratio - k2_ratio):
                print(f"    → closer to Θ(k)")
            else:
                print(f"    → closer to Θ(k²)")


def main():
    print("Query Complexity Lower Bound for Hub Certification")
    print("=" * 70)
    print()

    experiment_3_spanner_edge_certificate()
    print()

    experiment_4_what_must_be_read()
    print()

    experiment_5_adversarial_distinguishing()
    print()

    experiment_6_certificate_scaling()
    print()

    experiment_1_query_simulation()
    print()

    experiment_2_minimum_certificate()


if __name__ == '__main__':
    main()
