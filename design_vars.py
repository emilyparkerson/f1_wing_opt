#define data structure for an airfoil
#airfoil design
#aero result

from dataclasses import dataclass

#use this to store cl and cd results from MSES (add more variables as needed)
@dataclass
class AeroResult:
    cl: float
    cd: float