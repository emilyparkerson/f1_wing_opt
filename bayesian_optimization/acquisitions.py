'''
ACQUISITION FUNCTION

This is any function that reflects the location we want to evaluate next

We will use expected improvement

https://www.ritchievink.com/blog/2019/08/25/algorithm-breakdown-bayesian-optimization/

'''

'''
EXPECTED IMPROVEMENT  (Eq. 19.12, standardized form)

For MAXIMIZATION. xi is a small exploration parameter.
'''

import numpy as np
from scipy import stats
from gp import gp_predict


def expected_improvement(X, y, X_star, l, y_best, xi = 0.01):
    '''
    X:          array of shape (n, d), training inputs
    y:          array of shape (n,), training targets
    X_star:     array of shape (m,d), new points to predict at
    l:          scalar, kernal lengthscale hyperparameter
    y_best:     scalar, current best observed value
    xi:         scalar, encourages exploration 

    Returns: expected_improvement = E(max(f_proposed - f_current),0)
        # array, shape (m,) of EI at each point
    '''

    mu_star, var_star = gp_predict(X, y, X_star, l)
    sigma_star = np.sqrt(var_star)
    sigma_star = np.maximum(sigma_star, 1e-12)

    # Adding small term to favor exploration
    delta = mu_star - y_best - xi
    z = delta / sigma_star

    # Expected improvement
    EI = delta * stats.norm.cdf(z) + sigma_star * stats.norm.pdf(z)
    EI = np.where(sigma_star > 1e-9, EI, 0.0)

    return EI