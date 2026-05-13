import numpy as np
import matplotlib.pyplot as plt
import tempfile

from pymead.analysis.calc_aero_data import (
    calculate_aero_data,
    MSETSettings,
    MSESSettings,
    MPLOTSettings,
    AirfoilMSETMeshingParameters
)

from pymead.core.geometry_collection import GeometryCollection

from design_vars import AeroResult


# -------------------------------------------------
# OPTIONAL CUSTOM NACA GENERATOR
# CURRENTLY DISABLED
# -------------------------------------------------

# def generate_naca4(m, p, t, n_points=200):
#
#     beta = np.linspace(0.0, np.pi, n_points)
#
#     x = 0.5 * (1.0 - np.cos(beta))
#
#     yt = (
#         5.0 * t * (
#             0.2969 * np.sqrt(x)
#             - 0.1260 * x
#             - 0.3516 * x**2
#             + 0.2843 * x**3
#             - 0.1036 * x**4
#         )
#     )
#
#     yc = np.zeros_like(x)
#     dyc_dx = np.zeros_like(x)
#
#     for i in range(len(x)):
#
#         if x[i] < p:
#
#             yc[i] = (
#                 m / p**2
#                 * (2.0 * p * x[i] - x[i]**2)
#             )
#
#             dyc_dx[i] = (
#                 2.0 * m / p**2
#                 * (p - x[i])
#             )
#
#         else:
#
#             yc[i] = (
#                 m / (1.0 - p)**2
#                 * (
#                     (1.0 - 2.0 * p)
#                     + 2.0 * p * x[i]
#                     - x[i]**2
#                 )
#             )
#
#             dyc_dx[i] = (
#                 2.0 * m / (1.0 - p)**2
#                 * (p - x[i])
#             )
#
#     theta = np.arctan(dyc_dx)
#
#     xu = x - yt * np.sin(theta)
#     yu = yc + yt * np.cos(theta)
#
#     xl = x + yt * np.sin(theta)
#     yl = yc - yt * np.cos(theta)
#
#     x_coords = np.concatenate([
#         xu[::-1],
#         xl[1:]
#     ])
#
#     y_coords = np.concatenate([
#         yu[::-1],
#         yl[1:]
#     ])
#
#     coords = np.column_stack((x_coords, y_coords))
#
#     le_idx = np.argmin(coords[:,0])
#
#     coords[le_idx] = [0.0, 0.0]
#
#     return coords


# -------------------------------------------------
# RUN MSES
# -------------------------------------------------

def run_mses(design,
             name="naca23012-il",
             alpha=0.0,
             mach=0.2,
             reynolds=1e6):

    geo_col = GeometryCollection()

    print("\nCurrent Design:")

    print(f"Max Camber: {design.max_camber}")
    print(f"Max Camber Location: {design.max_camber_loc}")

    print(f"Max Thickness: {design.max_thickness}")
    print(f"Max Thickness Location: {design.max_thickness_loc}")

    # -------------------------------------------------
    # OPTIONAL CUSTOM GENERATED AIRFOIL
    # CURRENTLY DISABLED
    # -------------------------------------------------

    # coords = generate_naca4(
    #     m=design.max_camber,
    #     p=design.max_camber_loc,
    #     t=design.max_thickness,
    #     n_points=200
    # )
    #
    # plt.figure(figsize=(10,4))
    #
    # plt.plot(
    #     coords[:,0],
    #     coords[:,1],
    #     linewidth=2
    # )
    #
    # plt.axis('equal')
    #
    # plt.grid(True)
    #
    # plt.show()
    #
    # dat_file = tempfile.gettempdir() + "/candidate_airfoil.dat"
    #
    # np.savetxt(dat_file, coords)
    #
    # polyline = geo_col.add_polyline(
    #     source=dat_file
    # )

    # -------------------------------------------------
    # KNOWN WORKING AIRFOIL
    # -------------------------------------------------

    polyline = geo_col.add_polyline(
        source="naca23012-il"
    )

    airfoil = polyline.add_polyline_airfoil()

    print("\nAirfoil object created successfully")

    print(airfoil)

    mea = geo_col.add_mea([airfoil])

    # -------------------------------------------------
    # EXTRACT COORDS FOR PLOTTING
    # -------------------------------------------------

    coords = airfoil.coords

    # -------------------------------------------------
    # MSET SETTINGS
    # -------------------------------------------------

    mset_settings = MSETSettings(
        multi_airfoil_grid={
            "Airfoil-1": AirfoilMSETMeshingParameters()
        },
        airfoil_side_points=180
    )

    # -------------------------------------------------
    # MSES SETTINGS
    # -------------------------------------------------

    mses_settings = MSESSettings(
        xtrs={"Airfoil-1": [1.0, 1.0]},
        Ma=mach,
        Re=reynolds,
        alfa=alpha,
        alfa_Cl_mode=0,
        timeout=300.0
    )

    # -------------------------------------------------
    # MPLOT SETTINGS
    # -------------------------------------------------

    mplot_settings = MPLOTSettings(
        Tecplot=True
    )

    # -------------------------------------------------
    # RUN MSES
    # -------------------------------------------------

    try:

        print("\nRunning MSES...")

        aero_data, logs = calculate_aero_data(
            conn=None,
            airfoil_coord_dir=tempfile.gettempdir(),
            airfoil_name="naca23012-il",
            mea=mea,
            tool="MSES",
            mset_settings=mset_settings,
            mses_settings=mses_settings,
            mplot_settings=mplot_settings,
            export_Cp=False,
            save_aero_data=True,
        )

        print("\nAero Data:")
        print(aero_data)

        if not aero_data["converged"]:

            print("MSES did not converge")

            return AeroResult(
                cl=None,
                cd=None,
                coords=None
            )

        if aero_data["errored_out"]:

            print("MSES errored out")

            return AeroResult(
                cl=None,
                cd=None,
                coords=None
            )

        if aero_data["timed_out"]:

            print("MSES timed out")

            return AeroResult(
                cl=None,
                cd=None,
                coords=None
            )

        cl = aero_data["Cl"]
        cd = aero_data["Cd"]

        print(f"\nCl = {cl:.5f}")
        print(f"Cd = {cd:.5f}")

        return AeroResult(
            cl=cl,
            cd=cd,
            coords=coords
        )

    except Exception as e:

        print("\nMSES failed")
        print(e)

        return AeroResult(
            cl=None,
            cd=None,
            coords=None
        )