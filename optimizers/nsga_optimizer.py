import numpy as np
import matplotlib.pyplot as plt

#import pymoo objects
from pymoo.core.problem import ElementwiseProblem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.factory import get_termination
from pymoo.optimize import minimize

from setup.aero_interface import run_mses
from setup.design_vars import designParameters

from optimizers.run_bo_optimizer import is_valid_result

#FOR EXPORTING DATA
import os
import pandas as pd


class TargetValidEvaluationsReached(Exception):
    pass


def export_airfoil_coords(coords, filepath):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    np.savetxt(filepath, coords, fmt="%.8f", header="x y", comments="")


def export_history(history, filepath):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    df = pd.DataFrame({
        "eval": history["eval"],
        "score": history["score"],
        "cl": history["cl"],
        "cd": history["cd"],
    })

    df.to_csv(filepath, index=False)
#END EXPPORTING DATA FUNCTIONS

#convert optimizer variables into airfoil design object
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


#wrap airfoil optimization problem into a form pymoo can optmize
#inspiration taken from PymeadGAProblem shape_optimization.py
#pymoo evaluates one candidate at a time
class NSGAProblem(ElementwiseProblem):
    #initialize problem
    #double underscores for python object constructor
    def __init__(self, config, bounds_arr, constraints, history):
        #tells pymoo the structure of the problem
        super().__init__(
            n_var=4, #4 design vars
            n_obj=1, #1 objective function
            n_constr=0, #no formal pymoo constraints
            xl=bounds_arr[:, 0], #lower bounds
            xu=bounds_arr[:, 1], #upper bounds
        )

        #store inputs
        self.config = config
        self.constraints = constraints
        self.history = history

        #evluation counter
        self.eval_count = 0 #all attempted candidates
        self.valid_eval_count = 0 #only converged/valid MSES candidates
        self.target_valid_evals = config.get("nsga", {}).get("target_valid_evals", 300)

    #core objective function (inspiration from chromosome.forces)
    #pymoo requires this function name
    def _evaluate(self, x, out, *args, **kwargs):
        self.eval_count += 1

        #print evaluation number
        print("-----------------------------------")
        print(f"Eval {self.eval_count} | Valid Eval {self.valid_eval_count}/{self.target_valid_evals}")
        print("-----------------------------------")
        print(f"x = [{x[0]:.4f}, {x[1]:.4f}, {x[2]:.4f}, {x[3]:.4f}]")

        #rehect invalid candidate designs by assigning a large penalty value
        #okay here unlike BO because no need for training
        if not self.constraints(x):
            print("Rejected by constraints")
            out["F"] = [1e6]
            return

        #convert into design parameters object
        design = design_from_x(x)

        #run MSES (same as BO optimizer)
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

        #penalize invalid aero designs
        if not is_valid_result(aero):
            print("Invalid MSES result")
            out["F"] = [1e6]
            return

        self.valid_eval_count += 1

        #compute score
        scoring_fn = self.config["scoring_function"]
        score = scoring_fn(aero, design)

        #store history of cl, cd, and score for plotting
        self.history["eval"].append(self.valid_eval_count)
        self.history["x"].append(np.array(x, dtype=float))
        self.history["score"].append(score)
        self.history["cl"].append(aero.cl)
        self.history["cd"].append(aero.cd)

        #print cl, cd, and score for each candidate
        print(f"Cl = {aero.cl:.5f}")
        print(f"Cd = {aero.cd:.5f}")
        print(f"Score = {score:.5f}")
        print(f"Valid converged evaluations = {self.valid_eval_count}/{self.target_valid_evals}")

        #pymoo minimizes, so use negative score
        out["F"] = [-score]

        if self.valid_eval_count >= self.target_valid_evals:
            raise TargetValidEvaluationsReached


