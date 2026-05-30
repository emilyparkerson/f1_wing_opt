from setup.design_vars import designParameters

def airfoil_constraints(x):
    """Return True if x is feasible, False otherwise.
    x is a 1D numpy array: [max_camber, max_camber_loc, max_thickness, max_thickness_loc]
    """
    # Unpack into named parameters
    max_camber, max_camber_loc, max_thickness, max_thickness_loc = x
    
    
    # Geometric ordering constraints
    if max_thickness <= max_camber:
        return False
    # if max_thickness < 2.0 * max_camber:
    #     return False
    if max_thickness_loc >= max_camber_loc:
        return False
    
    # Bounds (could make this take in the bounds array)
    if not 0.06 <= max_thickness <= 0.25:
        return False
    if not 0.00 <= max_camber <= 0.15:
        return False
    if not 0.15 <= max_thickness_loc <= 0.45:
        return False
    if not 0.30 <= max_camber_loc <= 0.70:
        return False
    
    return True
    
def normalized_constraints(original_constraints, bounds_arr):
    """
    Wrap a constraints function so it can be called with normalized x.
    Denormalizes internally before checking.
    """

    def wrapped(x_norm):
        x_real = bounds_arr[:, 0] + x_norm * (bounds_arr[:, 1] - bounds_arr[:, 0])
        return original_constraints(x_real)
    
    return wrapped