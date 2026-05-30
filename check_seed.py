import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from setup.geometry import load_airfoil_dat

x, y = load_airfoil_dat("phase2/inboard_seed_phase2.dat")
chord = float(np.max(x) - np.min(x))
le_idx = int(np.argmin(x))
te_idx = int(np.argmax(x))
le_x, le_y = float(x[le_idx]), float(y[le_idx])
te_x, te_y = float(x[te_idx]), float(y[te_idx])
chord_angle = np.degrees(np.arctan2(te_y - le_y, te_x - le_x))
print(f'"chord":             {chord:.5f},')
print(f'"le_position":       ({le_x:.5f}, {le_y:.5f}),')
print(f'"installed_aoa_deg": {chord_angle:.2f},')