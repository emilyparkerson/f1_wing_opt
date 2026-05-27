import numpy as np
import matplotlib.pyplot as plt

from pymoo.core.problem import ElementwiseProblem
from pymoo.algorithms.moo.nsga2 import NSGA2

try:
    from pymoo.termination import get_termination
except ModuleNotFoundError:
    from pymoo.factory import get_termination

from pymoo.optimize import minimize

from setup.aero_interface import run_mses
from setup.design_vars import designParameters

from optimizers.run_bo_optimizer import is_valid_result


def design_from_x(x):
    return designParameters(
        max_camber=float(x[0]),
        max_camber_loc=float(x[1]),
        max_thickness=float(x[2]),
        max_thickness_loc=float(x[3]),
    )


def x_from_design(design):
    return np.array([
        design.max_camber,
        design.max_camber_loc,
        design.max_thickness,
        design.max_thickness_loc,
    ], dtype=float)


class NSGAProblem(ElementwiseProblem):
    def __init__(self, config, bounds_arr, constraints, history):
        super().__init__(
            n_var=4,
            n_obj=1,
            n_constr=0,
            xl=bounds_arr[:, 0],
            xu=bounds_arr[:, 1],
        )

        self.config = config
        self.constraints = constraints
        self.history = history

        self.eval_count = 0
        self.generation_guess = 0

    def _evaluate(self, x, out, *args, **kwargs):
        self.eval_count += 1

        pop_size = self.config.get("nsga", {}).get("population_size", 20)
        generation = int(np.ceil(self.eval_count / pop_size))
        candidate = ((self.eval_count - 1) % pop_size) + 1

        print("-----------------------------------")
        print(f"NSGA Generation {generation} | Candidate {candidate} | Eval {self.eval_count}")
        print("-----------------------------------")
        print(
            f"x = [{x[0]:.4f}, {x[1]:.4f}, {x[2]:.4f}, {x[3]:.4f}]"
        )

        if not self.constraints(x):
            print("Rejected by constraints")
            out["F"] = [1e6]
            return

        design = design_from_x(x)

        aero = run_mses(
            design=design,
            name=f"nsga_eval_{self.eval_count}",
            alpha=self.config["alpha"],
            mach=self.config["mach"],
            reynolds=self.config["reynolds"],
            seed_airfoil=self.config["seed_airfoil"],
            plot_geometry=False,
            plot_comparison=False,
        )

        if not is_valid_result(aero):
            print("Invalid MSES result")
            out["F"] = [1e6]
            return

        scoring_fn = self.config["scoring_function"]
        score = scoring_fn(aero, design)

        self.history["x"].append(np.array(x, dtype=float))
        self.history["score"].append(score)
        self.history["cl"].append(aero.cl)
        self.history["cd"].append(aero.cd)

        print(f"Cl = {aero.cl:.5f}")
        print(f"Cd = {aero.cd:.5f}")
        print(f"Score = {score:.5f}")

        # pymoo minimizes, so use negative score
        out["F"] = [-score]


def plot_history(history):
    if len(history["score"]) == 0:
        print("No valid NSGA evaluations to plot.")
        return

    evals = np.arange(1, len(history["score"]) + 1)

    best_so_far = np.maximum.accumulate(history["score"])

    plt.figure(figsize=(8, 4))
    plt.plot(evals, history["score"], marker="o", label="Score")
    plt.plot(evals, best_so_far, linestyle="--", label="Best Score So Far")
    plt.xlabel("Valid Evaluation")
    plt.ylabel("Score")
    plt.title("NSGA Score History")
    plt.grid(True)
    plt.legend()
    plt.show()

    plt.figure(figsize=(8, 4))
    plt.plot(evals, history["cl"], marker="o")
    plt.xlabel("Valid Evaluation")
    plt.ylabel("Cl")
    plt.title("NSGA Cl History")
    plt.grid(True)
    plt.show()

    plt.figure(figsize=(8, 4))
    plt.plot(evals, history["cd"], marker="o")
    plt.xlabel("Valid Evaluation")
    plt.ylabel("Cd")
    plt.title("NSGA Cd History")
    plt.grid(True)
    plt.show()


