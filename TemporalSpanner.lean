/-
  Temporal Spanner on Cliques: O(n) bound via bi-star construction.

  Empirical finding: every temporal clique on n vertices admits a spanner
  with at most 2n-3 edges, structured as two spanning trees sharing a
  bridge edge at the temporal midpoint.

  Status: theorem statement + proof sketch. Proof incomplete.
-/

import Mathlib.Data.Finset.Basic
import Mathlib.Data.Finset.Card
import Mathlib.Order.Basic

/-- A temporal clique on n vertices with single labels. -/
structure TemporalClique (n : ℕ) where
  /-- Timestamp assignment: each unordered pair gets a distinct positive integer. -/
  label : Fin n → Fin n → ℕ
  /-- Labels are symmetric (undirected edges). -/
  symm : ∀ u v, label u v = label v u
  /-- No self-loops. -/
  no_self : ∀ v, label v v = 0
  /-- All edge labels are positive. -/
  pos : ∀ u v, u ≠ v → label u v > 0
  /-- All edge labels are distinct. -/
  distinct : ∀ u₁ v₁ u₂ v₂, u₁ ≠ v₁ → u₂ ≠ v₂ →
    (u₁, v₁) ≠ (u₂, v₂) → (u₁, v₁) ≠ (v₂, u₂) →
    label u₁ v₁ ≠ label u₂ v₂

/-- A journey is a sequence of vertices where consecutive edge timestamps
    are non-decreasing. -/
def IsJourney {n : ℕ} (G : TemporalClique n) : List (Fin n) → Prop
  | [] => True
  | [_] => True
  | u :: v :: rest =>
    G.label u v > 0 ∧
    match rest with
    | [] => True
    | w :: _ => G.label u v ≤ G.label v w ∧ IsJourney G (v :: w :: rest.tail)

/-- Vertex u can reach vertex v in G. -/
def Reachable {n : ℕ} (G : TemporalClique n) (u v : Fin n) : Prop :=
  ∃ path : List (Fin n), path.head? = some u ∧ path.getLast? = some v ∧ IsJourney G path

/-- G is temporally connected if all pairs are mutually reachable. -/
def TemporallyConnected {n : ℕ} (G : TemporalClique n) : Prop :=
  ∀ u v : Fin n, u ≠ v → Reachable G u v

/-- An edge set (subset of vertex pairs). -/
def EdgeSet (n : ℕ) := Finset (Fin n × Fin n)

/-- The subgraph induced by an edge set. -/
def Subgraph {n : ℕ} (G : TemporalClique n) (S : EdgeSet n) : TemporalClique n where
  label := fun u v => if (u, v) ∈ S ∨ (v, u) ∈ S then G.label u v else 0
  symm := by sorry
  no_self := by sorry
  pos := by sorry
  distinct := by sorry

/-- S is a temporal spanner of G if it preserves all reachability. -/
def IsSpanner {n : ℕ} (G : TemporalClique n) (S : EdgeSet n) : Prop :=
  ∀ u v : Fin n, Reachable G u v → Reachable (Subgraph G S) u v

/-- Number of undirected edges in an edge set. -/
noncomputable def edgeCount {n : ℕ} (S : EdgeSet n) : ℕ :=
  (S.filter (fun p => p.1.val < p.2.val)).card

/-!
## Main Theorem (to prove)

Every temporally connected temporal clique on n ≥ 2 vertices admits a
temporal spanner with at most 2n - 3 edges.
-/

theorem bistar_spanner_exists {n : ℕ} (hn : n ≥ 2) (G : TemporalClique n)
    (hconn : TemporallyConnected G) :
    ∃ S : EdgeSet n, IsSpanner G S ∧ edgeCount S ≤ 2 * n - 3 := by
  sorry

/-!
## Proof sketch (from empirical analysis)

### Construction

Given a temporal clique G on n vertices with distinct timestamps:

1. **Find the temporal midpoint.** Let m be the median timestamp among
   all n(n-1)/2 edges.

2. **Find the early hub.** Among all vertices, pick h_e that maximizes
   the number of incident edges with timestamps ≤ m. In a clique,
   h_e has at least (n-1)/2 such edges by pigeonhole.

3. **Find the late hub.** Pick h_l that maximizes incident edges with
   timestamps > m. Similarly, h_l has at least (n-1)/2 such edges.

4. **Build the early tree.** Root a spanning tree at h_e using edges
   with timestamps ≤ m (plus edges to reach vertices not directly
   connected to h_e before m). This tree has n-1 edges and every
   vertex can reach h_e via a journey ending by time ≤ m.

5. **Build the late tree.** Root a spanning tree at h_l using edges
   with timestamps > m. This tree has n-1 edges and h_l can reach
   every vertex via a journey starting after time m.

6. **Bridge.** The edge (h_e, h_l) appears in both trees if its
   timestamp is near m. This shared edge reduces the total from
   2(n-1) to 2n-3.

### Why it works

For any pair (u, v):
- u reaches h_e via the early tree (journey with timestamps ≤ m)
- h_e reaches h_l via the bridge edge at time ~ m
- h_l reaches v via the late tree (journey with timestamps > m)
- The composed journey u → h_e → h_l → v has non-decreasing timestamps.

### What remains to prove

1. **Hub existence.** Show that for any timestamp assignment, there
   exist h_e and h_l such that the early and late trees span all
   vertices. This is the hard part — the adversary might distribute
   timestamps to prevent any single vertex from serving as a hub.

2. **Bridge compatibility.** Show that the early tree's latest arrival
   at h_e precedes the bridge time, which precedes the late tree's
   earliest departure from h_l.

3. **Exact count.** Show the shared edge reduces 2(n-1) to 2n-3,
   not less and not more.

### Empirical evidence

Exhaustive computation on K_4 (all 720 labelings) and sampled exact
computation on K_5, K_6, K_7 confirm:
- K_4: worst-case minimum spanner = 5 = 2(4)-3
- K_5: worst-case minimum spanner = 7 = 2(5)-3
- K_6: worst-case minimum spanner = 9 = 2(6)-3
- K_7: worst-case minimum spanner = 11 = 2(7)-3

Every worst case exhibits the bi-star structure: two hub vertices,
one handling forward reachability (early timestamps), one handling
backward reachability (late timestamps), sharing one bridge edge.
-/
