"""Detector 1 external validation on MIMIC-IV, with legitimate-variation controls.

Positive: ICD vs SOFA-window. Controls, all valid Sepsis-3:
  window vs single-point; window [-48,+24] vs [-24,+12]; vs [-72,+24].
MIMIC_DIR selects demo or full; cohort size is printed.

    PCL_TEST_MODE=1 python detectors/external/run_external1.py
"""
import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from detectors.harness import Case, confusion, fmt_matrix
from detectors.checks.check1_label_shift import diagnose

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(HERE, "results")

# (label, mode, pre_h, post_h)
SOFA_VARIANTS = [
    ("SOFA win[-48,+24]", "window", 48.0, 24.0),
    ("SOFA single-point", "single", 48.0, 24.0),
    ("SOFA win[-24,+12]", "window", 24.0, 12.0),
    ("SOFA win[-72,+24]", "window", 72.0, 24.0),
]


def mimic_labels(verbose=False):
    """(ids, icd, {variant: sofa}) over MIMIC-IV. One event-table read, all variants."""
    import time
    from config import MIMIC_DIR
    from src.data.mimic4 import load_stays
    from src.data.sepsis import mimic_sepsis_hadm_ids
    from src.data.sofa_sepsis import mimic_sofa_components, score_variants

    t0 = time.time()
    stays = load_stays(MIMIC_DIR)
    ids = stays["stay_id"].astype(int).values
    hadm_pos = mimic_sepsis_hadm_ids(MIMIC_DIR)
    icd = np.array([1 if int(h) in hadm_pos else 0
                    for h in stays["hadm_id"].astype(int).values])
    if verbose:
        print(f"  cohort+ICD read in {time.time() - t0:.1f}s "
              f"({len(ids)} stays)", flush=True)

    t1 = time.time()
    suspicion, C_by, stay_ids, infected, _ = mimic_sofa_components(MIMIC_DIR, stays)
    if verbose:
        print(f"  SOFA components read in {time.time() - t1:.1f}s "
              f"({len(infected)} suspected-infection stays)", flush=True)

    t2 = time.time()
    scored = score_variants(suspicion, C_by, stay_ids, SOFA_VARIANTS)
    sofa = {label: np.array([int(m.get(int(i), 0)) for i in ids])
            for label, m in scored.items()}
    if verbose:
        print(f"  {len(SOFA_VARIANTS)} variants scored in "
              f"{time.time() - t2:.1f}s (single read)", flush=True)
    return ids, icd, sofa


def eicu_labels(verbose=False):
    """(ids, icd, {variant: sofa}) over eICU. One read, all variants."""
    import time
    from config import EICU_DIR
    from src.data.sepsis import eicu_sepsis_stay_ids
    from src.data.sofa_sepsis import eicu_sofa_components, score_variants

    t0 = time.time()
    pats = pd.read_csv(os.path.join(EICU_DIR, "patient.csv.gz"),
                       usecols=["patientunitstayid", "unitdischargeoffset"],
                       encoding_errors="replace")
    pats = pats[pats["unitdischargeoffset"] / 60.0 >= 24].reset_index(drop=True)
    ids = pats["patientunitstayid"].astype(int).values
    pos = eicu_sepsis_stay_ids(EICU_DIR)
    icd = np.array([1 if i in pos else 0 for i in ids])
    if verbose:
        print(f"  cohort+ICD read in {time.time() - t0:.1f}s "
              f"({len(ids)} stays)", flush=True)

    t1 = time.time()
    suspicion, C_by, pid_set, infected, _ = eicu_sofa_components(EICU_DIR, pats)
    if verbose:
        print(f"  SOFA components read in {time.time() - t1:.1f}s "
              f"({len(infected)} suspected-infection stays)", flush=True)

    t2 = time.time()
    scored = score_variants(suspicion, C_by, pid_set, SOFA_VARIANTS)
    sofa = {label: np.array([int(m.get(int(i), 0)) for i in ids])
            for label, m in scored.items()}
    if verbose:
        print(f"  {len(SOFA_VARIANTS)} variants scored in "
              f"{time.time() - t2:.1f}s (single read)", flush=True)
    return ids, icd, sofa


