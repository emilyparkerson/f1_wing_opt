import csv
import numpy as np

from setup.aero_interface import run_mses, run_mses_elements
from setup.design_vars import designParameters
from setup.geometry import (
    load_airfoil_dat,
    get_seed as _gs,
    new_airfoil as _na,
    get_coords as _gc,
)

from log import initialize_log, log_iteration
from plotting import plot_seed_vs_optimized, plot_aero_history, plot_score_history

from bayesian_optimization.bayesian_optimizer import bayesian_loop


class ConvergedTargetReached(Exception):
    """Signals BO loop to stop once target converged-eval count is hit."""


class MSESConfig:
    """Bundle an MSES-runner fn with the kwargs that stay constant across a run.
    Per-call kwargs (design, name, plot flags) are merged in at call time."""
    def __init__(self, fn, **fixed_kwargs):
        self.fn = fn
        self.fixed_kwargs = fixed_kwargs

    def __call__(self, **call_kwargs):
        return self.fn(**{**self.fixed_kwargs, **call_kwargs})


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


def save_best_so_far(tracker, phase_name):
    """Overwrite best-so-far .dat + .csv. Called whenever a new best is found."""
    name = phase_name.replace(" ", "_")
    np.savetxt(f"best_so_far_{name}.dat", tracker["coords"])
    with open(f"best_so_far_{name}.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["max_camber", "max_camber_loc", "max_thickness",
                    "max_thickness_loc", "cl", "cd", "score"])
        d = tracker["design"]
        w.writerow([d.max_camber, d.max_camber_loc, d.max_thickness,
                    d.max_thickness_loc, tracker["cl"], tracker["cd"],
                    tracker["score"]])


def generate_training_data(seed_design, bounds_arr, training_n, scoring_fn,
                           mses_config, constraints, ref_vals):
    """
    Build initial training data: the seed design + (training_n - 1) random points.
    """
    # Seed airfoil + initializing the vectors of scores and designs
    X_list = [x_from_design(seed_design)]
    design = design_from_x(X_list[0])
    aero = mses_config(design=design, name="init")
    y_list = [scoring_fn(aero, ref_vals)]
    print("Added seed airfoil to training set")

    # Random perturbations of the seed
    rng = np.random.default_rng(42)
    while len(X_list) < training_n:
        x = rng.uniform(bounds_arr[:, 0], bounds_arr[:, 1])
        if constraints(x):
            design = design_from_x(x)
            aero = mses_config(design=design, name="init")
            score = scoring_fn(aero, ref_vals)
            if score != -1:
                X_list.append(x)
                y_list.append(score)
                print(f"Appended training airfoil {len(X_list)}")
    print(len(X_list), "training airfoils generated")
    print(len(y_list), "training scores generated")

    return np.array(X_list), np.array(y_list)


