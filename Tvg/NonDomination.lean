/-!
# Non-Domination Theorem

In an extremally matched biclique, no row dominates another row
and no column dominates another column.

This is the foundation for cross-only spanning: it guarantees that
for every pair (i, i'), there exists a column j with M[i][j] < M[i'][j],
enabling the 2-hop temporal journey a_i → b_j → a_{i'}.

## Proof (2 lines each)

Row non-domination: Suppose row i dominates row i' (M[i][j] > M[i'][j]
for all j). Since m⁻ is surjective, ∃ j₀ with m⁻(j₀) = i, giving
M[i][j₀] ≤ M[i'][j₀]. Contradicts domination.

Column non-domination: Symmetric, using m⁺ surjectivity.
-/

-- ============================================================
-- Extended biclique with both matchings
-- ============================================================

/-- Extremally matched biclique with M⁻ and M⁺ matchings.
    Extends PivotEdge.ExtBiclique with M⁺ and surjectivity. -/
structure ExtBicliqueFull (k : Nat) where
  /-- Cross-edge timestamps. -/
  M : Fin k → Fin k → Nat
  /-- M⁻ matching: for each column j, the row with minimum timestamp. -/
  m_minus : Fin k → Fin k
  /-- M⁺ matching: for each row i, the column with maximum timestamp. -/
  m_plus : Fin k → Fin k
  /-- M⁻ is minimum: M[m_minus j][j] ≤ M[i][j] for all i. -/
  m_minus_min : ∀ j i, M (m_minus j) j ≤ M i j
  /-- M⁺ is maximum: M[i][m_plus i] ≥ M[i][j] for all j. -/
  m_plus_max : ∀ i j, M i j ≤ M i (m_plus i)
  /-- M⁻ is surjective (hence a permutation): every row is some column's minimum. -/
  m_minus_surj : ∀ i, ∃ j, m_minus j = i
  /-- M⁺ is surjective (hence a permutation): every column is some row's maximum. -/
  m_plus_surj : ∀ j, ∃ i, m_plus i = j
  /-- All entries are distinct (needed for strict inequality). -/
  all_distinct : ∀ i₁ j₁ i₂ j₂, M i₁ j₁ = M i₂ j₂ → i₁ = i₂ ∧ j₁ = j₂

-- ============================================================
-- Row non-domination
-- ============================================================

/-- No row dominates another: for any two rows i ≠ i', there exists
    a column j where M[i][j] < M[i'][j]. -/
theorem row_non_domination {k : Nat} (B : ExtBicliqueFull k)
    (i i' : Fin k) (h_ne : i ≠ i') :
    ∃ j, B.M i j < B.M i' j := by
  -- Since m⁻ is surjective, find j₀ with m_minus j₀ = i
  let ⟨j₀, hj₀⟩ := B.m_minus_surj i
  exact ⟨j₀, by
    -- m_minus_min gives M[m_minus j₀][j₀] ≤ M[i'][j₀]
    have h_le := B.m_minus_min j₀ i'
    -- Rewrite m_minus j₀ = i
    rw [hj₀] at h_le
    -- Strict because equality contradicts h_ne via all_distinct
    exact Nat.lt_of_le_of_ne h_le (fun h_eq => h_ne (B.all_distinct i j₀ i' j₀ h_eq).1)⟩

-- ============================================================
-- Column non-domination
-- ============================================================

/-- No column dominates another: for any two columns j ≠ j', there exists
    a row i where M[i][j] < M[i][j']. -/
theorem col_non_domination {k : Nat} (B : ExtBicliqueFull k)
    (j j' : Fin k) (h_ne : j ≠ j') :
    ∃ i, B.M i j < B.M i j' := by
  -- Since m⁺ is surjective, find i₀ with m_plus i₀ = j'
  let ⟨i₀, hi₀⟩ := B.m_plus_surj j'
  exact ⟨i₀, by
    -- m_plus_max gives M[i₀][j] ≤ M[i₀][m_plus i₀]
    have h_le := B.m_plus_max i₀ j
    -- Rewrite m_plus i₀ = j'
    rw [hi₀] at h_le
    -- Strict because equality contradicts h_ne via all_distinct
    exact Nat.lt_of_le_of_ne h_le (fun h_eq => h_ne (B.all_distinct i₀ j i₀ j' h_eq).2)⟩

-- ============================================================
-- Cross-only 2-hop spanning
-- ============================================================

/-- Every A-A pair has a 2-hop witness column.
    For a_i → a_{i'}: column j with M[i][j] < M[i'][j] gives the
    temporal journey a_i →[time M[i][j]] b_j →[time M[i'][j]] a_{i'}. -/
theorem aa_witness {k : Nat} (B : ExtBicliqueFull k)
    (i i' : Fin k) (h_ne : i ≠ i') :
    ∃ j, B.M i j < B.M i' j :=
  row_non_domination B i i' h_ne

/-- Every B-B pair has a 2-hop witness row.
    For b_j → b_{j'}: row i with M[i][j] < M[i][j'] gives the
    temporal journey b_j →[time M[i][j]] a_i →[time M[i][j']] b_{j'}. -/
theorem bb_witness {k : Nat} (B : ExtBicliqueFull k)
    (j j' : Fin k) (h_ne : j ≠ j') :
    ∃ i, B.M i j < B.M i j' :=
  col_non_domination B j j' h_ne

/-!
## Summary

For any extremally matched biclique with all-distinct k×k matrix M:

1. **Row non-domination** (`row_non_domination`): ∀ i ≠ i', ∃ j, M[i][j] < M[i'][j]
2. **Column non-domination** (`col_non_domination`): ∀ j ≠ j', ∃ i, M[i][j] < M[i][j']
3. **A-A witness** (`aa_witness`): every A-A pair has a 2-hop relay column
4. **B-B witness** (`bb_witness`): every B-B pair has a 2-hop relay row

Combined with PivotEdge.lean (pivot covers > n/2 vertices) and edge
monotonicity (trivial), the asymmetric recursion T(n) = T(n/2) + O(n)
gives an O(n) temporal spanner.

No sorry. No induction. Uses only: m_minus_min, m_plus_max, surjectivity,
all_distinct.
-/
