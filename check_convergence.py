"""
Single MSES call on the current seed flap + main winner pair.
No morph, no BO, no geometry.py. Both airfoils loaded straight from
their .dat files and handed to MSES exactly as drawn.

Run from project root:
    python check_converge.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from setup.aero_interface import run_mses_elements
from phase2.phase2 import P2_RE_OB_CONFIG

# Both elements fixed, loaded straight from disk.
elements = [
    {"role": "fixed",
     "coords_path": P2_RE_OB_CONFIG["elements"][0]["seed_airfoil"],
     "place": "main"},
    {"role": "fixed",
     "coords_path": P2_RE_OB_CONFIG["elements"][1]["coords_path"],
     "place": "main"},
]

print("=" * 60)
print("MSES convergence check: seed flap + main winner, no morph")
print("=" * 60)
print(f"  flap: {elements[0]['coords_path']}")
print(f"  main: {elements[1]['coords_path']}")
print(f"  alpha={P2_RE_OB_CONFIG['alpha']}  mach={P2_RE_OB_CONFIG['mach']}  "
      f"Re={P2_RE_OB_CONFIG['reynolds']:.0f}")
print()

result = run_mses_elements(
    design=None,
    elements=elements,
    name="converge_check",
    alpha=P2_RE_OB_CONFIG["alpha"],
    mach=P2_RE_OB_CONFIG["mach"],
    reynolds=P2_RE_OB_CONFIG["reynolds"],
    xtr_upper=P2_RE_OB_CONFIG["xtr_upper"],
    xtr_lower=P2_RE_OB_CONFIG["xtr_lower"],
    plot_geometry=True,
)

print()
print("=" * 60)
if result.cl is not None:
    print(f"CONVERGED: Cl = {result.cl:+.5f}, Cd = {result.cd:.5f}")
else:
    print("DID NOT CONVERGE (see MSES log tail above)")
print("=" * 60)