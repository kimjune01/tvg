"""
Baligacs (arXiv:2606.05156, 3 Jun 2026) "Temporal Cliques Admit Linear
Spanners" -- faithful implementation of the BICLIQUE construction, raced
against our double-star on the same instances.

Pipeline (her proof):
  1. Dismountability (Lemma 5): peel dismountable sources/targets, paying
     <= 2 edges each, until G[S',T'] is extremally matched.
  2. Extremally-matched core (Theorem 18 recursion via Lemma 17):
       - s*-ordered labeling, cut at k = floor(n/2).
       - Lemma 17: a set E* of <= 6n edges covering either (S,T') or (S',T),
         via 3-hop-k-cut-crossing sources (Obs 9) OR extended stars (Lemma 16).
       - recurse on the uncovered half (dismount it first).
  Her bound: f(n) <= 14n for the biclique; 7n for the clique after halving.

Ground truth: every spanner is checked with the SAME reachability oracle
used by double_star.py. A bug shows up as an invalid spanner, not a silent
wrong count.
"""

import random
from double_star import (
    compute_reachability_pairs,
    generate_sm_matrix,
    get_matchings,
    double_star_construction,
)


# ----------------------------------------------------------------------
# Biclique primitives.  L is a dict-free k-agnostic label matrix: L[s][t].
# Sources and targets are arbitrary index sets (subsets during recursion).
# pos_s(t) ranks targets at s by ascending label; pos_t(s) ranks sources at t.
# N_min = smallest-label neighbor, N_max = largest-label neighbor.
# ----------------------------------------------------------------------

def nmin_source(s, T, L):       # target with min label at source s
    return min(T, key=lambda t: L[s][t])

def nmax_source(s, T, L):       # target with max label at source s
    return max(T, key=lambda t: L[s][t])

def nmin_target(t, S, L):       # source with min label at target t
    return min(S, key=lambda s: L[s][t])

def nmax_target(t, S, L):       # source with max label at target t
    return max(S, key=lambda s: L[s][t])


def is_extremally_matched(S, T, L):
    """E_min and E_max are both perfect matchings <=> extremally matched."""
    if len(S) != len(T):
        return False
    # E_min from sources vs from targets must agree as a perfect matching.
    emin_s = {(s, nmin_source(s, T, L)) for s in S}
    emin_t = {(nmin_target(t, S, L), t) for t in T}
    emax_s = {(s, nmax_source(s, T, L)) for s in S}
    emax_t = {(nmax_target(t, S, L), t) for t in T}
    if emin_s != emin_t or emax_s != emax_t:
        return False
    # perfect matching: each side covered exactly once
    if len({s for s, _ in emin_s}) != len(S) or len({t for _, t in emin_s}) != len(T):
        return False
    if len({s for s, _ in emax_s}) != len(S) or len({t for _, t in emax_s}) != len(T):
        return False
    return True


# ----------------------------------------------------------------------
# Lemma 5: dismountability reduction -> extremally matched core + E_extra.
# ----------------------------------------------------------------------

def dismount(S, T, L):
    S, T = set(S), set(T)
    E_extra = set()
    changed = True
    while changed:
        changed = False
        # source s' dismountable via (s, t): t = N_min(s), exists s' with
        # pos_t(s') < pos_t(s)  <=>  L[s'][t] < L[s][t].  Remove s'.
        for s in list(S):
            if len(S) <= 1:
                break
            t = nmin_source(s, T, L)
            cands = [sp for sp in S if sp != s and L[sp][t] < L[s][t]]
            if cands:
                sp = cands[0]
                S.discard(sp)
                E_extra.add((s, t))
                E_extra.add((sp, t))
                changed = True
                break
        if changed:
            continue
        # target t' dismountable via (s, t): s = N_max(t), exists t' with
        # pos_s(t') > pos_s(t)  <=>  L[s][t'] > L[s][t].  Remove t'.
        for t in list(T):
            if len(T) <= 1:
                break
            s = nmax_target(t, S, L)
            cands = [tp for tp in T if tp != t and L[s][tp] > L[s][t]]
            if cands:
                tp = cands[0]
                T.discard(tp)
                E_extra.add((s, t))
                E_extra.add((s, tp))
                changed = True
                break
    return S, T, E_extra


