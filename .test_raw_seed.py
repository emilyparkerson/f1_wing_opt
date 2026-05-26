import numpy as np
from pathlib import Path

from pymead.core.geometry_collection import GeometryCollection
from pymead.analysis.calc_aero_data import (
    calculate_aero_data,
    AirfoilMSETMeshingParameters,
    MSETSettings,
    MSESSettings,
    MPLOTSettings,
)

HERE = Path(__file__).parent

seed_airfoil = HERE / "phase1" / "inboard_seed_phase1.txt"

# -----------------------------------
# LOAD RAW SEED COORDINATES
# -----------------------------------

coords = np.loadtxt(seed_airfoil)

# Split into x and y
x = coords[:, 0]
y = coords[:, 1]

# -----------------------------------
# BUILD PYMEAD AIRFOIL DIRECTLY
# -----------------------------------

geo_col = GeometryCollection()

geo_col.add_airfoil(
    name="seed",
    coordinates=np.column_stack([x, y])
)

print("Raw seed airfoil loaded")

# -----------------------------------
# MSES SETTINGS
# -----------------------------------

mset_settings = MSETSettings()

mses_settings = MSESSettings(
    alfa=0.0,
    mach=0.23,
    reynolds_number=1e6,
)

mplot_settings = MPLOTSettings()

params = AirfoilMSETMeshingParameters()

# -----------------------------------
# RUN MSES
# -----------------------------------

print("\nRunning MSES on RAW seed geometry...\n")

result = calculate_aero_data(
    geo_col=geo_col,
    airfoil_name="seed",
    coords=np.column_stack([x, y]),
    tool="MSES",
    mset_settings=mset_settings,
    mses_settings=mses_settings,
    mplot_settings=mplot_settings,
    airfoil_mset_meshing_parameters=params,
)

print(result)