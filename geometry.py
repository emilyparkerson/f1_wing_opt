import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import PchipInterpolator
from config import PHASE1_SEED_PATH, SECOND_ELM_LOC

#NOTE1: CAMBERED AIRFOIL MUST BE USED AS SEED AIRFOIL
#NOTE2: PROVIDE SEED AIRFOIL IN SELIF FORMAT (DOES NOT HAVE TO BE INVERTED)

#function to generate new airfoil based on design parameters
def new_airfoil(thickness_seed, x_common, designParameters, n_points, smoothing_fac, aoa):

    #REMOVE ONCE DONE IN OPTIMZIER
    #check_constraints(designParameters)

    max_camber = designParameters.max_camber
    max_camber_loc = designParameters.max_camber_loc
    max_thickness = designParameters.max_thickness
    max_thickness_loc = designParameters.max_thickness_loc

    x_cos_coords = cosine_spacing(n_points)

    #numerical solution
    #camber_new = morph(x_common, camber_seed, max_camber_loc, max_camber, x_cos_coords, smoothing_fac)
    thickness_new = morph(x_common, thickness_seed, max_thickness_loc, max_thickness, x_cos_coords, smoothing_fac)

    #analytical solution (works better for camber)
    camber_new = analytical_camber(x_cos_coords, max_camber, max_camber_loc)

    #based on new thickness and camber distributions, rebuild coordinates
    xu_morph, yu_morph, xl_morph, yl_morph = rebuild(x_cos_coords, camber_new, thickness_new)

    #re-invert airfoil
    xu_morph, yu_morph, xl_morph, yl_morph = xu_morph, -yl_morph, xl_morph, -yu_morph

    #fix issues with leading edge
    xu_morph, yu_morph, xl_morph, yl_morph = fix_le(xu_morph, yu_morph, xl_morph, yl_morph)

    #re-rotate airfoil to seed angle of attack
    if abs(np.degrees(aoa)) > 0.0:
        xu_morph, yu_morph = unrotate_airfoil(xu_morph, yu_morph, aoa)
        xl_morph, yl_morph = unrotate_airfoil(xl_morph, yl_morph, aoa)

    return xu_morph, yu_morph, xl_morph, yl_morph, camber_new, thickness_new, x_cos_coords

#make sure inputted design parameters are withing constrained region (REMOVE ONCE DONE IN OPTIMIZER)
# def check_constraints(des):
#     assert des.max_thickness > des.max_camber, "thickness must exceed camber"
#     assert des.max_thickness >= 1.0 * des.max_camber, "thickness/camber ratio too low"
#     assert 0.06 <= des.max_thickness <= 0.25
#     assert 0.00 <= des.max_camber <= 0.15
#     assert 0.15 <= des.max_thickness_loc <= 0.45
#     assert 0.30 <= des.max_camber_loc <= 0.70
#     assert des.max_thickness_loc < des.max_camber_loc, "thickness peak should be forward of camber peak"

def plot_airfoil(des, phase):
    #update correct path in config.py
    x_seed, y_seed = load_airfoil_dat(PHASE1_SEED_PATH)

    #get seed airfoil and new airfoil
    x_common, camber_seed, thickness_seed, aoa = get_seed(x_seed, y_seed)
    xu_morph, yu_morph, xl_morph, yl_morph, camber_new, thickness_new, x_cos_coords = new_airfoil(thickness_seed, 
    x_common, des, 160, smoothing_fac= None, aoa=aoa)

    #get coordinates
    points = get_coords(xu_morph, xl_morph, yu_morph, yl_morph, phase)

    #plot
    plt.figure()
    plt.plot(points[:,0], points[:,1], '-')
    plt.axis("equal")
    plt.xlabel("x/c, dimensionless")
    plt.ylabel("y/c, dimensionless")
    plt.grid(True)
    plt.show()

