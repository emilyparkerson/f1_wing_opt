import matplotlib.pyplot as plt
import pandas as pd

# -------------------------------------------------
# OPTIMIZATION RESULT PLOTS
# -------------------------------------------------

def plot_seed_vs_optimized(seed_coords, optimized_coords, phase_name=""):
    """
    Compare seed airfoil against optimized airfoil.
    
    seed_coords:      (N, 2) array of [x, y] in Selig format
    optimized_coords: (M, 2) array of [x, y] in Selig format
    phase_name:       string for the suptitle (e.g. "Phase 1 Inboard")
    """
    fig, axes = plt.subplots(1, 3, figsize=(18, 4))
    
    # Left: seed alone
    axes[0].plot(seed_coords[:, 0], seed_coords[:, 1], linewidth=2)
    axes[0].set_title("Seed Airfoil")
    axes[0].axis("equal")
    axes[0].grid(True)
    axes[0].set_xlabel("x/c")
    axes[0].set_ylabel("y/c")
    
    # Middle: optimized alone
    axes[1].plot(optimized_coords[:, 0], optimized_coords[:, 1], linewidth=2)
    axes[1].set_title("Optimized Airfoil")
    axes[1].axis("equal")
    axes[1].grid(True)
    axes[1].set_xlabel("x/c")
    axes[1].set_ylabel("y/c")
    
    # Right: overlay
    axes[2].plot(seed_coords[:, 0], seed_coords[:, 1],
                 linewidth=2, label="Seed", linestyle="--", color="gray")
    axes[2].plot(optimized_coords[:, 0], optimized_coords[:, 1],
                 linewidth=2, label="Optimized", color="C0")
    axes[2].set_title("Overlay")
    axes[2].axis("equal")
    axes[2].grid(True)
    axes[2].set_xlabel("x/c")
    axes[2].set_ylabel("y/c")
    axes[2].legend()
    
    suptitle = f"{phase_name}: Seed vs Optimized" if phase_name else "Seed vs Optimized"
    fig.suptitle(suptitle, fontsize=14)
    fig.tight_layout()
    plt.show()


# -------------------------------------------------
# HISTORY PLOTS (existing, with phase_name added)
# -------------------------------------------------

def plot_score_history(csv_file, phase_name=""):
    data = pd.read_csv(csv_file)
    plt.figure()
    plt.plot(data["iteration"], data["score"], marker="o")
    plt.xlabel("Iteration")
    plt.ylabel("Score")
    plt.title(f"{phase_name}: Score History" if phase_name else "Score History")
    plt.grid(True)
    plt.show()


def plot_aero_history(csv_file, phase_name=""):
    data = pd.read_csv(csv_file)
    plt.figure()
    plt.plot(data["iteration"], data["cl"], marker="o", label="Cl")
    plt.plot(data["iteration"], data["cd"], marker="o", label="Cd")
    plt.xlabel("Iteration")
    plt.ylabel("Aerodynamic Coefficient")
    plt.title(f"{phase_name}: Aerodynamic History" if phase_name else "Aerodynamic History")
    plt.legend()
    plt.grid(True)
    plt.show()