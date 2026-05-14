from config import TRACK_WEIGHTS, REF_VALS, INVALID_SCORE


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
# CHECK DESIGN CONSTRAINTS
# -------------------------------------------------

def valid_constraints(des):

    if not 0.06 <= des.max_thickness <= 0.25:
        return False

    if not 0.00 <= des.max_camber <= 0.15:
        return False

    if not 0.15 <= des.max_thickness_loc <= 0.45:
        return False

    if not 0.30 <= des.max_camber_loc <= 0.70:
        return False

    if des.max_thickness <= des.max_camber:
        return False

    if des.max_thickness < 1.5 * des.max_camber:
        return False

    if des.max_thickness_loc >= des.max_camber_loc:
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

    if not valid_constraints(design):
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