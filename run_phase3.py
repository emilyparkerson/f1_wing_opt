"""
Phase 3 flap deflection sweep -- INDEPENDENT per side.

For each side (OB and IB) separately, this script:
  1. Loads the phase-2 winning two-element configuration.
  2. Sweeps the flap deflection from delta=0 down by STEP_DEG.
  3. Runs MSES at each angle with a 20-second timeout.
  4. Records angle, cl, cd, score, converged-flag.
  5. Stops when score drops for N consecutive steps or
     N consecutive MSES failures occur.

Each side gets its own CSV.  After both sweeps complete you can pick
a compromise angle by inspecting the two tables.

Run from project root on the phase-3 branch:
    python run_phase3.py
"""
import os
import sys
import csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np

from setup.aero_interface import run_mses_elements
from setup.scoring import scoring_p3
from setup.geometry import (
    load_airfoil_dat,
    get_aoa,
    rotate_airfoil_phase3,
)

HERE = os.path.dirname(os.path.abspath(__file__))


# --- sweep parameters ---
STEP_DEG           = 0.25
MAX_STEPS          = 200
STOP_AFTER_N_DROPS = 3
STOP_AFTER_N_FAILS = 3000
MSES_TIMEOUT_SEC   = 20.0   # NOTE: also set timeout in MSESSettings if not already


OB_CONFIG = {
    "label":      "OB",
    "winner_dat": os.path.join(HERE, "phase3", "phase2_winner_OB.dat"),
    "main_dat":   os.path.join(HERE, "phase3", "phase1_winner_OB.dat"),
    "alpha":    0.0,
    "mach":     0.08276085807,
    "reynolds": 2506449.402,
    "xtr_upper": 1.0,
    "xtr_lower": 1.0,
    "ref_vals": {
        "df": 2.76157,
        "cd": 0.02577,
    },
    "plot_geometry": True,
}

IB_CONFIG = {
    "label":      "IB",
    "winner_dat": os.path.join(HERE, "phase3", "phase2_winner_IB.dat"),
    "main_dat":   os.path.join(HERE, "phase3", "phase1_winner_IB.dat"),
    "alpha":    -2.5,
    "mach":     0.0630088633,
    "reynolds": 1908251.454,
    "xtr_upper": 0.05,
    "xtr_lower": 0.05,
    "ref_vals": {
        "df": 3.04152,
        "cd": 0.03028,
    },
    "plot_geometry": True,
}


# --------------------------------------------------------------------------
def split_elements(coords, gap_thresh=0.1):
    d = np.linalg.norm(np.diff(coords, axis=0), axis=1)
    breaks = np.where(d > gap_thresh)[0] + 1
    return np.split(coords, breaks)


def load_side(cfg):
    """Extract flap (Airfoil-1) + main and record flap LE + Z-angle."""
    x_w, y_w = load_airfoil_dat(cfg["winner_dat"])
    pieces = split_elements(np.column_stack([x_w, y_w]))

    if len(pieces) >= 2:
        flap = pieces[0]
        if cfg.get("main_dat") and os.path.exists(cfg["main_dat"]):
            mx, my = load_airfoil_dat(cfg["main_dat"])
            main = np.column_stack([mx, my])
        else:
            main = pieces[1]
    else:
        flap = pieces[0]
        mx, my = load_airfoil_dat(cfg["main_dat"])
        main = np.column_stack([mx, my])

    le_idx = int(np.argmin(flap[:, 0]))
    cfg["flap_coords_z"]       = flap
    cfg["main_coords"]         = main
    cfg["flap_le"]             = flap[le_idx].copy()
    cfg["installed_aoa_z_deg"] = float(np.degrees(get_aoa(flap[:, 0], flap[:, 1])))
    print(f"{cfg['label']}: loaded flap (N={len(flap)}) + main (N={len(main)}), "
          f"Z-angle = {cfg['installed_aoa_z_deg']:+.2f} deg")


def run_step(cfg, delta_deg, step_idx):
    """Rotate flap by delta_deg about its LE and run MSES on the pair."""
    flap = cfg["flap_coords_z"].copy()
    if delta_deg != 0.0:
        flap = rotate_airfoil_phase3(flap, delta_deg, pivot=tuple(cfg["flap_le"]))

    tmp_flap = os.path.join(HERE, f"_tmp_flap_{cfg['label']}_step{step_idx}.dat")
    tmp_main = os.path.join(HERE, f"_tmp_main_{cfg['label']}_step{step_idx}.dat")
    np.savetxt(tmp_flap, flap)
    np.savetxt(tmp_main, cfg["main_coords"])

    elements = [
        {"role": "fixed", "coords_path": tmp_flap},
        {"role": "fixed", "coords_path": tmp_main},
    ]
    try:
        result = run_mses_elements(
            design=None, elements=elements,
            name=f"phase3_{cfg['label']}_step{step_idx}",
            alpha=cfg["alpha"], mach=cfg["mach"], reynolds=cfg["reynolds"],
            plot_geometry=False,
        )
    finally:
        for p in (tmp_flap, tmp_main):
            try: os.remove(p)
            except OSError: pass
    return result


