from scoring import scoringp1
from ..bayesian_optimization.run_bo_phase import run_bo_phase

run_bo_phase(
    training_csv="training_data_p1.csv",
    bounds_csv="design_variable_bounds_p1.csv",
    scoring_function=scoringp1,
    phase_name="P1",
    max_iter=25,
)