from setup.track import PHASE1_WEIGHTS, PHASE2_WEIGHTS, PHASE3_WEIGHTS #INVALID_SCORE


#check if valid aero results are returned
def valid_aero(cl, cd):
    if cl is None or cd is None:
        return False
    if cd <= 0:
        return False
    
    return True

#phase 1 scoring function
def scoring_p1(aero_result, ref_vals):

    cl = aero_result.cl
    cd = aero_result.cd

    if valid_aero(cl,cd):
        cd_weight = PHASE1_WEIGHTS["drag"]
        cl_weight = PHASE1_WEIGHTS["downforce"]

        #rear wing downforce
        print(cl)
        df = -cl

        #heavily penalize positive lift
        # if df <= 0:
        #     return INVALID_SCORE

        #normalize with respect to seed
        df_n = df / ref_vals["df"]
        cd_n = cd / ref_vals["cd"]

        #maximize downforce, penalize drag
        score = 100 * (df_n * cl_weight - cd_n * cd_weight)

    else:
        score = -1

        # geometry sanity penalties
    if aero_result.coords is not None:
        y = aero_result.coords[:, 1]
        thickness_est = y.max() - y.min()

        # penalize very thick/extreme shapes
        if thickness_est > 0.20:
            score -= 2.0 * (thickness_est - 0.20)

        # penalize very large vertical excursions
        if abs(y.min()) > 0.18:
            score -= 2.0 * (abs(y.min()) - 0.18)

    return score

#phase 2 scoring function
def scoring_p2(aero_result, ref_vals):

    cl = aero_result.cl
    cd = aero_result.cd

    if valid_aero(cl,cd):
        cd_weight = PHASE2_WEIGHTS["drag"]
        cl_weight = PHASE2_WEIGHTS["downforce"]

        #rear wing downforce
        print(cl)
        df = -cl

        #heavily penalize positive lift
        if df <= 0:
            return INVALID_SCORE

        #normalize with respect to seed
        df_n = df / ref_vals["df"]
        cd_n = cd / ref_vals["cd"]

        #maximize downforce, penalize drag
        #score = df_n * cl_weight - cd_n * cd_weight
        score = df_n * 1.0 - cd_n * 0

    else:
        score = -1

    return score

def scoring_p3(aero_result, aoa_deg, ref_vals):
    cl = aero_result.cl
    cd = aero_result.cd

    if not valid_aero(cl, cd):
        return INVALID_SCORE

    #penalize unrealistic angles of attack
    if not -10 <= aoa_deg <= 5:
        return INVALID_SCORE

    cd_weight = PHASE3_WEIGHTS["drag"] 
    cl_weight = PHASE3_WEIGHTS["downforce"]

    #rear wing downforce
    df = -cl

    #heavily penalize positive lift
    if df <= 0:
        return INVALID_SCORE
    
    #normalize with respect to seed
    df_n = df / ref_vals["df"]
    cd_n = cd / ref_vals["cd"]

    #maximize downforce, penalize drag
    score = df_n * cl_weight - cd_n * cd_weight

    return score