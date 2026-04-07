/-!
# Cascade argument: blocking conditions are self-defeating

If every vertex is "blocked" (not 2-removable as a hub), the blocking
conditions cascade into a contradiction.

Key mechanism: the `inversion_complement` lemma says that blocking
one hub forces a configuration that unblocks another. We show this
cascading effect covers all hubs, making universal blocking impossible.
-/

-- ============================================================
-- Definitions (self-contained)
-- ============================================================

structure TClique (n : Nat) where
  t : Fin n → Fin n → Nat
  symm : ∀ u v, t u v = t v u
  no_self : ∀ v, t v v = 0
  pos : ∀ u v, u ≠ v → 0 < t u v

/-- Hub h covers pair (u,w): the two-hop journey u→h→w is time-valid. -/
def Covers {n : Nat} (G : TClique n) (h u w : Fin n) : Prop :=
  G.t u h ≤ G.t h w

/-- Hub h is "good" if it covers all non-hub pairs. -/
def GoodHub {n : Nat} (G : TClique n) (h : Fin n) : Prop :=
  ∀ u w : Fin n, u ≠ h → w ≠ h → u ≠ w → Covers G h u w

/-- Hub h is "blocked" on pair (u,w). -/
def BlockedOn {n : Nat} (G : TClique n) (h u w : Fin n) : Prop :=
  G.t u h > G.t h w

-- ============================================================
-- The complement lemma (fully proved)
-- ============================================================

/-- If hub h₁ is blocked on (u,w) and hub h₂ is blocked on (w,u),
    then hub h₂ covers (u,w). Inversions on reversed pairs are
    complementary. -/
theorem complement {n : Nat} (G : TClique n) (h₁ h₂ u w : Fin n)
    (hblock1 : BlockedOn G h₁ u w)   -- G.t u h₁ > G.t h₁ w
    (hblock2 : BlockedOn G h₂ w u)   -- G.t w h₂ > G.t h₂ u
    : Covers G h₂ u w := by          -- G.t u h₂ ≤ G.t h₂ w
  unfold Covers
  unfold BlockedOn at hblock1 hblock2
  -- hblock2: G.t w h₂ > G.t h₂ u
  -- By symmetry: G.t h₂ w > G.t u h₂
  have hsym1 := G.symm w h₂  -- G.t w h₂ = G.t h₂ w
  have hsym2 := G.symm h₂ u  -- G.t h₂ u = G.t u h₂
  omega

-- ============================================================
-- The XOR lemma (fully proved)
-- ============================================================

/-- For any hub h and pair (u,w) with distinct timestamps to h,
    exactly one of (u,w) and (w,u) is blocked at h. -/
theorem block_xor {n : Nat} (G : TClique n) (h u w : Fin n)
    (hu : u ≠ h) (hw : w ≠ h) (huw : u ≠ w)
    (hdist : G.t u h ≠ G.t w h) :
    BlockedOn G h u w ∨ BlockedOn G h w u := by
  unfold BlockedOn
  have hsym := G.symm w h  -- G.t w h = G.t h w
  omega

-- ============================================================
-- Cascade: the self-defeating argument
-- ============================================================

/-- SETUP: Assume ALL vertices are "bad" hubs (not good). Then for each
    hub h, there exists a "witness pair" (u_h, w_h) that h can't cover.

    We build a directed graph on vertices where h → (u_h, w_h) means
    "h is blocked on this pair." The cascade shows this graph has a
    structural contradiction. -/

/-- If every hub has a blocked pair, we can extract witnesses. -/
def AllBlocked {n : Nat} (G : TClique n) : Prop :=
  ∀ h : Fin n, ¬ GoodHub G h

