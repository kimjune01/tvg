/-!
# Two-hub spanner: early collector + late distributor

Construction: pick vertex `lo` with the globally minimum-timestamp edge,
and vertex `hi` with the globally maximum-timestamp edge. The spanner is:
  - All edges incident to `lo` (n-1 edges: the "early star")
  - All edges from `hi` to non-`lo` vertices (n-2 edges: the "late fan")
  - Total: (n-1) + (n-2) = 2n-3 (edge (lo, hi) counted once)

Routing for any pair (u, w):
  u → lo @ t(u, lo)  →  lo → hi @ t(lo, hi)  →  hi → w @ t(hi, w)

This works if: t(u, lo) ≤ t(lo, hi) ≤ t(hi, w)

We show:
  (a) t(u, lo) ≤ t(lo, hi) — because lo has the globally minimum edge,
      so t(lo, hi) ≥ t(lo, u) only if hi is not u's earliest neighbor.
      Actually: we need t(u, lo) ≤ t(lo, hi) for ALL u ≠ lo, hi.

  Hmm — t(u, lo) is the timestamp of edge {u, lo}. t(lo, hi) is the
  timestamp of edge {lo, hi}. We need {lo, hi}'s timestamp to be ≥
  every other edge incident to lo. That means hi is lo's LATEST neighbor.

  (b) t(lo, hi) ≤ t(hi, w) — because hi has the globally maximum edge,
      so t(hi, w) could be anything. We need t(lo, hi) ≤ t(hi, w) for
      ALL w ≠ lo, hi. That means {lo, hi} is hi's EARLIEST neighbor.

  So the bridge edge (lo, hi) must be BOTH:
    - lo's latest incident edge (so all u reach lo before the bridge)
    - hi's earliest incident edge (so the bridge precedes all of hi's fan)

  THIS IS THE KEY CONDITION. Does such a pair (lo, hi) always exist?
-/

structure TClique (n : Nat) where
  t : Fin n → Fin n → Nat
  symm : ∀ u v, t u v = t v u
  no_self : ∀ v, t v v = 0
  pos : ∀ u v, u ≠ v → 0 < t u v

inductive Journey {n : Nat} (G : TClique n) : Fin n → Fin n → Nat → Prop where
  | refl (v : Fin n) (after : Nat) : Journey G v v after
  | step (u v w : Fin n) (after : Nat)
    (huv : u ≠ v) (htime : after ≤ G.t u v)
    (rest : Journey G v w (G.t u v)) : Journey G u w after

def Reaches {n : Nat} (G : TClique n) (u w : Fin n) : Prop :=
  Journey G u w 0

-- ============================================================
-- The bridge condition
-- ============================================================

/-- Edge (lo, hi) is a "bridge" if it's lo's latest and hi's earliest
    incident edge. -/
def IsBridge {n : Nat} (G : TClique n) (lo hi : Fin n) : Prop :=
  lo ≠ hi ∧
  (∀ u : Fin n, u ≠ lo → G.t lo u ≤ G.t lo hi) ∧  -- hi is lo's latest neighbor
  (∀ w : Fin n, w ≠ hi → G.t hi lo ≤ G.t hi w)     -- lo is hi's earliest neighbor

/-- If a bridge exists, the three-hop routing works for all pairs. -/
theorem bridge_routes_all {n : Nat} (G : TClique n) (lo hi : Fin n)
    (hbridge : IsBridge G lo hi)
    (u w : Fin n) (hu : u ≠ lo) (hw : w ≠ hi) (huw : u ≠ w)
    (hulo : u ≠ lo) (hwhi : w ≠ hi) :
    -- Three-hop journey: u → lo → hi → w
    -- Need: t(u, lo) ≤ t(lo, hi) ≤ t(hi, w)
    G.t u lo ≤ G.t lo hi ∧ G.t lo hi ≤ G.t hi w := by
  obtain ⟨hne, hmax_lo, hmin_hi⟩ := hbridge
  constructor
  · -- t(u, lo) ≤ t(lo, hi)
    -- By symmetry: t(u, lo) = t(lo, u)
    have hsym := G.symm u lo
    rw [hsym]
    exact hmax_lo u hu
  · -- t(lo, hi) ≤ t(hi, w)
    -- By symmetry: t(lo, hi) = t(hi, lo)
    have hsym := G.symm lo hi
    rw [hsym]
    exact hmin_hi w hw

