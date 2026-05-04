"""
Monaco F1 track curvature analysis.

Pipeline:
  1. Mask out the red track line.
  2. Skeletonize to a 1-pixel-wide centerline.
  3. Order pixels into a continuous path by walking the skeleton.
  4. Smooth with a spline.
  5. Compute signed curvature kappa = (x'y'' - y'x'') / (x'^2 + y'^2)^1.5.
  6. Classify each sample as STRAIGHT or CURVED by thresholding |kappa|.
  7. Report arc lengths and plot.
"""

import numpy as np
import cv2
from skimage.morphology import skeletonize
from scipy.interpolate import splprep, splev
import matplotlib.pyplot as plt
from collections import defaultdict

OUT_PATH = "track_curvature_result.png"

# ---------------------------------------------------------------
# 1. Load image and mask the red rack
# ---------------------------------------------------------------
img = cv2.imread("preview.png")
img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Red wraps around hue=0 in HSV, so we need two ranges.
lower_red1 = np.array([0,   120, 80])
upper_red1 = np.array([10,  255, 255])
lower_red2 = np.array([170, 120, 80])
upper_red2 = np.array([180, 255, 255])
mask = cv2.inRange(hsv, lower_red1, upper_red1) | cv2.inRange(hsv, lower_red2, upper_red2)

# Clean up small specks; close small gaps.
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel, iterations=1)

# Keep only the largest connected component (the track itself).
num, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
if num > 1:
    biggest = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
    mask = np.where(labels == biggest, 255, 0).astype(np.uint8)

# ---------------------------------------------------------------
# 2. Skeletonize so we have a 1-pixel-wide centerline
# ---------------------------------------------------------------
skel = skeletonize(mask > 0)

# ---------------------------------------------------------------
# 3. Order skeleton pixels into a path by walking neighbors.
# ---------------------------------------------------------------
ys, xs = np.where(skel)
points = set(zip(ys.tolist(), xs.tolist()))

neighbors = defaultdict(list)
offsets = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
for (y, x) in points:
    for dy, dx in offsets:
        if (y+dy, x+dx) in points:
            neighbors[(y,x)].append((y+dy, x+dx))

start = min(points, key=lambda p: len(neighbors[p]))

path = [start]
visited = {start}
current = start
prev = None
while True:
    nbrs = [n for n in neighbors[current] if n not in visited]
    if not nbrs:
        nbrs_closing = [n for n in neighbors[current] if n == start and len(path) > 20]
        if nbrs_closing:
            path.append(start)
        break
    if prev is None:
        nxt = nbrs[0]
    else:
        vprev = (current[0]-prev[0], current[1]-prev[1])
        def score(n):
            v = (n[0]-current[0], n[1]-current[1])
            return v[0]*vprev[0] + v[1]*vprev[1]
        nxt = max(nbrs, key=score)
    visited.add(nxt)
    path.append(nxt)
    prev = current
    current = nxt

path = np.array(path, dtype=float)
print(f"Skeleton path length: {len(path)} pixels")

# ---------------------------------------------------------------
# 4. Smooth with a spline.
# ---------------------------------------------------------------
x_raw = path[:, 1]
y_raw = path[:, 0]

tck, u = splprep([x_raw, y_raw], s=len(x_raw)*0.5, per=False)
u_fine = np.linspace(0, 1, 3000)
x_s, y_s = splev(u_fine, tck)

dx,  dy  = splev(u_fine, tck, der=1)
ddx, ddy = splev(u_fine, tck, der=2)

# ---------------------------------------------------------------
# 5. Curvature and arc length
# ---------------------------------------------------------------
kappa = (dx*ddy - dy*ddx) / np.power(dx*dx + dy*dy, 1.5)

ds = np.sqrt(np.diff(x_s)**2 + np.diff(y_s)**2)
ds = np.concatenate([[ds[0]], ds])
total_length_px = ds.sum()

# ---------------------------------------------------------------
# 6. Classify straight vs curved (geometry only).
# ---------------------------------------------------------------
K_THR = 0.015
is_curved_raw = np.abs(kappa) > K_THR

# Convert to metres using real Monaco length.
REAL_LENGTH_M = 3337.0
px_per_m = total_length_px / REAL_LENGTH_M

