# The Random Version (CPS Open Question 3)

## Target

**Theorem.** Let K_n be the temporal clique with distinct edge timestamps drawn as a uniformly random permutation of {1, ..., C(n,2)}. Let S(σ) be the size of the minimum temporal spanner of K_n under assignment σ. Then:

$$\Pr_\sigma[S(\sigma) \le 2n-3] \to 1 \text{ as } n \to \infty.$$

This is CPS Open Question 3 (Casteigts-Peters-Schoeters 2021, arxiv:1810.00104).

## What we have (empirical)

From our session 4 data:
- P(random h is a valid hub via greedy) ≥ 64% at K_6, rising to 92.5% at K_20
- P(best hub ≤ 2n-3) → 1: 99.7% at K_6, 100% at K_10+
- The greedy tree cover = exactly n-2 at K_12+ for every instance tested

## The construction

Star + tree with hub h:
- star(h): n-1 edges, covers all "forward" pairs (where both endpoints have T > T_h for one and T < T_h for the other)
- Tree: n-2 edges from non-star, handling backward pairs

The question: for random σ, does P(some hub h has a valid (n-2)-tree) → 1?

## The probabilistic argument

**Step 1: Fix σ and pick h uniformly at random from V.**

For each hub h, let B(h) = set of backward pairs (pairs where star(h) alone doesn't route).

|B(h)| = C(n-1, 2) = (n-1)(n-2)/2, exactly, for every hub.

**Step 2: Define "good hub" as one where greedy finds an (n-2)-tree covering all backward pairs.**

Let G be the set of good hubs. We want: P(|G| ≥ 1) → 1.

By the probabilistic method: if E[|G|] > 0 and Var(|G|) isn't too large, |G| > 0 with high probability.

## What we need to prove

**Lemma 1 (easy).** For a random hub h, P(h is good) = p(n) where p(n) ≥ some constant p_0 > 0.

Empirical p(n): 64% at K_6, 92.5% at K_20. Monotone increasing. p_0 ≥ 0.5 seems safe.

**Lemma 2 (harder).** The events "hub h is good" for different h are approximately independent, or at least have bounded correlation.

**Lemma 3 (conclusion).** P(|G| ≥ 1) = 1 - P(|G| = 0) ≥ 1 - (1 - p_0)^n → 1.

This is the birthday bound structure. Needs Lemma 2 to be rigorous.

## The hard step

Lemma 2 is the hard step. The events aren't independent — different hubs share edges in the graph. Specifically, hub h_1 and hub h_2 share the edge {h_1, h_2}, which is a star edge for both (at different star ranks).

**Approach 1: FKG inequality.** If the events are positively correlated (good hub events are monotone in some partial order on σ), then FKG gives:
$$P(\text{all hubs bad}) \le \prod_h P(\text{hub } h \text{ bad}) \le (1-p_0)^n \to 0$$

FKG requires the good-hub events to be increasing in a specific product lattice. Does such a lattice exist for temporal permutations? Unclear.

**Approach 2: Second moment method.** Compute E[|G|] and E[|G|²]. Then:
$$P(|G| \ge 1) \ge \frac{E[|G|]^2}{E[|G|^2]}$$

Needs E[|G|²] not much larger than E[|G|]². Requires bounding correlations between pairs of hubs.

**Approach 3: Direct coupling.** Construct a coupling between the hub events that makes dependence explicit.

## What's genuinely easier than the adversarial version

- No adversarial timestamp construction to worry about
- Can use probabilistic tools (concentration, LLL, FKG, second moment)
- The empirical data is an overwhelming hint — we just need to make it rigorous
- CPS explicitly stated this as an open question (clear target audience)

## Concrete next steps

1. Compute E[|G|] rigorously for the random model. Is it ≥ pn for some p > 0?
2. Compute Var(|G|) or a correlation bound between pairs of hubs.
3. Check whether FKG applies to the "good hub" event.
4. If all three work: the proof is within reach.

## What would make this an actual contribution

Even a partial result — say, P(spanner ≤ 2n-3 for random σ) ≥ 1 - e^{-cn} for some c > 0 — would be a direct answer to CPS Q3. That's a publishable lemma.
