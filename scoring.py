<<<<<<< HEAD
#config.py contains information about track and seed airfoil values
from config import TRACK_WEIGHTS, REF_VALS, INVALID_SCORE
from design_vars import designParameters

#check if provided aero coefficients are valid
def valid_aero(cl, cd):
    if cl is None or cd is None:
        return "Error: cl or cd does not exist"
    
    if cd <= 0:
        return False
    
    return True

#make sure inputted design parameters are withing constrained region
def valid_constraints(des):
=======
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

>>>>>>> 33c4a9966f88cd4a82943f6e0f5ab3c66f50335e
    if not 0.06 <= des.max_thickness <= 0.25:
        return False

    if not 0.00 <= des.max_camber <= 0.15:
        return False

    if not 0.15 <= des.max_thickness_loc <= 0.45:
        return False

    if not 0.30 <= des.max_camber_loc <= 0.70:
        return False

<<<<<<< HEAD
    if des.max_thickness_loc < des.max_camber_loc:
        return False

    if des.max_thickness > des.max_camber:
        return False
    
    return True

#phase 1: fixed element, cl and cd are weighted based on track configuration
def scoring_p1(aero_result):
    cl = aero_result.cl
    cd = aero_result.cd
    
    if not valid_aero(cl, cd) or not valid_constraints(designParameters):
        return INVALID_SCORE
    
    cd_weight = TRACK_WEIGHTS["straights"]
    cl_weight = TRACK_WEIGHTS["turns"]

    #calculate downforce
    df = -cl

    #"normalize" df and cd with respect to seed airfoil 
    # so that improving cl and reducing cd from seed airfoil are awarded higher score
    df_n = df / REF_VALS["df_p1"]
    cd_n = cd / REF_VALS["cd_p1"]

    #calculate score (goal is to maximize this value)
    score = df_n*cl_weight - cd_n*cd_weight

    return score

def scoring_p2(aero_result):
    cl = aero_result.cl
    cd = aero_result.cd
    
    if not valid_aero(cl, cd):
        return INVALID_SCORE
    
    cd_weight = TRACK_WEIGHTS["straights"]
    cl_weight = TRACK_WEIGHTS["turns"]

    df = -cl
    
    # Use Phase 2 reference values from the two-element seed
    df_n = df / REF_VALS["df_p2"]
    cd_n = cd / REF_VALS["cd_p2"]

    score = df_n*cl_weight - cd_n*cd_weight
=======
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
>>>>>>> 33c4a9966f88cd4a82943f6e0f5ab3c66f50335e

    return score