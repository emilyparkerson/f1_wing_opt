from pathlib import Path
from setup.scoring import scoringp2
from bayesian_optimization.run_bo_phase import run_bo_phase

HERE = Path(__file__).parent

run_bo_phase(
    training_csv = HERE / "training_data_p2.csv",
    bounds_csv = HERE / "design_variable_bounds_p2.csv",
    scoring_function = scoringp2,
    phase_name = "P2",
    max_iter = 25,
)