import numpy as np
import matplotlib.pyplot as plt

from aero_interface import run_mses
from scoring import scoring_p1

from design_vars import (
    designParameters,
    airfoilBounds
)

from optimizer import perturb_design

from log import (
    initialize_log,
    log_iteration
)

from plotting import (
    plot_score_history,
    plot_aero_history
)


# -------------------------------------------------
# SETTINGS
# -------------------------------------------------

N_ITERATIONS = 5

STEP_SIZE = {
    "max_camber": 0.003,
    "max_camber_loc": 0.02,
    "max_thickness": 0.005,
    "max_thickness_loc": 0.02
}

BOUNDS = airfoilBounds(
    max_camber=(0.00, 0.15),
    max_camber_loc=(0.30, 0.70),
    max_thickness=(0.06, 0.25),
    max_thickness_loc=(0.15, 0.45)
)


# -------------------------------------------------
# MAIN
# -------------------------------------------------

def main():

    np.random.seed(1)

    log_file = "optimization_history.csv"

    initialize_log(log_file)

    # -------------------------------------------------
    # SEED AIRFOIL
    # -------------------------------------------------

    current_design = designParameters(
        max_camber=0.04358,
        max_camber_loc=0.635,
        max_thickness=0.17569,
        max_thickness_loc=0.2434
    )

    # current_design = designParameters(
    #      max_camber=0.0,
    #      max_camber_loc=0.5,
    #      max_thickness=0.08,
    #      max_thickness_loc=0.3
    # )

    # current_design = designParameters(
    #        max_camber=0.02,
    #        max_camber_loc=0.517,
    #        max_thickness=0.14,
    #        max_thickness_loc=0.413
    #   )

    #current_design = designParameters(
    #      max_camber=0.038,
    #      max_camber_loc=0.301,
    #      max_thickness=0.062,
    #      max_thickness_loc=0.3
     #)

    # current_design = designParameters(
    #      max_camber=0.02,
    #      max_camber_loc=0.4,
    #      max_thickness=0.12,
    #      max_thickness_loc=0.3
    # )

    # current_design = designParameters(
    #       max_camber=0.027,
    #       max_camber_loc=0.517,
    #       max_thickness=0.12,
    #       max_thickness_loc=0.413
    # )

    # current_design = designParameters(
    #       max_camber=0.081,
    #       max_camber_loc=0.49,
    #       max_thickness=0.121,
    #       max_thickness_loc=0.198
    # )

    # -------------------------------------------------
    # INITIAL EVALUATION
    # -------------------------------------------------

    print("\n===================================")
    print("INITIAL SEED AIRFOIL")
    print("===================================")

    aero_result = run_mses(
        design=current_design,
        name="seed_airfoil",
        alpha=0.0,
        mach=0.2,
        reynolds=1e6,
        plot_geometry=True,
        plot_comparison=True
    )

    score = scoring_p1(aero_result, current_design)

    print(f"\nInitial Score = {score:.4f}")

    log_iteration(
        log_file,
        0,
        aero_result.cl,
        aero_result.cd,
        score
    )

    best_design = current_design
    best_result = aero_result
    best_score = score

    first_coords = aero_result.coords

    # -------------------------------------------------
    # OPTIMIZATION LOOP
    # -------------------------------------------------

    for iteration in range(1, N_ITERATIONS + 1):

        print("\n===================================")
        print(f"Iteration {iteration}")
        print("===================================")

        # ---------------------------------------------
        # CREATE NEW DESIGN
        # ---------------------------------------------

        trial_design = perturb_design(
            best_design,
            BOUNDS,
            STEP_SIZE
        )

        # ---------------------------------------------
        # RUN MSES
        # ---------------------------------------------

        trial_result = run_mses(
            design=trial_design,
            name=f"candidate_{iteration}",
            alpha=0.0,
            mach=0.2,
            reynolds=1e6,
            plot_geometry=False,
            plot_comparison=False
        )

        # ---------------------------------------------
        # SCORE
        # ---------------------------------------------

        trial_score = scoring_p1(trial_result, trial_design)

        print(f"\nScore = {trial_score:.4f}")

        # ---------------------------------------------
        # LOG
        # ---------------------------------------------

        log_iteration(
            log_file,
            iteration,
            trial_result.cl,
            trial_result.cd,
            trial_score
        )

        # ---------------------------------------------
        # ACCEPT IF BETTER
        # ---------------------------------------------

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


if __name__ == "__main__":
    main()