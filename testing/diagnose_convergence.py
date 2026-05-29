"""
Pinpoint WHY MSES isn't converging, one config at a time.

Run:  python diagnose_convergence.py
It will, for each phase config:
  1. build the geometry (catch geometry errors)
  2. register with pymead (catch geometry-rejection errors)
  3. call MSES once at the seed design (catch solver/settings errors)
  4. print the raw aero_data dict so we see converged / errored_out / etc.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import traceback
import numpy as np

from phase1.phase1 import P1_IB_CONFIG, P1_OB_CONFIG
# phase 2 may need winner .dat files that don't exist yet; guard it
try:
    from phase2.phase2 import P2_RE_IB_CONFIG, P2_RE_OB_CONFIG
    HAVE_P2 = True
except Exception as e:
    print("could not import phase2:", e); HAVE_P2 = False

from setup.aero_interface import run_mses, run_mses_elements


def diagnose(tag, config):
    print("\n" + "="*60)
    print(f"DIAGNOSING: {tag}")
    print("="*60)
    print(f"  alpha={config['alpha']}  mach={config['mach']}  Re={config['reynolds']}")
    print(f"  ref_vals keys: {list(config['ref_vals'].keys())}")
    # check the ref_vals the scorer will need
    for k in ("df", "cd"):
        if k not in config["ref_vals"]:
            print(f"  *** ref_vals is MISSING '{k}' -> scoring will KeyError ***")

    seed_design = config["seed_design"]
    try:
        if "elements" in config:
            aero = run_mses_elements(
                design=seed_design,
                elements=config["elements"],
                name=f"diag_{tag}",
                alpha=config["alpha"], mach=config["mach"], reynolds=config["reynolds"],
            )
        else:
            aero = run_mses(
                design=seed_design,
                name=f"diag_{tag}",
                alpha=config["alpha"], mach=config["mach"], reynolds=config["reynolds"],
                seed_airfoil=config["seed_airfoil"],
            )
        print(f"  RESULT: cl={aero.cl}  cd={aero.cd}")
        if aero.cl is None:
            print("  -> MSES returned a failure (see messages above for which check tripped)")
        else:
            print("  -> CONVERGED")
    except Exception as e:
        print(f"  EXCEPTION before/around MSES: {type(e).__name__}: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    diagnose("P1_IB", P1_IB_CONFIG)
    diagnose("P1_OB", P1_OB_CONFIG)
    if HAVE_P2:
        diagnose("P2_IB", P2_RE_IB_CONFIG)
        diagnose("P2_OB", P2_RE_OB_CONFIG)