def plot_history(history):
    if len(history["score"]) == 0:
        print("No valid NSGA evaluations to plot.")
        return

    evals = np.array(history["eval"])

    best_so_far = np.maximum.accumulate(history["score"])

    #plot score
    plt.figure()
    plt.plot(evals, history["score"], marker="o", label="Score")
    plt.plot(evals, best_so_far, linestyle="--", label="Best Score So Far")
    plt.xlabel("Valid NSGA Iteration")
    plt.ylabel("Score")
    plt.title("NSGA-II Optimizer Score History")
    plt.grid(True)
    plt.legend()
    plt.show()

    #plot cl
    plt.figure()
    plt.plot(evals, history["cl"], marker="o")
    plt.xlabel("Valid NSGA Iteration")
    plt.ylabel("Cl")
    plt.title("NSGA-II Optimizer Cl History")
    plt.grid(True)
    plt.show()

    #plot cd
    plt.figure()
    plt.plot(evals, history["cd"], marker="o")
    plt.xlabel("Valid NSGA Iteration")
    plt.ylabel("Cd")
    plt.title("NSGA-II Optimizer Cd History")
    plt.grid(True)
    plt.show()


def plot_seed_vs_optimized(seed_result, best_result):

    plt.figure()
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

#function to run NSGA optimization (take input from Phase 1 config file)
def run_nsga_optimizer(config):
    #get any specific nsga configs, if none use empty dictionary
    nsga_config = config.get("nsga", {})

    #set default population size and number of generations
    population_size = nsga_config.get("population_size", 20)
    n_generations = nsga_config.get("n_generations", 1000)
    seed = nsga_config.get("seed", 2) #randomization parameter for algorithm
    target_valid_evals = nsga_config.get("target_valid_evals", 300)

    seed_design = config["seed_design"]
    seed_airfoil = config["seed_airfoil"]

    bounds_obj = config["bounds"]
    bounds = [
        bounds_obj.max_camber,
        bounds_obj.max_camber_loc,
        bounds_obj.max_thickness,
        bounds_obj.max_thickness_loc,
    ]
    #convert bounds into numpy array, so that pymoo can use them
    bounds_arr = np.array(bounds, dtype=float)

    constraints = config["constraints"]

    #create list to store all design variables from candidate
    history = {
        "eval": [],
        "x": [],
        "score": [],
        "cl": [],
        "cd": [],
    }

    #print optimizer settings
    print("-----------------------------------")
    print("Running NSGA optimization...")
    print("-----------------------------------")
    print(f"Population size: {population_size}")
    print(f"Generation limit: {n_generations}")
    print(f"Target valid converged evaluations: {target_valid_evals}")

    #create the problem optimziation object using inputs defined above
    problem = NSGAProblem(
        config=config,
        bounds_arr=bounds_arr,
        constraints=constraints,
        history=history,
    )

    #use NSGA-II algorithm from pymoo, avoid duplicate airfoils
    algorithm = NSGA2(
        pop_size=population_size,
        eliminate_duplicates=True,
    )

    #tell pymoo to stop after specific number of generations
    termination = get_termination("n_gen", n_generations)

    try:
        res = minimize(
            problem,
            algorithm,
            termination,
            seed=seed,
            verbose=True,
        )
    except TargetValidEvaluationsReached:
        print(f"\nReached {problem.valid_eval_count} valid converged airfoils. Stopping NSGA.")

    #if no scores, then all invalid iterations
    if len(history["score"]) == 0:
        raise RuntimeError("NSGA completed but produced no valid evaluations.")

    #find index of highest score and stores best design
    best_idx = int(np.argmax(history["score"]))
    x_best = history["x"][best_idx]
    y_best = history["score"][best_idx]

    best_design = design_from_x(x_best)

    print("\n===================================")
    print("NSGA OPTIMIZATION COMPLETE")
    print("===================================")
    print(f"\nValid converged evaluations = {len(history['score'])}")
    print(f"Best score = {y_best:.5f}")
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


    #EXPORT DATA
    export_airfoil_coords(seed_result.coords, "outputs/seed/seed_airfoil_outboard_05.dat")
    
    export_airfoil_coords(best_result.coords, "outputs/nsga/nsga_optimized_airfoil_outboard_05.dat")

    export_history(history, "outputs/nsga/nsga_history_outboard_05.csv")

    return np.array(history["x"]), np.array(history["score"]), x_best, y_best