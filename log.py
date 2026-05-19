import csv
import os

# creates csv file if it does not already exist
def initialize_log(filename):
    # don't overwrite existing log file
    if os.path.exists(filename):
        return
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        # column headers
        writer.writerow(["iteration","cl","cd","score"])

# appends optimization results to csv file
def log_iteration(filename,iteration,cl,cd,score):

    with open(filename, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([iteration,cl,cd,score])