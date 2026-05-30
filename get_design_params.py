"""Extract designParameters (max_camber, max_camber_loc, max_thickness,
max_thickness_loc) from an airfoil .dat file. Run from project root:

    python get_design_params.py path/to/airfoil.dat
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from setup.geometry import (
    load_airfoil_dat, get_aoa, rotate_airfoil, normalize, get_seed,
)

if len(sys.argv) < 2:
    sys.exit("Usage: python get_design_params.py path/to/airfoil.dat")

path = sys.argv[1]
x, y = load_airfoil_dat(path)

# Run the same de-rotate / LE-shift / normalize pipeline as _element_to_coords
aoa = get_aoa(x, y)
x, y = rotate_airfoil(x, y, aoa)
le_idx = int(np.argmin(x))
x = x - x[le_idx]
y = y - y[le_idx]
x, y = normalize(x, y)

# Extract camber + thickness distributions
x_common, camber, thickness, _ = get_seed(x, y)

# Pull the four design parameters
max_camber_idx = int(np.argmax(np.abs(camber)))
max_thickness_idx = int(np.argmax(thickness))

max_camber = float(camber[max_camber_idx])
max_camber_loc = float(x_common[max_camber_idx])
max_thickness = float(thickness[max_thickness_idx])
max_thickness_loc = float(x_common[max_thickness_idx])

print(f"Design parameters for {path}:")
print(f"    max_camber={abs(max_camber):.5f},")
print(f"    max_camber_loc={max_camber_loc:.5f},")
print(f"    max_thickness={max_thickness:.5f},")
print(f"    max_thickness_loc={max_thickness_loc:.5f},")