''' Phase 2 configs.

P2_RE_OB_CONFIG:
  Element 1 (Airfoil-1 in MSES): seed flap (morph). BO optimizes its
    shape. The seed file's chord/LE/angle are baked into the spec so the
    morphed flap lands exactly where the seed sits in MSES coords.
  Element 2 (Airfoil-2 in MSES): main winner from phase1_winner_OB.dat,
    loaded as-is.
'''

from pathlib import Path
from setup.scoring import scoring_p2
from setup.constraints import airfoil_constraints
from setup.design_vars import (
    designParameters,
    airfoilBounds,
)

HERE = Path(__file__).parent


P2_RE_OB_CONFIG = {

    # Phase info
    "phase_name": "P2 RE OB",
    "scoring_function": scoring_p2,
    "plotting": True,
    "logging": True,
    "plot_geometry": False,

    # Flow conditions (outboard from spreadsheet)
    "alpha": 0.0,
    "mach": 0.08276085807,
    "reynolds": 2506449.402,

    "xtr_upper": 1.0,
    "xtr_lower": 1.0,

    "target_cl": None,                # fixed-alpha mode

    # Training data
    "training_n": 5,

    # Initial design for the morph element (the seed flap)
    "seed_airfoil": HERE / "outboard_seed_phase2.dat",
    "winner_output": HERE / "phase2_winner_OB.dat",
    "seed_design": designParameters(
        max_camber=0.02544,
        max_camber_loc=0.6616,
        max_thickness=0.1421,
        max_thickness_loc=0.2919),

    # Element order: Airfoil-1 = seed flap (morph), Airfoil-2 = main winner (fixed).
    # The morph spec specifies chord/LE/AoA so the morphed flap lands where the
    # seed file sits in MSES coordinates -- matching the converged geometry
    # from check_converge.py.
    "elements": [
        {"role": "morph",
         "seed_airfoil": HERE / "outboard_seed_phase2.dat",
         "chord": 0.39357,
         "le_position": (0.88613, 0.12938),
         "installed_aoa_deg": 20.73},
        {"role": "fixed",
         "coords_path": HERE / "phase1_winner_OB.dat"},
    ],

    # Design variable bounds (BO morph variables for the seed flap)
    "bounds": airfoilBounds(
        max_camber=(0.02, 0.08),
        max_camber_loc=(0.50, 0.75),
        max_thickness=(0.10, 0.18),
        max_thickness_loc=(0.20, 0.40)),
    "constraints": airfoil_constraints,

    # Reference values for scoring
    "ref_vals": {
        "df": 3.04152,
        "cd": 0.03028,
    },

    # Bayesian optimization settings
    "bo": {"training_csv": HERE / "training_data_p2_OB.csv",
        "bounds_csv": HERE / "design_variable_bounds_p2.csv",
        "max_iter": 5000,  
        "target_converged": 400},

    # Random/local search settings
    "random_search": {"n_iterations": 5,
                      "step_size": {
                          "max_camber": 0.001,
                          "max_camber_loc": 0.01,
                          "max_thickness": 0.001,
                          "max_thickness_loc": 0.01}},
}





P2_RE_IB_CONFIG = {

    # Phase info
    "phase_name": "P2 RE IB",
    "scoring_function": scoring_p2,
    "plotting": True,
    "logging": True,
    "plot_geometry": False,

    # Flow conditions (outboard from spreadsheet)
    "alpha": -2.5,
    "mach": 0.0630088633,
    "reynolds": 1908251.454, 

    "xtr_upper": 1.0,
    "xtr_lower": 1.0,

    "target_cl": None, # fixed-alpha mode

    # Training data
    "training_n": 5,

    # Initial design for the morph element (the seed flap)
    "seed_airfoil": HERE / "inboard_seed_phase2.dat",
    "winner_output": HERE / "phase2_winner_IB.dat",
    "seed_design": designParameters(
        max_camber=0.02544,
        max_camber_loc=0.6616,
        max_thickness=0.1421,
        max_thickness_loc=0.2919),

    # Element order: Airfoil-1 = seed flap (morph), Airfoil-2 = main winner (fixed).
    # The morph spec specifies chord/LE/AoA so the morphed flap lands where the
    # seed file sits in MSES coordinates -- matching the converged geometry
    # from check_converge.py.
    "elements": [
        {"role": "morph",
         "seed_airfoil": HERE / "inboard_seed_phase2.dat",
         "chord": 0.39357,
         "le_position": (0.88613, 0.12938),
         "installed_aoa_deg": 20.73},
        {"role": "fixed",
         "coords_path": HERE / "phase1_winner_IB.dat"},
    ],

    # Design variable bounds (BO morph variables for the seed flap)
    "bounds": airfoilBounds(
        max_camber=(0.02, 0.08),
        max_camber_loc=(0.50, 0.75),
        max_thickness=(0.10, 0.18),
        max_thickness_loc=(0.20, 0.40)),
    "constraints": airfoil_constraints,

    # Reference values for scoring
    "ref_vals": {
        "df": 3.19640,
        "cd": 0.03808,
    },

    # Bayesian optimization settings
    "bo": {"training_csv": HERE / "training_data_p2_IB.csv",
        "bounds_csv": HERE / "design_variable_bounds_p2.csv",
        "max_iter": 5000,       
        "target_converged": 400},

    # Random/local search settings
    "random_search": {"n_iterations": 5,
                      "step_size": {
                          "max_camber": 0.001,
                          "max_camber_loc": 0.01,
                          "max_thickness": 0.001,
                          "max_thickness_loc": 0.01}},
}