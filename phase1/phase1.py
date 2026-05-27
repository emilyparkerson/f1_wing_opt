from pathlib import Path

from setup.scoring import scoring_p1

from setup.constraints import airfoil_constraints

from setup.design_vars import (
    designParameters,
    airfoilBounds
)

HERE = Path(__file__).parent


PHASE_CONFIG = {

    # Phase info
    "phase_name": "P1",
    "scoring_function": scoring_p1,

    # Flow conditions
    # "alpha": 0.0,
    # "mach": 0.23,
    # "reynolds": 1e6,

    # # Flow conditions
    # "alpha": 0.0,
    # "mach": 0.081627322,
    # "reynolds": 789563.2304,

    # Flow conditions
    "alpha": -2.5,
    "mach": 0.093871421,
    "reynolds": 907997.7149,

    # Training data
    "training_n":10,

    # Initial design (for MSES, training data is used for BO)
    "seed_airfoil": HERE / "inboard_seed_phase1.txt",
    # "seed_design": designParameters(
    #     max_camber=0.04358,
    #     max_camber_loc=0.635,
    #     max_thickness=0.17569,
    #     max_thickness_loc=0.2434),
    # "seed_design": designParameters(
    #     max_camber=0.045,
    #     max_camber_loc=0.45,
    #     max_thickness=0.175,
    #     max_thickness_loc=0.24),

    "seed_design": designParameters(
        max_camber=0.04382,
        max_camber_loc=0.45,
        max_thickness=0.1767,
        max_thickness_loc=0.24),

    # # Design variable bounds
    # "bounds": airfoilBounds(
    #     max_camber=(0.00, 0.08),
    #     max_camber_loc=(0.30, 0.70),
    #     max_thickness=(0.17, 0.225),
    #     max_thickness_loc=(0.15, 0.3)),
    # "constraints": airfoil_constraints,
        # Design variable bounds
    "bounds": airfoilBounds(
        max_camber=(0.00, 0.15),
        max_camber_loc=(0.30, 0.70),
        max_thickness=(0.17, 0.22),
        max_thickness_loc=(0.15, 0.35)),
    "constraints": airfoil_constraints,

    # Bayesian optimization settings
    "bo": {"training_csv": HERE / "training_data_p1.csv",
        "bounds_csv": HERE / "design_variable_bounds_p1.csv",
        "max_iter": 5},

    # Random/local search settings
    "random_search": {"n_iterations": 25,
        "step_size": {
            "max_camber": 0.003,
            "max_camber_loc": 0.02,
            "max_thickness": 0.005,
            "max_thickness_loc": 0.01}}
}