# very simple temporary scoring function
# this will later be replaced by Emily's full version


def scoring_p1(aero_result):

    if aero_result.cl is None:
        return -999.0

    # maximize lift and minimize drag
    score = aero_result.cl - 100 * aero_result.cd

    return score