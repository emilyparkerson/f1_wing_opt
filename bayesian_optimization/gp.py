'''
GAUSSIAN PROCESS PREDICTION

Posterior mean and variance at new points X_star
given training data (X, y).

Implements equations 18.14, 18.15, and 18.16 from Chapter 18.

Assumes zero mean function: m(x) = 0.
'''

import numpy as np
from .kernels import sq_exp_kernel

def m(x):
    mean = 0 # Right now assuming this is 0
    return mean

def gp_predict(X, y, X_star, l, jitter=1e-8):
    '''
    X:          array of shape (n, d), training inputs
    y:          array of shapte (n,), training targets
    X_star:     array of shape (m,d), new points to predict at
    l:          scalar, kernal lengthscale hyperparameter

    Returns:
    mu:         array of shape (m,), predicted mean at each new point
    var:        array of shape (m,), variance of predicted mean
    '''

    # Finding the Kernels of interest (Eq. 18.14)
    n = X.shape[0]
    K = sq_exp_kernel(X, X, l) + jitter * np.eye(n)
    K_star = sq_exp_kernel(X_star, X, l)
    K_starT = K_star.T
    K_starstar = sq_exp_kernel(X_star, X_star, l)

    # Predicted mean (Eq. 18.15)
    theta = np.linalg.solve(K, y - m(X))
    mu_hat = m(X_star) + K_star @ theta

    # Variation of the predicted mean (18.16)
    covar_hat = K_starstar - K_star @ np.linalg.solve(K, K_starT)
    var_hat = np.clip(np.diag(covar_hat), 1e-12, None)

    return mu_hat, var_hat