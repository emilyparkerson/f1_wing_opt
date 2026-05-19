from setup.track import TRACK_WEIGHTS, REF_VALS, INVALID_SCORE

# -------------------------------------------------
# CHECK AERO VALIDITY
# -------------------------------------------------

def valid_aero(cl, cd):
    if cl is None or cd is None:
        return False
    if cd <= 0:
        return False
    
    return True

# -------------------------------------------------
# PHASE 1 SCORING
# -------------------------------------------------

def scoring_p1(aero_result, design):

    cl = aero_result.cl
    cd = aero_result.cd

    if not valid_aero(cl, cd):
        return INVALID_SCORE

    cd_weight = TRACK_WEIGHTS["straights"]
    cl_weight = TRACK_WEIGHTS["turns"]

    # rear wing downforce
    df = -cl

    # normalize with respect to seed
    df_n = df / REF_VALS["df_p1"]
    cd_n = cd / REF_VALS["cd_p1"]

    # maximize downforce, penalize drag
    score = df_n * cl_weight - cd_n * cd_weight

    return score