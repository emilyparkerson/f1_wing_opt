from scoring import scoringp2
from ..bayesian_optimization.run_bo_phase import run_bo_phase

run_bo_phase(
    training_csv="training_data_p2.csv",
    bounds_csv="design_variable_bounds_p2.csv",
    scoring_function=scoringp2,
    phase_name="P2",
    max_iter=25,
)