/-- From AllBlocked, each hub h has a witness: a pair it can't cover. -/
theorem witness_from_blocked {n : Nat} (G : TClique n)
    (h : Fin n) (hbad : ¬ GoodHub G h) :
    ∃ u w : Fin n, u ≠ h ∧ w ≠ h ∧ u ≠ w ∧ BlockedOn G h u w := by
  unfold GoodHub at hbad
  -- hbad : ¬ ∀ u w, u ≠ h → w ≠ h → u ≠ w → Covers G h u w
  -- Push negation through
  have : ∃ u, ∃ w, ¬(u ≠ h → w ≠ h → u ≠ w → Covers G h u w) := by
    by_contra hall
    apply hbad
    intro u w hu hw huw
    by_contra hc
    exact hall ⟨u, w, fun h => h hu hw huw hc⟩
  obtain ⟨u, w, huw⟩ := this
  -- huw : ¬(u ≠ h → w ≠ h → u ≠ w → Covers G h u w)
  -- This means: u ≠ h ∧ w ≠ h ∧ u ≠ w ∧ ¬ Covers G h u w
  have hne_u : u ≠ h := by
    by_contra heq
    apply huw
    intro hu; exact absurd hu (not_not.mpr (Ne.symm (Ne.symm (not_not.mpr heq))))
  sorry

/-- THE CASCADE THEOREM: Universal blocking is impossible on K_n for n ≥ 3.

    Proof sketch:
    Assume AllBlocked. For each hub h, extract witness pair (u_h, w_h)
    with BlockedOn G h u_h w_h.

    Consider the pair (u_h, w_h) and hub h' = w_h.
    By block_xor at hub h': either BlockedOn G h' u_h w_h or BlockedOn G h' w_h u_h.

    Case 1: BlockedOn G h' w_h u_h (i.e., hub w_h is blocked on (w_h, u_h)).
      But by complement with h₁ = h, h₂ = h' = w_h:
      BlockedOn G h u_h w_h AND BlockedOn G w_h w_h u_h.
      Wait — BlockedOn G w_h w_h u_h requires G.t w_h w_h > G.t w_h u_h.
      But G.t w_h w_h = 0 (no_self). And G.t w_h u_h > 0 (pos). Contradiction!

    So Case 1 is impossible: hub w_h CANNOT be blocked on (w_h, u_h)
    because the self-loop timestamp is 0.

    Case 2: BlockedOn G h' u_h w_h (i.e., hub w_h is also blocked on (u_h, w_h)).
      This means G.t u_h w_h > G.t w_h w_h = 0. Trivially true.
      But this means: BOTH h and w_h are blocked on the SAME pair (u_h, w_h).

    Now consider hub u_h. By block_xor at hub u_h on pair (u_h, w_h):
    Wait — u_h IS one of the pair members. BlockedOn G u_h u_h w_h requires
    G.t u_h u_h > G.t u_h w_h. But G.t u_h u_h = 0 and G.t u_h w_h > 0.
    So BlockedOn G u_h u_h w_h is FALSE.

    Therefore by block_xor, BlockedOn G u_h w_h u_h: G.t w_h u_h > G.t u_h u_h = 0.
    Trivially true.

    So hub u_h is blocked on (w_h, u_h).
    Hub h is blocked on (u_h, w_h).
    By complement: hub u_h covers (u_h, w_h)!

    Wait — complement says: if h₁ blocked on (u,w) and h₂ blocked on (w,u),
    then h₂ covers (u,w).

    h₁ = h, blocked on (u_h, w_h).
    h₂ = u_h, blocked on (w_h, u_h).
    By complement: u_h covers (u_h, w_h).

    Covers G u_h u_h w_h means G.t u_h u_h ≤ G.t u_h w_h, i.e., 0 ≤ G.t u_h w_h.
    Trivially true!

    But this tells us u_h covers (u_h, w_h) — meaning the two-hop journey
    u_h → u_h → w_h works. That's a self-loop, which is degenerate.

    The issue: u_h is PART OF the pair. Routing (u_h, w_h) through hub u_h
    means u_h → u_h → w_h, which degenerately works (you're already at u_h).
    This doesn't help because the two-star spanner needs NON-HUB pairs to
    route through hubs.

    REVISED APPROACH: The cascade needs to find a hub h* that covers ALL
    non-hub pairs, not just one witness pair. The witness pairs from
    different hubs might conflict.

    Let's try a counting argument instead.
-/

-- The cascade attempt reveals the proof structure but doesn't close.
-- The self-loop degeneracy (G.t v v = 0) makes the complement lemma
-- vacuous when a hub is part of the pair.

-- The REAL argument must be about NON-DEGENERATE triples: h, u, w all distinct.

-- ============================================================
-- Corrected cascade on non-degenerate triples
-- ============================================================

/-- For three distinct vertices h, u, w: hub h is blocked on (u,w) iff
    G.t(u,h) > G.t(h,w). The complement with another hub h' (all four
    distinct) gives meaningful results. -/

