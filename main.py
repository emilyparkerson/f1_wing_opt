import numpy as np

from phase1.phase1 import PHASE_CONFIG

from optimizers.run_random_optimizer import run_random_optimizer
from optimizers.run_bo_optimizer import run_bo_optimizer

OPTIMIZER = "bo"
# OPTIMIZER = "random"

def main():

    np.random.seed(1)

    if OPTIMIZER == "random":
        run_random_optimizer(PHASE_CONFIG)

    elif OPTIMIZER == "bo":
        run_bo_optimizer(PHASE_CONFIG)

    else:
        raise ValueError(f"Unknown optimizer: {OPTIMIZER}")

if __name__ == "__main__":
    main()