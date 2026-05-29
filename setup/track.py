#create dictionary for track weights (adjust these possibly??)
TRACK_WEIGHTS = {
    "straights": 0.47,
    "turns": 0.53 
}

#create dictionary from seed airfoil data (df = -cl)
REF_VALS = {
    "df_p1": 0.87114,
    "cd_p1": 0.01284,
    "df_p2": 1.2,
    "cd_p2": 0.4,
    "alpha": 0
}

#invalid score for BAD designs (large negative number so that design is not chosen)
INVALID_SCORE = -10

#path to seed file
PHASE1_SEED_PATH = r"C:\Users\ecpar\Downloads\inboard_seed_phase1.txt"
PHASE2_SEED_PATH = r"C:\Users\ecpar\Downloads\inboard_seed_phase2.txt"

#design constraints
PHASE1_BOUNDS = {
    "max_camber": (0.02, 0.10),
    "max_camber_loc": (0.30, 0.45),
    "max_thickness": (0.06, 0.12),
    "max_thickness_loc": (0.20, 0.30),
}

#second element leading edge position relative to first element trailing edge
SECOND_ELM_LOC = {
    "horizontal": 0.90,
    "vertical": 0.20
}