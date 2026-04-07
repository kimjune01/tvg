/-!
# Connected Column Pair in Non-Dismountable Bicliques

Self-contained proof. The main theorem `exists_connected_pair` has no sorry.
Two standard axioms are declared (finite max, pigeonhole surjectivity).
-/

-- Standard facts about Fin k, declared as axioms to avoid Mathlib dependency.
-- Both follow from the pigeonhole principle / finiteness of Fin k.
axiom exists_fin_max (n : Nat) (f : Fin (n + 1) → Nat) :
    ∃ i : Fin (n + 1), ∀ j : Fin (n + 1), f j ≤ f i

axiom fin_inj_surj {k : Nat} (f : Fin k → Fin k) (hf : Function.Injective f) :
    Function.Surjective f

-- ============================================================
-- Biclique definitions
-- ============================================================

structure Biclique (k : Nat) where
  M : Fin k → Fin k → Nat
  distinct : ∀ i₁ j₁ i₂ j₂, M i₁ j₁ = M i₂ j₂ → (i₁ = i₂ ∧ j₁ = j₂)
  m_minus : Fin k → Fin k
  m_minus_is_min : ∀ j i, M (m_minus j) j ≤ M i j
  m_minus_inj : Function.Injective m_minus

def IsDownset {k : Nat} (B : Biclique k) (j : Fin k) (S : Fin k → Prop) : Prop :=
  ∀ i i' : Fin k, S i' → B.M i j ≤ B.M i' j → S i

def IsProper {k : Nat} (S : Fin k → Prop) : Prop :=
  (∃ i, S i) ∧ (∃ i, ¬ S i)

def Disconnected {k : Nat} (B : Biclique k) (j₁ j₂ : Fin k) : Prop :=
  ∃ S : Fin k → Prop, IsProper S ∧ IsDownset B j₁ S ∧ IsDownset B j₂ S

def Connected {k : Nat} (B : Biclique k) (j₁ j₂ : Fin k) : Prop :=
  ¬ Disconnected B j₁ j₂

-- ============================================================
-- Helpers
-- ============================================================

theorem exists_col_max {k : Nat} (hk : 1 ≤ k) (B : Biclique k) (j : Fin k) :
    ∃ i_max : Fin k, ∀ i : Fin k, B.M i j ≤ B.M i_max j := by
  obtain ⟨n, rfl⟩ : ∃ n, k = n + 1 := ⟨k - 1, by omega⟩
  exact exists_fin_max n (fun i => B.M i j)

theorem min_in_downset {k : Nat} (B : Biclique k) (j : Fin k)
    (S : Fin k → Prop) (hne : ∃ i, S i) (hdown : IsDownset B j S) :
    S (B.m_minus j) :=
  let ⟨x, hx⟩ := hne; hdown (B.m_minus j) x hx (B.m_minus_is_min j x)

theorem downset_of_max_is_all {k : Nat} (B : Biclique k) (j : Fin k)
    (i_max : Fin k) (h_max : ∀ i : Fin k, B.M i j ≤ B.M i_max j)
    (S : Fin k → Prop) (hdown : IsDownset B j S) (h_in : S i_max) :
    ∀ i : Fin k, S i :=
  fun i => hdown i i_max h_in (h_max i)

-- ============================================================
-- Main theorem: no sorry
-- ============================================================

/-- In any biclique with M⁻ matching and k ≥ 2,
    there exists a connected column pair. -/
theorem exists_connected_pair {k : Nat} (hk : 2 ≤ k) (B : Biclique k) :
    ∃ j₁ j₂ : Fin k, j₁ ≠ j₂ ∧ Connected B j₁ j₂ := by
  -- Pick column j₁ = 0
  let j₁ : Fin k := ⟨0, by omega⟩
  -- Find i_max = row with max value in column j₁
  obtain ⟨i_max, h_i_max⟩ := exists_col_max (by omega : 1 ≤ k) B j₁
  -- j₂ = column where i_max is the M⁻ minimum (by surjectivity)
  obtain ⟨j₂, hj₂⟩ := fin_inj_surj B.m_minus B.m_minus_inj i_max
  -- j₁ ≠ j₂: if equal, i_max is both min and max → all equal → contradicts distinct
  have hne : j₁ ≠ j₂ := by
    intro heq
    have h_is_min : ∀ i, B.M i_max j₁ ≤ B.M i j₁ := by
      intro i; have := B.m_minus_is_min j₂ i; rw [hj₂] at this; rw [← heq] at this; exact this
    have h_eq : ∀ i, B.M i j₁ = B.M i_max j₁ :=
      fun i => Nat.le_antisymm (h_i_max i) (h_is_min i)
    -- Two distinct rows have same value → contradicts B.distinct
    have h1 : (⟨0, by omega⟩ : Fin k) ≠ (⟨1, by omega⟩ : Fin k) :=
      fun h => absurd (Fin.mk.inj h) (by omega)
    exact h1 (B.distinct ⟨0, by omega⟩ j₁ ⟨1, by omega⟩ j₁
      (by rw [h_eq ⟨0, by omega⟩]; rw [h_eq ⟨1, by omega⟩])).1
  refine ⟨j₁, j₂, hne, ?_⟩
  -- Connected: no proper common downset
  intro ⟨S, ⟨hS_ne, hS_not_all⟩, hdown1, hdown2⟩
  -- S contains m_minus(j₂) = i_max (min of j₂ is in every nonempty downset)
  have h_in : S i_max := hj₂ ▸ min_in_downset B j₂ S hS_ne hdown2
  -- S contains everything (downset of j₁ containing max of j₁)
  have h_all := downset_of_max_is_all B j₁ i_max h_i_max S hdown1 h_in
  -- Contradicts S being proper
  exact (hS_not_all.choose_spec) (h_all hS_not_all.choose)
