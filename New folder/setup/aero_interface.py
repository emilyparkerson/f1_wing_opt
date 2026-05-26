import os
import tempfile
import numpy as np
import matplotlib.pyplot as plt

from pymead.analysis.calc_aero_data import (
    calculate_aero_data,
    MSETSettings,
    MSESSettings,
    MPLOTSettings,
    AirfoilMSETMeshingParameters,
)

from pymead.core.geometry_collection import GeometryCollection

from setup.design_vars import AeroResult
from setup.geometry import (
    load_airfoil_dat,
    get_seed,
    new_airfoil,
    get_coords,
)


# -------------------------------------------------
# CLOSE TRAILING EDGE
# -------------------------------------------------

def close_trailing_edge(coords):
    """
    Force the trailing edge to a single point by averaging the first
    and last points of the Selig-format coordinate array.
    
    In Selig format, coords start at the TE (upper), wrap to the LE,
    and end back at the TE (lower). So coords[0] and coords[-1] are
    the two TE points.
    """
    coords = coords.copy()
    
    te_x = 0.5 * (coords[0, 0] + coords[-1, 0])
    te_y = 0.5 * (coords[0, 1] + coords[-1, 1])
    
    coords[0]  = [te_x, te_y]
    coords[-1] = [te_x, te_y]
    
    return coords


# -------------------------------------------------
# RUN MSES
# -------------------------------------------------

def run_mses(
        design,
        name="candidate_airfoil",
        alpha=-2.0,
        mach=0.2,
        reynolds=1e6,
        plot_geometry=False,
        plot_comparison=False,
        seed_airfoil=""):
    
    geo_col = GeometryCollection()
    
    # Load seed and decompose into camber + thickness
    x_seed, y_seed = load_airfoil_dat(seed_airfoil)
    x_common, camber_seed, thickness_seed, aoa = get_seed(x_seed, y_seed)
    
    # Generate the morphed airfoil
    xu_morph, yu_morph, xl_morph, yl_morph, camber_new, thickness_new, x_cos_coords = new_airfoil(
        thickness_seed,
        x_common,
        design,
        160,
        smoothing_fac=None,
        aoa=aoa,
    )
    
    # Selig-format coordinates
    raw_coords = get_coords(xu_morph, xl_morph, yu_morph, yl_morph, phase=1)
    
    # ⬇ Force a closed trailing edge so MSES doesn't complain
    te_gap_before = np.sqrt(
        (raw_coords[0, 0] - raw_coords[-1, 0])**2 +
        (raw_coords[0, 1] - raw_coords[-1, 1])**2
    )
    raw_coords = close_trailing_edge(raw_coords)
    print(f"  TE gap before closure: {te_gap_before:.5f}c")
    
    # Optional geometry plot
    if plot_geometry:
        plt.figure(figsize=(10, 4))
        plt.plot(raw_coords[:, 0], raw_coords[:, 1], linewidth=2)
        plt.axis("equal")
        plt.grid(True)
        plt.xlabel("x/c")
        plt.ylabel("y/c")
        plt.title(f"{name} — morphed airfoil (closed TE)")
        plt.show()
    
    # Save coordinates to a temp .dat file for pymead
    dat_file = os.path.join(tempfile.gettempdir(), f"{name}_input.dat")
    np.savetxt(dat_file, raw_coords)
    
    # Load into pymead
    polyline = geo_col.add_polyline(source=dat_file)
    airfoil = polyline.add_polyline_airfoil()
    mea = geo_col.add_mea([airfoil])
    coords = np.array(airfoil.coords)
    
    # Optional comparison plot
    if plot_comparison:
        fig, axes = plt.subplots(1, 2, figsize=(14, 4))
        axes[0].plot(x_seed, y_seed)
        axes[0].set_title("Seed Airfoil")
        axes[0].axisls("equal")
        axes[0].grid(True)
        axes[1].plot(coords[:, 0], coords[:, 1])
        axes[1].set_title("Morphed Airfoil")
        axes[1].axis("equal")
        axes[1].grid(True)
        plt.suptitle(f"{name} — geometry comparison")
        plt.show()
    
    # MSES configuration
    mset_settings = MSETSettings(
        multi_airfoil_grid={"Airfoil-1": AirfoilMSETMeshingParameters()},
        airfoil_side_points=200,
    )
    
    mses_settings = MSESSettings(
        xtrs={"Airfoil-1": [0.05, 0.05]},
        Ma=mach,
        Re=reynolds,
        alfa=alpha,
        alfa_Cl_mode=0,
        timeout=500.0,
    )
    
    mplot_settings = MPLOTSettings(Tecplot=False)
    
    # Run MSES
    try:
        print("\nRunning MSES...")
        
        aero_data, logs = calculate_aero_data(
            conn=None,
            airfoil_coord_dir=tempfile.gettempdir(),
            airfoil_name=name,
            mea=mea,
            tool="MSES",
            mset_settings=mset_settings,
            mses_settings=mses_settings,
            mplot_settings=mplot_settings,
            export_Cp=False,
            save_aero_data=True,
        )
        
        if aero_data.get("errored_out", False):
            print("MSES errored out")
            return AeroResult(cl=None, cd=None, coords=coords)
        
        if aero_data.get("timed_out", False):
            print("MSES timed out")
            return AeroResult(cl=None, cd=None, coords=coords)
        
        if not aero_data.get("converged", False):
            print("MSES did not converge")
            return AeroResult(cl=None, cd=None, coords=coords)
        
        cl = aero_data["Cl"]
        cd = aero_data["Cd"]
        print(f"\nCl = {cl:.5f}")
        print(f"Cd = {cd:.5f}")
        
        return AeroResult(cl=cl, cd=cd, coords=coords)
    
    except Exception as e:
        print("\nMSES failed with exception:")
        print(e)
        return AeroResult(cl=None, cd=None, coords=coords)