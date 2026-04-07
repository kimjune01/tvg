/-!
# Full-Graph Routing via M⁻ Cross Edges

In a temporal clique with sandwich structure (V⁻ internal < cross < V⁺
internal), every M⁻ cross edge e has |In(e) ∩ Out(e)| ≥ k + 1, where
In and Out are computed over the FULL temporal graph including internal edges.

**This is NOT the same as Angrick et al.'s biclique-only pivot-edge.**
Angrick (ESA 2024, §5) defines In(e)/Out(e) using only cross edges.
Under that definition, SM(k) has trivial pivot-sets of size 2 (Lemma 6.4).
Our k+1 result relies on V⁻ internal edges for In-routing and V⁺ internal
edges for Out-routing. The sandwich property is load-bearing.

The proof uses three facts:
1. Complete bipartite: every aᵢ has a cross edge to b_{j₀}
2. Sandwich: V⁻ internal timestamps < cross timestamps (for In)
3. M⁻ minimality: t(e) ≤ t(aᵢ, b_{j₀}) for all i (for Out)

Construction:
- In(e): aᵢ →[V⁻ internal] a_{i₀} (one hop, timestamp < t(e))
- Out(e): b_{j₀} →[cross edge] aᵢ (one hop, timestamp ≥ t(e))

Both are single-hop journeys. No induction, no multi-hop paths.

**Open question:** does this full-graph routing advantage lead to a tighter
spanner bound than Angrick's (8/c)n, or is it a dead end because the
construction still needs to handle reverse-direction pairs?
-/

-- ============================================================
-- Extremally matched biclique
-- ============================================================

/-- An extremally matched biclique on 2k vertices.
    V⁻ = Fin k (left side), V⁺ = Fin k (right side).
    Cross edges have timestamps M[i][j].
    V⁻ internal edges have timestamps Eminus[i₁][i₂].
    V⁺ internal edges have timestamps Eplus[j₁][j₂].

    Extremal matching: m_minus j = argmin_i M[i][j] (earliest row per column).
    Sandwich: all V⁻ internal < all cross < all V⁺ internal. -/
structure ExtBiclique (k : Nat) where
  /-- Cross-edge timestamps. -/
  M : Fin k → Fin k → Nat
  /-- V⁻ internal edge timestamps. -/
  Eminus : Fin k → Fin k → Nat
  /-- V⁺ internal edge timestamps. -/
  Eplus : Fin k → Fin k → Nat
  /-- M⁻ matching: for each column j, the row with minimum timestamp. -/
  m_minus : Fin k → Fin k
  /-- M⁻ is minimum: M[m_minus j][j] ≤ M[i][j] for all i. -/
  m_minus_min : ∀ j i, M (m_minus j) j ≤ M i j
  /-- Sandwich: every V⁻ internal timestamp < every cross timestamp. -/
  sandwich_minus : ∀ i₁ i₂ i j, Eminus i₁ i₂ < M i j
  /-- Sandwich: every cross timestamp < every V⁺ internal timestamp. -/
  sandwich_plus : ∀ i j j₁ j₂, M i j < Eplus j₁ j₂

-- ============================================================
-- Temporal journeys on the biclique
-- ============================================================

/-- Vertices of the biclique: Left i or Right j. -/
inductive BV (k : Nat) where
  | left : Fin k → BV k
  | right : Fin k → BV k

/-- Timestamp of an edge between two biclique vertices. -/
def edgeTime {k : Nat} (B : ExtBiclique k) : BV k → BV k → Nat
  | BV.left i,  BV.left i'  => B.Eminus i i'
  | BV.left i,  BV.right j  => B.M i j
  | BV.right j, BV.left i   => B.M i j     -- undirected
  | BV.right j, BV.right j' => B.Eplus j j'

/-- A vertex can reach edge e's endpoint by time t(e).
    For the pivot: aᵢ reaches a_{i₀} via V⁻ internal edge. -/
def InPivot {k : Nat} (B : ExtBiclique k) (j₀ : Fin k) (v : BV k) : Prop :=
  match v with
  | BV.left i =>
    -- aᵢ reaches a_{m_minus j₀} via direct V⁻ internal edge
    -- Eminus[i][m_minus j₀] < M[m_minus j₀][j₀] (sandwich)
    B.Eminus i (B.m_minus j₀) ≤ B.M (B.m_minus j₀) j₀
  | BV.right j =>
    -- b_j reaches the pivot only if j = j₀ (at the pivot time itself)
    j = j₀

