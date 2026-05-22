import numpy as np

from setup.aero_interface import run_mses
from setup.design_vars import designParameters
from setup.geometry import load_airfoil_dat

from log import initialize_log, log_iteration
from plotting import (
    plot_seed_vs_optimized,
    plot_aero_history,
    plot_score_history,
)

from bayesian_optimization.bayesian_optimizer import bayesian_loop


INVALID_SCORE = -9999.0


def design_from_x(x):
    return designParameters(
        max_camber=x[0],
        max_camber_loc=x[1],
        max_thickness=x[2],
        max_thickness_loc=x[3],
    )


def x_from_design(design):
    return np.array([
        design.max_camber,
        design.max_camber_loc,
        design.max_thickness,
        design.max_thickness_loc,
    ])


def is_valid_score(score):
    if score is None:
        return False

    if not np.isfinite(score):
        return False

    if score <= INVALID_SCORE:
        return False

    return True


def evaluate_design(
    design,
    scoring_fn,
    ref_vals,
    alpha,
    mach,
    reynolds,
    seed_airfoil,
    name="candidate",
):
    try:
        aero = run_mses(
            design=design,
            name=name,
            alpha=alpha,
            mach=mach,
            reynolds=reynolds,
            seed_airfoil=seed_airfoil,
            plot_geometry=False,
            plot_comparison=False,
        )

    except Exception as e:
        print(f"{name}: geometry/XFOIL failed")
        print(e)
        return None, INVALID_SCORE

    if aero is None:
        return None, INVALID_SCORE

    if aero.cl is None or aero.cd is None:
        print(f"{name}: invalid aero result")
        return aero, INVALID_SCORE

    if aero.cd <= 0:
        print(f"{name}: invalid Cd")
        return aero, INVALID_SCORE

    try:
        score = scoring_fn(aero, ref_vals)

    except Exception as e:
        print(f"{name}: scoring failed")
        print(e)
        return aero, INVALID_SCORE

    if not is_valid_score(score):
        print(f"{name}: invalid score")
        return aero, INVALID_SCORE

    print(
        f"{name}: "
        f"Cl={aero.cl:.5f}, "
        f"Cd={aero.cd:.5f}, "
        f"Score={score:.5f}"
    )

    return aero, score


def generate_training_data(
    seed_design,
    bounds_arr,
    training_n,
    scoring_fn,
    ref_vals,
    alpha,
    mach,
    reynolds,
    seed_airfoil,
    constraints,
):
    X_list = []
    y_list = []

    rng = np.random.default_rng(42)

    print("Evaluating seed design...")

    aero, score = evaluate_design(
        design=seed_design,
        scoring_fn=scoring_fn,
        ref_vals=ref_vals,
        alpha=alpha,
        mach=mach,
        reynolds=reynolds,
        seed_airfoil=seed_airfoil,
        name="seed",
    )

    if is_valid_score(score):
        X_list.append(x_from_design(seed_design))
        y_list.append(score)

    attempts = 0
    max_attempts = training_n * 100

    while len(X_list) < training_n and attempts < max_attempts:
        attempts += 1

        x = rng.uniform(bounds_arr[:, 0], bounds_arr[:, 1])

        if not constraints(x):
            continue

        design = design_from_x(x)

        aero, score = evaluate_design(
            design=design,
            scoring_fn=scoring_fn,
            ref_vals=ref_vals,
            alpha=alpha,
            mach=mach,
            reynolds=reynolds,
            seed_airfoil=seed_airfoil,
            name=f"training_{len(X_list)}",
        )

        if not is_valid_score(score):
            continue

        X_list.append(x)
        y_list.append(score)

        print(f"Accepted training point {len(X_list)}")

    if len(X_list) == 0:
        raise RuntimeError("No valid training points generated.")

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

    ref_vals = config["ref_vals"]

    phase_name = config["phase_name"]

    logging = config["logging"]
    plotting = config["plotting"]

    bounds_arr = np.genfromtxt(
        bo_config["bounds_csv"],
        delimiter=",",
        usecols=(0, 1),
    )

    bounds = [tuple(b) for b in bounds_arr]

    if logging:
        log_file = f"bo_log_{phase_name.replace(' ', '_')}.csv"
        initialize_log(log_file)

    else:
        log_file = None

    best_tracker = {
        "score": -1e9,
        "coords": None,
        "aero": None,
    }

    print("-----------------------------------")
    print("Building initial training data...")
    print("-----------------------------------")

    X0, y0 = generate_training_data(
        seed_design=seed_design,
        bounds_arr=bounds_arr,
        training_n=training_n,
        scoring_fn=scoring_fn,
        ref_vals=ref_vals,
        alpha=alpha,
        mach=mach,
        reynolds=reynolds,
        seed_airfoil=seed_airfoil,
        constraints=constraints,
    )

    print("-----------------------------------")
    print("Running Bayesian Optimization...")
    print("-----------------------------------")

    iteration_counter = {"n": 0}

    def objective_fn(x):
        design = design_from_x(x)

        aero, score = evaluate_design(
            design=design,
            scoring_fn=scoring_fn,
            ref_vals=ref_vals,
            alpha=alpha,
            mach=mach,
            reynolds=reynolds,
            seed_airfoil=seed_airfoil,
            name=f"bo_iter_{iteration_counter['n']}",
        )

        if not is_valid_score(score):
            return INVALID_SCORE

        if score > best_tracker["score"]:
            best_tracker["score"] = score
            best_tracker["coords"] = aero.coords
            best_tracker["aero"] = aero

        if logging:
            log_iteration(
                log_file,
                iteration_counter["n"],
                aero.cl,
                aero.cd,
                score,
            )

        iteration_counter["n"] += 1

        return score

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

    print(f"Best score = {y_best:.5f}")

    best_design = design_from_x(x_best)

    print(f"max_camber:         {best_design.max_camber:.4f}")
    print(f"max_camber_loc:     {best_design.max_camber_loc:.4f}")
    print(f"max_thickness:      {best_design.max_thickness:.4f}")
    print(f"max_thickness_loc:  {best_design.max_thickness_loc:.4f}")

    if plotting and best_tracker["coords"] is not None:
        seed_x, seed_y = load_airfoil_dat(str(seed_airfoil))
        seed_coords = np.column_stack([seed_x, seed_y])

        plot_seed_vs_optimized(
            seed_coords=seed_coords,
            optimized_coords=best_tracker["coords"],
            phase_name=phase_name,
        )

    if logging:
        plot_score_history(log_file, phase_name=phase_name)
        plot_aero_history(log_file, phase_name=phase_name)

    return X, y, x_best, y_best