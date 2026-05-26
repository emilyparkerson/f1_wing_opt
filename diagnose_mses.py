"""
Diagnostic: run a single MSES call on the seed airfoil with verbose output.

This bypasses optimization / scoring / training-data generation and just
asks: can MSES converge on the seed itself, with no morph, no design
sweep? If not, where does it fail?

Run from the project root:
    python diagnose_mses.py
"""

import os, sys, tempfile, traceback
import numpy as np

# Adjust if your paths differ:
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from phase1.phase1 import P1_IB_CONFIG
from setup.geometry import new_airfoil, load_airfoil_dat


def main():
    cfg = P1_IB_CONFIG
    design = cfg["seed_design"]
    seed_path = cfg["seed_airfoil"]

    print("=" * 60)
    print("STEP 1: Load and inspect raw seed")
    print("=" * 60)
    x, y = load_airfoil_dat(str(seed_path))
    print(f"  raw seed points:     {len(x)}")
    print(f"  x range:             [{x.min():.4f}, {x.max():.4f}]")
    print(f"  y range:             [{y.min():.4f}, {y.max():.4f}]")
    print(f"  first point:         ({x[0]:.4f}, {y[0]:.4f})")
    print(f"  last point:          ({x[-1]:.4f}, {y[-1]:.4f})")
    print(f"  TE gap raw:          {np.hypot(x[0]-x[-1], y[0]-y[-1]):.4f}")

    print("\n" + "=" * 60)
    print("STEP 2: Build morphed airfoil at seed design (should be ~no-op)")
    print("=" * 60)
    coords = new_airfoil(design, str(seed_path), n=160)
    print(f"  output points:       {len(coords)}")
    print(f"  x range:             [{coords[:,0].min():.4f}, {coords[:,0].max():.4f}]")
    print(f"  y range:             [{coords[:,1].min():.4f}, {coords[:,1].max():.4f}]")
    print(f"  TE gap:              {np.linalg.norm(coords[0] - coords[-1]):.4f}")
    le = int(np.argmin(coords[:, 0]))
    print(f"  LE at index:         {le}")

    # Save coords so we can look at them outside this script too
    np.savetxt("diag_coords.dat", coords)
    print(f"  saved to:            diag_coords.dat")

    print("\n" + "=" * 60)
    print("STEP 3: Hand to pymead and see what it does")
    print("=" * 60)
    try:
        from pymead.core.geometry_collection import GeometryCollection
        dat_file = os.path.join(tempfile.gettempdir(), "diag_input.dat")
        np.savetxt(dat_file, coords)

        geo_col = GeometryCollection()
        polyline = geo_col.add_polyline(source=dat_file)
        airfoil = polyline.add_polyline_airfoil()
        mea = geo_col.add_mea([airfoil])
        pcoords = np.array(airfoil.coords)
        print(f"  pymead accepted:     {pcoords.shape[0]} points")
        print(f"  pymead x range:      [{pcoords[:,0].min():.4f}, {pcoords[:,0].max():.4f}]")
        print(f"  pymead first/last:   ({pcoords[0,0]:.4f},{pcoords[0,1]:.4f}) "
              f"-> ({pcoords[-1,0]:.4f},{pcoords[-1,1]:.4f})")
    except Exception as e:
        print(f"  pymead FAILED at load: {e}")
        traceback.print_exc()
        return

    print("\n" + "=" * 60)
    print("STEP 4: Run MSES")
    print("=" * 60)
    try:
        from pymead.analysis.calc_aero_data import (
            calculate_aero_data, MSETSettings, MSESSettings,
            AirfoilMSETMeshingParameters,
        )

        mset = MSETSettings(
            multi_airfoil_grid={"Airfoil-1": AirfoilMSETMeshingParameters()},
            airfoil_side_points=160,
        )
        mses = MSESSettings(
            xtrs={"Airfoil-1": [0.05, 0.05]},
            Ma=0.2, Re=1e6, alfa=0.0, alfa_Cl_mode=0,
            timeout=120.0,
        )
        # Pymead 2.0.0b13 bug workaround: pass a dict with the capitalized
        # 'Streamline_Grid' key that calc_aero_data actually reads.
        mplot = {
            "timeout": 15.0, "grid_stats": False, "Mach": False,
            "Streamline_Grid": False, "Grid": False, "Grid_Zoom": False,
            "flow_field": False, "Tecplot": False, "Paraview": False,
            "CPK": False,
        }

        print(f"  alpha = 0.0, Mach = 0.2, Re = 1e6")
        print(f"  calling calculate_aero_data...")
        aero_data, logs = calculate_aero_data(
            conn=None,
            airfoil_coord_dir=tempfile.gettempdir(),
            airfoil_name="diag",
            mea=mea,
            tool="MSES",
            mset_settings=mset,
            mses_settings=mses,
            mplot_settings=mplot,
            export_Cp=False,
            save_aero_data=True,
        )
        print(f"\n  aero_data keys:      {list(aero_data.keys())}")
        for k in ("errored_out", "timed_out", "converged"):
            print(f"  {k:20s} {aero_data.get(k)}")
        for k in ("Cl", "Cd", "Cm"):
            v = aero_data.get(k)
            print(f"  {k:20s} {v}")

        print(f"\n  --- LOGS ---")
        if isinstance(logs, dict):
            for k, v in logs.items():
                print(f"\n  [{k}]")
                if isinstance(v, str):
                    print(v[-2000:])  # last 2000 chars per log section
                else:
                    print(repr(v)[:500])
        else:
            print(str(logs)[-2000:])
    except Exception as e:
        print(f"  MSES call raised: {type(e).__name__}: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()