# ---------------------------------------------------------------
# 7. Buffer the curved mask along ARC LENGTH.
#
#    Braking distance for each corner scales with the PEAK curvature
#    of that corner: sharper turns need you to scrub more speed, so
#    the braking zone is longer.
#
#    Physics motivation:
#      Corner apex speed      v_apex ~ sqrt(a_lat / kappa_max)
#      Straight-line top speed v_top  (assumed constant)
#      Braking distance        d_brake = (v_top^2 - v_apex^2) / (2 a_brake)
#                                      = (v_top^2 - a_lat/kappa_max) / (2 a_brake)
#
#    So tighter corners (larger kappa_max) => smaller v_apex
#    => longer braking distance. We clamp to [BRAKE_MIN_M, BRAKE_MAX_M].
# ---------------------------------------------------------------
V_TOP       = 85.0     # m/s  (~305 km/h, Monaco tunnel-ish top speed)
A_LAT       = 25.0     # m/s^2 lateral grip (~2.5 g, F1-ish)
A_BRAKE     = 50.0     # m/s^2 braking decel (~4.5 g, F1-ish)
BRAKE_MIN_M = 10.0     # floor so even gentle kinks get a small buffer
BRAKE_MAX_M = 100.0    # ceiling so noise spikes don't blow up

ACCEL_M     = 15.0     # metres of throttle pickup after a corner (fixed)

px_per_m = total_length_px / REAL_LENGTH_M

def corner_brake_distance_m(kappa_max_per_px):
    """Brake distance in metres given the peak curvature of the
    upcoming corner (expressed in 1/pixel)."""
    # Convert curvature from 1/pixel to 1/metre.
    kappa_per_m = kappa_max_per_px * px_per_m
    # Apex speed from lateral grip limit.
    v_apex_sq = A_LAT / max(kappa_per_m, 1e-6)
    # Can't apex faster than top speed.
    v_apex_sq = min(v_apex_sq, V_TOP**2)
    # Braking from v_top to v_apex.
    d = max(V_TOP**2 - v_apex_sq, 0.0) / (2.0 * A_BRAKE)
    return float(np.clip(d, BRAKE_MIN_M, BRAKE_MAX_M))

def dilate_along_arclength_per_corner(mask_bool, kappa_abs, ds,
                                       brake_fn, after_px):
    """Expand each True run of mask_bool. Upstream buffer is computed
    from that run's peak |kappa| via brake_fn (returns metres).
    Downstream buffer is a fixed after_px."""
    n = len(mask_bool)
    out = mask_bool.copy()
    corner_info = []   # (start_idx, end_idx, kappa_max, brake_m)

    m_int = mask_bool.astype(np.int8)
    diffs = np.diff(m_int, prepend=0, append=0)
    starts = np.where(diffs ==  1)[0]
    ends   = np.where(diffs == -1)[0]

    for s, e in zip(starts, ends):
        # Peak curvature inside this corner (1/px).
        k_max = float(kappa_abs[s:e].max())
        brake_m  = brake_fn(k_max)
        brake_px = brake_m * px_per_m

        # Walk backwards from s until we've accumulated brake_px of arc length.
        acc = 0.0
        i = s
        while i > 0 and acc < brake_px:
            i -= 1
            acc += ds[i]
        out[i:s] = True

        # Walk forwards from e by a fixed after_px.
        acc = 0.0
        j = e
        while j < n and acc < after_px:
            acc += ds[j]
            j += 1
        out[e:j] = True

        corner_info.append((s, e, k_max, brake_m))

    return out, corner_info

accel_px = ACCEL_M * px_per_m
is_slow, corner_info = dilate_along_arclength_per_corner(
    is_curved_raw, np.abs(kappa), ds,
    corner_brake_distance_m, accel_px
)

# Print per-corner breakdown.
print(f"\n{'corner':>6}  {'kappa_max (1/m)':>16}  "
      f"{'v_apex (km/h)':>14}  {'brake (m)':>10}")
for idx, (s, e, k_max_px, brake_m) in enumerate(corner_info):
    k_per_m = k_max_px * px_per_m
    v_apex  = np.sqrt(min(A_LAT / max(k_per_m, 1e-6), V_TOP**2))
    print(f"{idx:>6}  {k_per_m:>16.4f}  {v_apex*3.6:>14.0f}  {brake_m:>10.1f}")

# ---------------------------------------------------------------
# 8. Report
# ---------------------------------------------------------------
straight_len_px = ds[~is_curved_raw].sum()
curved_len_px   = ds[is_curved_raw].sum()
fast_len_px     = ds[~is_slow].sum()
slow_len_px     = ds[is_slow].sum()

print("\n================ GEOMETRY ONLY ================")
print(f"Total track length: {total_length_px:8.1f} px   ({REAL_LENGTH_M:.0f} m real)")
print(f"Straight:           {straight_len_px/px_per_m:6.0f} m  "
      f"({100*straight_len_px/total_length_px:.1f}%)")
print(f"Curved:             {curved_len_px/px_per_m:6.0f} m  "
      f"({100*curved_len_px/total_length_px:.1f}%)")
print(f"Fast (on throttle): {fast_len_px/px_per_m:6.0f} m  "
      f"({100*fast_len_px/total_length_px:.1f}%)")