# ----------------------------------------------------------------------
# Extended stars (Def 12).  Each computes its own pivot-ordered labeling.
# ----------------------------------------------------------------------

def e_min_edges(S, T, L):
    return {(s, nmin_source(s, T, L)) for s in S}

def e_max_edges(S, T, L):
    return {(s, nmax_source(s, T, L)) for s in S}


def ext_star_source(s_star, S, T, L):
    """Ext(s*) (Def 12a) in the s*-ordered labeling."""
    edges = set()
    edges |= e_min_edges(S, T, L)
    edges |= e_max_edges(S, T, L)
    edges |= {(s_star, t) for t in T}                      # all edges at s*
    # s*-ordered labeling: t_0..t_{n-1} by ascending L[s*][t]; s_i = N_min(t_i)
    t_ord = sorted(T, key=lambda t: L[s_star][t])
    for s in S:
        if s == s_star:
            continue
        # ind(s) = max{ l : L[s][t_l] > L[s*][t_l] }
        idxs = [l for l, tl in enumerate(t_ord) if L[s][tl] > L[s_star][tl]]
        if idxs:
            edges.add((s, t_ord[max(idxs)]))
    return edges


def ext_star_target(t_star, S, T, L):
    """Ext(t*) (Def 12b) in the t*-ordered labeling."""
    edges = set()
    edges |= e_min_edges(S, T, L)
    edges |= e_max_edges(S, T, L)
    edges |= {(s, t_star) for s in S}                      # all edges at t*
    # t*-ordered labeling: s_0..s_{n-1} by DESCENDING L[s][t*]; t_i = N_max(s_i)
    s_ord = sorted(S, key=lambda s: -L[s][t_star])
    for t in T:
        if t == t_star:
            continue
        # ind(t) = max{ l : L[s_l][t] < L[s_l][t*] }
        idxs = [l for l, sl in enumerate(s_ord) if L[sl][t] < L[sl][t_star]]
        if idxs:
            edges.add((s_ord[max(idxs)], t))
    return edges


# ----------------------------------------------------------------------
# Cut-crossing (Def 8ii) + path search for Observation 9.
# In the s*-ordered labeling with cut k, s_i (i>k) is 3-hop-k-cut-crossing
# if it reaches s* by a temporal path of <= 4 edges whose last edge is
# {t_j, s*} with j <= k.  We BFS over temporal walks of <= 4 edges and
# return the path edges if found.
# ----------------------------------------------------------------------

def find_crossing_path(s_i, s_star, j_cut, S, T, L, max_edges=4):
    """Temporal path starting at s_i, ending with edge {t_j, s*}, j<=k(=j_cut),
    using <= max_edges edges, non-decreasing labels.  Returns set of edges or None.
    State = (current_vertex, is_source, last_label, edges_used, path_edges)."""
    from collections import deque
    targets_above = {t for idx, t in enumerate(j_cut['t_ord']) if idx <= j_cut['k']}
    start = (s_i, True, float('-inf'), 0, ())
    seen = {}
    dq = deque([start])
    while dq:
        v, is_src, last, used, path = dq.popleft()
        if used >= max_edges:
            continue
        if is_src:                       # at a source, step to a target
            for t in T:
                lab = L[v][t]
                if lab >= last:
                    npath = path + ((v, t),)
                    if t in targets_above and (v == s_star or True):
                        pass
                    nstate = (t, False, lab, used + 1, npath)
                    key = (t, False, used + 1)
                    if seen.get(key, float('inf')) > lab:
                        seen[key] = lab
                        dq.append(nstate)
        else:                            # at a target, step to a source
            for s in S:
                lab = L[s][v]
                if lab >= last:
                    npath = path + ((s, v),)
                    # success: this edge is {t_j, s*} with t_j above cut
                    if s == s_star and v in targets_above:
                        return set(npath)
                    nstate = (s, True, lab, used + 1, npath)
                    key = (s, True, used + 1)
                    if seen.get(key, float('inf')) > lab:
                        seen[key] = lab
                        dq.append(nstate)
    return None