/-- The three-hop journey u → lo → hi → w exists. -/
theorem three_hop {n : Nat} (G : TClique n) (lo hi u w : Fin n)
    (hne_lohi : lo ≠ hi) (hne_ulo : u ≠ lo) (hne_whi : w ≠ hi)
    (h1 : G.t u lo ≤ G.t lo hi)
    (h2 : G.t lo hi ≤ G.t hi w) :
    Journey G u w 0 := by
  have huw_ne : u ≠ w := by
    sorry -- need to handle u = w case separately (trivial: Journey.refl)
  -- u → lo
  apply Journey.step u lo w 0 hne_ulo
  · -- 0 ≤ G.t u lo
    exact Nat.zero_le _
  -- lo → hi → w at departure time G.t u lo
  apply Journey.step lo hi w (G.t u lo) (Ne.symm hne_lohi)
  · -- G.t u lo ≤ G.t lo hi
    exact h1
  -- hi → w at departure time G.t lo hi
  apply Journey.step hi w w (G.t lo hi) (by sorry) -- hi ≠ w
  · exact h2
  · exact Journey.refl w (G.t hi w)

-- ============================================================
-- Does a bridge always exist?
-- ============================================================

/-- CRITICAL LEMMA: In any temporal clique, a bridge pair (lo, hi) exists.

    That is: there exist vertices lo, hi such that edge {lo, hi} is
    simultaneously lo's maximum-timestamp incident edge and hi's
    minimum-timestamp incident edge.

    Proof attempt:
    Consider the edge with the globally maximum timestamp, say {a, b}.
    WLOG t(a,b) = max. Then for vertex a: is b its latest neighbor?
    Yes — t(a,b) is the global max, so t(a,b) ≥ t(a,w) for all w. ✓
    For vertex b: is a its earliest neighbor?
    t(b,a) = t(a,b) = global max. Is this ≤ t(b,w) for all w?
    NO — t(b,a) is the MAXIMUM, not the minimum. So a is b's LATEST
    neighbor, not earliest. ✗

    So the global max edge gives us: a's latest neighbor is b,
    AND b's latest neighbor is a. Both vertices' LATEST — not one
    latest and one earliest.

    Try instead: for vertex a (incident to global max), let c be
    a's EARLIEST neighbor. Then {a, c} has a as the vertex with
    c as earliest. Is c's latest neighbor a?
    t(c, a) is some value. t(c, a) must be ≥ t(c, w) for all w ≠ c.
    Not guaranteed.

    The bridge condition requires a SINGLE edge to be simultaneously
    a maximum for one endpoint and a minimum for the other. This is
    a "saddle point" in the timestamp matrix.

    Does a saddle point always exist? -/
theorem bridge_exists {n : Nat} (hn : 3 ≤ n) (G : TClique n) :
    ∃ lo hi : Fin n, IsBridge G lo hi := by
  sorry

-- ============================================================
-- Testing: does the saddle point exist?
-- ============================================================

/-! Saddle point in the adjacency timestamp matrix:

    M[i][j] = G.t(i,j) for i ≠ j, 0 on diagonal.

    A saddle point is (i,j) where M[i][j] = max of row i = min of row j
    (excluding diagonal).

    This is a minimax condition: max_j M[i][j] = min_i M[i][j] at (i,j).

    The minimax theorem (for finite matrices) says:
      max_i min_j M[i][j] ≤ min_j max_i M[i][j]

    A saddle point exists iff equality holds. For symmetric matrices
    with distinct entries, saddle points do NOT always exist.

    THEREFORE: the bridge approach might fail. The proof needs a
    different construction for cliques without saddle points.

    BUT: empirically, 2n-3 spanners always exist. So either:
    (a) Saddle points always exist in temporal clique timestamp matrices
        (unlikely for general matrices, but temporal cliques are special)
    (b) The spanner construction doesn't require a perfect bridge —
        a weaker condition suffices
    (c) A completely different construction achieves 2n-3

    Let's check computationally whether saddle points always exist.
-/
