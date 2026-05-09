#this is just a test for my specific functions (do not upload to main branch)

import numpy as np
import matplotlib.pyplot as plt
from scoring import scoring_p1
from design_vars import AeroResult, designParameters
from geometry import get_seed, new_airfoil

#cl_cand = -2.0
#cd_cand = 0.15

cand_result = AeroResult(cl=-2.0, cd=0.15)
#des = designParameters(max_camber=0.06, max_camber_loc=0.55, max_thickness=0.12, max_thickness_loc=0.30)
des = designParameters(max_camber=0.08, max_camber_loc=0.3, max_thickness=0.15, max_thickness_loc=0.20)
#des = designParameters(max_camber=0.04, max_camber_loc=0.60, max_thickness=0.15, max_thickness_loc=0.40)
#des = designParameters(max_camber=0.01, max_camber_loc=0.50, max_thickness=0.10, max_thickness_loc=0.30)

score = scoring_p1(cand_result)

print("Phase 1 score:", score)

#function to import dat file (coordinates must be in Selig format)
def load_airfoil_dat(filepath: str):
    x_list, y_list = [], []
    with open(filepath) as f:
        for line in f:
            #split coordinates based on white space
            parts = line.split()
            #if line has two values
            if len(parts) == 2:
                try:
                    x_list.append(float(parts[0]))
                    y_list.append(float(parts[1]))
                #skip if cannot be converted to a float
                except ValueError:
                    pass
    return np.array(x_list), np.array(y_list)

#exports Selig coordinates into dat file
def export_dat(xu, yu, xl, yl, filepath: str, name = "Morphed Coordinates"):
    #flip upper surface (TE-->LE)
    x_upper = xu[::-1]
    y_upper = yu[::-1]
    #keep lower surface as is
    x_lower = xl[1:]     
    y_lower = yl[1:]
 
    #write coordinates to file
    with open(filepath, "w") as f:
        f.write(f"{name}\n")
        for xi, yi in zip(x_upper, y_upper):
            f.write(f"  {xi:.6f}  {yi:.6f}\n")
        for xi, yi in zip(x_lower, y_lower):
            f.write(f"  {xi:.6f}  {yi:.6f}\n")

#test outboard (WORKS)
#x, y = load_airfoil_dat(r"C:\Users\ecpar\Downloads\outboard_seed_phase1.txt")

#test inboard
x, y = load_airfoil_dat(r"C:\Users\ecpar\Downloads\inboard_seed_phase1.txt")

x_common, camber_seed, thickness_seed, aoa = get_seed(x, y, smoothing_fac=None)
xu_morph, yu_morph, xl_morph, yl_morph, camber_new, thickness_new, x_cos_coords = new_airfoil(thickness_seed, x_common, des, 160, smoothing_fac= None, aoa=aoa)

export_dat(xu_morph, yu_morph, xl_morph, yl_morph, r"C:\Users\ecpar\Downloads\morphed_data.txt", "morphed_data")

plt.plot(x, y,  marker='o',label="seed")
plt.plot(xu_morph, yu_morph,  marker='o',label="upper new")
plt.plot(xl_morph, yl_morph, marker='o', label="lower new")
plt.axis("equal")
plt.legend()
plt.show()

# plt.plot(x_common, camber_seed,  marker='o',label="seed camberline")
# plt.plot(x_cos_coords, camber_new,  marker='o',label="new camberline")
# plt.axis("equal")
# plt.legend()
# plt.show()

# plt.plot(x_common, thickness_seed,  marker='o',label="seed thickness")
# plt.plot(x_cos_coords, thickness_new, marker='o', label="new thickness")
# plt.axis("equal")
# plt.legend()
# plt.show()

#checking trailing edge gap ... right now should be good for MSES
te_gap = np.sqrt((xu_morph[-1] - xl_morph[-1])**2 + (yu_morph[-1] - yl_morph[-1])**2)
print(f"TE gap: {te_gap:.6f}c")

# # Plot camber and thickness of the seed before morphing

# plt.figure()
# plt.plot(x_common, camber_seed, label="camber seed")
# plt.plot(x_common, thickness_seed, label="thickness seed")
# plt.xlim(0, 0.1)  # zoom into LE
# plt.legend()
# plt.title("Seed camber and thickness near LE")
# plt.show()