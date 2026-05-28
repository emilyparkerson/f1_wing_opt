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
    #if abs(aero.cl) > 1.4:
    #    return False

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

    # -------------------------------------------------
    # HISTORY STORAGE
    # -------------------------------------------------

    score_history = []
    cl_history = []
    cd_history = []
    coords_history = []
    design_history = []

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

        score = scoring_fn(aero_result, design)

        # save histories
        score_history.append(score)

        cl_history.append(aero_result.cl)

        cd_history.append(aero_result.cd)

        coords_history.append(aero_result.coords)

        design_history.append([
            design.max_camber,
            design.max_camber_loc,
            design.max_thickness,
            design.max_thickness_loc,
        ])

        return score

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

    # -------------------------------------------------
    # GET FINAL AIRFOILS
    # -------------------------------------------------

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

    # -------------------------------------------------
    # SAVE SEED AND OPTIMIZED AIRFOIL COORDINATES
    # -------------------------------------------------

    if is_valid_result(seed_result):

        np.savetxt(
            f"seed_airfoil_{config['phase_name']}.dat",
            seed_result.coords,
            header="x y",
            comments="",
            fmt="%.8f"
        )

        print(
            f"Saved seed coordinates to "
            f"seed_airfoil_{config['phase_name']}.dat"
        )

    if is_valid_result(best_result):

        np.savetxt(
            f"optimized_airfoil_{config['phase_name']}.dat",
            best_result.coords,
            header="x y",
            comments="",
            fmt="%.8f"
        )

        print(
            f"Saved optimized coordinates to "
            f"optimized_airfoil_{config['phase_name']}.dat"
        )

    # -------------------------------------------------
    # SCORE HISTORY
    # -------------------------------------------------

    plt.figure(figsize=(8,4))

    plt.plot(
        score_history,
        marker='o',
        linewidth=2
    )

    plt.xlabel("Valid BO Iteration")
    plt.ylabel("Score")

    plt.title("Bayesian Optimization Score History")

    plt.grid(True)

    plt.show()

    # -------------------------------------------------
    # BEST SCORE SO FAR
    # -------------------------------------------------

    best_so_far = np.maximum.accumulate(score_history)

    plt.figure(figsize=(8,4))

    plt.plot(
        best_so_far,
        marker='o',
        linewidth=2
    )

    plt.xlabel("Valid BO Iteration")
    plt.ylabel("Best Score So Far")

    plt.title("Bayesian Optimization Convergence")

    plt.grid(True)

    plt.show()

    # -------------------------------------------------
    # CL HISTORY
    # -------------------------------------------------

    plt.figure(figsize=(8,4))

    plt.plot(
        cl_history,
        marker='o',
        linewidth=2
    )

    plt.xlabel("Valid BO Iteration")
    plt.ylabel("Cl")

    plt.title("Bayesian Optimization Cl History")

    plt.grid(True)

    plt.show()

    # -------------------------------------------------
    # CD HISTORY
    # -------------------------------------------------

    plt.figure(figsize=(8,4))

    plt.plot(
        cd_history,
        marker='o',
        linewidth=2
    )

    plt.xlabel("Valid BO Iteration")
    plt.ylabel("Cd")

    plt.title("Bayesian Optimization Cd History")

    plt.grid(True)

    plt.show()

    # -------------------------------------------------
    # CD VS CL
    # -------------------------------------------------

    plt.figure(figsize=(6,6))

    plt.scatter(
        cd_history,
        cl_history,
        s=80
    )

    plt.xlabel("Cd")
    plt.ylabel("Cl")

    plt.title("Design Space Exploration")

    plt.grid(True)

    plt.show()

    # -------------------------------------------------
    # AIRFOIL EVOLUTION
    # -------------------------------------------------

    if is_valid_result(best_result) and is_valid_result(seed_result):

        plt.figure(figsize=(12,5))

        # plot all valid BO airfoils
        for coords in coords_history:

            plt.plot(
                coords[:,0],
                coords[:,1],
                color='gray',
                alpha=0.25,
                linewidth=1
            )

        # seed airfoil
        plt.plot(
            seed_result.coords[:,0],
            seed_result.coords[:,1],
            color='blue',
            linewidth=3,
            label='Seed Airfoil'
        )

        # optimized airfoil
        plt.plot(
            best_result.coords[:,0],
            best_result.coords[:,1],
            color='red',
            linewidth=3,
            label='Optimized Airfoil'
        )

        plt.axis("equal")

        plt.xlabel("x/c")
        plt.ylabel("y/c")

        plt.title("Airfoil Geometry Evolution")

        plt.grid(True)

        plt.legend()

        plt.show()

    else:

        print("Could not plot airfoils because one did not converge.")

    # -------------------------------------------------
    # SAVE HISTORY DATA
    # -------------------------------------------------

    best_so_far = np.maximum.accumulate(score_history)

    history_data = np.column_stack([

        np.arange(1, len(score_history)+1),

        score_history,

        best_so_far,

        cl_history,

        cd_history,

        np.array(design_history)
    ])

    np.savetxt(

        f"bo_history_{config['phase_name']}.csv",

        history_data,

        delimiter=",",

        header=(
            "iteration,"
            "score,"
            "best_score_so_far,"
            "Cl,"
            "Cd,"
            "max_camber,"
            "max_camber_loc,"
            "max_thickness,"
            "max_thickness_loc"
        ),

        comments="",

        fmt="%.6f"
    )

    print(
        f"\nSaved BO history to "
        f"bo_history_{config['phase_name']}.csv"
    )

    return X, y, x_best, y_best