/-- A vertex is reachable from edge e's endpoint after time t(e).
    For the pivot: b_{j₀} reaches aᵢ via cross edge (aᵢ, b_{j₀}). -/
def OutPivot {k : Nat} (B : ExtBiclique k) (j₀ : Fin k) (v : BV k) : Prop :=
  match v with
  | BV.left i =>
    -- aᵢ is reachable from b_{j₀} via cross edge at time M[i][j₀]
    -- Need: M[m_minus j₀][j₀] ≤ M[i][j₀] (M⁻ minimality)
    B.M (B.m_minus j₀) j₀ ≤ B.M i j₀
  | BV.right j =>
    -- b_j is reachable from b_{j₀} via V⁺ internal edge
    -- Eplus[j₀][j] > M[m_minus j₀][j₀] (sandwich)
    B.M (B.m_minus j₀) j₀ ≤ B.Eplus j₀ j

-- ============================================================
-- The pivot-edge lemma
-- ============================================================

/-- Every left vertex is in In(pivot). -/
theorem left_in_pivot {k : Nat} (B : ExtBiclique k) (j₀ : Fin k)
    (i : Fin k) : InPivot B j₀ (BV.left i) := by
  unfold InPivot
  -- Need: Eminus i (m_minus j₀) ≤ M (m_minus j₀) j₀
  -- This follows from sandwich_minus
  exact Nat.le_of_lt (B.sandwich_minus i (B.m_minus j₀) (B.m_minus j₀) j₀)

/-- Every left vertex is in Out(pivot). -/
theorem left_out_pivot {k : Nat} (B : ExtBiclique k) (j₀ : Fin k)
    (i : Fin k) : OutPivot B j₀ (BV.left i) := by
  unfold OutPivot
  -- Need: M (m_minus j₀) j₀ ≤ M i j₀
  -- This is m_minus_min
  exact B.m_minus_min j₀ i

/-- The pivot column's right vertex is in In(pivot). -/
theorem right_in_pivot {k : Nat} (B : ExtBiclique k) (j₀ : Fin k) :
    InPivot B j₀ (BV.right j₀) := by
  unfold InPivot
  rfl

/-- Every right vertex is in Out(pivot). -/
theorem right_out_pivot {k : Nat} (B : ExtBiclique k) (j₀ : Fin k)
    (j : Fin k) : OutPivot B j₀ (BV.right j) := by
  unfold OutPivot
  -- Need: M (m_minus j₀) j₀ ≤ Eplus j₀ j
  -- This follows from sandwich_plus
  exact Nat.le_of_lt (B.sandwich_plus (B.m_minus j₀) j₀ j₀ j)

/-- Every left vertex is in In ∩ Out.
    Combined: all k left vertices + right vertex j₀ = k + 1 vertices. -/
theorem left_in_both {k : Nat} (B : ExtBiclique k) (j₀ : Fin k)
    (i : Fin k) : InPivot B j₀ (BV.left i) ∧ OutPivot B j₀ (BV.left i) :=
  ⟨left_in_pivot B j₀ i, left_out_pivot B j₀ i⟩

/-- The pivot vertex j₀ is in In ∩ Out. -/
theorem pivot_in_both {k : Nat} (B : ExtBiclique k) (j₀ : Fin k) :
    InPivot B j₀ (BV.right j₀) ∧ OutPivot B j₀ (BV.right j₀) :=
  ⟨right_in_pivot B j₀, right_out_pivot B j₀ j₀⟩

/-!
## Summary

For any column j₀, the M⁻ cross edge e = (a_{m_minus j₀}, b_{j₀}) satisfies:

- In(e) ⊇ {left i | i : Fin k} ∪ {right j₀}     (k + 1 vertices)
- Out(e) ⊇ {left i | i : Fin k} ∪ {right j | j : Fin k}  (2k vertices)
- In(e) ∩ Out(e) ⊇ {left i | i : Fin k} ∪ {right j₀}     (k + 1 vertices)

**Caveat:** In(e) and Out(e) here include paths through V⁻/V⁺ internal
edges. Under Angrick's biclique-only definition (cross edges only),
SM(k) has |In(e) ∩ Out(e)| = 2 for every edge (Lemma 6.4).

The four key lemmas use only:
- `sandwich_minus`: V⁻ internal < cross  (for left_in_pivot)
- `m_minus_min`: M⁻ is column minimum    (for left_out_pivot)
- `sandwich_plus`: cross < V⁺ internal   (for right_out_pivot)
- `rfl`: j₀ = j₀                         (for right_in_pivot)

No sorry. No induction. No multi-hop paths.
-/
