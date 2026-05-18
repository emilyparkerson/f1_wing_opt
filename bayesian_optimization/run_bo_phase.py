import numpy as np
import matplotlib.pyplot as plt
from .bayesian_optimizer import bayesian_loop

def run_bo_phase(training_csv, bounds_csv, scoring_function, phase_name, max_iter=25,):

    # Load training data

    training_data = np.loadtxt(training_csv, delimiter=",")

    X0 = training_data[:, :-1]
    y0 = training_data[:, -1]

    n_initial = len(X0)

    bounds_arr = np.loadtxt(bounds_csv, delimiter=",")

    if bounds_arr.ndim == 1:
        bounds_arr = bounds_arr.reshape(1, -1)

    bounds = [tuple(b) for b in bounds_arr]

    print(f"\n===== {phase_name} =====")
    print(f"Initial points: {n_initial}")
    print(f"Initial best y: {y0.max():.4f}")

    # Run BO

    X, y, x_best, y_best = bayesian_loop(
        X0=X0, y0=y0, objective_fn=scoring_function, bounds=bounds, max_iter=max_iter,)

    print(f"\nFinal best y: {y_best:.4f}")
    print(f"Final best x:\n{x_best}")

    # Track best-so-far history

    n_vars = X.shape[1]
    n_iters = len(y)

    best_scores = np.zeros(n_iters)
    best_designs = np.zeros((n_iters, n_vars))

    current_best_idx = 0

    for i in range(n_iters):

        if y[i] > y[current_best_idx]:
            current_best_idx = i
        best_scores[i] = y[current_best_idx]
        best_designs[i, :] = X[current_best_idx, :]

    # Plot design variable evolution

    fig, axes = plt.subplots(n_vars, 1, figsize=(10, 2.5 * n_vars), sharex=True)

    # Handle 1D case
    if n_vars == 1:
        axes = [axes]

    iterations = np.arange(n_iters)

    for j, ax in enumerate(axes):

        scatter = ax.scatter(
            iterations, best_designs[:, j], c=best_scores,
            cmap='viridis', s=60, edgecolors='black')

        ax.plot(
            iterations, best_designs[:, j], alpha=0.5)

        ax.set_ylabel(f'x{j+1}')
        ax.grid(alpha=0.3)

    axes[-1].set_xlabel('Iteration')
    cbar = fig.colorbar(scatter, ax=axes)
    cbar.set_label('Best score so far')
    fig.suptitle(f'{phase_name}: Evolution of Best Design Variables', fontsize=14)
    fig.tight_layout()
    output_path = f"{phase_name}_bo_design_variable_evolution.png"
    plt.savefig(output_path, dpi=120, bbox_inches='tight')
    print(f"\nPlot saved to: {output_path}")
    plt.show()

    return X, y, x_best, y_best