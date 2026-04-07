"""
Timing probe: measure brute-force solve time scaling for minimum temporal clique spanner.

For each k, generates random k*k all-distinct matrices and finds the minimum
spanner by brute force. Records solve time to detect exponential vs polynomial scaling.
"""

import itertools
import time
import numpy as np
from x3c_reduction import temporal_reachable, all_reachable, covering_hypergraph


def forced_edges(M):
    """Return M^- (column minima) union M^+ (row maxima)."""
    k = M.shape[0]
    m_minus = set()
    m_plus = set()
    for j in range(k):
        min_i = np.argmin(M[:, j])
        m_minus.add((int(min_i), j))
    for i in range(k):
        max_j = np.argmax(M[i, :])
        m_plus.add((i, int(max_j)))
    return m_minus | m_plus


def min_spanner_brute_timed(M):
    """Find minimum spanner by brute force over non-forced edges.

    Returns (min_spanner_size, solve_time_seconds, subsets_checked).
    min_spanner_size = |forced| + |extra edges needed|.
    """
    k = M.shape[0]
    forced = forced_edges(M)
    all_edges_set = {(i, j) for i in range(k) for j in range(k)}
    optional = sorted(all_edges_set - forced)

    subsets_checked = 0
    t0 = time.perf_counter()

    # Check if forced edges alone suffice
    subsets_checked += 1
    if all_reachable(M, forced):
        elapsed = time.perf_counter() - t0
        return len(forced), elapsed, subsets_checked

    # Enumerate subsets of optional edges, smallest first
    for size in range(1, len(optional) + 1):
        for subset in itertools.combinations(optional, size):
            subsets_checked += 1
            candidate = forced | set(subset)
            if all_reachable(M, candidate):
                elapsed = time.perf_counter() - t0
                return len(candidate), elapsed, subsets_checked

    # Fallback: all edges
    elapsed = time.perf_counter() - t0
    return k * k, elapsed, subsets_checked


def run_probe(k_values, n_instances=20):
    """Run the timing probe across k values."""
    results = []

    for k in k_values:
        print(f"\n--- k={k} ---")
        n_optional = k * k - 2 * k  # approximate non-forced edges (upper bound)
        print(f"  (up to ~{n_optional} optional edges, 2^{n_optional} worst case)")

        for seed in range(n_instances):
            rng = np.random.default_rng(seed)
            vals = rng.permutation(k * k)
            M = vals.reshape(k, k)

            spanner_size, elapsed, checked = min_spanner_brute_timed(M)
            results.append({
                'k': k,
                'seed': seed,
                'min_spanner_size': spanner_size,
                'solve_time': elapsed,
                'subsets_checked': checked,
            })
            print(f"  seed={seed:2d}: size={spanner_size}, "
                  f"time={elapsed:.4f}s, checked={checked}")

    return results


def fit_models(results):
    """Fit exponential and polynomial models to median solve time vs k."""
    from scipy.optimize import curve_fit

    # Group by k, take median
    k_vals = sorted(set(r['k'] for r in results))
    medians = []
    for k in k_vals:
        times = [r['solve_time'] for r in results if r['k'] == k]
        medians.append(np.median(times))

    k_arr = np.array(k_vals, dtype=float)
    t_arr = np.array(medians)

    print(f"\nMedian solve times:")
    for k, t in zip(k_vals, medians):
        print(f"  k={k}: {t:.6f}s")

    # Exponential: a * 2^(b*k)
    def exp_model(k, a, b):
        return a * np.power(2.0, b * k)

    # Polynomial: a * k^b
    def poly_model(k, a, b):
        return a * np.power(k, b)

    # Fit exponential
    try:
        popt_exp, _ = curve_fit(exp_model, k_arr, t_arr, p0=[1e-6, 1.0], maxfev=10000)
        t_pred_exp = exp_model(k_arr, *popt_exp)
        ss_res_exp = np.sum((t_arr - t_pred_exp) ** 2)
        ss_tot = np.sum((t_arr - np.mean(t_arr)) ** 2)
        r2_exp = 1 - ss_res_exp / ss_tot if ss_tot > 0 else float('nan')
        print(f"\nExponential fit: a={popt_exp[0]:.2e}, b={popt_exp[1]:.4f}")
        print(f"  R^2 = {r2_exp:.6f}")
    except Exception as e:
        print(f"\nExponential fit failed: {e}")
        r2_exp = float('nan')
        popt_exp = None

    # Fit polynomial
    try:
        popt_poly, _ = curve_fit(poly_model, k_arr, t_arr, p0=[1e-6, 3.0], maxfev=10000)
        t_pred_poly = poly_model(k_arr, *popt_poly)
        ss_res_poly = np.sum((t_arr - t_pred_poly) ** 2)
        r2_poly = 1 - ss_res_poly / ss_tot if ss_tot > 0 else float('nan')
        print(f"\nPolynomial fit: a={popt_poly[0]:.2e}, b={popt_poly[1]:.4f}")
        print(f"  R^2 = {r2_poly:.6f}")
    except Exception as e:
        print(f"\nPolynomial fit failed: {e}")
        r2_poly = float('nan')
        popt_poly = None

    return {
        'k_vals': k_vals,
        'medians': medians,
        'r2_exp': r2_exp,
        'r2_poly': r2_poly,
        'popt_exp': popt_exp,
        'popt_poly': popt_poly,
    }


def main():
    # k=3..7 but bail if too slow
    k_values = [3, 4, 5, 6, 7]

    # Quick feasibility check for large k
    print("Feasibility check:")
    for k in k_values:
        n_opt_approx = k * k - 2 * k  # rough upper bound on optional edges
        total_subsets = 2 ** n_opt_approx
        print(f"  k={k}: ~{n_opt_approx} optional edges, ~2^{n_opt_approx} = {total_subsets:.0e} subsets")

    results = []
    for k in k_values:
        # Test one instance first to check feasibility
        rng = np.random.default_rng(999)
        vals = rng.permutation(k * k)
        M = vals.reshape(k, k)

        print(f"\nFeasibility test k={k}...")
        t0 = time.perf_counter()
        spanner_size, elapsed, checked = min_spanner_brute_timed(M)
        print(f"  Test instance: time={elapsed:.2f}s, checked={checked}")

        if elapsed > 120:  # 2 minute cutoff per instance
            print(f"  k={k} too slow ({elapsed:.1f}s for one instance), stopping.")
            break

        # Run full batch
        batch = run_probe([k], n_instances=20)
        results.extend(batch)

    if len(set(r['k'] for r in results)) >= 3:
        fits = fit_models(results)
    else:
        print("\nNot enough k values for model fitting.")
        fits = None

    return results, fits


if __name__ == "__main__":
    results, fits = main()