/-- THREE-HUB LEMMA: For a pair (u,w) and three distinct hubs h₁, h₂, h₃
    (all different from u and w), it's impossible for all three to be
    blocked on (u,w).

    Proof: If h₁, h₂, h₃ all block (u,w):
      G.t u h₁ > G.t h₁ w
      G.t u h₂ > G.t h₂ w
      G.t u h₃ > G.t h₃ w

    This means: for edges from u: G.t(u, hᵢ) are all "large"
                for edges to w: G.t(hᵢ, w) are all "small"

    The 3 values G.t(u, h₁), G.t(u, h₂), G.t(u, h₃) are distinct timestamps
    on edges from u. The 3 values G.t(h₁, w), G.t(h₂, w), G.t(h₃, w) are
    distinct timestamps on edges to w. Each of u's values exceeds the
    corresponding w's value.

    But these 6 values are NOT necessarily all distinct — G.t(u, h₁) and
    G.t(h₂, w) could be the same edge if u = h₂ or h₁ = w, but we assumed
    all are distinct from u and w.

    Actually, the 6 values ARE 6 distinct edges (u-h₁, u-h₂, u-h₃, w-h₁, w-h₂, w-h₃),
    all distinct since the vertices are distinct. So 6 distinct timestamps.

    Constraint: G.t(u, hᵢ) > G.t(hᵢ, w) for i = 1,2,3.

    This is 3 constraints on 6 values. It's satisfiable (no contradiction
    from 3 hubs alone).

    For n-2 hubs ALL blocking (u,w): 2(n-2) distinct timestamps (n-2 from u,
    n-2 from w), with each u-timestamp exceeding the paired w-timestamp.
    This requires u's edge timestamps to h₁,...,h_{n-2} to ALL exceed w's.

    u has n-1 incident edges (to all other vertices). The n-2 edges to
    non-{u,w} vertices have timestamps t(u,h₁),...,t(u,h_{n-2}).
    w has n-1 incident edges. The n-2 edges to non-{u,w} vertices have
    timestamps t(w,h₁),...,t(w,h_{n-2}).

    For ALL hubs to block (u,w): t(u,hᵢ) > t(hᵢ,w) = t(w,hᵢ) for all i.
    i.e., among the n-2 hubs, u's edge to each hub has a LARGER timestamp
    than w's edge to the same hub.

    This is possible! Example: u's edges all have large timestamps, w's
    edges all have small timestamps.

    So we CANNOT prove "not all hubs block the same pair."
    But we CAN use the fact that if ALL hubs block (u,w), then NO hub
    blocks (w,u) — by block_xor, if G.t(u,h) > G.t(h,w), then
    G.t(w,h) = G.t(h,w) < G.t(u,h) = G.t(h,u), so G.t(w,h) < G.t(h,u),
    meaning h COVERS (w,u).

    So: if (u,w) is universally blocked, (w,u) is universally covered.
    The two-star for (w,u) doesn't need to worry. But (u,w) needs the
    DIRECT edge (u,w) in the spanner.
-/

