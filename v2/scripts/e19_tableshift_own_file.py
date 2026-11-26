"""E19: the guarded and unguarded College Scorecard pipelines on the benchmark's own data file and its own domain split.

The benchmark's loader reads `Scorecard.csv` from the Kaggle dataset `kaggle/college-scorecard`, which needs a Kaggle login
(tableshift/core/data_source.py, class CollegeScorecardDataSource, at commit fca9429814). Download that file by hand and pass its folder.

    python -W ignore v2/scripts/e19_tableshift_own_file.py --data <dir containing Scorecard.csv> [--smoke]

What is reproduced from the benchmark (read from its source, not imported):
  - the verbatim `preprocess_college_scorecard` and its feature list (extracted at the pinned commit as in E12);
  - the domain split of benchmark_configs.py: observations whose CCBASIC is in the eight listed values are out of domain, the rest are in domain;
    in-domain rows are split into train, validation and in-domain test with sklearn train_test_split, test_size 0.2 and then 0.5 of that
    (validation 0.1, in-domain test 0.1), and out-of-domain rows into test and validation (validation 0.1), all with random_state 264738;
  - the default 'histgbm' model: HistGradientBoostingClassifier with library defaults.
Not reproduced: the benchmark's label-encoding and 100-bin discretization of the features (here categoricals are label-encoded and numeric
features are left raw, which a histogram gradient-boosted model bins itself), and its handling of 'PrivacySuppressed'.

Pipelines: unguarded keeps every row, so a missing completion rate becomes the label 0 (the shipped line). Guarded drops rows with a missing
completion rate before splitting. Reported per pipeline on its own out-of-domain test split: accuracy (the benchmark's reported metric), AUROC and
balanced accuracy. Both models are also scored on the observed-target out-of-domain test rows with true labels. 95% intervals are percentile
bootstraps that resample institutions (UNITID), not rows, because the file stacks years (2,000 resamples). Output: v2/results/e19_tableshift_own_file.json (aggregates only).
"""
import os
import sys
import json
import argparse
import tempfile

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score, balanced_accuracy_score
from sklearn.model_selection import train_test_split

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import e12_consequences as e12  # noqa: E402

RANDOM_STATE, VAL, ID_TEST, OOD_VAL = 264738, 0.1, 0.1, 0.1
OOD_VALUES = [
    "Special Focus Institutions--Other special-focus institutions",
    "Special Focus Institutions--Theological seminaries, Bible colleges, and other faith-related institutions",
    "Associate's--Private For-profit 4-year Primarily Associate's",
    "Baccalaureate Colleges--Diverse Fields",
    "Special Focus Institutions--Schools of art, music, and design",
    "Associate's--Private Not-for-profit",
    "Baccalaureate/Associate's Colleges",
    "Master's Colleges and Universities (larger programs)",
]


def domain_split(domain_vals):
    ood = np.nonzero(domain_vals.isin(OOD_VALUES).to_numpy())[0]
    idm = np.nonzero((~domain_vals.isin(OOD_VALUES)).to_numpy())[0]
    train, rest = train_test_split(idm, test_size=VAL + ID_TEST, random_state=RANDOM_STATE)
    val, id_test = train_test_split(rest, test_size=ID_TEST / (VAL + ID_TEST), random_state=RANDOM_STATE)
    ood_test, ood_val = train_test_split(ood, test_size=OOD_VAL, random_state=RANDOM_STATE)
    return train, val, id_test, ood_test, ood_val


def metrics(y, p, prob):
    return {"accuracy": float((p == y).mean()), "balanced_accuracy": float(balanced_accuracy_score(y, p)),
            "auroc": float(roc_auc_score(y, prob)) if len(np.unique(y)) > 1 else None}