def plot_seed_vs_optimized(seed_result, best_result):
    plt.figure(figsize=(10, 4))

    plt.plot(
        seed_result.coords[:, 0],
        seed_result.coords[:, 1],
        label="Seed Airfoil",
        linewidth=2,
    )

    plt.plot(
        best_result.coords[:, 0],
        best_result.coords[:, 1],
        label="NSGA Optimized Airfoil",
        linewidth=2,
    )

    plt.axis("equal")
    plt.grid(True)
    plt.legend()
    plt.xlabel("x/c")
    plt.ylabel("y/c")
    plt.title("Seed vs NSGA Optimized Airfoil")
    plt.show()


def run_nsga_optimizer(config):
    nsga_config = config.get("nsga", {})

    population_size = nsga_config.get("population_size", 20)
    n_generations = nsga_config.get("n_generations", 5)
    seed = nsga_config.get("seed", 42)

    seed_design = config["seed_design"]
    seed_airfoil = config["seed_airfoil"]

    bounds_obj = config["bounds"]
    bounds = [
        bounds_obj.max_camber,
        bounds_obj.max_camber_loc,
        bounds_obj.max_thickness,
        bounds_obj.max_thickness_loc,
    ]
    bounds_arr = np.array(bounds, dtype=float)

    constraints = config["constraints"]

    history = {
        "x": [],
        "score": [],
        "cl": [],
        "cd": [],
    }

    print("-----------------------------------")
    print("Running NSGA optimization...")
    print("-----------------------------------")
    print(f"Population size: {population_size}")
    print(f"Generations: {n_generations}")
    print(f"Expected evaluations: {population_size * n_generations}")

    problem = NSGAProblem(
        config=config,
        bounds_arr=bounds_arr,
        constraints=constraints,
        history=history,
    )

    algorithm = NSGA2(
        pop_size=population_size,
        eliminate_duplicates=True,
    )

    termination = get_termination("n_gen", n_generations)

    res = minimize(
        problem,
        algorithm,
        termination,
        seed=seed,
        verbose=True,
    )

    if len(history["score"]) == 0:
        raise RuntimeError("NSGA completed but produced no valid evaluations.")

    best_idx = int(np.argmax(history["score"]))
    x_best = history["x"][best_idx]
    y_best = history["score"][best_idx]

    best_design = design_from_x(x_best)

    print("\n===================================")
    print("NSGA OPTIMIZATION COMPLETE")
    print("===================================")
    print(f"\nBest score = {y_best:.5f}")
    print(f"Best Cl = {history['cl'][best_idx]:.5f}")
    print(f"Best Cd = {history['cd'][best_idx]:.5f}")
    print(f"  max_camber:         {best_design.max_camber:.4f}")
    print(f"  max_camber_loc:     {best_design.max_camber_loc:.4f}")
    print(f"  max_thickness:      {best_design.max_thickness:.4f}")
    print(f"  max_thickness_loc:  {best_design.max_thickness_loc:.4f}")

    plot_history(history)

    print("\n-----------------------------------")
    print("Running FINAL optimized airfoil evaluation...")
    print("-----------------------------------")

    best_result = run_mses(
        design=best_design,
        name="nsga_best_airfoil",
        alpha=config["alpha"],
        mach=config["mach"],
        reynolds=config["reynolds"],
        seed_airfoil=seed_airfoil,
    )

    print("\n-----------------------------------")
    print("Running SEED airfoil evaluation...")
    print("-----------------------------------")

    seed_result = run_mses(
        design=seed_design,
        name="seed_airfoil",
        alpha=config["alpha"],
        mach=config["mach"],
        reynolds=config["reynolds"],
        seed_airfoil=seed_airfoil,
    )

    if is_valid_result(best_result) and is_valid_result(seed_result):
        plot_seed_vs_optimized(seed_result, best_result)
    else:
        print("Could not plot airfoils because one did not converge.")

    return np.array(history["x"]), np.array(history["score"]), x_best, y_best