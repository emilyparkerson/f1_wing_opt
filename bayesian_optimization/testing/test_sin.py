import sys
import os
import numpy as np
import matplotlib.pyplot as plt

# Add parent directory to path so we can import bayesian_optimizer
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(SCRIPT_DIR, '..')))

from bayesian_optimizer import bayesian_loop, normalize
from gp import gp_predict
from kernels import lengthscale_hp_optimization


# Path setup — always relative to this script, not the working directory
TRAINING_CSV = os.path.join(SCRIPT_DIR, "training_data.csv")
BOUNDS_CSV   = os.path.join(SCRIPT_DIR, "design_variable_bounds.csv")

# Iterations at which to take a snapshot of the GP
SNAPSHOT_ITERS = [1, 3, 10, 25]


def sin_objective(x):
    """
    Test objective: sin(x). Maximum is 1.0 at x = π/2 ≈ 1.5708.
    BO is told to MAXIMIZE, so we want it to find x near π/2.
    """
    return float(np.sin(x[0]))


def plot_gp_snapshot(ax, X, y, n_initial, bounds, title):
    """
    Plot the GP fit at the current state of (X, y), along with the true
    sin function and the evaluated points.
    """
    bounds_arr = np.array(bounds)
    
    # Refit the GP at this snapshot (same as BO does internally)
    X_norm = normalize(X, bounds_arr)
    y_mean = y.mean()
    y_centered = y - y_mean
    l = lengthscale_hp_optimization(X_norm, y_centered)
    
    # Predict over a dense grid
    x_grid = np.linspace(bounds[0][0], bounds[0][1], 200).reshape(-1, 1)
    x_grid_norm = normalize(x_grid, bounds_arr)
    mu, var = gp_predict(X_norm, y_centered, x_grid_norm, l=l)
    mu = mu + y_mean   # undo centering
    std = np.sqrt(var)
    
    # Plot true function
    ax.plot(x_grid, np.sin(x_grid), 'k--', label='true: sin(x)', linewidth=1.5)
    
    # Plot GP mean and uncertainty band
    ax.plot(x_grid, mu, 'b', label='GP mean', linewidth=2)
    ax.fill_between(x_grid.flatten(), mu - 2*std, mu + 2*std,
                    alpha=0.2, color='blue', label='GP ±2σ')
    
    # Initial training points (red) vs. BO-selected points (green)
    ax.scatter(X[:n_initial, 0], y[:n_initial], c='red', s=60,
               edgecolors='black', label='initial points', zorder=5)
    if len(X) > n_initial:
        ax.scatter(X[n_initial:, 0], y[n_initial:], c='lime', s=60,
                   edgecolors='black', label='BO-selected', zorder=5)
    
    # Mark the true optimum
    ax.axvline(np.pi/2, color='gray', linestyle=':', label='true optimum', linewidth=1)
    
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.set_title(title)
    ax.set_ylim(-1.5, 1.5)
    ax.legend(loc='lower left', fontsize=8)
    ax.grid(alpha=0.3)


if __name__ == "__main__":
    # ---- Generate the CSVs ----
    print(f"Working directory: {os.getcwd()}")
    print(f"Script directory:  {SCRIPT_DIR}")
    print(f"Writing CSVs to:   {SCRIPT_DIR}\n")
    
    np.random.seed(0)
    X_train = np.random.uniform(0, 2*np.pi, size=3)
    y_train = np.sin(X_train)
    data = np.column_stack([X_train, y_train])
    
    np.savetxt(TRAINING_CSV, data, delimiter=",")
    np.savetxt(BOUNDS_CSV, np.array([[0.0, 2*np.pi]]), delimiter=",")
    
    assert os.path.isfile(TRAINING_CSV), f"Failed to create {TRAINING_CSV}"
    assert os.path.isfile(BOUNDS_CSV), f"Failed to create {BOUNDS_CSV}"
    print("CSV files created successfully.\n")
    
    # ---- Load them back in ----
    training_data = np.loadtxt(TRAINING_CSV, delimiter=",")
    X0 = training_data[:, 0:1]
    y0 = training_data[:, 1]
    n_initial = len(X0)
    
    bounds_arr = np.loadtxt(BOUNDS_CSV, delimiter=",")
    if bounds_arr.ndim == 1:
        bounds_arr = bounds_arr.reshape(1, -1)
    bounds = [tuple(b) for b in bounds_arr]
    
    print(f"Initial training data: {n_initial} points")
    print(f"Initial best y: {y0.max():.4f}")
    print(f"Bounds: {bounds}")
    print(f"True optimum: sin(π/2) = 1.0 at x = {np.pi/2:.4f}\n")
    
    # ---- Run BO ----
    max_iter = max(SNAPSHOT_ITERS)
    X, y, x_best, y_best = bayesian_loop(
        X0=X0,
        y0=y0,
        objective_fn=sin_objective,
        bounds=bounds,
        max_iter=max_iter,
    )
    
    # ---- Report ----
    print(f"\nFinal best x: {x_best[0]:.4f}  (true: {np.pi/2:.4f})")
    print(f"Final best y: {y_best:.4f}  (true: 1.0)")
    print(f"Distance to true optimum: {abs(x_best[0] - np.pi/2):.4f}\n")
    
    # ---- Plot snapshots at the requested iterations ----
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    axes = axes.flatten()
    
    for ax, iter_num in zip(axes, SNAPSHOT_ITERS):
        # At iter_num iterations, we have n_initial + iter_num total points
        n_points = n_initial + iter_num
        X_at_iter = X[:n_points]
        y_at_iter = y[:n_points]
        
        best_y_at_iter = y_at_iter.max()
        best_x_at_iter = X_at_iter[np.argmax(y_at_iter), 0]
        
        title = (f"After iter {iter_num} "
                 f"(best y = {best_y_at_iter:.4f}, best x = {best_x_at_iter:.4f})")
        
        plot_gp_snapshot(ax, X_at_iter, y_at_iter, n_initial, bounds, title)
    
    fig.suptitle("BO on sin(x): GP fit at selected iterations", fontsize=14)
    fig.tight_layout()
    
    output_path = os.path.join(SCRIPT_DIR, "bo_sin_snapshots.png")
    plt.savefig(output_path, dpi=120, bbox_inches='tight')
    print(f"Plot saved to: {output_path}")
    plt.show()