"""E12b (EXPLORATORY, not registered): base-rate check on the College Scorecard consequence study.

A mock review of the paper noted that the +13.1 point accuracy gap in E12 S1 compares test sets with different positive shares (0.189
among all rows after the unguarded line, 0.521 among rows with an observed target), so accuracy alone mixes the label change with the
base rate. This script reruns the same five splits and the same model and reports, on both test sets, accuracy, the accuracy of
always predicting the majority class, balanced accuracy and AUROC.

    python -W ignore v2/scripts/e12b_s1_base_rates.py --data <dir> [--out DIR]

Imports the extraction and preprocessing of e12_consequences.py unchanged. Output: v2/results/e12b_s1_base_rates.json (aggregates only).
"""
import io
import os
import sys
import json
import zipfile
import argparse
import shutil

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score, balanced_accuracy_score
from sklearn.model_selection import train_test_split

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import e12_consequences as e12  # noqa: E402


def metrics(y, p, prob):
    maj = max(float(y.mean()), 1 - float(y.mean()))
    return {"n": int(len(y)), "pos_share": float(y.mean()), "accuracy": float((p == y).mean()), "majority_accuracy": maj,
            "balanced_accuracy": float(balanced_accuracy_score(y, p)),
            "auroc": float(roc_auc_score(y, prob)) if len(set(y.tolist())) == 2 else None}


def tci(v):
    v = np.asarray(v, float)
    h = stats.t.ppf(0.975, len(v) - 1) * v.std(ddof=1) / np.sqrt(len(v))
    return [float(v.mean()), float(v.mean() - h), float(v.mean() + h)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", default=os.path.join(os.path.dirname(HERE), "results"))
    a = ap.parse_args()
    verb = os.path.join(a.out, "_verbatim_tmp_b")
    e12.extract(verb)

    class _F:
        target = "C150_4"
    ns = {}
    exec("import pandas as pd\n" + open(os.path.join(verb, "tableshift_preprocess.py"), encoding="utf-8").read().replace("import pandas as pd\n", "", 1),
         {"pd": pd, "COLLEGE_SCORECARD_FEATURES": _F}, ns)
    pre = ns["preprocess_college_scorecard"]
    pre.__globals__["COLLEGE_SCORECARD_FEATURES"] = _F
    z = zipfile.ZipFile(next(os.path.join(a.data, f) for f in os.listdir(a.data) if f.startswith("Most-Recent-Cohorts-Institution")))
    member = next(n for n in z.namelist() if n.lower().endswith(".csv") and "institution" in n.lower() and "data_dictionary" not in n.lower())
    raw = pd.read_csv(io.BytesIO(z.read(member)), low_memory=False, na_values=["NULL", "PrivacySuppressed"])
    feats = [f for f in json.load(open(os.path.join(verb, "tableshift_features.json"))) if f in raw.columns and f != "C150_4"]
    X = raw[feats].copy()
    for c in X.columns:
        if not pd.api.types.is_numeric_dtype(X[c]):
            X[c] = X[c].astype("category").cat.codes
    y_un = pre(raw.copy())["C150_4"].to_numpy()
    obs = raw["C150_4"].notna().to_numpy()
    rows = []
    for seed in range(5):
        tr, te = train_test_split(np.arange(len(raw)), test_size=0.3, random_state=seed)
        m = HistGradientBoostingClassifier(random_state=seed).fit(X.iloc[tr], y_un[tr])
        p, pr = m.predict(X.iloc[te]), m.predict_proba(X.iloc[te])[:, 1]
        k = obs[te]
        rows.append({"seed": seed, "unguarded_test": metrics(y_un[te], p, pr), "observed_rows_test": metrics(y_un[te][k], p[k], pr[k]),
                     "missing_rows_test": {"n": int((~k).sum()), "accuracy": float((p[~k] == y_un[te][~k]).mean())}})
    agg = {}
    for part in ("unguarded_test", "observed_rows_test"):
        agg[part] = {key: tci([r[part][key] for r in rows]) for key in ("pos_share", "accuracy", "majority_accuracy", "balanced_accuracy", "auroc")}
    agg["accuracy_above_majority_unguarded"] = tci([r["unguarded_test"]["accuracy"] - r["unguarded_test"]["majority_accuracy"] for r in rows])
    agg["accuracy_above_majority_observed"] = tci([r["observed_rows_test"]["accuracy"] - r["observed_rows_test"]["majority_accuracy"] for r in rows])
    agg["accuracy_on_missing_rows"] = tci([r["missing_rows_test"]["accuracy"] for r in rows])
    out = {"note": "exploratory; each entry is [mean, lower, upper] of a t-interval over five random 70/30 splits (df 4)", "aggregate": agg, "per_split": rows}
    os.makedirs(a.out, exist_ok=True)
    json.dump(out, open(os.path.join(a.out, "e12b_s1_base_rates.json"), "w"), indent=1)
    shutil.rmtree(verb, ignore_errors=True)
    print(json.dumps(agg, indent=1))


if __name__ == "__main__":
    main()