# ----------------------------------------------------------------------
# Lemma 17 + Theorem 18 recursion on an extremally-matched biclique.
# ----------------------------------------------------------------------

def emxm_spanner(S, T, L):
    S, T = list(S), list(T)
    n = len(S)
    assert len(T) == n
    if n == 0:
        return set()
    if n == 1:
        return {(S[0], T[0])}

    s_star = S[0]
    # s*-ordered labeling
    t_ord = sorted(T, key=lambda t: L[s_star][t])          # t_0..t_{n-1}
    s_ord = [nmin_target(t, S, L) for t in t_ord]          # s_i = N_min(t_i)
    k = n // 2

    star_sstar = e_min_edges(S, T, L) | {(s_star, t) for t in T}
    Emax = e_max_edges(S, T, L)

    # Lemma 17: are all s_i (i>k) 3-hop-k-cut-crossing?
    jc = {'t_ord': t_ord, 'k': k}
    E_cross = set()
    all_crossing = True
    non_crossing_i = None
    for i in range(k + 1, n):
        path = find_crossing_path(s_ord[i], s_star, jc, S, T, L, max_edges=4)
        if path is None:
            all_crossing = False
            non_crossing_i = i
            break
        E_cross |= path

    if all_crossing:
        # Case (i): E* = Star(s*) ∪ E_cross ∪ E_max covers (S, T')
        # (re-collect every crossing path; loop above broke only on failure)
        E_cross = set()
        for i in range(k + 1, n):
            E_cross |= find_crossing_path(s_ord[i], s_star, jc, S, T, L, 4)
        E_star = star_sstar | E_cross | Emax
        # covered (S, T'); remaining: (S, T \ T') with T' = {t_k..t_{n-1}}
        T_rem = t_ord[:k]                                  # {t_0..t_{k-1}}
        S_rem = list(S)
    else:
        # Case (ii): E* = Ext(s*) ∪ Ext(t_i) covers (S', T)
        t_i = t_ord[non_crossing_i]
        E_star = ext_star_source(s_star, S, T, L) | ext_star_target(t_i, S, T, L)
        # covered (S', T) with S' = {s_0..s_k}; remaining: (S \ S', T)
        S_rem = s_ord[k + 1:]                              # {s_{k+1}..s_{n-1}}
        T_rem = list(T)

    if not S_rem or not T_rem:
        return E_star

    # dismount the remaining half, then recurse on its extremally-matched core
    S2, T2, E_dis = dismount(S_rem, T_rem, L)
    E_rec = emxm_spanner(S2, T2, L)
    return E_star | E_dis | E_rec


def baligacs_spanner(S, T, L):
    """Full biclique pipeline: dismount to extremally-matched, then recurse."""
    S0, T0, E_dis = dismount(S, T, L)
    E_core = emxm_spanner(S0, T0, L)
    return E_dis | E_core


# ----------------------------------------------------------------------
# Harness: build matrix into (S, T, L), verify against the oracle, count.
# ----------------------------------------------------------------------

def matrix_to_biclique(M, k):
    S = list(range(k))
    T = list(range(k))
    L = [[M[i][j] for j in range(k)] for i in range(k)]
    return S, T, L


def full_reach_pairs(M, k):
    n = 2 * k
    timed = [(M[i][j], i, k + j) for i in range(k) for j in range(k)]
    return compute_reachability_pairs(n, timed), n


def verify(M, k, edges):
    """Biclique-spanner contract (Theorem 3): preserve SOURCE->TARGET pairs
    only. Targets-to-sources paths are explicitly not required. edges: set of
    (s, t) = (source 0..k-1, col 0..k-1)."""
    full, n = full_reach_pairs(M, k)
    full_st = {(s, t) for (s, t) in full if s < k and t >= k}
    timed = [(M[s][t], s, k + t) for (s, t) in edges]
    got = compute_reachability_pairs(n, timed)
    got_st = {(s, t) for (s, t) in got if s < k and t >= k}
    return full_st - got_st, len(full_st)


