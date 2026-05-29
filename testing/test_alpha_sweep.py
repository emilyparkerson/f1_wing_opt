"""
Alpha sweep: for each config, try MSES at several angles of attack at the
seed design. MSES is very sensitive to the starting alpha for loaded /
cambered sections -- a config that fails at alpha=0 often converges at a
small nonzero alpha. This tells us whether the failures are an incidence
problem (fixable in config) or a geometry problem (needs more work).

Run from project root:  python .\testing\alpha_sweep.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from phase1.phase1 import P1_IB_CONFIG, P1_OB_CONFIG
from phase2.phase2 import P2_RE_IB_CONFIG, P2_RE_OB_CONFIG
from setup.aero_interface import run_mses, run_mses_elements

ALPHAS = [-10.0, -8.0, -6.0, -5.0, -4.0, -3.0, -2.5, -2.0, -1.0, 0.0, 1.0, 2.0]

def sweep(tag, config):
    print("\n" + "="*60)
    print(f"ALPHA SWEEP: {tag}  (mach={config['mach']}, Re={config['reynolds']:.0f})")
    print("="*60)
    seed_design = config["seed_design"]
    for a in ALPHAS:
        try:
            if "elements" in config:
                aero = run_mses_elements(design=seed_design, elements=config["elements"],
                                         name=f"sw_{tag}_{a}", alpha=a,
                                         mach=config["mach"], reynolds=config["reynolds"])
            else:
                aero = run_mses(design=seed_design, name=f"sw_{tag}_{a}", alpha=a,
                                mach=config["mach"], reynolds=config["reynolds"],
                                seed_airfoil=config["seed_airfoil"])
            if aero.cl is None:
                print(f"  alpha={a:+5.1f}  ->  FAILED")
            else:
                print(f"  alpha={a:+5.1f}  ->  Cl={aero.cl:+.4f}  Cd={aero.cd:.5f}")
        except Exception as e:
            print(f"  alpha={a:+5.1f}  ->  EXCEPTION {type(e).__name__}: {e}")

if __name__ == "__main__":
    #sweep("P1_OB", P1_OB_CONFIG)        # the single-element one that failed
    sweep("P2_IB", P2_RE_IB_CONFIG) # two-element