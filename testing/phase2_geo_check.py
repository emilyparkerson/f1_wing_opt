"""
Standalone geometry check for a two-element phase-2 config.

Assembles the elements EXACTLY as run_mses_elements would (same
_element_to_coords path), then plots them together so you can eyeball
the layout before spending MSES calls. Catches the usual MSES killers:
overlapping elements, a flap placed too close/far, wrong orientation.

Run:  python check_phase2_geometry.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import matplotlib.pyplot as plt

from setup.aero_interface import _element_to_coords
from phase2.phase2 import P2_RE_IB_CONFIG, P2_RE_OB_CONFIG


def assemble(config, fixed_stand_in=None):
    """Build every element's coords. If the fixed element's .dat doesn't
    exist yet, pass fixed_stand_in (a path) to use in its place."""
    coords_list, labels = [], []
    for spec in config["elements"]:
        spec = dict(spec)  # copy so we can swap the path safely
        if spec["role"] == "fixed" and fixed_stand_in is not None:
            spec["coords_path"] = fixed_stand_in
        # morph element needs the seed design as its "design"
        design = config["seed_design"] if spec["role"] == "morph" else None
        coords = _element_to_coords(spec, design=design)
        coords_list.append(coords)
        labels.append(f'{spec["role"]} ({spec.get("place","main")})')
    return coords_list, labels


def plot_config(config, fixed_stand_in, title):
    coords_list, labels = assemble(config, fixed_stand_in)

    plt.figure(figsize=(12, 5))
    for coords, label in zip(coords_list, labels):
        plt.plot(coords[:, 0], coords[:, 1], "-", lw=1.5, label=label)
        le = coords[int(np.argmin(coords[:, 0]))]
        te = coords[int(np.argmax(coords[:, 0]))]
        plt.plot(*le, "o", ms=6)
        plt.plot(*te, "s", ms=6)

    # quick overlap diagnostic: bounding boxes
    print(f"\n=== {title} ===")
    for coords, label in zip(coords_list, labels):
        print(f"  {label:18s} x[{coords[:,0].min():+.3f}, {coords[:,0].max():+.3f}]  "
              f"y[{coords[:,1].min():+.3f}, {coords[:,1].max():+.3f}]")
    # gap between element 1 TE and element 2 LE (if two elements)
    if len(coords_list) == 2:
        te1 = coords_list[0][int(np.argmax(coords_list[0][:, 0]))]
        le2 = coords_list[1][int(np.argmin(coords_list[1][:, 0]))]
        gap = le2 - te1
        print(f"  element1 TE -> element2 LE offset: dx={gap[0]:+.3f}, dy={gap[1]:+.3f}")
        # crude x-overlap check
        x1max = coords_list[0][:, 0].max()
        x2min = coords_list[1][:, 0].min()
        if x2min < x1max:
            print(f"  *** X-OVERLAP: element 2 starts (x={x2min:.3f}) before "
                  f"element 1 ends (x={x1max:.3f}). MSES may fail. ***")
        else:
            print(f"  no x-overlap (element 2 starts {x2min - x1max:.3f} behind element 1 TE)")

    plt.title(title)
    plt.xlabel("x/c"); plt.ylabel("y/c")
    plt.axis("equal"); plt.grid(True); plt.legend()
    plt.tight_layout()
    return plt.gcf()


if __name__ == "__main__":
    import sys
    # Until phase 1 produces real winners, use the phase-1 seed as a
    # stand-in for the fixed (main) element so we can see the layout.
    ib_standin = "phase1/inboard_seed_phase1.txt"
    ob_standin = "phase1/outboard_seed_phase1.txt"

    plot_config(P2_RE_IB_CONFIG, ib_standin, "Phase 2 Inboard layout (fixed = phase-1 seed stand-in)")
    plot_config(P2_RE_OB_CONFIG, ob_standin, "Phase 2 Outboard layout (fixed = phase-1 seed stand-in)")
    plt.show()