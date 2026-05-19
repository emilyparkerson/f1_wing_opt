# Agnostic Bayesian Optimizer
# OUTLINE
    # Maintains X_history, y_history
    # Loop: fit gaussian process, maiximize EI, evaluate at suggested point
    # Returns best (x, y) found
'''
# Here's the idea:
We have an expensive objective function f(x). We cant compute its gradient.
We can only afford a small number of evaluations. We want to use each evaluation as wisely as possible
so be build a probabilistic model, a GP, that tells us 
not just what we think f looks like but how uncertain we are
we then pick the next x to evaluate by trading between "places that look good"
against "places we dont yet understant"

The GP gets refit at every iteration with new data. initiallyu, it knows almost nothing. 
After many evaluations, it knows the response surface well in the regions you've explored
'''

'''
X for training inputs, y for training targets (the book uses these)
x_* (or X_star in code) for prediction points (the book uses x_* and X_*)
K for the training-training kernel matrix (book: K)
k_* for the new-vs-training kernel vector/matrix (book: K_*)
K_** for the new-vs-new kernel (book: K_**)
var for variance (book uses ν̂ for predictive variance — equation 18.16)
'''

import numpy as np
from bayesian_optimization.kernels import lengthscale_hp_optimization
from bayesian_optimization.optimize_acquisition import optimize_acquisition

# By normalizing the variables, the applied length scale is meaningful to all of the design variables
def normalize(x, bounds):
    # Map x from [lo hi] bounds to [0 1] per dimension
    bounds = np.array(bounds)
    normalized_x = (x-bounds[:, 0])/ (bounds[:, 1] - bounds[:, 0])
    return normalized_x

def denormalize(x_norm, bounds):
    # Map normalized x back to original dimensions
    bounds = np.array(bounds)
    denormalized_x = bounds[:, 0] + x_norm * (bounds[:, 1] - bounds[:, 0])
    return denormalized_x

def bayesian_loop(X0, y0, objective_fn, bounds, max_iter=20):
    '''
    Run Bayesian optimization for max_iter iterations

    objective-fn:   scalar to maximize from callable f(x_1d)
    X0:             array of size (n0,d), initial training inputs
    y0:             array of size (n0,), initial training targets
    bounds:         list of (low, high) per dimension

    Returns:
    X:              (n0 + max_iter, d), final training inputs
    y:              (n0 + max_iter,), final training targets
    x_best:         (d,), best design point found
    y_best:         scalar, best target found
    '''
    bounds_arr = np.array(bounds)
    X = np.copy(X0)
    y = np.copy(y0)

    for i in range(max_iter):

        # Normalize for internal optimization
        X_norm = normalize(X, bounds_arr)

        # Center outputs to mean of zero
        y_mean = y.mean()
        y_centered = y - y_mean

        # Fit the GP parameters (only lengthscale at the moment)
        l = lengthscale_hp_optimization(X_norm, y_centered)

        # Finds next point in the normalized space
        y_best_centered = y_centered.max()
        normalized_bounds = [(0,1)] * X.shape[1]
        x_next_norm = optimize_acquisition(X_norm, y_centered, y_best_centered, 
                                           normalized_bounds, l)

        # Denormalize and evaluate the expensive objective
        x_next = denormalize(x_next_norm, bounds)
        y_next = objective_fn(x_next, )

        # Update the history
        X = np.vstack([X, x_next])
        y = np.append(y, y_next)

        print(f"Iter {i+1}: y_next = {y_next:.4f}  |  best so far = {y.max():.4f}")

    best_idx = np.argmax(y)

    return X, y, X[best_idx], y[best_idx]
