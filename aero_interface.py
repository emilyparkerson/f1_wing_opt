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


# runs MSES and returns cl/cd values
def run_mses(name="candidate_airfoil",
             alpha=2.0,
             mach=0.2,
             reynolds=1e6):

    # create geometry collection object
    geo_col = GeometryCollection()

    # temporary placeholder airfoil
    # later this will be replaced with our optimized geometry
    polyline = geo_col.add_polyline(source="naca23012-il")
    airfoil = polyline.add_polyline_airfoil()

    # create MEA object for MSES
    mea = geo_col.add_mea([airfoil])

    # meshing settings
    mset_settings = MSETSettings(
        multi_airfoil_grid={
            "Airfoil-1": AirfoilMSETMeshingParameters()
        },
        airfoil_side_points=180
    )

    # solver settings
    mses_settings = MSESSettings(
        xtrs={"Airfoil-1": [1.0, 1.0]},
        Ma=mach,
        Re=reynolds,
        alfa=alpha,
        alfa_Cl_mode=0,
        timeout=60.0
    )

    # Tecplot output off for now
    mplot_settings = MPLOTSettings(
        Tecplot=True
    )

    try:

        print("Running MSES...")

        # run aerodynamic analysis
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

        # convergence checks
        if not aero_data["converged"]:
            print("MSES did not converge")
            return AeroResult(cl=None, cd=None)

        if aero_data["errored_out"]:
            print("MSES errored out")
            return AeroResult(cl=None, cd=None)

        if aero_data["timed_out"]:
            print("MSES timed out")
            return AeroResult(cl=None, cd=None)

        # extract aero coefficients
        cl = aero_data["Cl"]
        cd = aero_data["Cd"]

        print(f"Cl = {cl:.4f}")
        print(f"Cd = {cd:.5f}")

        # store results in dataclass
        return AeroResult(cl=cl, cd=cd)

    except Exception as e:

        print("MSES failed")
        print(e)

        return AeroResult(cl=None, cd=None)