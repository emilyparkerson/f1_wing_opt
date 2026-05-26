import os
import tempfile
import numpy as np

from pymead.analysis.calc_aero_data import (
    calculate_aero_data,
    MSETSettings,
    MSESSettings,
    MPLOTSettings,
    AirfoilMSETMeshingParameters
)

from pymead.core.geometry_collection import GeometryCollection

from phase1.phase1 import PHASE_CONFIG

config = PHASE_CONFIG

seed_airfoil = config["seed_airfoil"]

# -----------------------------------
# LOAD RAW SEED COORDINATES
# -----------------------------------

coords = np.loadtxt(seed_airfoil)

from scipy.signal import savgol_filter

coords[:,1] = savgol_filter(
    coords[:,1],
    11,
    3
)

print("-----------------------------------")
print("TESTING TRUE RAW SEED")
print("-----------------------------------")

print("Loaded raw seed coordinates")

# -----------------------------------
# SAVE TEMP DAT FILE
# -----------------------------------

dat_file = os.path.join(
    tempfile.gettempdir(),
    "true_seed_input.dat"
)

np.savetxt(dat_file, coords)

# -----------------------------------
# LOAD INTO PYMEAD
# -----------------------------------

geo_col = GeometryCollection()

polyline = geo_col.add_polyline(source=dat_file)

airfoil = polyline.add_polyline_airfoil()

mea = geo_col.add_mea([airfoil])

print("Raw seed airfoil loaded into pymead")

# -----------------------------------
# MSET SETTINGS
# -----------------------------------

mset_settings = MSETSettings(

    multi_airfoil_grid={
        "Airfoil-1": AirfoilMSETMeshingParameters()
    },

    # finer surface discretization
    airfoil_side_points=320
)

# -----------------------------------
# MSES SETTINGS
# -----------------------------------

mses_settings = MSESSettings(

    # transition locations
    xtrs={
        "Airfoil-1": [1.0, 1.0]
    },

    # flow conditions
    Ma=0.05,
    Re=2.5e5,
    alfa=0.0,

    alfa_Cl_mode=0,

    # allow more iterations
    timeout=1200.0,
)

mplot_settings = MPLOTSettings(
    Tecplot=True
)

# -----------------------------------
# RUN MSES
# -----------------------------------

print("\nRunning MSES on TRUE seed geometry...\n")

try:

    aero_data, logs = calculate_aero_data(

        conn=None,

        airfoil_coord_dir=tempfile.gettempdir(),

        airfoil_name="true_seed",

        mea=mea,

        tool="MSES",

        mset_settings=mset_settings,

        mses_settings=mses_settings,

        mplot_settings=mplot_settings,

        export_Cp=False,

        save_aero_data=True,
    )

    print("\n-----------------------------------")
    print("RESULT")
    print("-----------------------------------")

    print(aero_data)

    if aero_data.get("converged", False):

        print("\nSUCCESS")

        print(f"Cl = {aero_data['Cl']:.5f}")
        print(f"Cd = {aero_data['Cd']:.5f}")

    else:

        print("\nMSES still did not converge")

except Exception as e:

    print("\nMSES crashed with exception:")
    print(e)