#function to return thickness and camber distributions based on seed coordinates
def get_seed(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    #get seed angle of attack (for re-rotation later)
    aoa = get_aoa(x, y)
    #print(f"Detected Seed Airfoil AoA: {np.degrees(aoa):.2f} degrees")

    #remove original angle of attack (functions only work at 0 degrees)
    if abs(np.degrees(aoa)) > 0.0:
        x, y = rotate_airfoil(x, y, aoa)

    #uninvert airfoil (putting in standard orientation)
    y = -y

    x, y = normalize(x, y)
    xu_seed, yu_seed, xl_seed, yl_seed = split_ul(x, y)
    x_common, camber_seed, thickness_seed = get_c_t(xu_seed, yu_seed, xl_seed, yl_seed, n_common=200)
    return x_common, camber_seed, thickness_seed, aoa

def normalize(x, y):
    x_min, x_max = x.min(),x.max()
    chord = x_max - x_min

    #normalize with respect to the chord
    x = (x - x_min)/chord
    y = y/chord

    return x, y

def split_ul(x, y):
    #find leading edge index
    le_idx = np.argmin(x)
    n = len(x)

    #if in Selif format
    if 0 < le_idx < n-1:
        #slice from TE to LE
        seg_a = slice(0, le_idx + 1)
        #slice from LE to TE
        seg_b = slice(le_idx, n)

        #flip so all coordinates go from LE to TE
        xa, ya = x[seg_a][::-1], y[seg_a][::-1]
        xb, yb = x[seg_b], y[seg_b]

        #determine which is upper/lower surface
        if np.mean(ya) > np.mean(yb):
            xu, yu = xa, ya
            xl, yl = xb, yb
        else:
            xu, yu = xb, yb
            xl, yl = xa, ya

#if not in Selig format
    else:
        raise ValueError("Coordinates must be in Selig format")
    
    #unique values are required for fitting splines
    xu, yu = deduplicate(xu, yu)
    xl, yl = deduplicate(xl, yl)

    return xu, yu, xl, yl

def deduplicate(x, y):
    #find index of unique values
    _,idx = np.unique(x, return_index=True)
    return x[idx], y[idx]

def arc_length(x, y):
    """Cumulative arc length along a surface, normalized to [0, 1]."""
    dx = np.diff(x)
    dy = np.diff(y)
    ds = np.sqrt(dx**2 + dy**2)
    s = np.concatenate([[0.0], np.cumsum(ds)])
    s /= s[-1]  # normalize to [0, 1]
    return s

def resample_surface(x, y, n):
    #resample surfaces using arc length 
    s = arc_length(x, y)
    s_new = cosine_spacing(n)  #denser at LE (s=0) and TE (s=1)
    
    x_spl = PchipInterpolator(s, x)
    y_spl = PchipInterpolator(s, y)
    
    return x_spl(s_new), y_spl(s_new)

def get_c_t(xu, yu, xl, yl, n_common):

    #resample each surface to the same number of points
    xu_r, yu_r = resample_surface(xu, yu, n_common)
    xl_r, yl_r = resample_surface(xl, yl, n_common)

    #now interpolate both onto a shared x grid using Pchip
    #(surfaces are now smooth so x-space interpolation works fine)
    x_common = cosine_spacing(n_common)
    
    yu_interp = PchipInterpolator(xu_r, yu_r, extrapolate=False)(x_common)
    yl_interp = PchipInterpolator(xl_r, yl_r, extrapolate=False)(x_common)
    
    yu_interp = np.nan_to_num(yu_interp, nan=0.0)
    yl_interp = np.nan_to_num(yl_interp, nan=0.0)

    camber = 0.5 * (yu_interp + yl_interp)
    thickness = yu_interp - yl_interp

    #pin leading edge at 0
    camber[0] = 0.0
    thickness[0] = 0.0
    thickness = np.clip(thickness, 0, None)

    return x_common, camber, thickness

#using an analytic function works better than spline interppolation for the camberline
def analytical_camber(x, max_camber, max_camber_loc):
   #NACA 4 digit style parabolic camber line
    p = max_camber_loc
    m = max_camber
    camber = np.where(
        x < p,
        m / p**2 * (2*p*x - x**2),
        m / (1-p)**2 * ((1 - 2*p) + 2*p*x - x**2)
    )
    return camber

def cosine_spacing(n):
    beta = np.linspace(0, np.pi, n)
    return 1/2 * (1 - np.cos(beta))

#uses spline interpolation to return either new camber or thickness distribution based on design parameters
def morph(x_seed, val_seed, x_new, val_new, x_cos_coords, s):
    #x_seed = common evaluation coordinates for seed
    #val_seed = seed values for camber/thickness
    #x_new = desired max camber/thickness location
    #val_new = desired max camber/thickness
    #x_cos_coords = cosine spacing points for new airfoil dist.

    n_pts = len(x_seed)
    #s_val = s if s is not None else n_pts * (1e-5 ** 2)

    #find seed peak location
    peak_idx = np.argmax(np.abs(val_seed))
    x_peak_seed = x_seed[peak_idx]
    val_peak_seed = val_seed[peak_idx]

    #NEED TO ADJUST LEADING EDGE, SHOULD NOT BE FORCED TO 0??
    #use a cubic spline to smoothly fit points between 0, adjusted max value, and 1 (using 5 control points, can be adjusted later)
    x_map = np.array([0.0, x_peak_seed*0.5, x_peak_seed, x_peak_seed + (1.0 - x_peak_seed)*0.5, 1.0])
    x_map_adj = np.array([0.0, x_new*0.5, x_new, x_new + (1.0 - x_new)*0.5, 1.0])
    morph_surf = PchipInterpolator(x_map, x_map_adj)
    x_morph = np.clip(morph_surf(x_seed), 0, 1)

    #scale amplitude values
    scale = val_new / val_peak_seed
    val_morph = val_seed * scale

    #sort values 
    sort_idx = np.argsort(x_morph)
    x_morph_sort = x_morph[sort_idx]
    val_morph_sort = val_morph[sort_idx]

    #remove duplicate values (required for splines)
    x_morph_sort, unique_idx = np.unique(x_morph_sort, return_index=True)
    val_morph_sort = val_morph_sort[unique_idx]

    #use Pchip instead of UnivariateSpline to prevent overshoot
    spl_fit = PchipInterpolator(x_morph_sort, val_morph_sort, extrapolate=False)
    final_morph = spl_fit(x_cos_coords)
    final_morph = np.nan_to_num(final_morph, nan=0.0)

    return final_morph

#function fixes most osciallations at leading edge by preventing doubling back and negative x-values
def fix_le(xu, yu, xl, yl, n=160):
    def clean_and_resample(x, y, n):
        keep = [0]
        for i in range(1, len(x)):
            #keep point only if x increases and stays non-negative
            if x[i] > x[keep[-1]] and x[i] >= 0.0:
                keep.append(i)
        x_clean = x[keep]
        y_clean = y[keep]

        x_new = cosine_spacing(n)
        #clip coordinates to stay withing the cleaned range
        x_new = np.clip(x_new, x_clean[0], x_clean[-1])
        #fits Pchip spline through cleaned coordinates and evaluates it at all x_new points
        y_new = PchipInterpolator(x_clean, y_clean)(x_new)

        return x_new, y_new

    xu_fixed, yu_fixed = clean_and_resample(xu, yu, n)
    xl_fixed, yl_fixed = clean_and_resample(xl, yl, n)

    #trim trailing edge to prevent irregular coordinates 
    te_cutoff = 0.99 #trimming starting at 99% of chord)
    #trim coordinates
    mask_u = xu_fixed <= te_cutoff
    mask_l = xl_fixed <= te_cutoff
    xu_fixed = xu_fixed[mask_u]
    yu_fixed = yu_fixed[mask_u]
    xl_fixed = xl_fixed[mask_l]
    yl_fixed = yl_fixed[mask_l]

    return xu_fixed, yu_fixed, xl_fixed, yl_fixed

#rebuild airfoil based on new camber and thickness distributions
def rebuild(x, camber, thickness):
    #linspace to compute dydx (using cosine coordinates blows this up)
    x_uniform = np.linspace(0, 1, len(x))
    #interpolate camber distribution and evaluate x_uniform
    camber_uniform = PchipInterpolator(x, camber)(x_uniform)

    #calculate gradient and map it back to cosine coordinates
    dydx_uniform = np.gradient(camber_uniform, x_uniform)
    dydx = PchipInterpolator(x_uniform, dydx_uniform)(x)
    #prevent slope from going beyond +-2 rad
    dydx = np.clip(dydx, -2.0, 2.0)
    #force trailing edge and leading edge to have 0 slope (thickness added vertically instead of normal here)
    dydx[0] = 0.0
    dydx[-1] = 0.0

    #compute angle theta
    theta = np.arctan(dydx)

    #blend: 0 = pure vertical, 1 = full perpendicular
    blend = np.ones_like(x)
    #use vertical application for first 30% and last 10% of chord (otherwise many oscillations)
    le_end = np.searchsorted(x, 0.30)
    te_start = np.searchsorted(x, 0.90)
    blend[:le_end] = np.linspace(0, 1, le_end)
    blend[te_start:] = np.linspace(1, 0, len(x) - te_start)
    theta_blended = theta * blend

    half_t = 0.5 * thickness

    #generate coordinates by adding thickness normal to camberline
    xu = x - half_t * np.sin(theta_blended)
    yu = camber + half_t * np.cos(theta_blended)
    xl = x + half_t * np.sin(theta_blended)
    yl = camber - half_t * np.cos(theta_blended)

    return xu, yu, xl, yl

def trim_te(xu, yu, xl, yl, te_cutoff=0.99):
    #cut any points past te_cutoff on either surface (MSES will remesh TE to close surfaces)
    mask_u = xu <= te_cutoff
    mask_l = xl <= te_cutoff
    return xu[mask_u], yu[mask_u], xl[mask_l], yl[mask_l]

def get_aoa(x, y):
    #estimate the angle of attack from the geometry by finding the chord line and computing its angle
    le_idx = np.argmin(x)
    te_idx = np.argmax(x)
    
    dx = x[te_idx] - x[le_idx]
    dy = y[te_idx] - y[le_idx]
    
    #print(np.arctan2(dy, dx))

    return np.arctan2(dy, dx)  #radians

def rotate_airfoil(x, y, angle_rad):
    #rotate coordinates by -angle_rad to align chord with x-axis
    cos_a = np.cos(-angle_rad)
    sin_a = np.sin(-angle_rad)
    
    x_rot = x * cos_a - y * sin_a
    y_rot = x * sin_a + y * cos_a
    
    return x_rot, y_rot

def unrotate_airfoil(x, y, angle_rad):
    #rotate back by +angle_rad after processing
    cos_a = np.cos(angle_rad)
    sin_a = np.sin(angle_rad)
    
    x_rot = x * cos_a - y * sin_a
    y_rot = x * sin_a + y * cos_a
    
    return x_rot, y_rot

#PHASE TWO: TWO ELEMENT, OPTIMIZING ROTATING ELEMENT
def scale_airfoil(points, scale, origin=(0.0, 0.0)):

    origin = np.array(origin)
    return origin + scale * (points - origin)

def translate_airfoil(points, dx, dy):
    translated_points = points.copy()

    #shift points by dx and dy
    translated_points[:,0] = translated_points[:,0] + dx
    translated_points[:,1] = translated_points[:,1] + dy

    return translated_points

#FOR PHASE 3 (IN PROGRESS)
def rotate_airfoil_phase3(points, angle_deg, pivot=(0.0,0.0)):

    #convert to radians
    angle_rad = np.radians(angle_deg)
    rotation_matrix = np.array([[np.cos(angle_rad), -np.sin(angle_rad)],
                               [np.sin(angle_rad), np.cos(angle_rad)]])
    
    pivot = np.array(pivot)

    shifted_points = points - pivot
    #multiply each point by the rotation matrix transpose
    rotated_points = shifted_points @ rotation_matrix.T
    rotated_points = rotated_points + pivot

    return rotated_points

#FOR IMPORTING AND EXPORTING COORDINATES
def get_coords(xu_morph, xl_morph, yu_morph, yl_morph, phase):
    #get data from second element location dictionary
    h = SECOND_ELM_LOC["horizontal"]
    v = SECOND_ELM_LOC["vertical"]
    #create arrays with upper and lower points (in Selig format)
    upper = np.column_stack((xu_morph[::-1], yu_morph[::-1]))
    lower = np.column_stack((xl_morph, yl_morph))
    points = np.vstack((upper, lower[1:]))
    
    if phase == 2:
        #rotate airfoil if needed (rotating about leading edge)
        #points_p2 = rotate_airfoil_phase3(points_p2, 10, pivot=(0.0,0.0))

        points_scaled = scale_airfoil(points, scale=0.435, origin=(0.0, 0.0))
        translated_pts = translate_airfoil(points_scaled, h, v)
        points = translated_pts
    
    return points

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

def export_mses_geometry(filename, elements):

    with open(filename, "w") as f:

        f.write(f"{len(elements)}\n")

        for i, element in enumerate(elements):

            f.write(f"element_{i+1}\n")

            for point in element:
                f.write(f"{point[0]:.6f} {point[1]:.6f}\n")

            f.write("\n") 