import matplotlib.pyplot as plt
import pandas as pd

# plot optimization score history
def plot_score_history(csv_file):

    data = pd.read_csv(csv_file)
    plt.figure()
    plt.plot(data["iteration"],data["score"],marker="o")
    plt.xlabel("Iteration")
    plt.ylabel("Score")
    plt.title("Score History")
    plt.grid(True)
    plt.show()

# plot cl and cd over iterations
def plot_aero_history(csv_file):

    data = pd.read_csv(csv_file)
    plt.figure()
    plt.plot(data["iteration"],data["cl"],marker="o",label="Cl")
    plt.plot(data["iteration"],data["cd"],marker="o",label="Cd")
    plt.xlabel("Iteration")
    plt.ylabel("Aerodynamic Coefficient")
    plt.title("Aerodynamic History")
    plt.legend()
    plt.grid(True)
    plt.show()