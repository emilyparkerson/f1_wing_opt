from phase1.phase1 import P1_IB_CONFIG
from optimizers.run_bo_optimizer import run_bo_optimizer

phase_configs = [P1_IB_CONFIG]
OPTIMIZER = "bo"

def main():
    for phase_config in phase_configs:
        run_bo_optimizer(phase_config)

if __name__ == "__main__":
    main()