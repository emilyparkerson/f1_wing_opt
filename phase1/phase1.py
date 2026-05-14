
from pathlib import Path
from scoring import scoringp1
from bayesian_optimization.run_bo_phase import run_bo_phase

HERE = Path(__file__).parent

run_bo_phase(
    training_csv = HERE / "training_data_p1.csv",
    bounds_csv = HERE / "design_variable_bounds_p1.csv",
    scoring_function = scoringp1,
    phase_name = "P1",
    max_iter = 25,
)