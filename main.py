from phase1.phase1 import P1_IB_CONFIG
from phase1.phase1 import P1_OB_CONFIG

from optimizers.run_random_optimizer import run_random_optimizer
from optimizers.run_bo_optimizer import run_bo_optimizer

phase_configs = [P1_IB_CONFIG, P1_OB_CONFIG]
OPTIMIZER = "bo"

def main():
    for phase_config in phase_configs:
        if OPTIMIZER == "random": run_random_optimizer(phase_config)
        elif OPTIMIZER == "bo": run_bo_optimizer(phase_config)
        else: raise ValueError(f"Unknown optimizer: {OPTIMIZER}")

if __name__ == "__main__":
    main()


    