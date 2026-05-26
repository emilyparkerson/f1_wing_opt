"""
---------------------------------------------------------------------
AERO INTERFACE
---------------------------------------------------------------------
Take in geometry from geometry.py
Build a morphed airfoil, hand it to MSES, return Cl/Cd.

Uses the original geometry.py API:
    load_airfoil_dat -> get_seed -> new_airfoil -> get_coords

The seed is loaded in inverted (rear-wing / downforce) orientation, and
that orientation is preserved through to MSES. Scoring uses df = -cl,
so a properly cambered wing yields cl < 0 (lift down in MSES frame
= downforce in car frame) and df > 0.
"""

import os
import tempfile
import numpy as np
import matplotlib.pyplot as plt

from pymead.analysis.calc_aero_data import (
    calculate_aero_data,
    MSETSettings,
    MSESSettings,
    AirfoilMSETMeshingParameters,
)
from pymead.core.geometry_collection import GeometryCollection

from setup.design_vars import AeroResult
from setup.geometry import (
    load_airfoil_dat,
    new_airfoil,
)


def run_mses(design,
             name="candidate_airfoil",
             alpha=0.0,
             mach=0.08,
             reynolds=0.7e6,
             seed_airfoil="",
             plot_geometry=False,
             plot_comparison=False):

    # Geometry --------------------------------------------------------
    coords = new_airfoil(design, seed_airfoil, n=160)

    if plot_geometry:
        plt.figure(figsize=(10, 4))
        plt.plot(coords[:, 0], coords[:, 1], lw=2)
        plt.axis("equal")
        plt.grid(True)
        plt.xlabel("x/c")
        plt.ylabel("y/c")
        plt.title(name)
        plt.show()

    if plot_comparison:
        x_seed, y_seed = load_airfoil_dat(seed_airfoil)

        fig, axes = plt.subplots(1, 2, figsize=(14, 4))

        axes[0].plot(x_seed, y_seed)
        axes[0].set_title("Seed Airfoil")
        axes[0].axis("equal")
        axes[0].grid(True)

        axes[1].plot(coords[:, 0], coords[:, 1])
        axes[1].set_title("Morphed Airfoil")
        axes[1].axis("equal")
        axes[1].grid(True)

        plt.suptitle(f"{name} - geometry comparison")
        plt.show()

    # Write coordinates for pymead -----------------------------------------
    dat_file = os.path.join(tempfile.gettempdir(), f"{name}_input.dat")
    np.savetxt(dat_file, coords)

    geo_col = GeometryCollection()
    polyline = geo_col.add_polyline(source=dat_file)
    airfoil = polyline.add_polyline_airfoil()
    mea = geo_col.add_mea([airfoil])
    pymead_coords = np.array(airfoil.coords)

    # MSES settings --------------------------------------------------------
    mset = MSETSettings(
        multi_airfoil_grid={"Airfoil-1": AirfoilMSETMeshingParameters()},
        airfoil_side_points=200,
    )
    mses = MSESSettings(
        xtrs={"Airfoil-1": [0.05, 0.05]},
        Ma=mach, Re=reynolds, alfa=alpha,
        alfa_Cl_mode=0,
        timeout=500.0,
    )
    # NOTE: pymead 2.0.0b13 has a bug: MPLOTSettings.get_dict_rep() returns
    # the key "streamline_grid" (lowercase) but the consumer in
    # calculate_aero_data reads "Streamline_Grid" (capitalized). Pass a dict
    # directly with the keys the consumer actually uses.
    mplot = {
        "timeout":         15.0,
        "grid_stats":      False,
        "Mach":            False,
        "Streamline_Grid": False,
        "Grid":            False,
        "Grid_Zoom":       False,
        "flow_field":      False,
        "Tecplot":         False,
        "Paraview":        False,
        "CPK":             False,
    }

    # Run --------------------------------------------------------------------
    fail = AeroResult(cl=None, cd=None, coords=pymead_coords)
    try:
        print("\nRunning MSES...")
        aero_data, _ = calculate_aero_data(
            conn=None,
            airfoil_coord_dir=tempfile.gettempdir(),
            airfoil_name=name,
            mea=mea,
            tool="MSES",
            mset_settings=mset,
            mses_settings=mses,
            mplot_settings=mplot,
            export_Cp=False,
            save_aero_data=True,
        )
    except Exception as e:
        print(f"MSES exception: {e}")
        return fail

    if aero_data.get("errored_out"):    print("MSES errored out");      return fail
    if aero_data.get("timed_out"):      print("MSES timed out");        return fail
    if not aero_data.get("converged"):  print("MSES did not converge"); return fail

    cl, cd = aero_data["Cl"], aero_data["Cd"]
    if not (np.isfinite(cl) and np.isfinite(cd)):
        print("MSES returned non-finite Cl/Cd"); return fail

    print(f"Cl = {cl:+.5f}   Cd = {cd:.5f}")
    return AeroResult(cl=cl, cd=cd, coords=pymead_coords)