def main():
    random.seed(7)
    print("=" * 78)
    print("BALIGACS biclique construction  vs  double-star  (same instances)")
    print("oracle-verified; n = 2k vertices; lower bound 2n-4; her bound 14n (biclique)")
    print("=" * 78)

    print("\n--- SM(k) (shifted matching; double-star known 100% valid) ---")
    print(f"{'k':>3} {'n':>4} {'2n-4':>5} {'2n-3':>5} | "
          f"{'baligacs':>9} {'valid':>6} {'/n':>5} | {'dstar':>6} {'valid':>6} {'/n':>5}")
    for k in range(3, 17):
        M = generate_sm_matrix(k)
        S, T, L = matrix_to_biclique(M, k)
        n = 2 * k
        be = baligacs_spanner(S, T, L)
        bmiss, _ = verify(M, k, be)
        # double-star: best over m+(h)=c choices
        m_minus, m_plus = get_matchings(M, k)
        best = None
        for h in range(k):
            c = m_plus[h]
            de = double_star_construction(M, k, h, c)
            dmiss, _ = verify(M, k, de)
            if best is None or (len(dmiss), len(de)) < best[0]:
                best = ((len(dmiss), len(de)), de)
        (dmiss_n, _), de = best
        print(f"{k:>3} {n:>4} {2*n-4:>5} {2*n-3:>5} | "
              f"{len(be):>9} {'OK' if len(bmiss)==0 else 'X'+str(len(bmiss)):>6} "
              f"{len(be)/n:>5.2f} | "
              f"{len(de):>6} {'OK' if dmiss_n==0 else 'X'+str(dmiss_n):>6} "
              f"{len(de)/n:>5.2f}")

    print("\n--- random all-distinct k x k (temporally-connected only) ---")
    print(f"{'k':>3} {'n':>4} | {'baligacs avg':>12} {'/n':>5} {'valid':>7} | "
          f"{'dstar valid%':>12} {'dstar avg/n(valid)':>18}")
    for k in range(3, 13):
        n = 2 * k
        trials = 40
        b_counts, b_valid = [], 0
        d_validcount, d_pernodes = 0, []
        done = 0
        attempts = 0
        while done < trials and attempts < trials * 20:
            attempts += 1
            vals = list(range(1, k * k + 1))
            random.shuffle(vals)
            M = [[vals[i * k + j] for j in range(k)] for i in range(k)]
            full, _ = full_reach_pairs(M, k)
            # require full biclique temporally complete: every source reaches
            # every target (k*k such pairs), so both methods are in scope
            src_tgt = sum(1 for (s, t) in full if s < k and t >= k)
            if src_tgt != k * k:
                continue
            done += 1
            S, T, L = matrix_to_biclique(M, k)
            be = baligacs_spanner(S, T, L)
            bmiss, _ = verify(M, k, be)
            b_counts.append(len(be))
            if len(bmiss) == 0:
                b_valid += 1
            # double-star best
            m_minus, m_plus = get_matchings(M, k)
            bestd = None
            for h in range(k):
                c = m_plus[h]
                de = double_star_construction(M, k, h, c)
                dmiss, _ = verify(M, k, de)
                if bestd is None or (len(dmiss), len(de)) < bestd:
                    bestd = (len(dmiss), len(de))
            if bestd[0] == 0:
                d_validcount += 1
                d_pernodes.append(bestd[1] / n)
        avgb = sum(b_counts) / len(b_counts)
        dvalpct = 100 * d_validcount / done
        davg = (sum(d_pernodes) / len(d_pernodes)) if d_pernodes else float('nan')
        print(f"{k:>3} {n:>4} | {avgb:>12.1f} {avgb/n:>5.2f} {b_valid}/{done:>4} | "
              f"{dvalpct:>11.0f}% {davg:>18.2f}")


if __name__ == '__main__':
    main()
