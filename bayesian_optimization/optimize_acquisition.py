'''
OPTIMIZE ACQUISITION

Random sampling + local refinement

This finds the x that maximizes the expected improvement (EI).

This is the inner optimization, independent of MSES, just GP predictions

Approach:
    1. Sample many random points in the design space bounds
    2. Evaluate EI at each
    3. Take the top few, refine with scipy.optimize.minimize (L-BFGD-B with bounds)
    4. Return best x found

'''

from acquisitions import expected_improvement
import numpy as np
from scipy.optimize import minimize

def optimize_acquisition(X, y, y_best, bounds, l, n_rand=1000, n_local_starts=10):
    '''
    Maximize EI over the bounded domain.

    predict_fn:     GP prediction function. Takes (m, d) array, returns (mu, var)
    y_current:      scalar, current best observed objective value
    bounds:         list of (low, high) tuples for each design variable

    Returns:
    x_best:         design point (1D array of length d) with highest EI found.
    '''
    bounds = np.array(bounds)  # size (d, 2)
    d = bounds.shape[0]        # number of design variables because each has bounds

    # Sample many random points in the design space bounds
    X_random = np.random.uniform(bounds[:, 0], bounds[:, 1], size=(n_rand, d))

    # Evaluate the expected improvement at each point
    EI_rand = expected_improvement(X, y, X_random, l, y_best)

    # Take top few of the evaluated points
    top_idx = np.argsort(EI_rand)[-n_local_starts:]
    EI_rand_top = EI_rand[top_idx]
    X_rand_top = X_random[top_idx]

    # Initialize EI_best and x_best from the best random point
    EI_best = EI_rand[top_idx[-1]] # last in sorted order = highest EI
    x_best = X_random[top_idx[-1]] # the corresponding point

    # Local refinement (more expensive)
    def neg_EI(x):
        # Wrap EI for scipy.minimize: takes 1D x, returns negated scalar EI
        x_2d = x.reshape(1, -1)
        EI_value = expected_improvement(X, y, x_2d, l, y_best)[0]
        return -EI_value

    for i in top_idx:
        result = minimize(neg_EI, X_random[i], method='L-BFGS-B', bounds=bounds)

        # result.fun is -EI at the optimum, so EI = -result.fun
        EI_refined = -result.fun

        # Return best x found
        if EI_refined > EI_best:
            EI_best = EI_refined
            x_best = result.x

    return x_best

