import numpy as np

from aero_interface import run_mses
from design_vars import designParameters
from scoring import valid_constraints

from bayesian_optimization.bayesian_optimizer import bayesian_loop


def run_bo_optimizer(config):

    bo_config = config["bo"]

    training_data = np.genfromtxt(
        bo_config["training_csv"],
        delimiter=",",
    )

    X0 = training_data[:, :-1]
    y0 = training_data[:, -1]

    bounds_arr = np.genfromtxt(
        bo_config["bounds_csv"],
        delimiter=",",
        usecols=(0, 1)
    )

    bounds = [tuple(b) for b in bounds_arr]

    scoring_function = config["scoring_function"]

    alpha = config["alpha"]
    mach = config["mach"]
    reynolds = config["reynolds"]

    def objective_fn(x):

        design = designParameters(
            max_camber=x[0],
            max_camber_loc=x[1],
            max_thickness=x[2],
            max_thickness_loc=x[3]
        )

        if not valid_constraints(design):
            return -1e6

        aero_result = run_mses(
            design=design,
            name="bo_candidate",
            alpha=alpha,
            mach=mach,
            reynolds=reynolds,
            plot_geometry=False,
            plot_comparison=False
        )

        score = scoring_function(aero_result, design)

        return score

    X, y, x_best, y_best = bayesian_loop(
        X0=X0,
        y0=y0,
        objective_fn=objective_fn,
        bounds=bounds,
        max_iter=bo_config["max_iter"]
    )

    print("\n===================================")
    print("BO OPTIMIZATION COMPLETE")
    print("===================================")

    print(f"\nBest score = {y_best:.5f}")
    print(f"Best design = {x_best}")