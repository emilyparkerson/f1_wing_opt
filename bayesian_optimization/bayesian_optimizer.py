import numpy as np

from bayesian_optimization.kernels import lengthscale_hp_optimization
from bayesian_optimization.optimize_acquisition import optimize_acquisition
from setup.constraints import normalized_constraints


def normalize(x, bounds):
    bounds = np.array(bounds)
    return (x - bounds[:, 0]) / (bounds[:, 1] - bounds[:, 0])


def denormalize(x_norm, bounds):
    bounds = np.array(bounds)
    return bounds[:, 0] + x_norm * (bounds[:, 1] - bounds[:, 0])


def bayesian_loop(X0, y0, objective_fn, bounds, constraints, max_iter=20):
    """
    Run Bayesian optimization, but skip failed MSES evaluations.
    """

    bounds_arr = np.array(bounds)

    X = np.copy(X0)
    y = np.copy(y0)

    for i in range(max_iter):

        X_norm = normalize(X, bounds_arr)

        y_mean = y.mean()
        y_centered = y - y_mean

        l = lengthscale_hp_optimization(X_norm, y_centered)

        y_best_centered = y_centered.max()
        normalized_bounds = [(0, 1)] * X.shape[1]

        valid_candidate_found = False

        for attempt in range(20):

            x_next_norm = optimize_acquisition(
                X_norm,
                y_centered,
                y_best_centered,
                normalized_bounds,
                l,
                constraints=normalized_constraints(constraints, bounds_arr),
            )

            x_next = denormalize(x_next_norm, bounds_arr)
            y_next = objective_fn(x_next)

            if y_next is None:
                print(f"Iter {i+1}, attempt {attempt+1}: failed airfoil, trying another")
                continue

            X = np.vstack([X, x_next])
            y = np.append(y, y_next)

            print(f"Iter {i+1}: y_next = {y_next:.4f}  |  best so far = {y.max():.4f}")

            valid_candidate_found = True
            break

        if not valid_candidate_found:
            print(f"Iter {i+1}: no valid candidate found, skipping this BO iteration")
            continue

    best_idx = np.argmax(y)

    return X, y, X[best_idx], y[best_idx]