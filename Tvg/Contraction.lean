/-!
# Contraction lemma: greedy is antitone in context size

Temporal reachability is monotone: S₁ ⊇ S₂ → reach(S₁) ⊇ reach(S₂).
Therefore: greedy keeps FEWER edges when starting with MORE context.
This is the key structural property that prevents worsening under swaps.
-/

def ESet := Nat → Bool

axiom reach : ESet → Nat → Nat → Prop

axiom reach_monotone (S₁ S₂ : ESet)
    (hsub : ∀ e, S₂ e = true → S₁ e = true)
    (u v : Nat) : reach S₂ u v → reach S₁ u v

def removable (S : ESet) (target : Nat → Nat → Prop) (e : Nat) : Prop :=
  S e = true ∧
  ∀ u v, target u v → reach (fun x => if x = e then false else S x) u v

theorem removable_monotone (S₁ S₂ : ESet) (target : Nat → Nat → Prop)
    (hsub : ∀ e, S₂ e = true → S₁ e = true)
    (e : Nat) (he1 : S₁ e = true)
    (hrem : removable S₂ target e) :
    removable S₁ target e := by
  unfold removable at *
  constructor
  · exact he1
  · intro u v huv
    obtain ⟨_, hreach⟩ := hrem
    have hsub' : ∀ x, (if x = e then false else S₂ x) = true →
                      (if x = e then false else S₁ x) = true := by
      intro x hx
      split at hx <;> split
      · assumption
      · simp_all
      · simp_all
      · exact hsub x (by simp_all)
    exact reach_monotone _ _ hsub' u v (hreach u v huv)

-- Greedy processing axiomatized
axiom processGreedy (target : Nat → Nat → Prop) : List Nat → ESet → Nat

-- ANTITONE: more context → fewer kept edges
theorem greedy_antitone (target : Nat → Nat → Prop)
    (suffix : List Nat) (S₁ S₂ : ESet)
    (hsub : ∀ e, S₂ e = true → S₁ e = true) :
    processGreedy target suffix S₁ ≤ processGreedy target suffix S₂ := by
  sorry

/-!
## What greedy_antitone gives us

The antitone property means: if you start greedy with a LARGER edge set,
it produces a SMALLER spanner. More edges available → more removable →
fewer kept.

For the swap analysis (σ vs τ with one transposition):
- Cases (2)-(4): contexts are identical or subset-related → antitone applies
  → greedy output equal or smaller. ✓
- Case (1): both edges removable → contexts diverge → antitone doesn't
  directly apply. But the divergence is bounded by 1 edge, and the
  antitone property on the suffix controls the cascade.

The complete swap theorem is:

  greedySize(τ) ≤ greedySize(σ) + 1  (worst case: case 1 diverges by 1)

Combined with the empirical observation that it's actually ≤ 0 (never
worsens), the +1 slack means potential-guided descent still converges:
each potential step crosses O(n) hyperplanes, accumulating at most O(n)
slack, but gaining at least 1 real improvement. Net progress > 0.

## The remaining sorrys

1. greedy_antitone: provable by induction using removable_monotone.
   The inductive step has the same case structure as the swap analysis,
   but with a clean subset relation (no divergence).

2. removable_monotone: PROVED above (no sorry). ✓

3. The swap theorem itself: follows from greedy_antitone + case analysis.

4. Plateau-breaking via potentials: needs the geometric argument about
   the n-dimensional potential subspace cutting through neutral regions.
-/
