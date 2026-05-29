from pathlib import Path
from setup.scoring import scoring_p1
from setup.constraints import airfoil_constraints
from setup.geometry import plot_airfoil
from setup.design_vars import (
    designParameters,
    airfoilBounds
)

from setup.geometry import plot_airfoil

HERE = Path(__file__).parent
PHASE2_DIR = HERE.parent / "phase2"   # where phase 2 reads fixed elements from

P1_IB_CONFIG = {

    # Phase info
    "phase_name": "Phase 2 Inboard Configuration",
    "scoring_function": scoring_p2,
    "plotting": True,
    "logging": True,
    "plot_geometry": True,

    # Flow conditions
    "alpha": -2.5,
    "mach": 0.093871421,
    #"mach": 0.05,
    "reynolds": 907997.7149,

    # Training data
    "training_n":5,

    # Initial design (for MSES, training data is used for BO)
    "seed_airfoil": HERE / "inboard_seed_phase2.txt",
    "winner_output": PHASE2_DIR / "phase2_winner_IB.dat",
    "seed_design": designParameters(
        max_camber=0.04382,
        max_camber_loc=0.45,
        max_thickness=0.1767,
        max_thickness_loc=0.24),

    # Design variable bounds
    "bounds": airfoilBounds(
        max_camber=(0.01, 0.15),
        max_camber_loc=(0.30, 0.70),
        max_thickness=(0.17, 0.22),
        max_thickness_loc=(0.15, 0.35)),
    "constraints": airfoil_constraints,

    #Reference values
    "ref_vals": {
        "df": 1.21820,
        "cd": 0.01635,
    },

    # Bayesian optimization settings
    "bo": {"training_csv": HERE / "training_data_p2.csv",
        "bounds_csv": HERE / "design_variable_bounds_p2.csv",
        "max_iter": 5},

    # Random/local search settings
    "random_search": {"n_iterations": 5,
        "step_size": {
            "max_camber": 0.003,
            "max_camber_loc": 0.02,
            "max_thickness": 0.005,
            "max_thickness_loc": 0.01}},

}


P1_OB_CONFIG = {

    # Phase info
    "phase_name": "Phase 2 Outboard Configuration",
    "scoring_function": scoring_p2,
    "plotting": True,
    "logging": True,

    # Flow conditions
    "alpha": 0.0,
    "mach": 0.122440983,
    #"mach": 0.05,
    "reynolds": 1184344.846,

    # Training data
    "training_n":5,

    # Initial design (for MSES, training data is used for BO)
    "seed_airfoil": HERE / "outboard_seed_phase2.txt",
    "winner_output": PHASE2_DIR / "phase2_winner_OB.dat",
    "seed_design": designParameters(
        max_camber=0.02544,
        # can't go any higher for max camber location or seed diverges
        max_camber_loc=0.65,
        max_thickness=0.1421,
        max_thickness_loc=0.2919),

    # Design variable bounds
    "bounds": airfoilBounds(
        max_camber=(0.01, 0.15),
        max_camber_loc=(0.30, 0.70),
        max_thickness=(0.17, 0.22),
        max_thickness_loc=(0.15, 0.35)),
    "constraints": airfoil_constraints,

    #Reference values
    "ref_vals": {
        "df": 0.87898,
        "cd": 0.01145,
    },

    # Bayesian optimization settings
    "bo": {"training_csv": HERE / "training_data_p2.csv",
        "bounds_csv": HERE / "design_variable_bounds_p2.csv",
        "max_iter": 5},

    # Random/local search settings
    "random_search": {"n_iterations": 5,
        "step_size": {
            "max_camber": 0.003,
            "max_camber_loc": 0.02,
            "max_thickness": 0.005,
            "max_thickness_loc": 0.01}}
}