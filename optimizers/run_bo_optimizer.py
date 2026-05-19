import numpy as np

from setup.aero_interface import run_mses
from setup.design_vars import designParameters

from bayesian_optimization.bayesian_optimizer import bayesian_loop


def design_from_x(x):
    """Convert BO's optimization vector to design parameters."""
    return designParameters(
        max_camber=x[0],
        max_camber_loc=x[1],
        max_thickness=x[2],
        max_thickness_loc=x[3],
    )

def x_from_design(design):
    """Convert design parameters to BO's optimization vector."""
    return np.array([
        design.max_camber,
        design.max_camber_loc,
        design.max_thickness,
        design.max_thickness_loc,
    ])


def generate_training_data(seed_design, bounds_arr, training_n, scoring_fn,
                           alpha, mach, reynolds, seed_airfoil, constraints):
    """
    Build initial training data: the seed design + (training_n - 1) random points.
    """
    X_list = [x_from_design(seed_design)]

    # Random perturbations of the seed
    rng = np.random.default_rng(42)
    while len(X_list) < training_n:
        x = rng.uniform(bounds_arr[:, 0], bounds_arr[:, 1])
        if constraints(x):      
            X_list.append(x)
            print("Appended training airfoil")
    print(len(X_list), "training airfoils generated")
        
    # Evaluate all of them
    print(len(X_list), "evaluating training airfoils...")

    y_list = []
    for x in X_list:
        design = design_from_x(x)
        aero = run_mses(
            design=design,
            name="init",
            alpha=alpha,
            mach=mach,
            reynolds=reynolds,
            seed_airfoil=seed_airfoil,
        )
        y_list.append(scoring_fn(aero, design))
    print(len(y_list), "training scores generated")


    return np.array(X_list), np.array(y_list)


def run_bo_optimizer(config):
    bo_config = config["bo"]
    scoring_fn = config["scoring_function"]
    seed_design = config["seed_design"]
    seed_airfoil = config["seed_airfoil"]

    alpha = config["alpha"]
    mach = config["mach"]
    reynolds = config["reynolds"]
    constraints = config["constraints"]
    training_n = config["training_n"]

    # Load bounds first (needed for both initial training and BO)
    bounds_arr = np.genfromtxt(
        bo_config["bounds_csv"],
        delimiter=",",
        usecols=(0, 1),
    )
    bounds = [tuple(b) for b in bounds_arr]

    # Build initial training data from the seed
    print("-----------------------------------")
    print("Building initial training data...")
    print("-----------------------------------")

    X0, y0 = generate_training_data(
        seed_design=seed_design,
        bounds_arr=bounds_arr,
        training_n=training_n,
        scoring_fn=scoring_fn,
        alpha=alpha,
        mach=mach,
        reynolds=reynolds,
        seed_airfoil=seed_airfoil,
        constraints=constraints,
    )

    # Objective for BO to call each iteration
    def objective_fn(x):
        design = design_from_x(x)
        aero_result = run_mses(
            design=design,
            name="bo_candidate",
            alpha=alpha,
            mach=mach,
            reynolds=reynolds,
            seed_airfoil=seed_airfoil,
            plot_geometry=False,
            plot_comparison=False,
        )
        return scoring_fn(aero_result, design)

    # Run BO
    print("-----------------------------------")
    print("Running the Bayesian Optimization loop...")
    print("-----------------------------------")

    X, y, x_best, y_best = bayesian_loop(
        X0=X0,
        y0=y0,
        objective_fn=objective_fn,
        bounds=bounds,
        constraints=constraints,
        max_iter=bo_config["max_iter"],
    )

    # Report
    print("\n===================================")
    print("BO OPTIMIZATION COMPLETE")
    print("===================================")
    print(f"\nBest score = {y_best:.5f}")
    best_design = design_from_x(x_best)
    print(f"  max_camber:         {best_design.max_camber:.4f}")
    print(f"  max_camber_loc:     {best_design.max_camber_loc:.4f}")
    print(f"  max_thickness:      {best_design.max_thickness:.4f}")
    print(f"  max_thickness_loc:  {best_design.max_thickness_loc:.4f}")

    return X, y, x_best, y_best