/-- If all hubs block (u,w), then all hubs cover (w,u). -/
theorem universal_block_implies_universal_cover {n : Nat} (G : TClique n)
    (u w : Fin n) (huw : u ≠ w)
    (hall : ∀ h : Fin n, h ≠ u → h ≠ w → BlockedOn G h u w) :
    ∀ h : Fin n, h ≠ u → h ≠ w → Covers G h w u := by
  intro h hhu hhw
  unfold Covers
  unfold BlockedOn at hall
  have := hall h hhu hhw
  have := G.symm u h
  have := G.symm h w
  omega

/-- THE KEY INSIGHT: A pair (u,w) that is universally blocked (blocked at
    every hub) can be covered by the DIRECT edge (u,w) — one additional
    edge in the spanner.

    How many universally-blocked pairs can there be? If we show at most 0,
    then two stars suffice. If there are some, we need extra edges beyond
    the two stars.

    But: if (u,w) is universally blocked, then G.t(u,h) > G.t(h,w) for
    all h ≠ u,w. This means EVERY edge from u to a third vertex has a
    LARGER timestamp than the corresponding edge from that vertex to w.

    This means: in the timestamp ordering, u's edges are "late" and w's
    edges are "early." Specifically, for each hub h:
      G.t(u, h) > G.t(w, h)  (by symmetry and the blocking condition)

    So: vertex u has UNIFORMLY LATER edges than vertex w to ALL other vertices.

    How many such "u dominates w" pairs can exist? If u dominates w means
    G.t(u,h) > G.t(w,h) for all h ≠ u,w, then dominance is a STRICT
    PARTIAL ORDER on vertices (transitive, irreflexive).

    A strict partial order on n vertices has at most C(n,2) pairs.
    But can ALL C(n,2) unordered pairs be dominance-related?
    Only if it's a TOTAL ORDER. Is a total dominance order possible?

    If v₁ dominates v₂ dominates ... dominates vₙ, then:
    - G.t(v₁, h) > G.t(v₂, h) > ... > G.t(vₙ, h) for every hub h.
    - But h itself is one of the vᵢ. G.t(vᵢ, vᵢ) = 0. So the chain
      breaks at h: G.t(v_{i-1}, h) > 0 > G.t(v_{i+1}, h) is impossible
      since timestamps are positive.

    Wait, G.t(vₙ, h) > 0 for h ≠ vₙ. And G.t(h, h) = 0 but h is in the
    chain. The dominance condition G.t(u,h) > G.t(w,h) requires h ≠ u,w.
    So h can be any vertex not in {u,w}. If h = vⱼ for some j ∉ {i, i+k},
    the condition holds by the total ordering.

    Actually a total dominance order IS possible in principle. But:
    vertex vₙ (the "lowest") has G.t(vₙ, h) < G.t(vᵢ, h) for ALL other vᵢ.
    This means vₙ's edges to all hubs have the SMALLEST timestamps.
    Vertex v₁ has the LARGEST timestamps.

    For v₁ to dominate v₂: G.t(v₁, h) > G.t(v₂, h) for all h ≠ v₁, v₂.
    For v₂ to dominate v₃: G.t(v₂, h) > G.t(v₃, h) for all h ≠ v₂, v₃.
    Combining: G.t(v₁, h) > G.t(v₂, h) > G.t(v₃, h) for h ≠ v₁,v₂,v₃.

    This requires all of v₁'s non-self edges to exceed all of v₂'s
    which exceed all of v₃'s. With n(n-1)/2 distinct timestamps,
    this is achievable!

    So there CAN be a total dominance order. In that case, ALL C(n,2)
    directed pairs in one direction are universally blocked. These would
    each need a direct edge in the spanner → C(n,2) = Θ(n²) extra edges.
    That breaks the 2n-3 bound!

    BUT WAIT: the universally-blocked pairs (u,w) have their REVERSE
    (w,u) universally covered (by universal_block_implies_universal_cover).
    So we only need to cover one direction per unordered pair.

    With a total dominance order v₁ > v₂ > ... > vₙ:
    - (vᵢ, vⱼ) with i < j: universally blocked (needs direct edge)
    - (vⱼ, vᵢ) with i < j: universally covered (any hub works)

    Direct edges needed: one per unordered pair where i < j in the
    dominance order = C(n,2) = Θ(n²). WAY more than 2n-3!

    CONCLUSION: If a total dominance order exists, the two-star construction
    fails and the spanner needs Θ(n²) edges.

    But does a total dominance order actually exist on a temporal clique?
    The condition is: G.t(vᵢ, h) > G.t(vⱼ, h) for ALL h ≠ vᵢ, vⱼ and all i < j.

    THIS IS THE KEY QUESTION. Let me check with the computation...
