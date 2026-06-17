"""
Run the morph pipeline at the seed design at unit chord and plot the
intermediate stages. Helps locate where the LE eye is being introduced.

Run from project root:
    python diagnose_morph.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
from setup.geometry import (
    load_airfoil_dat, get_seed, new_airfoil, get_coords,
)
from phase2.phase2 import P2_RE_OB_CONFIG

morph_spec = P2_RE_OB_CONFIG["elements"][0]
seed_path = str(morph_spec["seed_airfoil"])
design = P2_RE_OB_CONFIG["seed_design"]

# Stage 0: raw seed file
x_seed, y_seed = load_airfoil_dat(seed_path)

# Stage 1: get_seed (decompose to thickness/camber at unit chord)
x_common, camber_seed, thickness_seed, aoa_seed = get_seed(x_seed, y_seed)

# Stage 2: new_airfoil (morph at aoa=0)
xu, yu, xl, yl, camber_new, thickness_new, x_cos = new_airfoil(
    thickness_seed=thickness_seed, x_common=x_common,
    designParameters=design, n_points=160, smoothing_fac=None, aoa=0.0,
)

# Stage 3: get_coords (stitch upper + lower into a Selig loop)
coords = get_coords(xu, xl, yu, yl, phase=1)

# Plot everything
fig, axes = plt.subplots(2, 2, figsize=(14, 9))

axes[0, 0].plot(x_seed, y_seed, "-o", ms=2)
axes[0, 0].set_title("Stage 0: raw seed file")
axes[0, 0].axis("equal"); axes[0, 0].grid(True)

axes[0, 1].plot(x_common, camber_seed, label="seed camber")
axes[0, 1].plot(x_common, thickness_seed, label="seed thickness")
axes[0, 1].plot(x_cos, camber_new, "--", label="new camber")
axes[0, 1].plot(x_cos, thickness_new, "--", label="new thickness")
axes[0, 1].set_title("Stage 1-2: camber/thickness distributions")
axes[0, 1].grid(True); axes[0, 1].legend()

axes[1, 0].plot(xu, yu, "-o", ms=2, label="upper")
axes[1, 0].plot(xl, yl, "-o", ms=2, label="lower")
axes[1, 0].set_title("Stage 2: morphed upper/lower surfaces (before stitch)")
axes[1, 0].axis("equal"); axes[1, 0].grid(True); axes[1, 0].legend()
# zoom in on LE
ax_inset = axes[1, 0].inset_axes([0.05, 0.55, 0.4, 0.4])
ax_inset.plot(xu, yu, "-o", ms=2)
ax_inset.plot(xl, yl, "-o", ms=2)
ax_inset.set_xlim(-0.005, 0.05); ax_inset.set_ylim(-0.04, 0.04)
ax_inset.set_title("LE zoom"); ax_inset.grid(True)

axes[1, 1].plot(coords[:, 0], coords[:, 1], "-o", ms=2)
axes[1, 1].set_title("Stage 3: final Selig loop")
axes[1, 1].axis("equal"); axes[1, 1].grid(True)
# zoom on LE
ax_inset2 = axes[1, 1].inset_axes([0.05, 0.55, 0.4, 0.4])
ax_inset2.plot(coords[:, 0], coords[:, 1], "-o", ms=2)
ax_inset2.set_xlim(-0.005, 0.05); ax_inset2.set_ylim(-0.04, 0.04)
ax_inset2.set_title("LE zoom"); ax_inset2.grid(True)

plt.tight_layout()
plt.savefig("/tmp/morph_diagnose.png" if os.name != "nt" else "morph_diagnose.png", dpi=110)
plt.show()

# Print some numbers
print(f"detected seed AoA: {np.degrees(aoa_seed):+.2f} deg")
print(f"morphed coords: N={len(coords)}, x range [{coords[:,0].min():.4f}, {coords[:,0].max():.4f}]")
# check for crossings near LE
n_le = 20
# find segments that go backwards in arc-length
v = np.diff(coords, axis=0)
norms = np.linalg.norm(v, axis=1)
print(f"min segment length: {norms.min():.5f}")
print(f"max segment length: {norms.max():.5f}")
# look for x going backwards on upper or lower
print(f"\nfirst 10 upper x values: {xu[:10]}")
print(f"first 10 lower x values: {xl[:10]}")