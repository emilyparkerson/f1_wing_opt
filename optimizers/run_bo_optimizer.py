import numpy as np
import matplotlib.pyplot as plt

from setup.aero_interface import run_mses
from setup.design_vars import designParameters

from bayesian_optimization.bayesian_optimizer import bayesian_loop


def design_from_x(x):
    """Convert BO vector to design parameters."""
    return designParameters(
        max_camber=x[0],
        max_camber_loc=x[1],
        max_thickness=x[2],
        max_thickness_loc=x[3],
    )


def x_from_design(design):
    """Convert design parameters to BO vector."""
    return np.array([
        design.max_camber,
        design.max_camber_loc,
        design.max_thickness,
        design.max_thickness_loc,
    ])


# -------------------------------------------------
# FRONT THICKNESS CHECK
# -------------------------------------------------

def thickness_at_x(coords, x_check=0.05):

    le_idx = np.argmin(coords[:, 0])

    upper = coords[:le_idx + 1]
    lower = coords[le_idx:]

    upper = upper[np.argsort(upper[:, 0])]
    lower = lower[np.argsort(lower[:, 0])]

    yu = np.interp(x_check, upper[:, 0], upper[:, 1])
    yl = np.interp(x_check, lower[:, 0], lower[:, 1])

    return yu - yl


# -------------------------------------------------
# VALIDITY CHECK
# -------------------------------------------------

def is_valid_result(aero):

    if aero is None:
        return False

    if aero.cl is None or aero.cd is None:
        return False

    if aero.coords is None:
        return False

    if aero.cd <= 0:
        return False

    # reject absurd lift values
    if abs(aero.cl) > 1.4:
        return False

    # enforce minimum front thickness
    front_thickness = thickness_at_x(
        aero.coords,
        x_check=0.05
    )

    if front_thickness < 0.055:
        return False

    return True


# -------------------------------------------------
# GENERATE TRAINING DATA
# -------------------------------------------------

def generate_training_data(seed_design, bounds_arr, training_n, scoring_fn,
                           alpha, mach, reynolds, seed_airfoil, constraints):

    X_list = []
    y_list = []

    rng = np.random.default_rng(42)

    # Always try seed first
    candidates = [x_from_design(seed_design)]

    while len(candidates) < 200:

        x = rng.uniform(
            bounds_arr[:, 0],
            bounds_arr[:, 1]
        )

        if constraints(x):
            candidates.append(x)

    print("Evaluating training airfoils...")

    for x in candidates:

        if len(X_list) >= training_n:
            break

        design = design_from_x(x)

        aero = run_mses(
            design=design,
            name="init",
            alpha=alpha,
            mach=mach,
            reynolds=reynolds,
            seed_airfoil=seed_airfoil,
        )

        if not is_valid_result(aero):

            print("Skipping failed airfoil")

            continue

        score = scoring_fn(aero, design)

        X_list.append(x)
        y_list.append(score)

        print("Appended valid training airfoil")

    if len(X_list) < training_n:

        raise RuntimeError(
            "Could not get enough valid training airfoils."
        )

    print(len(X_list), "valid training airfoils generated")

    return np.array(X_list), np.array(y_list)


# -------------------------------------------------
# MAIN BO DRIVER
# -------------------------------------------------

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

    bounds_obj = config["bounds"]

    bounds = [
        bounds_obj.max_camber,
        bounds_obj.max_camber_loc,
        bounds_obj.max_thickness,
        bounds_obj.max_thickness_loc,
    ]

    bounds_arr = np.array(bounds, dtype=float)

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

    # -------------------------------------------------
    # OBJECTIVE FUNCTION
    # -------------------------------------------------

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

        if not is_valid_result(aero_result):
            return None

        return scoring_fn(aero_result, design)

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

    print("\n===================================")
    print("BO OPTIMIZATION COMPLETE")
    print("===================================")

    print(f"\nBest score = {y_best:.5f}")

    best_design = design_from_x(x_best)

    print(f"  max_camber:         {best_design.max_camber:.4f}")
    print(f"  max_camber_loc:     {best_design.max_camber_loc:.4f}")
    print(f"  max_thickness:      {best_design.max_thickness:.4f}")
    print(f"  max_thickness_loc:  {best_design.max_thickness_loc:.4f}")

    # -----------------------------------
    # PLOT BEST AIRFOIL VS SEED
    # -----------------------------------

    best_result = run_mses(
        design=best_design,
        name="best_airfoil",
        alpha=alpha,
        mach=mach,
        reynolds=reynolds,
        seed_airfoil=seed_airfoil,
    )

    seed_result = run_mses(
        design=seed_design,
        name="seed_airfoil",
        alpha=alpha,
        mach=mach,
        reynolds=reynolds,
        seed_airfoil=seed_airfoil,
    )

    if is_valid_result(best_result) and is_valid_result(seed_result):

        plt.figure(figsize=(10,4))

        plt.plot(
            seed_result.coords[:,0],
            seed_result.coords[:,1],
            label="Seed Airfoil",
            linewidth=2
        )

        plt.plot(
            best_result.coords[:,0],
            best_result.coords[:,1],
            label="Optimized Airfoil",
            linewidth=2
        )

        plt.axis("equal")
        plt.grid(True)
        plt.legend()

        plt.xlabel("x/c")
        plt.ylabel("y/c")

        plt.title("Seed vs Optimized Airfoil")

        plt.show()

    else:
        print("Could not plot airfoils because one did not converge.")

    return X, y, x_best, y_best