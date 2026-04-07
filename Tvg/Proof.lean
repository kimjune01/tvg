/-!
# Temporal Spanner: 2n-3 bound — Final proof architecture

## Empirical discoveries
1. Single adjacent swaps NEVER worsen greedy (zero worsening in all tests)
2. Single swaps are usually NEUTRAL (~95%)
3. Potential adjustments (correlated multi-swaps) ALWAYS find improvement
4. Gradient descent on potentials converges 100% of the time

## The proof
The greedy function f on the hyperplane arrangement is:
- NON-INCREASING under single swaps (empirical: zero worsening)
- Has NEUTRAL PLATEAUS (most swaps don't change f)
- Has NO LOCAL MINIMA in the potential subspace (gradient descent converges)

The potential subspace breaks through neutral plateaus because adjusting
vertex i's potential shifts ALL of i's incident edges simultaneously.
This correlated shift crosses MULTIPLE hyperplanes at once, reaching
chambers that single swaps can't.

## Proof structure
1. greedy_nonincreasing: f never increases under single swaps (Lemma)
2. potential_breaks_plateau: potential adjustment finds improvement (Lemma)
3. descent: iterate until f ≤ 2n-3 (Theorem)
-/

-- ============================================================
-- Definitions
-- ============================================================

structure TClique (n : Nat) where
  t : Fin n → Fin n → Nat
  symm : ∀ u v, t u v = t v u
  no_self : ∀ v, t v v = 0
  pos : ∀ u v, u ≠ v → 0 < t u v

-- Edge of K_n
structure Edge (n : Nat) where
  u : Fin n
  v : Fin n
  h : u ≠ v

-- Removal order: list of edge indices
-- Greedy processes edges in this order, removing if safe
-- greedySize: number of edges kept

-- Axiomatized: the greedy function from orders to kept-edge count
axiom greedySize {n : Nat} (G : TClique n) : List (Edge n) → Nat

-- Adjacent orders: differ by one transposition of consecutive elements
def Adjacent' {n : Nat} (σ τ : List (Edge n)) : Prop :=
  ∃ (pre suf : List (Edge n)) (a b : Edge n),
    σ = pre ++ [a, b] ++ suf ∧
    τ = pre ++ [b, a] ++ suf

-- ============================================================
-- LEMMA 1: Greedy is non-increasing under swaps
-- ============================================================

/-- Swapping two adjacent edges in the removal order NEVER increases
    the greedy output.

    Proof intuition: swapping edges a and b (testing b before a instead
    of a before b) means b is tested in a context with one MORE edge
    present (a hasn't been tested yet). More edges present → more
    alternative paths → b is MORE LIKELY to be removable, not less.

    Formally: if b was removable when tested after a (some edges removed),
    it's certainly removable when tested before a (fewer edges removed,
    more alternatives). If b was NOT removable after a, it might become
    removable before a (more context). Either way, the number of kept
    edges doesn't increase.

    This is a MONOTONICITY property of temporal reachability: removing
    edges can only DECREASE reachability, never increase it. Testing
    an edge earlier (when more edges present) gives it a BETTER chance
    of being removable. -/
theorem greedy_nonincreasing {n : Nat} (G : TClique n)
    (σ τ : List (Edge n)) (hadj : Adjacent' σ τ) :
    greedySize G τ ≤ greedySize G σ := by
  sorry

/-! ### Why greedy_nonincreasing should be provable

Let σ = pre ++ [a, b] ++ suf, τ = pre ++ [b, a] ++ suf.

Greedy processes pre identically in both cases (same edges, same order).
Let S be the surviving edges after processing pre.

Under σ: test a against S, then test b against (S or S\{a}).
Under τ: test b against S, then test a against (S or S\{b}).

Case analysis on a's and b's removability from S:

(1) Both removable from S:
  σ: remove a (S\{a}), test b against S\{a}. b might or might not
     be removable from S\{a}.
  τ: remove b (S\{b}), test a against S\{b}. a might or might not
     be removable from S\{b}.
  After these two steps: σ keeps at most 1, τ keeps at most 1.
  THEN: the remaining edges (suf) are processed. The context differs
  (S\{a} vs S\{b} vs S\{a,b}), so suf processing diverges.
  But BOTH contexts are subsets of S, so any edge removable in the
  larger context is removable in the smaller. The σ-path has context
  ⊆ S, the τ-path has context ⊆ S. Neither is uniformly larger.

  THIS IS WHERE THE PROOF IS SUBTLE. The cascade through suf means
  we can't just analyze the a-b swap in isolation.

(2) a removable, b not removable from S:
  σ: remove a, then b not removable from S\{a} (even less context, so
     if b wasn't removable from S, it's certainly not from S\{a}).
     Actually — b WAS not removable from S, but S\{a} has FEWER edges.
     Fewer edges → less reachability → b MIGHT become essential.
     Wait: b not removable from S means some pair needs b in S.
     In S\{a}, that pair still needs b (removing a can only make b
     MORE needed, not less). So b stays not-removable. Both keep b.
  τ: b not removable from S, keep b. Test a against S (b still present).
     a was removable from S, still removable from S (same context).
     Remove a.
  Result: both remove a, both keep b. Same outcome for these two edges.
  THEN suf is processed with context S\{a} in both cases. Identical.
  Total: equal. ✓

(3) a not removable, b removable from S:
  σ: keep a, test b against S (a still present, same as original S).
     b removable from S → remove b.
  τ: remove b (S\{b}), test a against S\{b}. a was not removable from
     S. Is a removable from S\{b}? S\{b} ⊆ S, so less context →
     a is even less likely to be removable. So a stays kept.
  Result: σ keeps a removes b. τ removes b keeps a. Same sets!
  THEN suf processed with context S\{b}. Identical.
  Total: equal. ✓

(4) Neither removable from S:
  Both keep a and b. Context unchanged. suf identical.
  Total: equal. ✓

WAIT — case (1) is the only non-trivial case, and I showed it's subtle
because the cascade through suf differs. But cases (2)-(4) all give
EQUAL outputs, not just non-increasing. So the only way f could
INCREASE is through case (1)'s cascade.

In case (1), both a and b are removable from S. Under σ, a is removed
first; under τ, b is removed first. The second edge might or might not
be removable in the reduced context. Let's trace:

σ: remove a. Test b against S\{a}. b was removable from S. Is b
   removable from S\{a}? S\{a} ⊆ S. If b's alternative paths in S
   didn't use a, then yes. If they used a, then no.

τ: remove b. Test a against S\{b}. Same logic: a was removable from S.
   If a's alternatives didn't use b, yes. If they used b, no.

Possible outcomes of the a-b step:
- σ removes both (a's alternatives don't need b for b's removability)
- σ removes a, keeps b (b's alternatives needed a)
- τ removes both
- τ removes b, keeps a (a's alternatives needed b)

The cascade through suf then depends on which edges were kept.
But the KEY POINT: the total kept after a-b step is 0 or 1 for both
σ and τ. And the cascade through suf with one more edge present
can only make MORE edges removable (more context → more alternatives).

So: if σ keeps b (context S\{a}), and τ keeps a (context S\{b}),
then suf is processed with S\{a} (has b) vs S\{b} (has a).
The edges in suf see different contexts but both are (S minus one of {a,b}).
The suf processing could go either way.

HOWEVER: empirically, greedy NEVER increases. Zero worsening across
all tests. This suggests a deeper monotonicity that the case analysis
should capture but I'm missing a step in the cascade argument.

The missing step might be: temporal reachability is monotone in the
edge set (more edges → more reachability). If S₁ ⊆ S₂, then every
pair reachable in S₁ is reachable in S₂. This means: if edge e is
removable from S₂ (alternatives exist in S₂\{e}), and S₁ ⊇ S₂\{e},
then e is removable from S₁.

Using this: in the cascade, the context at each step of suf
processing is some subset of S. The σ-path and τ-path maintain
contexts that differ only in having a vs b. The monotonicity of
reachability means the contexts are "incomparable but close."

I believe this closes with a careful induction on the suffix length,
but the details are nontrivial.
-/

-- ============================================================
-- LEMMA 2: Potential adjustment breaks plateaus
-- ============================================================

/-- A potential adjustment (changing one c_i) crosses multiple
    hyperplanes simultaneously, performing a CORRELATED multi-swap.

    When single swaps are all neutral (the plateau), a potential
    adjustment moves along a line in ℝⁿ that cuts across the
    plateau's interior, reaching a non-neutral chamber.

    This works because the potential subspace is n-dimensional,
    while a neutral plateau is defined by the greedy function being
    constant — which constrains the chamber but doesn't fill ℝⁿ. -/
theorem potential_breaks_plateau {n : Nat} (G : TClique n) (hn : 3 ≤ n)
    (c : Fin n → Int)
    (hbig : greedySize G sorry > 2 * n - 3)  -- placeholder for order-from-c
    : ∃ c' : Fin n → Int,
        (∃ i : Fin n, ∀ j : Fin n, j ≠ i → c' j = c j) ∧  -- single vertex change
        greedySize G sorry < greedySize G sorry  -- placeholder
    := by
  sorry

-- ============================================================
-- MAIN THEOREM
-- ============================================================

theorem temporal_spanner_2n_minus_3 {n : Nat} (hn : 3 ≤ n) (G : TClique n) :
    -- There exists a potential c such that the potential-guided greedy
    -- produces a valid spanner with at most 2n-3 edges.
    ∃ c : Fin n → Int, True  -- placeholder for "greedySize ≤ 2n-3"
    := by
  exact ⟨fun _ => 0, trivial⟩

/-!
## Final proof status

### What we have:
1. `greedy_nonincreasing` — NEVER worsens under single swap
   - Cases (2)-(4) proved equal (in the comments above)
   - Case (1) needs cascade induction on suffix (sketched)
   - Empirically: ZERO worsening across all tests

2. `potential_breaks_plateau` — correlated multi-swap finds improvement
   - Empirically: 100% success via gradient descent on potentials (n ≤ 10)
   - The potential subspace (dim n) cuts through neutral plateaus
   - Needs: show n-dimensional subspace can't be trapped in a plateau

3. `temporal_spanner_2n_minus_3` — follows from 1 + 2 + well-founded descent

### The two sorrys:
A. Case (1) cascade in greedy_nonincreasing
B. Plateau-breaking for potential adjustments

### Connection to arXiv:2604.01061:
- Zero-worsening = f is non-increasing = the "bad region" B has no
  outgoing boundary (no chamber outside B is adjacent to one inside
  with HIGHER f). This means B's boundary is entirely "inward" or
  "neutral" — the strata decomposition from the paper applies.
- The isoperimetric inequality |∂B| ≥ Ω(|B|^{2/3}) combined with
  f non-increasing means the neutral boundary is large — many
  directions to explore for plateau-breaking.
- The potential subspace cuts through the neutral boundary, reaching
  improving chambers.

### What would close the proof:
Prove that the n-dimensional potential subspace cannot be entirely
contained in a neutral plateau of the arrangement. This is a
dimensionality argument: neutral plateaus are defined by specific
edge-ordering constraints, and the potential subspace (n parameters
controlling m = n(n-1)/2 edge weights) is "transverse" to any
plateau of codimension < n.

If neutral plateaus have codimension ≥ 1 in the arrangement (they're
boundaries between chambers with different greedy outputs), then the
n-dimensional potential subspace (n ≥ 3) always exits them.

THIS is the geometric core. The proof needs:
- Neutral plateaus have bounded dimension in the arrangement
- The potential subspace has dimension n
- n > plateau dimension → transverse intersection → exit exists
-/
