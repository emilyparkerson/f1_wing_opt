from phase1.phase1 import PHASE_CONFIG

from setup.aero_interface import run_mses
from setup.design_vars import designParameters

config = PHASE_CONFIG

# -----------------------------------
# CHANGE THESE VALUES
# -----------------------------------

design = designParameters(

    max_camber=0.045,
        max_camber_loc=0.525,
        max_thickness=0.175,
        max_thickness_loc=0.24,
)

# -----------------------------------
# PRINT DESIGN
# -----------------------------------

print("-----------------------------------")
print("TESTING MORPHED AIRFOIL")
print("-----------------------------------")

print(design)

# -----------------------------------
# RUN SAME PIPELINE AS MAIN.PY
# -----------------------------------

result = run_mses(

    design=design,

    name="test_seed",

    alpha=config["alpha"],

    mach=config["mach"],

    reynolds=config["reynolds"],

    seed_airfoil=config["seed_airfoil"],

    plot_geometry=True,

    plot_comparison=True,
)

# -----------------------------------
# RESULTS
# -----------------------------------

print("\n-----------------------------------")
print("RESULT")
print("-----------------------------------")

print("Cl:", result.cl)
print("Cd:", result.cd)

if result.coords is not None:
    print("Geometry exists")
else:
    print("No geometry returned")