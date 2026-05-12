#create dictionary for track weights (adjust these possibly??)
TRACK_WEIGHTS = {
    "straights": 0.47,
    "turns": 0.53 
}

#create dictionary from seed airfoil data (df = -cl)
REF_VALS = {
    "df_p1": 1.2,
    "cd_p1": 0.4,
    "df_p2": 1.2,
    "cd_p2": 0.4,
    "alpha": -2
}

#invalid score for BAD designs (large negative number so that design is not chosen)
INVALID_SCORE = -1e8

#design constraints
PHASE1_BOUNDS = {
    "max_camber": (0.02, 0.20),
    "max_camber_loc": (0.30, 0.65),
    "max_thickness": (0.06, 0.18),
    "max_thickness_loc": (0.20, 0.45),
}

#second element leading edge position relative to first element trailing edge
SECOND_ELM_LOC = {
    "horizontal": 0.90,
    "vertical": 0.20
}