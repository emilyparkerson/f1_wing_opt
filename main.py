from aero_interface import run_mses
from scoring import scoring_p1
from design_vars import designParameters

from log import (
    initialize_log,
    log_iteration
)

from plotting import (
    plot_score_history,
    plot_aero_history
)


def main():

    # csv file for saving optimization history
    log_file = "optimization_history.csv"

    initialize_log(log_file)

    # temporary loop for testing
    n_iterations = 5

    first_coords = None
    last_coords = None

    for i in range(n_iterations):

        print(f"\nIteration {i}")

        # temporary test design
        design = designParameters(
            max_camber=0.02,
            max_camber_loc=0.4,
            max_thickness=0.1,
            max_thickness_loc=0.3
        )
        #design = designParameters(
        #    max_camber=0.0436,
        #    max_camber_loc=0.635,
        #    max_thickness=0.1757,
        #    max_thickness_loc=0.2434
        #)

        # run aerodynamic analysis
        aero_result = run_mses(
            design=design,
            name=f"candidate_airfoil_{i}",
            alpha=0.0
        )

        # save first airfoil
        if i == 0:
            first_coords = aero_result.coords

        # continuously overwrite last airfoil
        last_coords = aero_result.coords

        # calculate score
        score = scoring_p1(aero_result)

        print(f"Score = {score:.4f}")

        # save results to csv
        log_iteration(
            log_file,
            i,
            aero_result.cl,
            aero_result.cd,
            score
        )

    # plotting functions
    plot_score_history(log_file)

    plot_aero_history(log_file)

    import matplotlib.pyplot as plt

    plt.figure(figsize=(10,4))

    plt.plot(
        first_coords[:,0],
        first_coords[:,1],
        linewidth=2,
        label="Initial Airfoil"
    )

    plt.plot(
        last_coords[:,0],
        last_coords[:,1],
        linewidth=2,
        label="Final Airfoil"
    )

    plt.axis('equal')

    plt.xlabel("x/c")
    plt.ylabel("y/c")

    plt.title("Initial vs Final Airfoil")

    plt.grid(True)

    plt.legend()

    plt.show()


if __name__ == "__main__":
    main()