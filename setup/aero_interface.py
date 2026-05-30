"""
---------------------------------------------------------------------
AERO INTERFACE
---------------------------------------------------------------------
Build morphed geometry via geometry.py, run MSES through pymead,
return Cl/Cd.

Morph elements: the seed file is used only to extract the unit-chord
thickness distribution. The morph runs at aoa=0, so the output sits
with LE at origin and chord on x-axis. Then we scale to the spec's
`chord`, rotate by `installed_aoa_deg` about the LE, and translate to
`le_position`. No de-rotate / re-rotate round-trip.

Fixed elements: loaded straight from the .dat file, no transformation.
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
    get_seed,
    new_airfoil,
    get_coords,
    scale_airfoil,
    translate_airfoil,
    rotate_airfoil_phase3,
    rotate_airfoil,
    normalize,
    get_aoa
)


# Shared MSES-settings / run / failure-check block
def _run_mses_on_mea(mea, pymead_coords, names, name, alpha, mach, reynolds,
                     target_cl=None, xtr_upper=0.05, xtr_lower=0.05):
    mset = MSETSettings(
        multi_airfoil_grid={
            nm: AirfoilMSETMeshingParameters(dsLE_dsAvg=0.25, dsTE_dsAvg=0.70)
            for nm in names
        },
        airfoil_side_points=180,    # was 120; matches screenshot
    )
    if target_cl is None:
        mses = MSESSettings(
            #xtrs={nm: [0.05, 0.05] for nm in names},   # free transition (was 1.0),
            xtrs={nm: [xtr_upper, xtr_lower] for nm in names},
            Ma=mach, Re=reynolds, alfa=alpha,
            alfa_Cl_mode=0,
            timeout=60.0,                             # was 800.0
            iterations=300,                           # new; was pymead default 100
        )
    else:
        mses = MSESSettings(
            xtrs={nm: [xtr_upper, xtr_lower] for nm in names},
            Ma=mach, Re=reynolds,
            alfa=alpha,
            Cl=target_cl,
            alfa_Cl_mode=1,
            timeout=60.0,
            iterations=300,
        )
    # pymead 2.0.0b13 bug workaround: consumer reads capitalized keys.
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

    fail = AeroResult(cl=None, cd=None, coords=pymead_coords)
    try:
        print("\nRunning MSES...")
        aero_data, logs = calculate_aero_data(
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
        if not aero_data.get("converged"):
            print("---- MSES log tail ----")
            for tool, path in logs.items():
                if path and os.path.exists(path):
                    with open(path) as f:
                        tail = f.readlines()[-50:]
                    print(f"\n[{tool}] last 50 lines of {path}:")
                    print("".join(tail))
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


# Single element (legacy phase-1 path; also used for seed-only tests)
def run_mses(design,
             name="candidate_airfoil",
             alpha=0.0,
             mach=0.08,
             reynolds=0.7e6,
             seed_airfoil="",
             phase=1,
             aoa_phase3=0.0,
             plot_geometry=False,
             plot_comparison=False,
             target_cl=None):

    # Geometry: load seed -> decompose -> morph flat -> assemble loop
    x_seed, y_seed = load_airfoil_dat(seed_airfoil)
    x_common, camber_seed, thickness_seed, aoa_seed = get_seed(x_seed, y_seed)
    print(f"derotated to {np.degrees(aoa_seed):+.2f} deg (seed's detected angle, removed)")
    print(f"re-rotated to 0.00 deg (morphing flat; alpha={alpha} controls flow angle)")

    xu, yu, xl, yl, _, _, _ = new_airfoil(
        thickness_seed=thickness_seed,
        x_common=x_common,
        designParameters=design,
        n_points=160,
        smoothing_fac=None,
        aoa=0.0,
    )
    coords = get_coords(xu, xl, yu, yl, phase=phase, aoa_deg=aoa_phase3)

    if plot_geometry:
        plt.figure(figsize=(10, 4))
        plt.plot(coords[:, 0], coords[:, 1], lw=2)
        plt.axis("equal"); plt.grid(True)
        plt.xlabel("x/c"); plt.ylabel("y/c"); plt.title(name)
        plt.show()

    if plot_comparison:
        fig, axes = plt.subplots(1, 2, figsize=(14, 4))
        axes[0].plot(x_seed, y_seed)
        axes[0].set_title("Seed Airfoil"); axes[0].axis("equal"); axes[0].grid(True)
        axes[1].plot(coords[:, 0], coords[:, 1])
        axes[1].set_title("Morphed Airfoil"); axes[1].axis("equal"); axes[1].grid(True)
        plt.suptitle(f"{name} - geometry comparison"); plt.show()

    # Register with pymead (single element)
    dat_file = os.path.join(tempfile.gettempdir(), f"{name}_input.dat")
    np.savetxt(dat_file, coords)

    geo_col = GeometryCollection()
    polyline = geo_col.add_polyline(source=dat_file)
    airfoil = polyline.add_polyline_airfoil()
    mea = geo_col.add_mea([airfoil])
    pymead_coords = np.array(airfoil.coords)

    return _run_mses_on_mea(
        mea, pymead_coords, ["Airfoil-1"], name, alpha, mach, reynolds,
        target_cl=target_cl,
    )


# Multi-element
# Element spec keys (read by _element_to_coords):
#   morph:
#     "role": "morph"
#     "seed_airfoil": path -- shape source (thickness distribution)
#     "chord": float -- actual chord length to scale to (default 1.0)
#     "le_position": (x, y) -- where the LE should land (default (0,0))
#     "installed_aoa_deg": float -- chord angle in global frame (default 0)
#   fixed:
#     "role": "fixed"
#     "coords_path": path -- loaded as-is, no transformation

def _element_to_coords(spec, design=None):
    """Turn one element spec into an (N,2) Selig coordinate loop."""

    if spec["role"] == "morph":
        x_seed, y_seed = load_airfoil_dat(str(spec["seed_airfoil"]))
        aoa = get_aoa(x_seed, y_seed)
        x_seed, y_seed = rotate_airfoil(x_seed, y_seed, aoa)
        # Shift LE to origin -- rotate_airfoil pivots about (0,0), not LE.
        le_idx = int(np.argmin(x_seed))
        x_seed = x_seed - x_seed[le_idx]
        y_seed = y_seed - y_seed[le_idx]
        x_seed, y_seed = normalize(x_seed, y_seed)

        x_common, _, thickness_seed, _ = get_seed(x_seed, y_seed)
        xu, yu, xl, yl, _, _, _ = new_airfoil(
            thickness_seed=thickness_seed,
            x_common=x_common,
            designParameters=design,
            n_points=160,
            smoothing_fac=None,
            aoa=0.0,
        )
        coords = get_coords(xu, xl, yu, yl, phase=1)

        # Explicit placement from the spec.
        chord = spec.get("chord", 1.0)
        coords = scale_airfoil(coords, scale=chord, origin=(0.0, 0.0))

        installed = spec.get("installed_aoa_deg", 0.0)
        if installed != 0.0:
            coords = rotate_airfoil_phase3(coords, installed, pivot=(0.0, 0.0))

        le_pos = spec.get("le_position", (0.0, 0.0))
        coords = translate_airfoil(coords, le_pos[0], le_pos[1])

    elif spec["role"] == "fixed":
        x, y = load_airfoil_dat(str(spec["coords_path"]))
        coords = np.column_stack([x, y])

    else:
        raise ValueError(f"Unknown element role: {spec['role']}")

    return coords


def run_mses_elements(design, elements,
                      name="candidate_airfoil",
                      alpha=0.0,
                      mach=0.08,
                      reynolds=0.7e6,
                      plot_geometry=False,
                      plot_comparison=False,
                      target_cl=None,
                      xtr_upper=0.05, xtr_lower=0.05):
    # Build coords for every element, in config order.
    all_coords = []
    for spec in elements:
        d = design if spec["role"] == "morph" else None
        all_coords.append(_element_to_coords(spec, design=d))

    if plot_geometry:
        plt.figure(figsize=(10, 4))
        for c in all_coords:
            plt.plot(c[:, 0], c[:, 1], lw=2)
        plt.axis("equal"); plt.grid(True)
        plt.xlabel("x/c"); plt.ylabel("y/c"); plt.title(name)
        plt.show()

    # Register every element with pymead, in config order.
    # First in the list -> Airfoil-1, second -> Airfoil-2, etc.
    geo_col = GeometryCollection()
    airfoils = []
    for i, coords in enumerate(all_coords):
        dat_i = os.path.join(tempfile.gettempdir(), f"{name}_el{i}.dat")
        np.savetxt(dat_i, coords)
        pl = geo_col.add_polyline(source=dat_i)
        airfoils.append(pl.add_polyline_airfoil())
    mea = geo_col.add_mea(airfoils)
    pymead_coords = np.vstack([np.array(a.coords) for a in airfoils])

    names = [f"Airfoil-{i+1}" for i in range(len(airfoils))]
    return _run_mses_on_mea(
        mea, pymead_coords, names, name, alpha, mach, reynolds,
        target_cl=target_cl,
        xtr_upper=xtr_upper, xtr_lower=xtr_lower,      
    )