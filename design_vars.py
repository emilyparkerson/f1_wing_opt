<<<<<<< HEAD
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
=======
from dataclasses import dataclass

@dataclass
class AeroResult:

    cl: float
    cd: float
    coords: object = None


# optimizer design variables
@dataclass
class designParameters:

>>>>>>> 33c4a9966f88cd4a82943f6e0f5ab3c66f50335e
    max_camber: float
    max_camber_loc: float
    max_thickness: float
    max_thickness_loc: float

<<<<<<< HEAD
#use this to set design bounds
@dataclass
class airfoilBounds:
=======

# bounds for optimization
@dataclass
class airfoilBounds:

>>>>>>> 33c4a9966f88cd4a82943f6e0f5ab3c66f50335e
    max_camber: float
    max_camber_loc: float
    max_thickness: float
    max_thickness_loc: float

<<<<<<< HEAD
#use this to set horizontal and vertical location of second element (LE relative to TE) if constraining
#if not delete and see config.py
@dataclass
class secondElementPos:
=======

# optional second element positioning
@dataclass
class secondElementPos:

>>>>>>> 33c4a9966f88cd4a82943f6e0f5ab3c66f50335e
    horizontal: float
    vertical: float