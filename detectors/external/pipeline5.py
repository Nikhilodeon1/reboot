"""Detector 5 external testbed on MIMIC-IV and eICU.

Reads raw_ts (keep_raw=True). Processed values are normalized and forward-filled,
which breaks the identities and erases missingness.

Oxygen term: Severinghaus (SpO2 vs PaO2), not PhysioNet's O2Sat vs SaO2.
Analogous component set, not identical.

Ground truth from controlled ablation (PREREGISTRATION.md).
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from src.data.variables import VAR_TO_IDX

# term -> canonical inputs
TERMS = {
    "MAP":          ["SBP", "DBP", "MAP"],
    "HH":           ["pH", "HCO3", "pCO2"],
    "Severinghaus": ["SpO2", "PaO2"],
}
EXTERNAL_KEYS = ["MAP", "HH", "Severinghaus"]


def load_site(which, keep_raw=True):
    """('mimic'|'eicu') -> list of raw_ts arrays, one per stay."""
    from config import MIMIC_DIR, EICU_DIR
    if which == "mimic":
        from src.data.mimic4 import load_mimic4
        samples, _ = load_mimic4(MIMIC_DIR, fraction=1.0, seed=0,
                                 keep_raw=keep_raw)
    elif which == "eicu":
        from src.data.eicu import load_eicu
        samples, _ = load_eicu(EICU_DIR, fraction=1.0, seed=0,
                               keep_raw=keep_raw)
    else:
        raise ValueError(f"unknown site {which!r}")
    missing = [s for s in samples if "raw_ts" not in s]
    if missing:
        raise RuntimeError("loader returned no raw_ts; keep_raw was not honoured")
    return [np.asarray(s["raw_ts"], dtype=float) for s in samples]


def stay_components(ts):
    """Per-stay {term: mean residual}, PhysioNet-compatible units."""
    out = {}
    col = {v: VAR_TO_IDX[v] for v in VAR_TO_IDX}

    sbp, dbp, mp = ts[:, col["SBP"]], ts[:, col["DBP"]], ts[:, col["MAP"]]
    ok = ~np.isnan(sbp) & ~np.isnan(dbp) & ~np.isnan(mp)
    if ok.any():
        out["MAP"] = float(np.mean(
            np.abs((mp[ok] - (dbp[ok] + (sbp[ok] - dbp[ok]) / 3.0)) / 180.0)))

    ph, hco3, pco2 = ts[:, col["pH"]], ts[:, col["HCO3"]], ts[:, col["pCO2"]]
    ok = (~np.isnan(ph) & ~np.isnan(hco3) & ~np.isnan(pco2)
          & (hco3 > 0) & (pco2 > 0))
    if ok.any():
        pred = 6.1 + np.log10(hco3[ok] / (0.0307 * pco2[ok]))
        out["HH"] = float(np.mean(((ph[ok] - pred) / 1.4) ** 2))

    spo2, pao2 = ts[:, col["SpO2"]], ts[:, col["PaO2"]]
    ok = ~np.isnan(spo2) & ~np.isnan(pao2) & (pao2 > 0)
    if ok.any():
        # Severinghaus: SpO2 from PaO2
        inner = 23400.0 / (pao2[ok] ** 3 + 150.0 * pao2[ok]) + 1.0
        pred = 100.0 / inner
        out["Severinghaus"] = float(np.mean(((spo2[ok] - pred) / 50.0) ** 2))

    return out


def to_stays(arrays):
    """Per-stay component dicts; stays with nothing computable dropped."""
    out = []
    for ts in arrays:
        c = stay_components(ts)
        if c:
            out.append(c)
    return out


def ablate(arrays, variable, p, seed):
    """Drop fraction p of one variable's observations per stay. Values untouched."""
    idx = VAR_TO_IDX[variable]
    rng = np.random.default_rng(seed)
    out = []
    for ts in arrays:
        a = ts.copy()
        obs = np.flatnonzero(~np.isnan(a[:, idx]))
        if len(obs):
            n_drop = int(round(p * len(obs)))
            if n_drop:
                a[rng.permutation(obs)[:n_drop], idx] = np.nan
        out.append(a)
    return out


def split_arrays(arrays, seed):
    """Two disjoint random halves."""
    rng = np.random.default_rng(seed)
    perm = rng.permutation(len(arrays))
    half = len(arrays) // 2
    return ([arrays[i] for i in perm[:half]],
            [arrays[i] for i in perm[half:]])
