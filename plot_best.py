"""Plot the best-so-far airfoil + seed flap on the same axes."""
import numpy as np
import matplotlib.pyplot as plt

paths = {
    "best":  "best_so_far_Phase_2_Rear_Element_Outboard_Configuration.dat",
    "seed":  "phase2/outboard_seed_phase2.dat",
}

def split_elements(coords, gap_thresh=0.1):
    """Split coords into separate element loops by detecting big jumps."""
    d = np.linalg.norm(np.diff(coords, axis=0), axis=1)
    breaks = np.where(d > gap_thresh)[0] + 1
    return np.split(coords, breaks)

plt.figure(figsize=(10, 5))
for label, path in paths.items():
    coords = np.loadtxt(path)
    elements = split_elements(coords)
    for i, el in enumerate(elements):
        # Label only the first chunk so the legend stays clean
        lbl = label if i == 0 else None
        plt.plot(el[:, 0], el[:, 1], "-", label=lbl, lw=2)

plt.axis("equal")
plt.grid(True)
plt.xlabel("x/c")
plt.ylabel("y/c")
plt.title("Seed flap vs best-so-far")
plt.legend()
plt.show()