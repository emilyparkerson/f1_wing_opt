# Squared exponential kernel

'''
SQUARED EXPONENTIAL KERNEL  (Eq. 18.9)

k(x, x') = exp(-||x - x'||² / (2l²))

Plus maximum-likelihood lengthscale fitting (Eq. 18.32).

The distributed function evaluations are distributed
according to Eq. 18.8. Where m(x) is a mean function
and the covariance function (kernel) is k(x,x_prime).

'''

import numpy as np
from scipy.optimize import minimize

def sq_exp_kernel(X1, X2, l):
    '''
    Squared exponential kernel between two sets of points.
    X1: shape(n1, d), first set of design points evaluated
    X2: shape(n2, d), second set of design points evaluates
    Returns: shape n1 x n2 (there is a kernel value for every pair)
    '''
    
    # Pairwise squared distance
    X1_sq = np.sum(X1**2, axis=1, keepdims=True) # n1, 1
    X2_sq = np.sum(X2**2, axis=1, keepdims=True).T # 1, n2

    # ||xi - xj||^2 = ||x1||^2 -2xi*xj + ||xj||^2
    norm = X1_sq - 2*X1@X2.T + X2_sq # numpy broadcasting

    # K
    K = np.exp(-norm / (2*l**2))
    return K


def lengthscale_hp_optimization(X, y):

    n = X.shape[0]

    def neg_log_marginal_likelihood(log_l):

        # Enfornce positivity
        l = np.exp(log_l[0])

        # Covariance matrix with small deviation 
        jitter = 10e-6
        K = sq_exp_kernel(X, X, l) + jitter*np.eye(n)

        # Eq. 18.32: nll = (0.5 * y.T @ alpha + np.sum(np.log(np.diag(L))) + 0.5 * n * np.log(2*np.pi))
        try:
            L = np.linalg.cholesky(K)
        except np.linalgnLinAlgError:
            return 1e10 # rejects lengthscale if K not pos def
        
        # Solve K * alpha = y via two triangular solves
        z = np.linalg.solve(L, y)
        alpha = np.linalg.solve(L.T, z)

        term1 = 0.5 * y.T @ alpha # = 0.5 * log|K|
        term2 = np.sum(np.log(np.diag(L)))
        term3 = 0.5 * n * np.log(2 * np.pi)
        nl1 = term1 + term2 + term3

        return nl1
    
    # Optimize log lengthscale
    result = minimize(neg_log_marginal_likelihood,
        x0=[0.0], method="L-BFGS-B", bounds=[(np.log(1e-2), np.log(1e2))])

    best_l = np.exp(result.x[0])

    return best_l