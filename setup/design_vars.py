from dataclasses import dataclass

@dataclass
class AeroResult:

    cl: float
    cd: float
    coords: object = None


# optimizer design variables
@dataclass
class designParameters:

    max_camber: float
    max_camber_loc: float
    max_thickness: float
    max_thickness_loc: float


# bounds for optimization
@dataclass
class airfoilBounds:

    max_camber: float
    max_camber_loc: float
    max_thickness: float
    max_thickness_loc: float


# optional second element positioning
@dataclass
class secondElementPos:

    horizontal: float
    vertical: float