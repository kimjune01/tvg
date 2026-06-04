"""
Baligacs CLIQUE pipeline (arXiv:2606.05156) -- the level where the famous
2n-3 conjecture actually lives (all-to-all gossip).

We use her Lemma 4 reduction (Section 2.2), which is cleaner than the
{1,2}-hop peeling and reuses our verified bi-clique spanner verbatim:

  - For each clique vertex v, make a source copy v_S and a target copy v_T.
  - Bi-clique labels: lambda'(v_S, v_T) = 0; lambda'(v_S, u_T) = lambda(v,u).
  - Run the Thm-18 bi-clique spanner (source->target).
  - Project {v_S, u_T} back to the clique edge {v, u}; drop diagonal copies.
  The projected edge set is a clique spanner (Lemma 4).

Her proof: <= 14n via this route (<= 7n with the CCC25 halving).  The
conjecture: <= 2n-3.  Lower bound: 2n-4 (gossip).  All-to-all oracle-verified.
"""

import random
from double_star import compute_reachability_pairs
from baligacs_construction import baligacs_spanner, is_extremally_matched


# ----------------------------------------------------------------------
# Clique primitives.  Lc[u][v] symmetric label matrix; vertices 0..n-1.
# ----------------------------------------------------------------------

def cn_min(v, V, Lc):
    return min((u for u in V if u != v), key=lambda u: Lc[v][u])

def cn_max(v, V, Lc):
    return max((u for u in V if u != v), key=lambda u: Lc[v][u])


def clique_full_pairs(Lc, V):
    timed = [(Lc[u][v], u, v) for i, u in enumerate(V) for v in V[i + 1:]]
    return compute_reachability_pairs_subset(timed, V)


def compute_reachability_pairs_subset(timed_edges, V):
    """All-to-all temporal reachability over vertex set V (arbitrary ids)."""
    reached = {v: {v: float('-inf')} for v in V}
    for t, u, v in sorted(timed_edges):
        for s, arr in list(reached[u].items()):
            if arr <= t and (s not in reached[v] or t < reached[v][s]):
                reached[v][s] = t
        for s, arr in list(reached[v].items()):
            if arr <= t and (s not in reached[u] or t < reached[u][s]):
                reached[u][s] = t
    pairs = set()
    for v in V:
        for s in reached[v]:
            if s != v:
                pairs.add((s, v))
    return pairs


# ----------------------------------------------------------------------
# {1,2}-hop dismountable peeling (Obs 19).
# v is {1,2}-hop dismountable if there exist u, w with
#   (v, N_min(u), u) a temporal walk  AND  (w, N_max(w), v) a temporal walk.
# Reintroduce v with the (<=4) edges of the two walks.
# ----------------------------------------------------------------------

def witness_in(v, V, Lc):
    """Walk (v, N_min(u), u): lambda(v,m) <= lambda(m,u), m=N_min(u)!=v."""
    for u in V:
        if u == v:
            continue
        m = cn_min(u, V, Lc)
        if m != v and m != u and Lc[v][m] <= Lc[m][u]:
            return [(v, m), (m, u)]
    return None


def witness_out(v, V, Lc):
    """Walk (w, N_max(w), v): lambda(w,m) <= lambda(m,v), m=N_max(w)!=v."""
    for w in V:
        if w == v:
            continue
        m = cn_max(w, V, Lc)
        if m != v and m != w and Lc[w][m] <= Lc[m][v]:
            return [(w, m), (m, v)]
    return None


def peel_dismountable(Lc, n):
    V = list(range(n))
    E_peel = set()
    changed = True
    while changed and len(V) > 2:
        changed = False
        for v in list(V):
            win = witness_in(v, V, Lc)
            wout = witness_out(v, V, Lc)
            if win is not None and wout is not None:
                for (a, b) in win + wout:
                    E_peel.add((min(a, b), max(a, b)))
                V.remove(v)
                changed = True
                break
    return V, E_peel


# ----------------------------------------------------------------------
# Full clique spanner.
# ----------------------------------------------------------------------