def run_bo_optimizer(config):
    bo_config = config["bo"]
    scoring_fn = config["scoring_function"]
    seed_design = config["seed_design"]
    seed_airfoil = config.get("seed_airfoil", None)

    alpha = config["alpha"]
    mach = config["mach"]
    reynolds = config["reynolds"]
    constraints = config["constraints"]
    training_n = config["training_n"]
    ref_vals = config["ref_vals"]

    logging = config["logging"]
    phase_name = config["phase_name"]

    # Build the MSES runner: if the config supplies an "elements" list we
    # run the multi-element path; otherwise fall back to single element.
    if "elements" in config:
        mses_config = MSESConfig(
            fn=run_mses_elements,
            elements=config["elements"],
            alpha=alpha, mach=mach, reynolds=reynolds,
            plot_geometry=config.get("plot_geometry", False),
            target_cl=config.get("target_cl"),
        )
    else:
        mses_config = MSESConfig(
            fn=run_mses,
            alpha=alpha, mach=mach, reynolds=reynolds,
            seed_airfoil=seed_airfoil,
            plot_geometry=config.get("plot_geometry", False),
            target_cl=config.get("target_cl"),
        )

    # Setup logging
    if logging:
        log_file = f"bo_log_{phase_name.replace(' ', '_')}.csv"
        initialize_log(log_file)
        iter_counter = {"n": 0}

    # Track the best result for plotting + saving
    best_tracker = {"coords": None, "score": float("-inf"),
                    "design": None, "cl": None, "cd": None}

    # Track how many MSES calls converged (used for early stop)
    converged_counter = {"n": 0}
    target_converged = bo_config.get("target_converged", bo_config["max_iter"])

    # Load bounds from the config's airfoilBounds dataclass.
    b = config["bounds"]
    bounds_arr = np.array([
        list(b.max_camber),
        list(b.max_camber_loc),
        list(b.max_thickness),
        list(b.max_thickness_loc),
    ])
    bounds = [tuple(row) for row in bounds_arr]

    # Build initial training data from the seed
    print("-----------------------------------")
    print("Building initial training data...")
    print("-----------------------------------")

    X0, y0 = generate_training_data(
        seed_design=seed_design,
        bounds_arr=bounds_arr,
        training_n=training_n,
        scoring_fn=scoring_fn,
        mses_config=mses_config,
        constraints=constraints,
        ref_vals=ref_vals,
    )

    # Run MSES on seed at the start (baseline)
    print("Obtaining seed's coordinates before beginning optimization...")
    seed_aero = mses_config(design=seed_design, name="seed_baseline")
    seed_coords = seed_aero.coords

    # Objective for BO to call each iteration
    def objective_fn(x):
        design = design_from_x(x)
        aero_result = mses_config(
            design=design,
            name="bo_candidate",
        )
        score = scoring_fn(aero_result, ref_vals)
        converged = aero_result.cl is not None

        # Track best over CONVERGED runs only; save snapshot when a new best
        # is found so we always have the current best on disk.
        if converged and score > best_tracker["score"]:
            best_tracker["score"] = score
            best_tracker["coords"] = aero_result.coords
            best_tracker["design"] = design
            best_tracker["cl"] = aero_result.cl
            best_tracker["cd"] = aero_result.cd
            save_best_so_far(best_tracker, phase_name)

        # Log every call (converged or not), with design vars + converged flag
        log_iteration(log_file, iter_counter["n"],
                      aero_result.cl, aero_result.cd, score,
                      design.max_camber, design.max_camber_loc,
                      design.max_thickness, design.max_thickness_loc,
                      converged)
        iter_counter["n"] += 1

        if converged:
            converged_counter["n"] += 1
            print(f"[converged {converged_counter['n']}/{target_converged}]")
            if converged_counter["n"] >= target_converged:
                raise ConvergedTargetReached()

        return score

    # Run BO
    print("-----------------------------------")
    print(f"Running the Bayesian Optimization loop "
          f"(target {target_converged} converged, hard cap {bo_config['max_iter']})...")
    print("-----------------------------------")

    try:
        X, y, x_best, y_best = bayesian_loop(
            X0=X0,
            y0=y0,
            objective_fn=objective_fn,
            bounds=bounds,
            constraints=constraints,
            max_iter=bo_config["max_iter"],
        )
    except ConvergedTargetReached:
        print(f"\nReached {target_converged} converged evals -- stopping BO.")
        # Pull best from tracker since bayesian_loop didn't return cleanly
        x_best = x_from_design(best_tracker["design"]) \
            if best_tracker["design"] is not None else None
        y_best = best_tracker["score"]
        X, y = None, None

    # Report
    print("\n===================================")
    print("BO OPTIMIZATION COMPLETE")
    print("===================================")
    print(f"Total MSES calls:     {iter_counter['n']}")
    print(f"Converged evaluations: {converged_counter['n']}")
    print(f"\nBest score = {y_best:.5f}")
    if x_best is not None:
        best_design = design_from_x(x_best)
        print(f"  max_camber:         {best_design.max_camber:.4f}")
        print(f"  max_camber_loc:     {best_design.max_camber_loc:.4f}")
        print(f"  max_thickness:      {best_design.max_thickness:.4f}")
        print(f"  max_thickness_loc:  {best_design.max_thickness_loc:.4f}")

    # Save the winning geometry so a later phase can load it as a fixed element.
    winner_path = config.get("winner_output", None)
    if winner_path is not None and best_tracker["coords"] is not None:
        np.savetxt(str(winner_path), best_tracker["coords"])
        print(f"Saved winning geometry to {winner_path}")

    # Plot seed vs optimized
    if config["plotting"] and best_tracker["coords"] is not None:
        # Seed coords go through the SAME pipeline as the optimized airfoil
        # (de-rotate, morph at seed_design, re-rotate to 0). With an
        # "elements" config the seed lives in the morph element spec.
        if "elements" in config:
            morph_spec = next(e for e in config["elements"] if e["role"] == "morph")
            plot_seed_path = str(morph_spec["seed_airfoil"])
        else:
            plot_seed_path = str(seed_airfoil)

        sx, sy = load_airfoil_dat(plot_seed_path)
        xc, _, t, _ = _gs(sx, sy)
        xu, yu, xl, yl, _, _, _ = _na(
            thickness_seed=t, x_common=xc,
            designParameters=seed_design, n_points=160,
            smoothing_fac=None, aoa=0.0,
        )
        seed_coords_plot = _gc(xu, xl, yu, yl, phase=1)

        plot_seed_vs_optimized(
            seed_coords=seed_coords_plot,
            optimized_coords=best_tracker["coords"],
            phase_name=phase_name,
        )

    if config["logging"]:
        # Plot the score/aero history if logging is enabled
        plot_score_history(log_file, phase_name=phase_name)
        plot_aero_history(log_file, phase_name=phase_name)

    return X, y, x_best, y_best