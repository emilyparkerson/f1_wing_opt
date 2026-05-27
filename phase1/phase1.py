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

    # Flow conditions
    "alpha": 0.0,
    "mach": 0.122440983,
    "reynolds": 1184344.846,

    # Training data
    "training_n":10,

    # Initial design (for MSES, training data is used for BO)
    "seed_airfoil": HERE / "outboard_seed_phase1.txt",
    # "seed_design": designParameters(
    #     max_camber=0.02544,
    #     max_camber_loc=0.6616,
    #     max_thickness=0.1421,
    #     max_thickness_loc=0.2919),
    "seed_design": designParameters(
          max_camber=0.02544,
          # can't go any higher for max camber location or seed diverges
        max_camber_loc=0.65,
        max_thickness=0.1421,
        max_thickness_loc=0.2919),

    # Design variable bounds
    "bounds": airfoilBounds(
        max_camber=(0.00, 0.15),
        max_camber_loc=(0.30, 0.70),
        max_thickness=(0.14, 0.22),
        max_thickness_loc=(0.15, 0.35)),
    "constraints": airfoil_constraints,

    # Bayesian optimization settings
    "bo": {"training_csv": HERE / "training_data_p1.csv",
        "bounds_csv": HERE / "design_variable_bounds_p1.csv",
        "max_iter": 50},

    # Random/local search settings
    "random_search": {"n_iterations": 25,
        "step_size": {
            "max_camber": 0.003,
            "max_camber_loc": 0.02,
            "max_thickness": 0.005,
            "max_thickness_loc": 0.01}}
}