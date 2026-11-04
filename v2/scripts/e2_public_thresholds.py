"""E2 (PREREG_V2_ADDENDUM_1.md): the four-fifths rule on a frozen public family of cases.

    python -W ignore v2/scripts/e2_public_thresholds.py --data <dir with the public files> [--draws 2000] [--out DIR]

Reads the ACS 2018 1-year person files (zip), UCI Adult, and the ProPublica COMPAS file. Writes aggregates only.
"""
import os
import io
import sys
import json
import zipfile
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import numpy as np
import pandas as pd

from stats_util import clopper_pearson

THRESH = 0.8
SIZES = [250, 500, 1000]
STATES = ["ak", "nd", "nh", "nm", "ri", "vt", "wy", "ny"]
ACS_COLS = ["AGEP", "SEX", "RAC1P", "HISP", "PINCP", "ESR", "HICOV", "SCHL"]


def acs_cases(df, state):
    """Yield (name, y, g, eligible) with g = 1 for group A, 2 for group B, 0 otherwise."""
    age = df["AGEP"].to_numpy()
    outs = {
        "O1_income_gt_50k": (age >= 16) & df["PINCP"].notna().to_numpy(), "O2_employed": (age >= 16) & (age <= 64) & df["ESR"].notna().to_numpy(),
        "O3_insured": np.ones(len(df), bool), "O4_bachelors_plus": age >= 25,
    }
    ys = {
        "O1_income_gt_50k": (df["PINCP"].to_numpy() > 50000), "O2_employed": df["ESR"].isin([1, 2, 4, 5]).to_numpy(),
        "O3_insured": (df["HICOV"].to_numpy() == 1), "O4_bachelors_plus": (df["SCHL"].to_numpy() >= 21),
    }
    sex, rac, hisp = df["SEX"].to_numpy(), df["RAC1P"].to_numpy(), df["HISP"].to_numpy()
    contrasts = {
        "C1_sex_F_vs_M": (np.where(sex == 2, 1, np.where(sex == 1, 2, 0))),
        "C2_white_vs_black": (np.where(rac == 1, 1, np.where(rac == 2, 2, 0))),
        "C3_white_vs_asian": (np.where(rac == 1, 1, np.where(rac == 6, 2, 0))),
        "C4_hisp_vs_nonhisp": (np.where(hisp != 1, 1, 2)),
    }
    for o, elig in outs.items():
        for c, g in contrasts.items():
            yield f"ACS_{state.upper()}__{o}__{c}", ys[o].astype(int), g, elig


def table_cases(name, y, g, elig=None):
    yield name, np.asarray(y).astype(int), np.asarray(g), (np.ones(len(y), bool) if elig is None else elig)


def load_cases(data):
    cases = []
    for s in STATES:
        z = zipfile.ZipFile(os.path.join(data, f"csv_p{s}.zip"))
        member = next(n for n in z.namelist() if n.lower().endswith(".csv"))
        df = pd.read_csv(io.BytesIO(z.read(member)), usecols=ACS_COLS)
        cases += list(acs_cases(df, s))
    names = ["age", "workclass", "fnlwgt", "education", "education-num", "marital-status", "occupation", "relationship", "race", "sex",
             "capital-gain", "capital-loss", "hours-per-week", "native-country", "income"]
    ad = pd.read_csv(os.path.join(data, "adult.data"), header=None, names=names, skipinitialspace=True)
    y = (ad["income"] == ">50K").to_numpy()
    cases += list(table_cases("Adult__income_gt_50k__sex_F_vs_M", y, np.where(ad["sex"] == "Female", 1, np.where(ad["sex"] == "Male", 2, 0))))
    cases += list(table_cases("Adult__income_gt_50k__white_vs_black", y, np.where(ad["race"] == "White", 1, np.where(ad["race"] == "Black", 2, 0))))
    cases += list(table_cases("Adult__income_gt_50k__white_vs_asian", y, np.where(ad["race"] == "White", 1, np.where(ad["race"] == "Asian-Pac-Islander", 2, 0))))
    cp = pd.read_csv(os.path.join(data, "compas-scores-two-years.csv"))
    g = np.where(cp["race"] == "African-American", 1, np.where(cp["race"] == "Caucasian", 2, 0))
    cases += list(table_cases("COMPAS__score_not_low__aa_vs_cauc", (cp["score_text"] != "Low").to_numpy(), g))
    cases += list(table_cases("COMPAS__two_year_recid__aa_vs_cauc", cp["two_year_recid"].to_numpy(), g))
    return cases


