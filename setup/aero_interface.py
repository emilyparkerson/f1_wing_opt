import os
import tempfile
import numpy as np
import matplotlib.pyplot as plt

from pymead.analysis.calc_aero_data import (
    calculate_aero_data,
    MSETSettings,
    MSESSettings,
    MPLOTSettings,
    AirfoilMSETMeshingParameters
)

from pymead.core.geometry_collection import GeometryCollection

from setup.design_vars import AeroResult

from setup.geometry import (
    load_airfoil_dat,
    get_seed,
    new_airfoil,
    get_coords
)


# -------------------------------------------------
# RUN MSES
# -------------------------------------------------

def run_mses(
        design,
        name="candidate_airfoil",
        alpha=0.0,
        mach=0.081627322,
        reynolds=789563.2304,
        plot_geometry=False,
        plot_comparison=False,
        seed_airfoil=''):

    '''
    print("\nCurrent Design:")
    print(f"Max Camber:          {design.max_camber}")
    print(f"Max Camber Location: {design.max_camber_loc}")
    print(f"Max Thickness:       {design.max_thickness}")
    print(f"Max Thickness Loc:   {design.max_thickness_loc}")
    '''

    geo_col = GeometryCollection()

    # -------------------------------------------------
    # LOAD SEED AIRFOIL
    # -------------------------------------------------

    x_seed, y_seed = load_airfoil_dat(seed_airfoil)

    # -------------------------------------------------
    # GET SEED CAMBER/THICKNESS
    # -------------------------------------------------

    x_common, camber_seed, thickness_seed, aoa = get_seed(
        x_seed,
        y_seed
    )

    # -------------------------------------------------
    # GENERATE NEW AIRFOIL
    # -------------------------------------------------

    xu_morph, yu_morph, xl_morph, yl_morph, camber_new, thickness_new, x_cos_coords = new_airfoil(
        thickness_seed,
        x_common,
        design,
        160,
        smoothing_fac=None,
        aoa=aoa
    )

    # -------------------------------------------------
    # CONVERT TO SELIG FORMAT COORDS
    # -------------------------------------------------

    raw_coords = get_coords(
        xu_morph,
        xl_morph,
        yu_morph,
        yl_morph,
        phase=1
    )

    # -------------------------------------------------
    # PLOT GEOMETRY
    # -------------------------------------------------

    if plot_geometry:
        plt.figure(figsize=(10, 4))
        plt.plot(raw_coords[:, 0],raw_coords[:, 1],linewidth=2)
        plt.axis("equal")
        plt.grid(True)
        plt.xlabel("x/c")
        plt.ylabel("y/c")
        plt.title(f"{name} — morphed airfoil")
        plt.show()

    # -------------------------------------------------
    # SAVE DAT FILE
    # -------------------------------------------------

    dat_file = os.path.join(tempfile.gettempdir(),f"{name}_input.dat")
    np.savetxt(dat_file, raw_coords)

    # -------------------------------------------------
    # LOAD INTO PYMEAD
    # -------------------------------------------------

    polyline = geo_col.add_polyline(source=dat_file)
    airfoil = polyline.add_polyline_airfoil()
    print("\nAirfoil object created successfully")
    mea = geo_col.add_mea([airfoil])
    coords = np.array(airfoil.coords)

    # -------------------------------------------------
    # OPTIONAL COMPARISON PLOT
    # -------------------------------------------------

    if plot_comparison:
        fig, axes = plt.subplots(1,2,figsize=(14, 4))
        axes[0].plot(x_seed,y_seed)
        axes[0].set_title("Seed Airfoil")
        axes[0].axis("equal")
        axes[0].grid(True)
        axes[1].plot(coords[:, 0],coords[:, 1])
        axes[1].set_title("Morphed Airfoil")
        axes[1].axis("equal")
        axes[1].grid(True)
        plt.suptitle(f"{name} — geometry comparison")
        plt.show()

    # -------------------------------------------------
    # MSES SETTINGS
    # -------------------------------------------------

    mset_settings = MSETSettings(
        multi_airfoil_grid={"Airfoil-1": 
            AirfoilMSETMeshingParameters()},
        airfoil_side_points=240
    )

    mses_settings = MSESSettings(

        xtrs={
            "Airfoil-1": [1.0, 1.0]
        },

        Ma=mach,
        Re=reynolds,
        alfa=alpha,
        alfa_Cl_mode=0,
        timeout=800.0
    )

    # pymead 2.0.0b13 bug workaround
    # MPLOTSettings uses "streamline_grid"
    # but pymead internally expects "Streamline_Grid"

    mplot_settings = {
        "timeout":         15.0,
        "grid_stats":      False,
        "Mach":            False,
        "Streamline_Grid": False,
        "Grid":            False,
        "Grid_Zoom":       False,
        "flow_field":      False,
        "Tecplot":         False,
        "Paraview":        False,
        "CPK":             False,
    }

    # -------------------------------------------------
    # RUN MSES
    # -------------------------------------------------

    try:

        print("\nRunning MSES...")

        aero_data, logs = calculate_aero_data(

            conn=None,
            airfoil_coord_dir=tempfile.gettempdir(),
            airfoil_name=name,
            mea=mea,
            tool="MSES",
            mset_settings=mset_settings,
            mses_settings=mses_settings,
            mplot_settings=mplot_settings,
            export_Cp=False,
            save_aero_data=True,
        )
        '''
        print("\nAero Data:")
        print(aero_data)
        '''

        if aero_data.get("errored_out", False):

            print("MSES errored out")

            return AeroResult(
                cl=None,
                cd=None,
                coords=coords
            )

        if aero_data.get("timed_out", False):
            print("MSES timed out")
            return AeroResult(cl=None,cd=None,coords=coords)

        if not aero_data.get("converged", False):
            print("MSES did not converge")
            return AeroResult(cl=None,cd=None,coords=coords)

        cl = aero_data["Cl"]
        cd = aero_data["Cd"]

        print(f"\nCl = {cl:.5f}")
        print(f"Cd = {cd:.5f}")

        return AeroResult(cl=cl,cd=cd,coords=coords)

    except Exception as e:

        print("\nMSES failed with exception:")
        print(e)

        return AeroResult(cl=None,cd=None,coords=coords)
