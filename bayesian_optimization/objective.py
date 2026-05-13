def objective_fake(x):
    """
    Fake objective for testing BO without MSES.
    
    A simple analytical function with a known optimum.
    Replace with the real one once you've confirmed BO works.
    """
    alpha, thickness, thickness_loc, max_camber, camber_loc = x
    
    # Pretend the optimum is at some specific point
    target = np.array([3.0, 0.12, 0.30, 0.04, 0.40])
    distance = np.sum((np.array(x) - target) ** 2)
    
    # Higher = better. Add small noise to simulate MSES jitter.
    return -distance + np.random.normal(0, 0.01)

'''
Claude's idea of our objective function:
"""
from objective import objective, DESIGN_VAR_NAMES

# Bounds on each design variable (must match DESIGN_VAR_NAMES order)
bounds = [
    (-5.0, 15.0),    # alpha (degrees)
    (0.05, 0.20),    # thickness
    (0.20, 0.50),    # thickness_loc
    (0.00, 0.10),    # max_camber
    (0.20, 0.60),    # camber_loc
]

# Generate initial training data
n_initial = 15
X0 = np.array([
    np.random.uniform(b[0], b[1], n_initial) for b in bounds
]).T   # shape (n_initial, d)

y0 = np.array([objective(x) for x in X0])

# Run BO
X, y, x_best, y_best = bayesian_loop(
    objective_fn=objective,
    X0=X0,
    y0=y0,
    bounds=bounds,
    max_iter=85,
)


_eval_cache = {}

def objective_cached(x):
    key = tuple(np.round(x, 4))   # round so near-duplicates hit the cache
    if key in _eval_cache:
        return _eval_cache[key]
    result = objective(np.array(key))
    _eval_cache[key] = result
    return result


import csv

def objective_logged(x):
    score = objective(x)
    with open("eval_log.csv", "a", newline="") as f:
        csv.writer(f).writerow([*x, score])
    return score

import time
t0 = time.time()
score = objective(np.array([2.0, 0.12, 0.30, 0.04, 0.40]))
print(f"One evaluation: {time.time() - t0:.1f} sec")

'''
