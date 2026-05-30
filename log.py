import csv
import os

def initialize_log(log_file):
    with open(log_file, "w", newline="") as f:
        csv.writer(f).writerow(["iter", "cl", "cd", "score",
                                "max_camber", "max_camber_loc",
                                "max_thickness", "max_thickness_loc",
                                "converged"])

def log_iteration(log_file, n, cl, cd, score,
                  max_camber, max_camber_loc, max_thickness, max_thickness_loc,
                  converged):
    with open(log_file, "a", newline="") as f:
        csv.writer(f).writerow([n, cl, cd, score,
                                max_camber, max_camber_loc,
                                max_thickness, max_thickness_loc,
                                converged])