print(f"Slow (brake+corner+exit): {slow_len_px/px_per_m:6.0f} m  "
      f"({100*slow_len_px/total_length_px:.1f}%)")
print("=============================================")

# ---------------------------------------------------------------
# 9. Plot
# ---------------------------------------------------------------
# "Not straight" = anywhere you're not at full throttle = the slow mask.
not_straight_len_px = slow_len_px
straight_only_len_px = fast_len_px

# Shared masks for consistent plotting
buffer_only = is_slow & ~is_curved_raw        # braking / accel zones
straight_only = ~is_slow                      # true full-throttle straights

import matplotlib as mpl
from matplotlib.offsetbox import AnchoredText

# ---- LaTeX-style typesetting ----
# Option A: use matplotlib's built-in mathtext (no external LaTeX install needed)
mpl.rcParams.update({
    "text.usetex":       False,          # set True if you have a TeX installation
    "font.family":       "serif",
    "font.serif":        ["Computer Modern Roman", "CMU Serif", "DejaVu Serif"],
    "mathtext.fontset":  "cm",           # Computer Modern for any $...$ math
})
# Option B: if you DO have LaTeX installed, set text.usetex=True above and
# you'll get the real thing. Slower, but sharper.

fig, ax = plt.subplots(1, 1, figsize=(12, 8))

ax.imshow(img_rgb, alpha=0.35)
ax.plot(x_s[straight_only], y_s[straight_only], '.', color='tab:green',
        markersize=1.5,
        label=f'Straight           ({straight_only_len_px/px_per_m:.0f} m)')
ax.plot(x_s[buffer_only], y_s[buffer_only], '.', color='tab:orange',
        markersize=1.5,
        label=f'Brake / Accel      ({(slow_len_px-curved_len_px)/px_per_m:.0f} m)')
ax.plot(x_s[is_curved_raw], y_s[is_curved_raw], '.', color='tab:red',
        markersize=1.5,
        label=f'Cornering          ({curved_len_px/px_per_m:.0f} m)')

ax.set_title("Circuit de Monaco Track Breakdown", fontsize=25)

# Primary legend (distances) in the lower left
leg1 = ax.legend(loc='lower left', fontsize=18)
ax.add_artist(leg1)   # keep this legend when we add a second one

# Secondary "legend" (mode percentages) in the lower right
mode_text = (
    f"X-Mode (Low Drag): "
    f"{straight_only_len_px/px_per_m:.0f} m "
    f"({100*straight_only_len_px/total_length_px:.0f}%)\n"
    f"Z-Mode (High Downforce): "
    f"{not_straight_len_px/px_per_m:.0f} m "
    f"({100*not_straight_len_px/total_length_px:.0f}%)"
)
at = AnchoredText(
    mode_text,
    loc='lower right',
    prop=dict(size=18),
    frameon=True,
    borderpad=0.6,
    pad=0.5,
)
at.patch.set_boxstyle("round,pad=0.3,rounding_size=0.2")
at.patch.set_edgecolor("0.5")
at.patch.set_facecolor("white")
at.patch.set_alpha(0.9)
ax.add_artist(at)

ax.set_xticks([]); ax.set_yticks([])
ax.set_aspect('equal')

plt.tight_layout()
plt.savefig(OUT_PATH, dpi=140, bbox_inches='tight')
print(f"\nSaved plot to {OUT_PATH}")


'''
ax.legend(loc='lower right', fontsize=15)
ax.set_xticks([]); ax.set_yticks([])
ax.set_aspect('equal')

# Right: slow vs fast summary (same dimensions, same aspect)
ax = axes[1]
ax.imshow(img_rgb, alpha=0.35)
ax.plot(x_s[~is_slow], y_s[~is_slow], '.', color='tab:green',
        markersize=1.5,
        label=f'Fast (throttle)    ({fast_len_px/px_per_m:.0f} m)')
ax.plot(x_s[is_slow], y_s[is_slow], '.', color='tab:red',
        markersize=1.5,
        label=f'Slow (brake+corner+exit) ({slow_len_px/px_per_m:.0f} m)')
ax.set_title(
    f"X-Mode vs Z-Mode\n"
    f"Cornerning (Z-Mode) Zone: {slow_len_px/px_per_m:.0f} m "
    f"({100*slow_len_px/total_length_px:.0f}%)"
)
ax.legend(loc='lower right', fontsize=15)
ax.set_xticks([]); ax.set_yticks([])
ax.set_aspect('equal')

# Lock both axes to the same extent so the subplots are truly the same size.
xlim = (min(x_s) - 20, max(x_s) + 20)
ylim = (max(y_s) + 20, min(y_s) - 20)   # inverted for image coords
for ax in axes:
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)


plt.tight_layout()
plt.savefig(OUT_PATH, dpi=140, bbox_inches='tight')
print(f"\nSaved plot to {OUT_PATH}")

'''