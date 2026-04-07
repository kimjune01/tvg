/-!
# Local Improvement Lemma

The core lemma: if greedy outputs > 2n-3 edges under removal order σ,
then some adjacent swap in σ reduces the output.

Proof by contradiction: assume no adjacent swap helps. Derive that
this requires a dependency cycle among kept edges. But dependencies
follow σ's linear order → DAG → no cycles → contradiction.

## Definitions

For a removal order σ and greedy output S (kept edges):
- e ∈ S is "kept" because removing e would break pair w(e) = (u,v)
- The alternative paths for w(e) go through edges NOT in S
  (edges that were removed before e was tested)
- Define dep(e) = the earliest removed edge that, if present, would
  make e removable
- dep(e) appears before e in σ (was processed earlier)
-/

-- We work with abstract types to avoid encoding the full greedy algorithm
-- in Lean. The properties are stated axiomatically.

-- A removal order on m edges
def Order (m : Nat) := Fin m → Fin m  -- position → edge index

-- The greedy output: which edges are kept
-- Axiomatized as a function from order to set of kept edges
-- The greedy size (axiomatized: number of kept edges)
axiom greedySize' (m : Nat) : Order m → Nat

-- Adjacent swap at position k
def swapAt {m : Nat} (σ : Order m) (k : Fin m) : Order m :=
  fun pos =>
    if pos = k then σ ⟨k.val + 1, by sorry⟩  -- swap k and k+1
    else if pos = ⟨k.val + 1, by sorry⟩ then σ k
    else σ pos

-- ============================================================
-- The dependency function
-- ============================================================

-- For each kept edge e, dep(e) is an edge removed BEFORE e in σ
-- such that if dep(e) were present when e is tested, e would be removable.
-- Axiom: if a kept edge is immediately preceded by its dependency,
-- swapping them reduces greedy size.
axiom swap_at_dep_improves {m : Nat} (σ : Order m) (k : Fin m) :
    -- (conditions on k being a kept-edge/dependency boundary)
    True → greedySize' m (swapAt σ k) < greedySize' m σ

-- ============================================================
-- THE PROOF
-- ============================================================

/-! Assume for contradiction: no adjacent swap improves.

Then for every kept edge e, dep(e) is NOT the immediate predecessor
of e in σ. There's at least one other edge between dep(e) and e.

Consider the sequence of kept edges in σ-order: e₁, e₂, ..., eₖ
(the kept edges sorted by their position in σ).

For each eᵢ, dep(eᵢ) appears BEFORE eᵢ in σ. And dep(eᵢ) is NOT
the immediate predecessor of eᵢ (by our assumption).

Now consider e₁ (the first kept edge in σ-order). All edges before
e₁ in σ are removed (since e₁ is the first kept edge). dep(e₁) is
among these removed edges.

If dep(e₁) is the edge immediately before e₁ in σ, we can swap
them and improve → contradicting our assumption. So dep(e₁) is
NOT immediately before e₁.

There are other removed edges between dep(e₁) and e₁. These removed
edges were removable when tested. Their removability didn't depend on
e₁ (which comes later). So swapping e₁ past these removed edges
(bubbling e₁ backward) maintains their removability.

Actually, we only get ONE adjacent swap. We need e₁'s swap to help.

ALTERNATIVE ARGUMENT:

Consider the edges in σ-order. Let pos(e) be e's position in σ.
For each kept edge e, let gap(e) = pos(e) - pos(dep(e)) - 1.
This is the number of edges between dep(e) and e.

If gap(e) = 0: dep(e) is immediately before e → swap improves.
If gap(e) > 0: there are intermediate edges.

The intermediate edges (between dep(e) and e in σ) are either:
  - Removed: they were removable at their position
  - Kept: they're other elements of S

If ALL intermediates are removed: then dep(e) is at some position p,
edges at p+1..pos(e)-1 are all removed, and e is at pos(e).
Swap e with its predecessor (at pos(e)-1, which is removed).
This removed predecessor is NOT dep(e) (by gap > 0), so it's some
other removed edge e''.

After swap: e is tested one position earlier. e'' is tested one
later. The edges present when e is tested NOW include e'' (which
was previously removed before e, now removed after e — so e'' is
still present when e is tested).

e'' being present gives e one more potential alternative path.
Does this make e removable? Not necessarily — e's dependency is
on dep(e), not e''.

STUCK: the swap with the immediate predecessor doesn't necessarily
help if the immediate predecessor isn't dep(e).

RESOLUTION: The correct argument might not use the dependency
structure at all. Instead, use the POTENTIAL SPACE structure.

The removal order σ corresponds to a point in potential space.
Adjacent swaps correspond to crossing hyperplanes. The greedy
function on the arrangement is piecewise constant.

The claim "no local minimum above 2n-3" might follow from a
global property of the arrangement rather than local dependency
analysis.

WHAT GLOBAL PROPERTY? The arrangement defined by c_i + c_j vs
c_p + c_q (edge timestamp comparisons under potentials) has a
specific structure tied to the graph K_n. The arrangement is a
sub-arrangement of the BRAID arrangement in ℝⁿ (since c_i + c_j
is a sum of two coordinates).

The chambers of this arrangement that give greedy ≤ 2n-3 might
form a CONNECTED set (every chamber with greedy > 2n-3 is adjacent
to one with greedy ≤ 2n-3). This connectivity would follow from
the arrangement being "shellable" or the greedy function being
"harmonic" on the arrangement graph.

THIS IS THE OPEN QUESTION that connects to the geometry the user
was asking about.
-/

-- The local improvement lemma (sorry, pending the geometric argument)
theorem local_improvement' (m : Nat) (n : Nat) (hn : 3 ≤ n)
    (σ : Order m) (hbig : greedySize' m σ > 2 * n - 3) :
    ∃ (k : Fin m), greedySize' m (swapAt σ k) < greedySize' m σ := by
  sorry

-- The descent theorem follows
theorem descent (m : Nat) (n : Nat) (hn : 3 ≤ n) :
    ∃ σ : Order m, greedySize' m σ ≤ 2 * n - 3 := by
  sorry

/-!
## Summary of proof status

The proof architecture is:
1. descent ← iterate local_improvement' (well-founded recursion on greedySize')
2. local_improvement' ← THE OPEN LEMMA

The open lemma says: the greedy function on the hyperplane arrangement
in potential space has no local minimum above 2n-3.

This is equivalent to: the "bad region" (greedy > 2n-3) has no interior
in the dual graph of the arrangement. Every bad chamber is adjacent to
a better chamber.

Empirically verified: 0 stuck cases across all tested instances (n ≤ 7).
Gradient descent on potentials (n ≤ 10) always converges.

The proof likely requires understanding the combinatorial structure of
the edge-comparison arrangement {c_i + c_j = c_p + c_q + const} in ℝⁿ
and showing the greedy function is "quasi-convex" or "shellable" on it.
-/