def ratio(y, g):
    a, b = g == 1, g == 2
    na, nb = int(a.sum()), int(b.sum())
    if na == 0 or nb == 0:
        return None
    ra, rb = float(y[a].mean()), float(y[b].mean())
    hi = max(ra, rb)
    if hi == 0:
        return None
    return min(ra, rb) / hi


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--draws", type=int, default=2000)
    ap.add_argument("--out", default=os.path.join(ROOT, "v2", "results"))
    a = ap.parse_args()
    cases = load_cases(a.data)
    assert len(cases) == 133, len(cases)
    out = {"threshold": THRESH, "sizes": SIZES, "draws": a.draws, "cases": []}
    for ci, (name, y, g, elig) in enumerate(cases):
        idx_pop = np.where(elig)[0]
        yp, gp = y[idx_pop], g[idx_pop]
        theta = ratio(yp, gp)
        rec = {"case": name, "N_pop": int(len(idx_pop)), "n_group_a": int((gp == 1).sum()), "n_group_b": int((gp == 2).sum()),
               "theta_star": theta, "rows": []}
        for si, n in enumerate(SIZES):
            if len(idx_pop) < 4 * n or theta is None:
                rec["rows"].append({"n": n, "skipped": True})
                continue
            rng = np.random.default_rng(70000 + 1000 * ci + si)
            vals, und = [], 0
            for _ in range(a.draws):
                sel = rng.choice(len(idx_pop), size=n, replace=False)
                r = ratio(yp[sel], gp[sel])
                if r is None:
                    und += 1
                else:
                    vals.append(r)
            dec = a.draws - und
            flags = int(sum(v < THRESH for v in vals))
            sd = float(np.std(vals, ddof=1)) if len(vals) > 1 else None
            m = abs(THRESH - theta) / sd if sd else None
            rec["rows"].append({"n": n, "decidable": dec, "undecidable": und, "flags": flags,
                                "p_flag": flags / dec if dec else None, "cp95": clopper_pearson(flags, dec),
                                "sd_R": sd, "margin_m": m, "mean_R": float(np.mean(vals)) if vals else None})
        out["cases"].append(rec)
    summ = {}
    for n in SIZES:
        rows = [(c, next(r for r in c["rows"] if r["n"] == n)) for c in out["cases"]]
        ok = [(c, r) for c, r in rows if not r.get("skipped") and r.get("margin_m") is not None]
        k_m = sum(r["margin_m"] <= 3 for c, r in ok)
        k_p = sum(0.05 <= r["p_flag"] <= 0.95 for c, r in ok)
        disagree = sum((c["theta_star"] < THRESH) != (r["p_flag"] > 0.5) for c, r in ok)
        summ[str(n)] = {"cases_evaluated": len(ok), "skipped": len(rows) - len(ok),
                        "m_le_3": [k_m, len(ok), clopper_pearson(k_m, len(ok))],
                        "p_between_0.05_and_0.95": [k_p, len(ok), clopper_pearson(k_p, len(ok))],
                        "population_verdict_differs_from_majority_flag": disagree,
                        "closest_ten": [{"case": c["case"], "theta_star": round(c["theta_star"], 4), "margin_m": round(r["margin_m"], 3),
                                         "p_flag": round(r["p_flag"], 3), "undecidable_share": round(r["undecidable"] / a.draws, 3)}
                                        for c, r in sorted(ok, key=lambda cr: cr[1]["margin_m"])[:10]],
                        "undecidable_draws_total": int(sum(r["undecidable"] for c, r in ok)),
                        "draws_total": int(len(ok) * a.draws)}
    out["summary"] = summ
    os.makedirs(a.out, exist_ok=True)
    json.dump(out, open(os.path.join(a.out, "e2_public_thresholds.json"), "w"), indent=1, default=float)
    for n, s in summ.items():
        print(n, "evaluated", s["cases_evaluated"], "m<=3", s["m_le_3"], "coin-flip zone", s["p_between_0.05_and_0.95"], "undecidable draws", s["undecidable_draws_total"], "/", s["draws_total"])


if __name__ == "__main__":
    main()
