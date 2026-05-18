#this is just a test for my specific functions (do not upload to main branch)

#general process:
''' phase 1: 
    1. get seed airfoil (call get_seed) ... run through MSES to get base cl and cd (input into REF_VALS config.py)
    2. set design limits (locaated in config.py)
    3. optimizer chooses design parameters
    4. store design parameters is designParameters dataclass
    5. create new airfoil (call new_airfoil)
    6. generate coordinates in Selig format (call get_coords)
    7. export geometry into dat file (call export_mses_geometry)
    8. run design through mses, get cl and cd and store in AeroResult dataclass
    9. call scoring function and save result
    10. repeat 3-10 until ...
    11. repeat 1-10 for phase 2

'''
import numpy as np
import matplotlib.pyplot as plt
from scoring import scoring_p1
from design_vars import AeroResult, designParameters
from config import SECOND_ELM_LOC
from geometry import (get_seed, new_airfoil, get_coords, plot_airfoil, load_airfoil_dat, export_mses_geometry)

#cl_cand = -2.0
#cd_cand = 0.15

cand_result = AeroResult(cl=-2.0, cd=0.15)
#des = designParameters(max_camber=0.06, max_camber_loc=0.55, max_thickness=0.12, max_thickness_loc=0.30)
des = designParameters(max_camber=0.08, max_camber_loc=0.3, max_thickness=0.15, max_thickness_loc=0.20)
des_p2 = designParameters(max_camber=0.04, max_camber_loc=0.60, max_thickness=0.15, max_thickness_loc=0.40)
#des = designParameters(max_camber=0.01, max_camber_loc=0.50, max_thickness=0.10, max_thickness_loc=0.30)

score = scoring_p1(cand_result, des)

print("Phase 1 score:", score)

#exports Selig coordinates into dat file
# def export_dat(xu, yu, xl, yl, filepath: str, name = "Morphed Coordinates"):
#     #flip upper surface (TE-->LE)
#     x_upper = xu[::-1]
#     y_upper = yu[::-1]
#     #keep lower surface as is
#     x_lower = xl[1:]     
#     y_lower = yl[1:]
 
#     #write coordinates to file
#     with open(filepath, "w") as f:
#         f.write(f"{name}\n")
#         for xi, yi in zip(x_upper, y_upper):
#             f.write(f"  {xi:.6f}  {yi:.6f}\n")
#         for xi, yi in zip(x_lower, y_lower):
#             f.write(f"  {xi:.6f}  {yi:.6f}\n")

#test outboard (WORKS)
#x, y = load_airfoil_dat(r"C:\Users\ecpar\Downloads\outboard_seed_phase1.txt")

#test inboard
x_p1, y_p1 = load_airfoil_dat(r"C:\Users\ecpar\Downloads\inboard_seed_phase1.txt")

#PHASE 1
x_common, camber_seed, thickness_seed, aoa = get_seed(x_p1, y_p1)
xu_morph, yu_morph, xl_morph, yl_morph, camber_new, thickness_new, x_cos_coords = new_airfoil(thickness_seed, 
    x_common, des, 160, smoothing_fac= None, aoa=aoa)

points_p1 = get_coords(xu_morph, xl_morph, yu_morph, yl_morph, phase=1)

export_mses_geometry(r"C:\Users\ecpar\Downloads\phase1_geometry.txt", [points_p1])

plot_airfoil(des, phase=1)

#PHASE 2
x_p2, y_p2 = load_airfoil_dat(r"C:\Users\ecpar\Downloads\outboard_seed_phase2.txt")
#to shift coords when plotting 
h = SECOND_ELM_LOC["horizontal"]
v = SECOND_ELM_LOC["vertical"]

x_common_p2, camber_seed_p2, thickness_seed_p2, aoa_p2 = get_seed(x_p2, y_p2)
xu_morph_p2, yu_morph_p2, xl_morph_p2, yl_morph_p2, camber_new_p2, thickness_new_p2, x_cos_coords_p2 = new_airfoil(thickness_seed_p2, 
    x_common_p2, des_p2, 160, smoothing_fac= None, aoa=aoa_p2)

points_p2 = get_coords(xu_morph_p2, xl_morph_p2, yu_morph_p2, yl_morph_p2, phase=2)

phase2_elements = [points_p1, points_p2]

export_mses_geometry(r"C:\Users\ecpar\Downloads\phase2_geometry.txt", phase2_elements)

plt.plot(x_p1, y_p1,  marker='o',label="seed")
plt.plot(xu_morph, yu_morph,  marker='o',label="upper new")
plt.plot(xl_morph, yl_morph, marker='o', label="lower new")
plt.axis("equal")
plt.legend()
plt.title("Fixed Element (Phase 1)")
plt.show()

# plt.plot(x_p2, y_p2,  marker='o',label="seed")
# plt.plot(points_p2_scaled[:,0], points_p2_scaled[:, 1],  marker='o',label="upper new")
# plt.axis("equal")
# plt.legend()
# plt.title("Rotating Element (Phase 2)")
# plt.show()
plt.plot(x_p1, y_p1,  marker='o',label="seed first element")
plt.plot(x_p2 + h, y_p2 + v,  marker='o',label="seed second element")
plt.plot(points_p1[:,0], points_p1[:, 1],  marker='o',label="new first element")
plt.plot(points_p2[:, 0], points_p2[:, 1],  marker='o',label="new second element")
plt.axis("equal")
plt.legend()
plt.title("Two Element Wing")
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
# te_gap = np.sqrt((xu_morph[-1] - xl_morph[-1])**2 + (yu_morph[-1] - yl_morph[-1])**2)
# print(f"TE gap: {te_gap:.6f}c")

# # Plot camber and thickness of the seed before morphing

# plt.figure()
# plt.plot(x_common, camber_seed, label="camber seed")
# plt.plot(x_common, thickness_seed, label="thickness seed")
# plt.xlim(0, 0.1)  # zoom into LE
# plt.legend()
# plt.title("Seed camber and thickness near LE")
# plt.show()