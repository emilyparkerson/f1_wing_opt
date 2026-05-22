import csv
import os


def initialize_log(log_file):
    """
    Create a fresh log file every run.
    """
    if os.path.exists(log_file):
        os.remove(log_file)

    with open(log_file, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["iteration", "cl", "cd", "score"])


def log_iteration(log_file, iteration, cl, cd, score):
    """
    Append one optimizer evaluation.
    """
    with open(log_file, mode="a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([iteration, cl, cd, score])