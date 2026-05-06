#config.py contains information about track and seed airfoil values
from config import TRACK_WEIGHTS, REF_VALS, INVALID_SCORE

#check if provided aero coefficients are valid
def valid_aero(cl, cd):
    if cl is None or cd is None:
        return "Error: cl or cd does not exist"
    
    if cd <= 0:
        raise ValueError("Drag cannot be negative")
    
    return True

#phase 1: fixed element, cl and cd are weighted based on track configuration
def scoring_p1(aero_result):
    cl = aero_result.cl
    cd = aero_result.cd
    
    if not valid_aero(cl, cd):
        return INVALID_SCORE
    
    cd_weight = TRACK_WEIGHTS["straights"]
    cl_weight = TRACK_WEIGHTS["turns"]

    #calculate downforce
    df = -cl

    #"normalize" df and cd with respect to seed airfoil 
    # so that improving cl and reducing cd from seed airfoil are awarded higher score
    df_n = df / REF_VALS["df"]
    cd_n = cd / REF_VALS["cd"]

    #calculate score (goal is to maximize this value)
    score = df_n*cl_weight - cd_n*cd_weight

    return score
