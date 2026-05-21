import numpy as np

from setup.aero_interface import run_mses
from setup.design_vars import designParameters
from setup.geometry import load_airfoil_dat
from setup.scoring import scoring_p1

from log import initialize_log, log_iteration
from plotting import plot_seed_vs_optimized, plot_aero_history, plot_score_history

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
                           alpha, mach, reynolds, seed_airfoil, constraints, ref_vals):
    """
    Build initial training data: the seed design + (training_n - 1) random points.
    """

    # Seed airfoil + initializing the vectors of scores and designs
    X_list = [x_from_design(seed_design)]
    design = design_from_x(X_list[0])
    aero = run_mses(
            design=design,
            name="init",
            alpha=alpha,
            mach=mach,
            reynolds=reynolds,
            seed_airfoil=seed_airfoil,
        )
    y_list = [scoring_fn(aero, ref_vals)]
    print(y_list)

    # Random perturbations of the seed
    rng = np.random.default_rng(42)
    while len(X_list) < training_n:
        x = rng.uniform(bounds_arr[:, 0], bounds_arr[:, 1])
        if constraints(x): 
            design = design_from_x(x)
            aero = run_mses(
                design=design,
                name="init",
                alpha=alpha,
                mach=mach,
                reynolds=reynolds,
                seed_airfoil=seed_airfoil,
            )
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
    seed_airfoil = config["seed_airfoil"]

    alpha = config["alpha"]
    mach = config["mach"]
    reynolds = config["reynolds"]
    constraints = config["constraints"]
    training_n = config["training_n"]
    ref_vals = config["ref_vals"]

    plotting = config["plotting"]
    logging = config["logging"]
    phase_name = config["phase_name"]

    # Setup logging
    if logging:
        log_file = f"bo_log_{phase_name.replace(' ', '_')}.csv"
        initialize_log(log_file)
        
        # Mutable counter so we can update from inside the closure
        iter_counter = {"n": 0}
        
        # Track the best result for plotting
        best_tracker = {"coords": None, "score": float("-inf")}

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
        ref_vals=ref_vals
    )

    # Run MSES on seed at the start
    print("Obtaining seed's coordinates before beginning optimization...")
    seed_aero = run_mses(
        design=seed_design,
        name="seed_baseline",
        alpha=alpha, mach=mach, reynolds=reynolds,
        seed_airfoil=seed_airfoil,
    )
    seed_coords = seed_aero.coords
    
    # Store the best coords as BO progresses
    best_tracker = {"coords": None, "score": float("-inf")}

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
        score = scoring_fn(aero_result, ref_vals)

        # Track best result for plotting later
        if score > best_tracker["score"]:
            best_tracker["score"] = score
            best_tracker["coords"] = aero_result.coords

        # Log this evaluation
        log_iteration(log_file, iter_counter["n"], 
            aero_result.cl,aero_result.cd,score,)
        iter_counter["n"] += 1

        return score

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

    # Plot
    if config["plotting"]:
        # Load seed coords from the .txt file
        seed_x, seed_y = load_airfoil_dat(str(seed_airfoil))
        seed_coords = np.column_stack([seed_x, seed_y])
        
        # Plot seed vs optimized
        plot_seed_vs_optimized(
            seed_coords=seed_coords,
            optimized_coords=best_tracker["coords"],
            phase_name=phase_name,
        )
    if config["logging"]:
        # Plot the score/aero history if logging is enabled
        plot_score_history(log_file, phase_name=phase_name)
        plot_aero_history(log_file, phase_name=phase_name)

    return X, y, x_best, y_best