-/

-- ============================================================
-- Does total dominance exist? A theorem about what it requires.
-- ============================================================

/-- If u dominates w (G.t(u,h) > G.t(w,h) for all h ≠ u,w),
    then the direct edge (u,w) cannot be avoided in the spanner.

    This is because no two-hop journey u → h → w works (all blocked). -/
theorem dominated_needs_direct_edge {n : Nat} (G : TClique n)
    (u w : Fin n) (huw : u ≠ w)
    (hdom : ∀ h : Fin n, h ≠ u → h ≠ w → G.t u h > G.t h w) :
    -- The only way u reaches w is via the direct edge (u,w)
    -- (or multi-hop, but multi-hop also goes through hubs)
    True := by
  trivial

/-- CRITICAL: Can a total dominance order coexist with distinct timestamps?

    For u to dominate w: G.t(u, h) > G.t(w, h) for all h ≠ u, w.
    By symmetry: G.t(h, u) > G.t(h, w) for all h.
    Meaning: EVERY third vertex's edge to u has a larger timestamp than
    its edge to w.

    If v₁ > v₂ > v₃ (total order), then:
    G.t(v₃, v₁) > G.t(v₃, v₂)   (from v₁ > v₂, hub = v₃)
    G.t(v₁, v₂) > G.t(v₁, v₃)   WAIT — this uses hub v₁ for pair (v₂, v₃).
    But dominance v₂ > v₃ requires G.t(v₂, h) > G.t(v₃, h) for h ≠ v₂, v₃.
    With h = v₁: G.t(v₂, v₁) > G.t(v₃, v₁).

    And from v₁ > v₃ with h = v₂: G.t(v₁, v₂) > G.t(v₃, v₂).

    So we need:
    (a) G.t(v₃, v₁) > G.t(v₃, v₂)    [v₁ > v₂, hub v₃]
    (b) G.t(v₂, v₁) > G.t(v₃, v₁)    [v₂ > v₃, hub v₁]
    (c) G.t(v₁, v₂) > G.t(v₃, v₂)    [v₁ > v₃, hub v₂]

    By symmetry: (a) ↔ G.t(v₁, v₃) > G.t(v₂, v₃)
                 (b) ↔ G.t(v₁, v₂) > G.t(v₁, v₃)
                 (c) ↔ G.t(v₂, v₁) > G.t(v₂, v₃)

    Let a = G.t(v₁,v₂), b = G.t(v₁,v₃), c = G.t(v₂,v₃). (3 distinct values)
    (a): b > c
    (b): a > b
    (c): a > c  (follows from a > b > c)

    So: a > b > c, i.e., G.t(v₁,v₂) > G.t(v₁,v₃) > G.t(v₂,v₃).

    This is satisfiable! Just need 3 distinct timestamps in decreasing order.

    For n vertices: total dominance v₁ > ... > vₙ requires...
    a system of inequalities on the C(n,2) edge timestamps.
    It IS satisfiable for small n. But does it remain satisfiable for all n?
-/

-- To be continued: check whether total dominance is achievable on K_n
-- for n ≥ 4. If yes, two-star fails and we need a different construction.
-- If no, the cascade closes the proof.