def sweep_side(cfg):
    """Run an independent sweep for one side. Returns list of dicts and
    writes per-side CSV."""
    load_side(cfg)

    csv_path = f"phase3_sweep_{cfg['label']}.csv"
    rows = []
    ref_vals = None

    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "step", "delta_deg", "aoa_abs_deg",
            "cl", "cd", "score", "converged",
        ])

        best = {"step": None, "delta": None, "score": -np.inf,
                "aoa": None, "cl": None, "cd": None}
        consecutive_drops = 0
        consecutive_fails = 0
        prev_score = None

        print(f"\n===== sweeping {cfg['label']} =====")

        for step in range(MAX_STEPS):
            delta = -STEP_DEG * step
            if delta < -10.0:
                print(f"\nStopping {cfg['label']}: hit minimum allowed delta")
                break
            aoa = cfg["installed_aoa_z_deg"] + delta
            print(f"--- {cfg['label']} step {step}: delta={delta:+.2f}  aoa={aoa:+.2f} ---")

            result = run_step(cfg, delta, step)
            converged = result.cl is not None

            row = {
                "step": step, "delta_deg": delta, "aoa_abs_deg": aoa,
                "cl": result.cl, "cd": result.cd,
                "score": None, "converged": converged,
            }

            if not converged:
                print(f"  failed")
                writer.writerow([step, delta, aoa, None, None, None, False])
                f.flush()
                rows.append(row)
                consecutive_fails += 1
                if consecutive_fails >= STOP_AFTER_N_FAILS:
                    print(f"\nStopping {cfg['label']}: {STOP_AFTER_N_FAILS} consecutive failures")
                    break
                continue
            consecutive_fails = 0

            if step == 0 or ref_vals is None:
                # First successful run sets the reference
                ref_vals = {"df": -result.cl, "cd": result.cd}
                cfg["ref_vals"] = ref_vals
                print(f"  reference set: df={ref_vals['df']:.5f}  cd={ref_vals['cd']:.5f}")

            score = scoring_p3(result, delta, ref_vals)
            row["score"] = score
            print(f"  Cl={result.cl:+.5f}  Cd={result.cd:.5f}  score={score:+.5f}")

            writer.writerow([step, delta, aoa, result.cl, result.cd, score, True])
            f.flush()
            rows.append(row)

            if score > best["score"]:
                best = {"step": step, "delta": delta, "score": score,
                        "aoa": aoa, "cl": result.cl, "cd": result.cd}

            if prev_score is not None:
                if score < prev_score:
                    consecutive_drops += 1
                    print(f"  score dropped ({consecutive_drops}/{STOP_AFTER_N_DROPS})")
                else:
                    consecutive_drops = 0
            prev_score = score

            if consecutive_drops >= STOP_AFTER_N_DROPS:
                print(f"\nStopping {cfg['label']}: score dropped "
                      f"{STOP_AFTER_N_DROPS} steps in a row")
                break

    print(f"\n--- {cfg['label']} best ---")
    if best["step"] is not None:
        print(f"  step {best['step']}: aoa={best['aoa']:+.2f}, "
              f"Cl={best['cl']:+.5f}, Cd={best['cd']:.5f}, "
              f"score={best['score']:+.5f}")
    else:
        print("  no converged steps")
    print(f"  CSV: {csv_path}")

    return rows, best


def main():
    print(f"MSES timeout: {MSES_TIMEOUT_SEC}s per call")
    print(f"Sweep step:   {-STEP_DEG:+.2f} deg, max {MAX_STEPS} steps")

    ob_rows, ob_best = sweep_side(OB_CONFIG)
    ib_rows, ib_best = sweep_side(IB_CONFIG)

    print("\n" + "=" * 60)
    print("PHASE 3 SWEEP SUMMARY")
    print("=" * 60)
    if ob_best["step"] is not None:
        print(f"OB best: aoa={ob_best['aoa']:+.2f}  "
              f"Cl={ob_best['cl']:+.5f}  Cd={ob_best['cd']:.5f}  "
              f"score={ob_best['score']:+.5f}")
    else:
        print("OB: no converged steps")
    if ib_best["step"] is not None:
        print(f"IB best: aoa={ib_best['aoa']:+.2f}  "
              f"Cl={ib_best['cl']:+.5f}  Cd={ib_best['cd']:.5f}  "
              f"score={ib_best['score']:+.5f}")
    else:
        print("IB: no converged steps")
    if ob_best["aoa"] is not None and ib_best["aoa"] is not None:
        print(f"\nSimple average of best angles: "
              f"{0.5 * (ob_best['aoa'] + ib_best['aoa']):+.2f} deg")
    print("\nIndividual CSVs: phase3_sweep_OB.csv, phase3_sweep_IB.csv")


if __name__ == "__main__":
    main()