#create dictionary for track weights
TRACK_WEIGHTS = {
    "straights": 0.47,
    "turns": 0.53 
}

#create dictionary from seed airfoil data (df = -cl
REF_VALS = {
    "df": 1.2,
    "cd": 0.4,
    "alpha": -2
}

#invalid score for BAD designs (large negative number so that design is not chosen)
INVALID_SCORE = -1e8