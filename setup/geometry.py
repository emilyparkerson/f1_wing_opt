"""
Airfoil geometry - minimal version.

The seed airfoil is given in Selig order, possibly in inverted (rear-wing
/ downforce) orientation: the suction surface points DOWN, so the seed's
bulge is on the negative-y side of the chord line.

We decompose the seed into a camber line c(x) and a thickness
distribution t(x) on a cosine x-grid, build a new (c, t) from the
design, and stitch back into a Selig loop. If the seed was inverted,
the output is flipped vertically so it sits in the same inverted pose
as the seed. MSES sees the wing in its installed (downforce-producing)
pose, and with df = -cl in the scoring, a properly cambered rear wing
gives cl < 0 and df > 0.

The trailing edge is left open with whatever finite gap the seed
thickness implies - MSES handles open TEs natively.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import PchipInterpolator

from setup.track import SECOND_ELM_LOC


# -----------------------------------------------------------------------
# I/O
# -----------------------------------------------------------------------

def load_airfoil_dat(path):
    """Read a Selig .dat / .txt file. Returns (x, y) as 1-D arrays."""
    xs, ys = [], []
    with open(path) as f:
        for line in f:
            parts = line.split()
            if len(parts) != 2:
                continue
            try:
                xs.append(float(parts[0])); ys.append(float(parts[1]))
            except ValueError:
                pass
    return np.asarray(xs), np.asarray(ys)


# -----------------------------------------------------------------------
# Basic utilities
# -----------------------------------------------------------------------

def cosine_spacing(n):
    """n points in [0, 1], denser at the endpoints."""
    return 0.5 * (1.0 - np.cos(np.linspace(0.0, np.pi, n)))


# -----------------------------------------------------------------------
# Seed decomposition
# -----------------------------------------------------------------------

def decompose_seed(x, y, n=200):
    """
    Decompose a Selig-ordered seed into camber and thickness on a
    shared cosine x-grid.

    We work in an upright frame: temporarily flip the seed so that the
    geometric upper surface (the one farther from the camber line in
    +y) is on top. The returned 'inverted' flag tells the caller
    whether the original seed was upside down so the final morphed
    airfoil can be flipped back to match.

    Returns (x_grid, camber_upright, thickness, inverted).
    """
    x = np.asarray(x, float)
    y = np.asarray(y, float)

    le = int(np.argmin(x))

    # Split at LE. Reverse first half so both run LE -> TE.
    xa, ya = x[: le + 1][::-1], y[: le + 1][::-1]
    xb, yb = x[le:], y[le:]

    # In an upright airfoil, the upper surface (higher mean y) appears
    # first in the file (the file starts at TE_upper, descends to LE).
    # If the seed is upright, mean(ya) > mean(yb).
    # If inverted (rear wing), the suction bulge is on the bottom and
    # mean(ya) < mean(yb) -- the file starts at TE_lower.
    inverted = np.mean(ya) <= np.mean(yb)

    if inverted:
        # Flip the seed vertically so we can work in an upright frame.
        ya, yb = -ya, -yb

    # In the (now-upright) frame: ya is the upper surface (high y).
    if np.mean(ya) > np.mean(yb):
        xu, yu, xl, yl = xa, ya, xb, yb
    else:
        xu, yu, xl, yl = xb, yb, xa, ya

    # Drop any non-monotone-x points (rare LE wobbles in raw seed files
    # break PCHIP, which needs strictly increasing x).
    def _strict(x, y):
        keep = [0]
        for i in range(1, len(x)):
            if x[i] > x[keep[-1]]:
                keep.append(i)
        return x[keep], y[keep]
    xu, yu = _strict(xu, yu)
    xl, yl = _strict(xl, yl)

    # Common x-grid from the LE to the shorter of the two TEs.
    x_max = min(xu[-1], xl[-1])
    x_grid = cosine_spacing(n) * x_max

    yu_g = PchipInterpolator(xu, yu)(x_grid)
    yl_g = PchipInterpolator(xl, yl)(x_grid)

    camber = 0.5 * (yu_g + yl_g)
    thickness = yu_g - yl_g

    return x_grid, camber, thickness, inverted


# -----------------------------------------------------------------------
# Morphing
# -----------------------------------------------------------------------

def naca4_camber(x, m, p):
    """NACA 4-digit parabolic camber line. Positive m bows up."""
    if m == 0.0 or p == 0.0 or p == 1.0:
        return np.zeros_like(x)
    fwd = m / p**2 * (2*p*x - x**2)
    aft = m / (1 - p)**2 * ((1 - 2*p) + 2*p*x - x**2)
    return np.where(x < p, fwd, aft)


def warp_thickness(t_seed, x_grid, t_max_new, x_t_new):
    """
    Warp seed thickness t_seed(x_grid) to have peak t_max_new at x_t_new.

    Piecewise-linear x-warp mapping the seed peak location to x_t_new
    with the endpoints fixed. Amplitude is rescaled to hit t_max_new.
    """
    t_seed = np.asarray(t_seed)
    x_grid = np.asarray(x_grid)
    L = x_grid[-1]

    i_peak = int(np.argmax(np.abs(t_seed)))
    x_peak = x_grid[i_peak]
    t_peak = t_seed[i_peak]
    if t_peak == 0.0:
        return np.zeros_like(x_grid)

    def w_inv(x):
        u = np.empty_like(x)
        left = x < x_t_new
        u[left]  = x[left] * (x_peak / x_t_new)
        u[~left] = x_peak + (x[~left] - x_t_new) * (L - x_peak) / (L - x_t_new)
        return np.clip(u, x_grid[0], x_grid[-1])

    t_amp = t_seed * (t_max_new / t_peak)
    return PchipInterpolator(x_grid, t_amp)(w_inv(x_grid))


# -----------------------------------------------------------------------
# Build airfoil from (camber, thickness)
# -----------------------------------------------------------------------

def build_loop(x_grid, camber, thickness):
    """
    Assemble a closed Selig loop from camber and thickness in upright
    orientation:

        y_upper = c + t/2  (bulge on top, suction surface on top)
        y_lower = c - t/2

        Selig order: TE_upper -> LE -> TE_lower

    Caller flips the result vertically if the seed was inverted.
    """
    half_t = 0.5 * thickness
    yu = camber + half_t
    yl = camber - half_t

    upper = np.column_stack([x_grid[::-1], yu[::-1]])   # TE -> LE
    lower = np.column_stack([x_grid[1:],   yl[1:]])     # skip duplicate LE
    return np.vstack([upper, lower])


# -----------------------------------------------------------------------
# Top-level
# -----------------------------------------------------------------------

def new_airfoil(design, seed_path, n=160):
    """
    Build a morphed airfoil from the seed at seed_path.

    Parameters
    ----------
    design : has fields max_camber, max_camber_loc, max_thickness, max_thickness_loc
    seed_path : path to a Selig-format .dat / .txt file
    n : points per surface (~160 is what MSES is happy with)

    Returns
    -------
    coords : (2n - 1, 2) array, Selig order, open TE.
        If the seed was inverted (rear-wing orientation), the output is
        flipped vertically to match.
    """
    x_seed, y_seed = load_airfoil_dat(seed_path)
    x_grid, _, t_seed, inverted = decompose_seed(x_seed, y_seed, n=200)

    # Resample seed thickness onto the output grid.
    x_out = cosine_spacing(n) * x_grid[-1]
    t_seed_out = PchipInterpolator(x_grid, t_seed)(x_out)

    # New camber: analytic NACA-4 (bows up in the upright frame).
    camber = naca4_camber(x_out / x_grid[-1],
                          design.max_camber, design.max_camber_loc)

    # New thickness from seed warp. Force non-negative.
    thickness = np.abs(warp_thickness(t_seed_out, x_out,
                                      design.max_thickness, design.max_thickness_loc))

    # Re-add the seed's chord-line slope so the morphed airfoil keeps
    # the seed's installed angle. (After temporarily flipping for
    # decomposition, we still want the same chord angle in the upright
    # frame; flipping back later will negate y including this slope.)
    le = int(np.argmin(x_seed))
    te = int(np.argmax(x_seed))
    dx = x_seed[te] - x_seed[le]
    dy = y_seed[te] - y_seed[le]
    if dx > 0:
        slope = dy / dx
        if inverted:
            # Seed was inverted; the slope we measured is in the inverted
            # frame. In our upright working frame, the chord goes the
            # other way.
            slope = -slope
        camber = camber + slope * x_out

    coords = build_loop(x_out, camber, thickness)

    # If the seed was inverted, flip the output back so it matches.
    if inverted:
        coords = coords.copy()
        coords[:, 1] = -coords[:, 1]

    return coords


# -----------------------------------------------------------------------
# Phase 2 / 3 placement helpers
# -----------------------------------------------------------------------

def place_second_element(coords, scale=0.435,
                         h=SECOND_ELM_LOC["horizontal"],
                         v=SECOND_ELM_LOC["vertical"]):
    out = coords * scale
    out[:, 0] += h
    out[:, 1] += v
    return out


def rotate_about(coords, angle_deg, pivot):
    a = np.radians(angle_deg)
    R = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
    return (coords - np.asarray(pivot)) @ R.T + np.asarray(pivot)


# -----------------------------------------------------------------------
# Plotting (kept for phase1.py compatibility)
# -----------------------------------------------------------------------

def plot_airfoil(design, seed_path, phase, fixed_el_pts=None, aoa_phase3=0.0):
    coords = new_airfoil(design, seed_path)
    if phase == 2:
        coords = place_second_element(coords)
    if phase == 3 and aoa_phase3 != 0.0:
        le = coords[int(np.argmin(coords[:, 0]))]
        coords = rotate_about(coords, aoa_phase3, pivot=le)

    plt.figure()
    if fixed_el_pts is not None:
        plt.plot(fixed_el_pts[:, 0], fixed_el_pts[:, 1], "-")
    plt.plot(coords[:, 0], coords[:, 1], "-")
    plt.xlabel("x/c"); plt.ylabel("y/c")
    plt.grid(True); plt.axis("equal")
    plt.show()
