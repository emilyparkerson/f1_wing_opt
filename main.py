from aero_interface import run_mses
from scoring import scoring_p1

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

    for i in range(n_iterations):

        print(f"\nIteration {i}")

        # run aerodynamic analysis
        aero_result = run_mses(
            alpha=2.0
        )

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


if __name__ == "__main__":
    main()