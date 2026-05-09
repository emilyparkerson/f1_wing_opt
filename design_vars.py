#define data structure for an airfoil
#airfoil design
#aero result

from dataclasses import dataclass

#use this to store cl and cd results from MSES (add more variables as needed)
@dataclass
class AeroResult:
    cl: float
    cd: float

@dataclass
class designParameters:
    max_camber: float
    max_camber_loc: float
    max_thickness: float
    max_thickness_loc: float

