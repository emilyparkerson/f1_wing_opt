import matplotlib.pyplot as plt

from setup.aero_interface import run_mses

from optimizers.optimizer import perturb_design

from log import (
    initialize_log,
    log_iteration
)

from plotting import (
    plot_score_history,
    plot_aero_history
)


def run_random_optimizer(config):

    scoring_function = config["scoring_function"]

    bounds = config["bounds"]

    seed_design = config["seed_design"]

    random_config = config["random_search"]

    step_size = random_config["step_size"]

    n_iterations = random_config["n_iterations"]

    alpha = config["alpha"]
    mach = config["mach"]
    reynolds = config["reynolds"]

    phase_name = config["phase_name"]

    log_file = f"{phase_name}_optimization_history.csv"

    initialize_log(log_file)

    # -------------------------------------------------
    # INITIAL EVALUATION
    # -------------------------------------------------

    print("\n===================================")
    print("INITIAL SEED AIRFOIL")
    print("===================================")

    aero_result = run_mses(
        design=seed_design,
        name="seed_airfoil",
        alpha=alpha,
        mach=mach,
        reynolds=reynolds,
        plot_geometry=True,
        plot_comparison=True
    )

    score = scoring_function(
        aero_result,
        seed_design
    )

    print(f"\nInitial Score = {score:.4f}")

    log_iteration(
        log_file,
        0,
        aero_result.cl,
        aero_result.cd,
        score
    )

    best_design = seed_design
    best_result = aero_result
    best_score = score

    first_coords = aero_result.coords

    # -------------------------------------------------
    # OPTIMIZATION LOOP
    # -------------------------------------------------

    for iteration in range(1, n_iterations + 1):

        print("\n===================================")
        print(f"Iteration {iteration}")
        print("===================================")

        trial_design = perturb_design(
            best_design,
            bounds,
            step_size
        )

        trial_result = run_mses(
            design=trial_design,
            name=f"candidate_{iteration}",
            alpha=alpha,
            mach=mach,
            reynolds=reynolds,
            plot_geometry=False,
            plot_comparison=False
        )

        trial_score = scoring_function(
            trial_result,
            trial_design
        )

        print(f"\nScore = {trial_score:.4f}")

        log_iteration(
            log_file,
            iteration,
            trial_result.cl,
            trial_result.cd,
            trial_score
        )

        if trial_score > best_score:

            print("\nNEW BEST DESIGN FOUND")

            best_design = trial_design
            best_result = trial_result
            best_score = trial_score

    # -------------------------------------------------
    # FINAL RESULTS
    # -------------------------------------------------

    print("\n===================================")
    print("OPTIMIZATION COMPLETE")
    print("===================================")

    print("\nBest Design:")

    print(f"Max Camber:          {best_design.max_camber}")
    print(f"Max Camber Location: {best_design.max_camber_loc}")
    print(f"Max Thickness:       {best_design.max_thickness}")
    print(f"Max Thickness Loc:   {best_design.max_thickness_loc}")

    print(f"\nBest Cl = {best_result.cl:.5f}")
    print(f"Best Cd = {best_result.cd:.5f}")
    print(f"Best Score = {best_score:.5f}")

    # -------------------------------------------------
    # PLOTS
    # -------------------------------------------------

    plot_score_history(log_file)

    plot_aero_history(log_file)

    if first_coords is not None and best_result.coords is not None:

        plt.figure(figsize=(10, 4))

        plt.plot(
            first_coords[:, 0],
            first_coords[:, 1],
            linewidth=2,
            label="Initial Airfoil"
        )

        plt.plot(
            best_result.coords[:, 0],
            best_result.coords[:, 1],
            linewidth=2,
            label="Best Airfoil"
        )

        plt.axis("equal")

        plt.xlabel("x/c")
        plt.ylabel("y/c")

        plt.title("Initial vs Best Airfoil")

        plt.grid(True)
        plt.legend()

        plt.show()