def clique_spanner(Lc, n):
    """Lemma 4 reduction: clique -> bi-clique (diagonal label 0) -> project."""
    # source i ~ vertex i, target j ~ vertex j; Lb[i][j] = 0 if i==j else lambda
    Lb = [[0 if i == j else Lc[i][j] for j in range(n)] for i in range(n)]
    S = list(range(n))
    T = list(range(n))
    bic_edges = baligacs_spanner(S, T, Lb)
    # project: drop diagonal copies (label-0 self edges); rest -> clique edges
    E_bic = {(min(s, t), max(s, t)) for (s, t) in bic_edges if s != t}
    info = {'n_peeled': 0, 'bic_edges': len(bic_edges)}
    return E_bic, info


def verify_clique(Lc, n, edges):
    V = list(range(n))
    full = clique_full_pairs(Lc, V)
    timed = [(Lc[u][v], u, v) for (u, v) in edges]
    got = compute_reachability_pairs_subset(timed, V)
    return full - got, len(full)


def greedy_prune(Lc, n, edges):
    """Remove edges one at a time while all-to-all reachability is preserved.
    Yields a minimal (irreducible) spanner -> an upper bound on OPT."""
    V = list(range(n))
    full = clique_full_pairs(Lc, V)
    E = set(edges)
    # try larger-label edges first: they tend to be more redundant relays
    for e in sorted(E, key=lambda uv: -Lc[uv[0]][uv[1]]):
        E.discard(e)
        timed = [(Lc[u][v], u, v) for (u, v) in E]
        if compute_reachability_pairs_subset(timed, V) != full:
            E.add(e)                          # removal broke it; keep edge
    return E


# ----------------------------------------------------------------------
def random_temporal_clique(n, rng):
    m = n * (n - 1) // 2
    labels = list(range(1, m + 1))
    rng.shuffle(labels)
    Lc = [[None] * n for _ in range(n)]
    idx = 0
    for u in range(n):
        for v in range(u + 1, n):
            Lc[u][v] = Lc[v][u] = labels[idx]
            idx += 1
    return Lc


def is_temporally_complete(Lc, n):
    full = clique_full_pairs(Lc, list(range(n)))
    return len(full) == n * (n - 1)


def main():
    rng = random.Random(11)
    print("=" * 74)
    print("BALIGACS CLIQUE construction -- the 2n-3 conjecture level (all-to-all)")
    print("her bound 7n | conjecture 2n-3 | gossip lower bound 2n-4 | oracle-verified")
    print("=" * 74)
    print("raw = her construction;  pruned = greedily minimized (upper bnd on OPT)")
    print(f"{'n':>4} {'2n-4':>5} {'2n-3':>5} {'7n':>5} | "
          f"{'raw/n':>6} {'valid':>7} | "
          f"{'pruned/n':>9} {'pr.min':>6} {'pr.max':>6} {'pr<=2n-3':>9}")

    for n in range(4, 49, 2):
        trials = 60 if n <= 20 else (30 if n <= 32 else 15)
        raw, pruned, valids, le_conj, done = [], [], 0, 0, 0
        attempts = 0
        while done < trials and attempts < trials * 30:
            attempts += 1
            Lc = random_temporal_clique(n, rng)
            if not is_temporally_complete(Lc, n):
                continue
            done += 1
            edges, info = clique_spanner(Lc, n)
            miss, _ = verify_clique(Lc, n, edges)
            raw.append(len(edges))
            if len(miss) == 0:
                valids += 1
            pe = greedy_prune(Lc, n, edges)
            pmiss, _ = verify_clique(Lc, n, pe)
            assert len(pmiss) == 0, "prune broke validity"
            pruned.append(len(pe))
            if len(pe) <= 2 * n - 3:
                le_conj += 1
        ravg = sum(raw) / len(raw)
        pavg = sum(pruned) / len(pruned)
        print(f"{n:>4} {2*n-4:>5} {2*n-3:>5} {7*n:>5} | "
              f"{ravg/n:>6.2f} {str(valids)+'/'+str(done):>7} | "
              f"{pavg/n:>9.2f} {min(pruned):>6} {max(pruned):>6} "
              f"{str(le_conj)+'/'+str(done):>9}")


if __name__ == '__main__':
    main()