def scenarios(db, ids, icd, sofa, seed=0, verbose=False):
    """One positive (ICD vs SOFA) and three legitimate-variation negatives."""
    rng = np.random.default_rng(seed)
    perm = rng.permutation(len(ids))
    half = len(ids) // 2
    s1, s2 = perm[:half], perm[half:]
    audit = rng.choice(len(ids), size=min(500, len(ids)), replace=False)

    base = "SOFA win[-48,+24]"
    specs = [(f"{db} POSITIVE ICD vs {base}", icd, sofa[base], True)]
    for label in ("SOFA single-point", "SOFA win[-24,+12]", "SOFA win[-72,+24]"):
        specs.append((f"{db} negative {base} vs {label}",
                      sofa[base], sofa[label], False))

    out = []
    for name, a, b, expected in specs:
        flag, k, ratio = diagnose(name, a[s1], b[s2], a[audit], b[audit],
                                  verbose=verbose)
        out.append(Case(name, bool(flag), bool(expected),
                        {"kappa": float(k), "prevalence_ratio": float(ratio),
                         "n_audit": int(len(audit)), "n_cohort": int(len(ids)),
                         "prev_a": float(a.mean()), "prev_b": float(b.mean())}))
    return out


def save_labels(path, m, e):
    """Cache label arrays (npz) for bootstrap_kappa.py. Per-stay; not committed."""
    (m_ids, m_icd, m_sofa), (e_ids, e_icd, e_sofa) = m, e
    payload = {"mimic_ids": m_ids, "mimic_icd": m_icd,
               "eicu_ids": e_ids, "eicu_icd": e_icd,
               "variant_labels": np.array([v[0] for v in SOFA_VARIANTS])}
    for i, (label, *_) in enumerate(SOFA_VARIANTS):
        payload[f"mimic_sofa_{i}"] = m_sofa[label]
        payload[f"eicu_sofa_{i}"] = e_sofa[label]
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    np.savez_compressed(path, **payload)
    print(f"\nlabel arrays cached -> {path}")


def load_labels(path):
    """Inverse of save_labels. ((ids, icd, sofa), (ids, icd, sofa))."""
    z = np.load(path, allow_pickle=False)
    labels = [str(x) for x in z["variant_labels"]]
    m_sofa = {lab: z[f"mimic_sofa_{i}"] for i, lab in enumerate(labels)}
    e_sofa = {lab: z[f"eicu_sofa_{i}"] for i, lab in enumerate(labels)}
    return ((z["mimic_ids"], z["mimic_icd"], m_sofa),
            (z["eicu_ids"], z["eicu_icd"], e_sofa))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--save-labels", default=None,
                    help="write label arrays here so the bootstrap can reuse "
                         "them instead of re-labelling (hours on full data)")
    args = ap.parse_args()

    print("=" * 78)
    print("DETECTOR 1 — external validation (MIMIC-IV) + broadened controls")
    print("=" * 78, flush=True)

    print(f"\nlabelling MIMIC-IV from "
          f"{os.environ.get('MIMIC_DIR', '<config default>')} ...", flush=True)
    m_ids, m_icd, m_sofa = mimic_labels(verbose=True)
    print(f"  cohort n={len(m_ids)}  ICD prevalence={m_icd.mean():.3f}")
    for k, v in m_sofa.items():
        print(f"    {k:<22} prevalence={v.mean():.3f}")

    print("\nlabelling eICU ...", flush=True)
    e_ids, e_icd, e_sofa = eicu_labels(verbose=True)
    print(f"  cohort n={len(e_ids)}  ICD prevalence={e_icd.mean():.3f}")
    for k, v in e_sofa.items():
        print(f"    {k:<22} prevalence={v.mean():.3f}")

    if args.save_labels:
        save_labels(args.save_labels, (m_ids, m_icd, m_sofa),
                    (e_ids, e_icd, e_sofa))

    cases = (scenarios("MIMIC", m_ids, m_icd, m_sofa, args.seed, verbose=True)
             + scenarios("eICU", e_ids, e_icd, e_sofa, args.seed, verbose=True))

    print("\n" + "-" * 78)
    for c in cases:
        ok = (c.flagged == c.expected)
        print(f"{c.name:<44} kappa={c.stats['kappa']:.3f}  "
              f"flagged={str(c.flagged):<6} expected={str(c.expected):<6} "
              f"{'PASS' if ok else 'FAIL'}")

    ext = [c for c in cases if c.name.startswith("MIMIC")]
    print("\n" + fmt_matrix("check1 EXTERNAL (MIMIC)", confusion(ext)))
    print(fmt_matrix("check1 eICU (original db)",
                     confusion([c for c in cases if c.name.startswith("eICU")])))
    print(fmt_matrix("check1 combined", confusion(cases)))

    neg = [c for c in cases if not c.expected]
    worst = min(neg, key=lambda c: c.stats["kappa"])
    print(f"\nthinnest margin on a legitimate variant: {worst.name} "
          f"kappa={worst.stats['kappa']:.3f} (flag threshold 0.60)")

    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, "external1.json"), "w", encoding="utf-8") as fh:
        json.dump({c.name: {"flagged": c.flagged, "expected": c.expected,
                            **c.stats} for c in cases}, fh, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
