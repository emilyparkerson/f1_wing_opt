from pathlib import Path
from setup.scoring import scoring_p1
from setup.constraints import airfoil_constraints
from setup.geometry import plot_airfoil
from setup.design_vars import (
    designParameters,
    airfoilBounds
)

HERE = Path(__file__).parent

P1_IB_CONFIG = {

    # Phase info
    "phase_name": "Phase 1 Inboard Configuration",
    "scoring_function": scoring_p1,
    "plotting": True,
    "logging": True,
    "plot_geometry": True,

    # Flow conditions
    "alpha": 0.0,
    "mach": 0.23,
    "reynolds": 1e6,

    # Training data
    "training_n":10,

    # Initial design (for MSES, training data is used for BO)
    "seed_airfoil": HERE / "inboard_seed_phase1.txt",
    "seed_design": designParameters(
        max_camber=0.04358,
        max_camber_loc=0.635,
        max_thickness=0.17569,
        max_thickness_loc=0.2434),

    # Design variable bounds
    "bounds": airfoilBounds(
        max_camber=(0.00, 0.15),
        max_camber_loc=(0.30, 0.70),
        max_thickness=(0.06, 0.25),
        max_thickness_loc=(0.15, 0.45)),
    "constraints": airfoil_constraints,

    # Bayesian optimization settings
    "bo": {"training_csv": HERE / "training_data_p1.csv",
        "bounds_csv": HERE / "design_variable_bounds_p1.csv",
        "max_iter": 25},

    # Random/local search settings
    "random_search": {"n_iterations": 25,
        "step_size": {
            "max_camber": 0.003,
            "max_camber_loc": 0.02,
            "max_thickness": 0.005,
            "max_thickness_loc": 0.01}}
}


P1_OB_CONFIG = {

    # Phase info
    "phase_name": "Phase 1 Outboard Configuration",
    "scoring_function": scoring_p1,
    "plotting": True,
    "logging": True,

    # Flow conditions
    "alpha": 0.0,
    "mach": 0.23,
    "reynolds": 1e6,

    # Training data
    "training_n":10,

    # Initial design (for MSES, training data is used for BO)
    "seed_airfoil": HERE / "outboard_seed_phase1.txt",
    "seed_design": designParameters(
        max_camber=0.02544,
        max_camber_loc=0.6616,
        max_thickness=0.1421,
        max_thickness_loc=0.2919), 

    # Design variable bounds
    "bounds": airfoilBounds(
        max_camber=(0.00, 0.15),
        max_camber_loc=(0.30, 0.70),
        max_thickness=(0.06, 0.25),
        max_thickness_loc=(0.15, 0.45)),
    "constraints": airfoil_constraints,

    # Bayesian optimization settings
    "bo": {"training_csv": HERE / "training_data_p1.csv",
        "bounds_csv": HERE / "design_variable_bounds_p1.csv",
        "max_iter": 25},

    # Random/local search settings
    "random_search": {"n_iterations": 25,
        "step_size": {
            "max_camber": 0.003,
            "max_camber_loc": 0.02,
            "max_thickness": 0.005,
            "max_thickness_loc": 0.01}}
}