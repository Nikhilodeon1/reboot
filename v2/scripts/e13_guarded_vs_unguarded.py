"""E13 (PREREG_V2_ADDENDUM_5.md): guarded against unguarded College Scorecard pipeline.

Two pipelines on the same official institution file, the same features, the same five 70/30 splits and the same model as E12:
  unguarded: the shipped line, (target > 0.5).astype(int) with every row kept, so a missing target becomes 0;
  guarded:   rows with a missing target are dropped before thresholding, and the model is trained and tested on the rest.
Reported per pipeline on its own test set (what a user would report), and the two models are also scored on the observed-target test
rows with their true labels (what the model is worth).

    python -W ignore v2/scripts/e13_guarded_vs_unguarded.py --data <dir containing Most-Recent-Cohorts-Institution*.zip> [--out DIR]

Imports extraction and preprocessing of e12_consequences.py unchanged. Output: v2/results/e13_guarded_vs_unguarded.json (aggregates only).
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


def m(y, p, prob):
    return {"accuracy": float((p == y).mean()), "balanced_accuracy": float(balanced_accuracy_score(y, p)),
            "auroc": float(roc_auc_score(y, prob))}


def tci(v):
    v = np.asarray(v, float)
    h = stats.t.ppf(0.975, len(v) - 1) * v.std(ddof=1) / np.sqrt(len(v))
    return [float(v.mean()), float(v.mean() - h), float(v.mean() + h)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", default=os.path.join(os.path.dirname(HERE), "results"))
    a = ap.parse_args()
    verb = os.path.join(a.out, "_verbatim_tmp_e13")
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
    y_g = (raw["C150_4"] > 0.5).astype(int).to_numpy()          # label with true meaning; used only where observed
    rows = []
    for seed in range(5):
        tr, te = train_test_split(np.arange(len(raw)), test_size=0.3, random_state=seed)
        # unguarded pipeline
        mu = HistGradientBoostingClassifier(random_state=seed).fit(X.iloc[tr], y_un[tr])
        pu, pru = mu.predict(X.iloc[te]), mu.predict_proba(X.iloc[te])[:, 1]
        # guarded pipeline: drop missing targets, train and test on observed rows only
        trg, teg = tr[obs[tr]], te[obs[te]]
        mg = HistGradientBoostingClassifier(random_state=seed).fit(X.iloc[trg], y_g[trg])
        pg, prg = mg.predict(X.iloc[teg]), mg.predict_proba(X.iloc[teg])[:, 1]
        # both models on the guarded test rows with true labels
        pu_on_g, pru_on_g = mu.predict(X.iloc[teg]), mu.predict_proba(X.iloc[teg])[:, 1]
        rows.append({"seed": seed,
                     "n_train_unguarded": int(len(tr)), "n_train_guarded": int(len(trg)),
                     "reported_unguarded": m(y_un[te], pu, pru),
                     "reported_guarded": m(y_g[teg], pg, prg),
                     "unguarded_model_on_observed_rows": m(y_g[teg], pu_on_g, pru_on_g),
                     "guarded_model_on_observed_rows": m(y_g[teg], pg, prg)})
    agg = {}
    for key in ("accuracy", "balanced_accuracy", "auroc"):
        agg["reported_gap_" + key] = tci([r["reported_unguarded"][key] - r["reported_guarded"][key] for r in rows])
        agg["true_label_gap_" + key] = tci([r["unguarded_model_on_observed_rows"][key] - r["guarded_model_on_observed_rows"][key] for r in rows])
        agg["reported_unguarded_" + key] = tci([r["reported_unguarded"][key] for r in rows])
        agg["reported_guarded_" + key] = tci([r["reported_guarded"][key] for r in rows])
    out = {"note": "each entry is [mean, lower, upper], a t-interval over five random 70/30 splits (df 4). reported_gap = unguarded pipeline's own test metric minus guarded pipeline's own test metric; true_label_gap = unguarded-trained minus guarded-trained model, both scored on observed-target test rows with their true labels",
           "aggregate": agg, "per_split": rows}
    os.makedirs(a.out, exist_ok=True)
    json.dump(out, open(os.path.join(a.out, "e13_guarded_vs_unguarded.json"), "w"), indent=1)
    shutil.rmtree(verb, ignore_errors=True)
    print(json.dumps(agg, indent=1))


if __name__ == "__main__":
    main()
