"""Check 1: label-definition shift across sites.

Flags when Cohen's kappa between two labelling criteria, scored on the same
audit subset, is below KAPPA_FLAG. Prevalence ratio reported, not used to flag.

Positive: ICD vs SOFA-window. Negative: SOFA-window vs SOFA-single-point.
"""
import os
import sys
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

import numpy as np
import pandas as pd

logging.disable(logging.WARNING)

KAPPA_FLAG = 0.60          # Landis-Koch "substantial" boundary
PREV_RATIO_FLAG = 1.50     # reported only


def cohens_kappa(a, b):
    a, b = np.asarray(a, int), np.asarray(b, int)
    n = len(a)
    if n == 0:
        return float("nan")
    po = float((a == b).mean())
    pa1, pb1 = a.mean(), b.mean()
    pe = pa1 * pb1 + (1 - pa1) * (1 - pb1)
    return 1.0 if pe >= 1.0 else float((po - pe) / (1 - pe))


def diagnose(name, site1, site2, audit_1, audit_2, verbose=True):
    """site1/site2: labels as shipped. audit_1/audit_2: both criteria, same patients."""
    p1, p2 = float(np.mean(site1)), float(np.mean(site2))
    ratio = max(p1, p2) / max(min(p1, p2), 1e-9)
    k = cohens_kappa(audit_1, audit_2)
    agree = float((np.asarray(audit_1) == np.asarray(audit_2)).mean())
    flagged = (k < KAPPA_FLAG)
    if verbose:
        print(f"\n--- {name} ---")
        print(f"  prevalence      site1={p1:.3f}  site2={p2:.3f}  ratio={ratio:.2f}"
              f"   (weak signal, flag>{PREV_RATIO_FLAG})")
        print(f"  audit subset    n={len(audit_1)}  raw agreement={agree:.3f}  "
              f"kappa={k:.3f}   (flag<{KAPPA_FLAG})")
        print(f"  ==> {'FLAGGED: label-definition mismatch' if flagged else 'clean'}")
    return flagged, k, ratio


def build_scenarios(ids, icd, sofa_single, sofa_window, s1, s2, audit):
    """Scenario -> (site1, site2, audit_a, audit_b, expected).

    Audit arrays must be computed independently; one array twice gives kappa 1.0.
    """
    return {
        # reference: window-mode SOFA (Sepsis-3); single-point is a control only
        "positive (ICD vs SOFA window)": (
            icd[s1], sofa_window[s2], icd[audit], sofa_window[audit], True),
        "negative (SOFA window vs single-point)": (
            sofa_window[s1], sofa_single[s2],
            sofa_window[audit], sofa_single[audit], False),
    }


_LABELS = None


def load_labels(verbose=False):
    """(ids, icd, sofa_single, sofa_window) over eICU. Cached; seed-independent."""
    global _LABELS
    if _LABELS is not None:
        return _LABELS

    from config import EICU_DIR
    from src.data.sepsis import eicu_sepsis_stay_ids
    from src.data.sofa_sepsis import eicu_sofa_sepsis_labels

    if verbose:
        print(f"data: {EICU_DIR}")
    pats = pd.read_csv(os.path.join(EICU_DIR, "patient.csv.gz"),
                       usecols=["patientunitstayid", "unitdischargeoffset"],
                       encoding_errors="replace")
    pats = pats[pats["unitdischargeoffset"] / 60.0 >= 24].reset_index(drop=True)
    ids = pats["patientunitstayid"].astype(int).values

    # A: ICD codes. B: SOFA Sepsis-3.
    icd_set = eicu_sepsis_stay_ids(EICU_DIR)
    icd = np.array([1 if i in icd_set else 0 for i in ids])
    sofa_map, _ = eicu_sofa_sepsis_labels(EICU_DIR, pats, mode="single")
    sofa = np.array([int(sofa_map.get(int(i), 0)) for i in ids])
    # negative-control variant
    sofa_win_map, _ = eicu_sofa_sepsis_labels(EICU_DIR, pats, mode="window")
    sofa_window = np.array([int(sofa_win_map.get(int(i), 0)) for i in ids])

    if verbose:
        print(f"cohort n={len(ids)}   ICD prevalence={icd.mean():.3f}   "
              f"SOFA(single) prevalence={sofa.mean():.3f}   "
              f"SOFA(window) prevalence={sofa_window.mean():.3f}")
    _LABELS = (ids, icd, sofa, sofa_window)
    return _LABELS


def split(ids, seed):
    """Two disjoint site halves plus a fixed audit subset."""
    rng = np.random.default_rng(seed)
    perm = rng.permutation(len(ids))
    half = len(ids) // 2
    # audit subset: fixed patients scored under both criteria
    audit = rng.choice(len(ids), size=min(500, len(ids)), replace=False)
    return perm[:half], perm[half:], audit


def run(seed=0, verbose=False):
    from detectors.harness import Case
    ids, icd, sofa, sofa_window = load_labels(verbose=verbose)
    s1, s2, audit = split(ids, seed)

    out = []
    for name, (a, b, aa, ab, e) in build_scenarios(
            ids, icd, sofa, sofa_window, s1, s2, audit).items():
        flag, k, ratio = diagnose(name, a, b, aa, ab, verbose=verbose)
        out.append(Case(name, bool(flag), bool(e),
                        {"kappa": k, "prevalence_ratio": ratio, "seed": seed}))
    return out


def split_noise(seed=0):
    """Prevalence ratio between halves under one criterion, for each criterion."""
    ids, icd, sofa, _ = load_labels()
    s1, s2, _ = split(ids, seed)
    out = {}
    for cname, arr in (("ICD", icd), ("SOFA", sofa)):
        pa, pb = float(arr[s1].mean()), float(arr[s2].mean())
        out[cname] = (pa, pb, max(pa, pb) / max(min(pa, pb), 1e-9))
    return out


def main():
    from detectors.harness import confusion, fmt_matrix

    print("=" * 78)
    print("CHECK 1 — label-definition shift across sites")
    print("=" * 78)

    cases = run(seed=0, verbose=True)

    print("\n" + "-" * 78)
    for c in cases:
        ok = (c.flagged == c.expected)
        print(f"{c.name:<34} flagged={str(c.flagged):<6} "
              f"expected={str(c.expected):<6} kappa={c.stats['kappa']:.3f}  "
              f"{'PASS' if ok else 'FAIL'}")
    counts = confusion(cases)
    print("\n" + fmt_matrix("check1", counts))
    print("verdict:", "DETECTOR VALIDATED"
          if counts["FP"] == 0 and counts["FN"] == 0 else "NEEDS WORK")

    # prevalence-only baseline
    pos_ratio = next(c.stats["prevalence_ratio"] for c in cases if c.expected)
    print("\nsame-criterion split noise (one criterion, disjoint halves):")
    neg_ratio = 0.0
    for cname, (pa, pb, r) in split_noise(seed=0).items():
        neg_ratio = max(neg_ratio, r)
        near = (f"   <-- within reach of the {PREV_RATIO_FLAG} threshold"
                if r > 1.25 else "")
        print(f"  {cname:<5} prevalence {pa:.3f} vs {pb:.3f}  ratio={r:.2f}{near}")
    print(f"\nprevalence ratio, positive={pos_ratio:.2f} vs negative={neg_ratio:.2f}: "
          f"{'separable' if pos_ratio > PREV_RATIO_FLAG >= neg_ratio else 'NOT separable'}"
          " — kappa on a fixed audit subset is the reliable signal.")


if __name__ == "__main__":
    main()
