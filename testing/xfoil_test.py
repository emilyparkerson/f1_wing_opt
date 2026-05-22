print("SCRIPT STARTED")

import os
import re
import subprocess
import textwrap
import numpy as np

from setup.design_vars import AeroResult
from setup.geometry import (
    load_airfoil_dat,
    get_seed,
    new_airfoil,
    get_coords,
)

XFOIL_EXE = r"C:\Users\ecpar\Documents\XFOIL6.99\xfoil.exe"
XFOIL_WORKDIR = r"C:\xfoil_tmp"
XFOIL_ITER = 200
XFOIL_TIMEOUT = 45

os.makedirs(XFOIL_WORKDIR, exist_ok=True)


def normalize_coords(coords):
    coords = coords.copy()
    x_min = coords[:, 0].min()
    x_max = coords[:, 0].max()
    chord = x_max - x_min

    coords[:, 0] = (coords[:, 0] - x_min) / chord
    coords[:, 1] = coords[:, 1] / chord

    return coords


def force_te_midpoint(coords):
    coords = coords.copy()

    te_x = 0.5 * (coords[0, 0] + coords[-1, 0])
    te_y = 0.5 * (coords[0, 1] + coords[-1, 1])

    coords[0] = [te_x, te_y]
    coords[-1] = [te_x, te_y]

    return coords


def make_geometry_airfoil(design, seed_airfoil):
    x_seed, y_seed = load_airfoil_dat(seed_airfoil)

    x_common, camber_seed, thickness_seed, aoa = get_seed(
        x_seed,
        y_seed,
    )

    (
        xu_morph,
        yu_morph,
        xl_morph,
        yl_morph,
        camber_new,
        thickness_new,
        x_cos_coords,
    ) = new_airfoil(
        thickness_seed,
        x_common,
        design,
        160,
        smoothing_fac=None,
        aoa=aoa,
    )

    coords = get_coords(
        xu_morph,
        xl_morph,
        yu_morph,
        yl_morph,
        phase=1,
    )

    coords = normalize_coords(coords)

    return coords


def _run_xfoil(coords, alpha, reynolds, mach):
    dat_path = os.path.join(XFOIL_WORKDIR, "test_airfoil.dat")
    script_path = os.path.join(XFOIL_WORKDIR, "xfoil_script.txt")

    for path in [dat_path, script_path]:
        if os.path.exists(path):
            os.remove(path)

    np.savetxt(dat_path, coords, fmt="%.8f")

    dat_path_xfoil = dat_path.replace("\\", "/")

    script = textwrap.dedent(f"""
    PLOP
    G F

    LOAD {dat_path_xfoil}

    PANE

    OPER
    VISC {reynolds:.0f}
    MACH {mach:.4f}
    ITER {XFOIL_ITER}
    ALFA {alpha:.4f}

    QUIT
    """)

    with open(script_path, "w", newline="\n") as f:
        f.write(script)

    cmd = f'cmd /c ""{XFOIL_EXE}" < "{script_path}""'

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=XFOIL_TIMEOUT,
            shell=True,
            cwd=XFOIL_WORKDIR,
        )
    except subprocess.TimeoutExpired:
        print("XFOIL timed out.")
        return {}

    stdout = proc.stdout

    matches = re.findall(
        r"CL\s*=\s*([-+]?\d*\.\d+|[-+]?\d+).*?CD\s*=\s*([-+]?\d*\.\d+|[-+]?\d+)",
        stdout,
        flags=re.DOTALL,
    )

    if matches:
        cl, cd = matches[-1]
        return {
            "alpha": alpha,
            "cl": float(cl),
            "cd": float(cd),
        }

    print("Could not parse CL/CD from XFOIL output.")
    return {}


def run_xfoil(
    design,
    alpha=-2.0,
    mach=0.23,
    reynolds=1e6,
    plot_geometry=False,
    seed_airfoil="",
):
    import matplotlib.pyplot as plt

    coords = make_geometry_airfoil(
        design=design,
        seed_airfoil=seed_airfoil,
    )

    print(f"x range: {coords[:, 0].min():.5f} to {coords[:, 0].max():.5f}")
    print(f"y range: {coords[:, 1].min():.5f} to {coords[:, 1].max():.5f}")
    print(f"first point: {coords[0]}")
    print(f"last point:  {coords[-1]}")

    if plot_geometry:
        plt.figure(figsize=(10, 4))
        plt.plot(coords[:, 0], coords[:, 1], "-o", markersize=2)
        plt.axis("equal")
        plt.grid(True)
        plt.xlabel("x/c")
        plt.ylabel("y/c")
        plt.title("Geometry.py morphed airfoil")
        plt.show()

    result = _run_xfoil(
        coords=coords,
        alpha=alpha,
        reynolds=reynolds,
        mach=mach,
    )

    if not result:
        return AeroResult(cl=None, cd=None, coords=coords)

    cl = result["cl"]
    cd = result["cd"]

    print("\nXFOIL RESULT")
    print(f"alpha = {result['alpha']:.4f}")
    print(f"Cl    = {cl:.6f}")
    print(f"Cd    = {cd:.6f}")

    return AeroResult(
        cl=cl,
        cd=cd,
        coords=coords,
    )


run_mses = run_xfoil


if __name__ == "__main__":
    from setup.design_vars import designParameters

    design = designParameters(
        max_camber=0.04358,
        max_camber_loc=0.635,
        max_thickness=0.17569,
        max_thickness_loc=0.2434,
    )

    result = run_xfoil(
        design=design,
        alpha=-2.0,
        mach=0.23,
        reynolds=1e6,
        plot_geometry=True,
        seed_airfoil="phase1/inboard_seed_phase1.txt",
    )

    print(result)