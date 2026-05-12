# Agnostic Bayesian Optimizer
# OUTLINE
    # Maintains X_history, y_history
    # Loop: fit gaussian process, maiximize EI, evaluate at suggested point
    # Returns best (x, y) found

import numpy as np

def bayesian_monte_carlo(GP, w, mu_z, sigma_z):
    W = np.diag(w**2)
    invK = np.invert(K(GP.X, GP.X, GP.k))
    for i, z in enumerate(GP.X):
        q[i] = np.exp(-((z - mu_z)⋅(inv(W + sigma_z)*(z - mu_z)))/2)
        q *= np.det(W\sigma_z + I))**(-0.5)
        mu = np.transpose(q) * invK * GP.y
        nu = np.det(2*W\sigma_z + I) ^ (-0.5) - (np.transpose(q) * invK * q)[1]
 
    return mu, nu