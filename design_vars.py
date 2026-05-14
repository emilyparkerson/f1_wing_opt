#define data structure for an airfoil
#airfoil design
#aero result

from dataclasses import dataclass

#use this to store cl and cd results from MSES (add more variables as needed)
@dataclass
class AeroResult:
    cl: float
    cd: float

#use this to store optimizer solutions
@dataclass
class designParameters:
    max_camber: float
    max_camber_loc: float
    max_thickness: float
    max_thickness_loc: float

#use this to set design bounds
@dataclass
class airfoilBounds:
    max_camber: float
    max_camber_loc: float
    max_thickness: float
    max_thickness_loc: float

#use this to set horizontal and vertical location of second element (LE relative to TE) if constraining
#if not delete and see config.py
@dataclass
class secondElementPos:
    horizontal: float
    vertical: float