def boot(fn, n, rng, B=2000):
    vals = [fn(rng.integers(0, n, n)) for _ in range(B)]
    vals = [v for v in vals if v is not None]
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--smoke", action="store_true", help="smoke test on a synthetic frame; writes nothing to results")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(HERE), "results"))
    a = ap.parse_args()
    verb = tempfile.mkdtemp(prefix="e19_verbatim_")
    e12.extract(verb)

    class _F:
        target = "C150_4"
    ns = {}
    exec("import pandas as pd\n" + open(os.path.join(verb, "tableshift_preprocess.py"), encoding="utf-8").read().replace("import pandas as pd\n", "", 1),
         {"pd": pd, "COLLEGE_SCORECARD_FEATURES": _F}, ns)
    pre = ns["preprocess_college_scorecard"]
    pre.__globals__["COLLEGE_SCORECARD_FEATURES"] = _F
    feats_all = json.load(open(os.path.join(verb, "tableshift_features.json")))
    if a.smoke:
        rng = np.random.default_rng(0)
        n = 4000
        raw = pd.DataFrame({"UNITID": rng.integers(0, 900, n), "C150_4": np.where(rng.random(n) < 0.4, np.nan, rng.random(n)),
                            "CCBASIC": rng.choice(OOD_VALUES + ["Doctoral Universities", "Baccalaureate Colleges--Arts & Sciences"], n),
                            "CONTROL": rng.choice(["Public", "Private"], n), "ADM_RATE": rng.random(n), "UGDS": rng.random(n) * 1e4})
    else:
        path = os.path.join(a.data, "Scorecard.csv")
        header = list(pd.read_csv(path, nrows=0).columns)
        needed = [c for c in header if c in set(feats_all) | {"C150_4", "CCBASIC", "UNITID", "Year"}]
        missing = [c for c in ("C150_4", "CCBASIC", "UNITID") if c not in needed]
        if missing:
            raise SystemExit(f"columns missing from Scorecard.csv: {missing}; first columns are {header[:10]}")
        parts = pd.read_csv(path, usecols=needed, na_values=["NULL", "PrivacySuppressed"], chunksize=20000, low_memory=False)
        raw = pd.concat(parts, ignore_index=True)
    feats = [f for f in feats_all if f in raw.columns and f not in ("C150_4", "CCBASIC")]
    X = raw[feats].copy()
    for c in X.columns:
        if not pd.api.types.is_numeric_dtype(X[c]):
            X[c] = X[c].astype("category").cat.codes
    dom = raw["CCBASIC"]
    y_un = pre(raw.copy())["C150_4"].to_numpy().astype(int)
    obs = raw["C150_4"].notna().to_numpy()
    y_g = (raw["C150_4"] > 0.5).astype(int).to_numpy()
    out = {"rows": int(len(raw)), "rows_with_completion_rate": int(obs.sum()), "features_used": len(feats), "smoke": bool(a.smoke),
           "benchmark_commit": "fca9429814", "random_state": RANDOM_STATE}

    # unguarded: split all rows
    tr, va, idt, oot, oov = domain_split(dom)
    mu = HistGradientBoostingClassifier().fit(X.iloc[tr], y_un[tr])
    # guarded: drop rows without a completion rate, then split
    keep = np.nonzero(obs)[0]
    Xg, yg, dg = X.iloc[keep], y_g[keep], dom.iloc[keep].reset_index(drop=True)
    trg, vag, idtg, ootg, oovg = domain_split(dg)
    mg = HistGradientBoostingClassifier().fit(Xg.iloc[trg], yg[trg])
    rng = np.random.default_rng(20261201)
    res = {}
    # reported on each pipeline's own out-of-domain test split
    pu, pru = mu.predict(X.iloc[oot]), mu.predict_proba(X.iloc[oot])[:, 1]
    pg, prg = mg.predict(Xg.iloc[ootg]), mg.predict_proba(Xg.iloc[ootg])[:, 1]
    res["reported_unguarded"] = metrics(y_un[oot], pu, pru)
    res["reported_guarded"] = metrics(yg[ootg], pg, prg)
    res["n_ood_test_unguarded"], res["n_ood_test_guarded"] = int(len(oot)), int(len(ootg))
    # both models on the observed-target out-of-domain rows of the unguarded split, true labels
    oo_obs = oot[obs[oot]]
    pu2, pru2 = mu.predict(X.iloc[oo_obs]), mu.predict_proba(X.iloc[oo_obs])[:, 1]
    pg2, prg2 = mg.predict(X.iloc[oo_obs]), mg.predict_proba(X.iloc[oo_obs])[:, 1]
    res["observed_rows_unguarded_model"] = metrics(y_g[oo_obs], pu2, pru2)
    res["observed_rows_guarded_model"] = metrics(y_g[oo_obs], pg2, prg2)
    res["n_observed_ood_rows"] = int(len(oo_obs))
    # percentile bootstrap that resamples institutions (UNITID), because the file stacks years and one institution has many rows;
    # one draw of institutions weights both pipelines' test rows
    unit = raw["UNITID"].to_numpy()
    rows_g = keep[ootg]  # row numbers in the full frame of the guarded out-of-domain test rows
    ids = np.unique(np.concatenate([unit[oot], unit[rows_g]]))
    pos = {u: k for k, u in enumerate(ids)}
    at_u = np.array([pos[u] for u in unit[oot]])
    at_g = np.array([pos[u] for u in unit[rows_g]])
    at_o = np.array([pos[u] for u in unit[oo_obs]])

    def wmetrics(y, p, prob, w):
        m_ = w > 0
        y, p, prob, w = y[m_], p[m_], prob[m_], w[m_]
        if len(np.unique(y)) < 2:
            return None
        return {"accuracy": float(np.average(p == y, weights=w)), "auroc": float(roc_auc_score(y, prob, sample_weight=w)),
                "balanced_accuracy": float(balanced_accuracy_score(y, p, sample_weight=w))}

    keys = ("accuracy", "auroc", "balanced_accuracy")
    rep_vals, true_vals = {k: [] for k in keys}, {k: [] for k in keys}
    for _ in range(2000):
        mult = np.bincount(rng.integers(0, len(ids), len(ids)), minlength=len(ids)).astype(float)
        a_ = wmetrics(y_un[oot], pu, pru, mult[at_u])
        b_ = wmetrics(yg[ootg], pg, prg, mult[at_g])
        c_ = wmetrics(y_g[oo_obs], pu2, pru2, mult[at_o])
        d_ = wmetrics(y_g[oo_obs], pg2, prg2, mult[at_o])
        for k in keys:
            if a_ and b_:
                rep_vals[k].append(a_[k] - b_[k])
            if c_ and d_:
                true_vals[k].append(c_[k] - d_[k])
    res["institutions_in_bootstrap"] = int(len(ids))
    for k in keys:
        for name, vals, first, second in (("reported_gap", rep_vals, "reported_unguarded", "reported_guarded"),
                                          ("true_label_gap", true_vals, "observed_rows_unguarded_model", "observed_rows_guarded_model")):
            point = None if res[first][k] is None or res[second][k] is None else res[first][k] - res[second][k]
            res[f"{name}_{k}"] = {"point": point, "ci95": [float(np.percentile(vals[k], 2.5)), float(np.percentile(vals[k], 97.5))]}
    out["result"] = res
    if a.smoke:
        print(json.dumps(out, indent=1)[:1500])
        return
    os.makedirs(a.out, exist_ok=True)
    json.dump(out, open(os.path.join(a.out, "e19_tableshift_own_file.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
