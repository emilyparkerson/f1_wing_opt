import matplotlib.pyplot as plt
import pandas as pd


def _get_col(data, possible_names, fallback_index=None):
    for name in possible_names:
        if name in data.columns:
            return data[name]

    if fallback_index is not None and fallback_index < len(data.columns):
        return data.iloc[:, fallback_index]

    raise KeyError(f"Could not find columns: {possible_names}")


def plot_seed_vs_optimized(seed_coords, optimized_coords, phase_name=""):
    fig, axes = plt.subplots(1, 3, figsize=(18, 4))

    axes[0].plot(seed_coords[:, 0], seed_coords[:, 1], linewidth=2)
    axes[0].set_title("Seed Airfoil")
    axes[0].axis("equal")
    axes[0].grid(True)
    axes[0].set_xlabel("x/c")
    axes[0].set_ylabel("y/c")

    axes[1].plot(optimized_coords[:, 0], optimized_coords[:, 1], linewidth=2)
    axes[1].set_title("Optimized Airfoil")
    axes[1].axis("equal")
    axes[1].grid(True)
    axes[1].set_xlabel("x/c")
    axes[1].set_ylabel("y/c")

    axes[2].plot(seed_coords[:, 0], seed_coords[:, 1], linewidth=2, label="Seed", linestyle="--", color="gray")
    axes[2].plot(optimized_coords[:, 0], optimized_coords[:, 1], linewidth=2, label="Optimized", color="C0")
    axes[2].set_title("Overlay")
    axes[2].axis("equal")
    axes[2].grid(True)
    axes[2].set_xlabel("x/c")
    axes[2].set_ylabel("y/c")
    axes[2].legend()

    fig.suptitle(f"{phase_name}: Seed vs Optimized" if phase_name else "Seed vs Optimized", fontsize=14)
    fig.tight_layout()
    plt.show()


def plot_score_history(csv_file, phase_name=""):
    data = pd.read_csv(csv_file)

    iteration = _get_col(data, ["iteration", "iter", "Iteration"], fallback_index=0)
    score = _get_col(data, ["score", "Score"], fallback_index=len(data.columns) - 1)

    valid = score > -1000
    iteration = iteration[valid]
    score = score[valid]

    plt.figure(figsize=(8, 5))
    plt.plot(iteration, score, marker="o")
    plt.xlabel("Iteration")
    plt.ylabel("Score")
    plt.title(f"{phase_name}: Score History" if phase_name else "Score History")
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def plot_aero_history(csv_file, phase_name=""):
    data = pd.read_csv(csv_file)

    iteration = _get_col(data, ["iteration", "iter", "Iteration"], fallback_index=0)
    cl = _get_col(data, ["cl", "Cl", "CL"], fallback_index=1)
    cd = _get_col(data, ["cd", "Cd", "CD"], fallback_index=2)

    plt.figure(figsize=(8, 5))
    plt.plot(iteration, cl, marker="o", label="Cl")
    plt.plot(iteration, cd, marker="o", label="Cd")
    plt.xlabel("Iteration")
    plt.ylabel("Aerodynamic Coefficient")
    plt.title(f"{phase_name}: Aerodynamic History" if phase_name else "Aerodynamic History")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()