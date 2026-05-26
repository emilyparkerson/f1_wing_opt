import numpy as np
from setup.design_vars import designParameters


def clip_design(design, bounds):

    return designParameters(
        max_camber=np.clip(
            design.max_camber,
            bounds.max_camber[0],
            bounds.max_camber[1]
        ),
        max_camber_loc=np.clip(
            design.max_camber_loc,
            bounds.max_camber_loc[0],
            bounds.max_camber_loc[1]
        ),
        max_thickness=np.clip(
            design.max_thickness,
            bounds.max_thickness[0],
            bounds.max_thickness[1]
        ),
        max_thickness_loc=np.clip(
            design.max_thickness_loc,
            bounds.max_thickness_loc[0],
            bounds.max_thickness_loc[1]
        )
    )


def is_valid_design(design):

    if design.max_thickness <= design.max_camber:
        return False

    if design.max_thickness < 1.5 * design.max_camber:
        return False

    if design.max_thickness_loc >= design.max_camber_loc:
        return False

    return True


def perturb_design(current_design, bounds, step_size):

    for _ in range(100):

        new_design = designParameters(
            max_camber=current_design.max_camber
            + step_size["max_camber"] * np.random.randn(),

            max_camber_loc=current_design.max_camber_loc
            + step_size["max_camber_loc"] * np.random.randn(),

            max_thickness=current_design.max_thickness
            + step_size["max_thickness"] * np.random.randn(),

            max_thickness_loc=current_design.max_thickness_loc
            + step_size["max_thickness_loc"] * np.random.randn()
        )

        new_design = clip_design(new_design, bounds)

        if is_valid_design(new_design):
            return new_design

    return current_design