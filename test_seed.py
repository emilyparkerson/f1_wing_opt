from phase1.phase1 import PHASE_CONFIG

from setup.aero_interface import run_mses
from optimizers.run_bo_optimizer import is_valid_result


config = PHASE_CONFIG

design = config["seed_design"]

print("-----------------------------------")
print("TESTING SEED DESIGN")
print("-----------------------------------")

print(design)

result = run_mses(
    design=design,
    name="seed_test",
    alpha=config["alpha"],
    mach=config["mach"],
    reynolds=config["reynolds"],
    seed_airfoil=config["seed_airfoil"],
    plot_geometry=True,
    plot_comparison=True,
)

print("\n-----------------------------------")
print("RESULT")
print("-----------------------------------")

print("Valid:", is_valid_result(result))
print("Cl:", result.cl)
print("Cd:", result.cd)

if result.coords is not None:
    print("Geometry exists")
else:
    print("No geometry returned")