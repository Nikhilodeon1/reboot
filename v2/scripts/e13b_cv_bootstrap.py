"""E13b: Non-overlapping 5-fold CV + paired institution-level bootstrap for College Scorecard.

Eliminates the overlapping-split dependence of E13's five random 70/30 splits by evaluating
each of the 6,272 institutions in exactly one held-out fold, then computing 2,000 paired
institution-level bootstrap resamples for valid 95% confidence intervals.

    python -W ignore v2/scripts/e13b_cv_bootstrap.py --data C:\\Users\\nikhi\\Codes\\RES\\datasets\\public_v2
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
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score, balanced_accuracy_score
from sklearn.model_selection import KFold

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import e12_consequences as e12  # noqa: E402


def metrics(y, p, prob):
    return {
        "accuracy": float((p == y).mean()),
        "balanced_accuracy": float(balanced_accuracy_score(y, p)),
        "auroc": float(roc_auc_score(y, prob)),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", default=os.path.join(os.path.dirname(HERE), "results"))
    ap.add_argument("--boot", type=int, default=2000)
    a = ap.parse_args()

    verb = os.path.join(a.out, "_verbatim_tmp_e13b")
    e12.extract(verb)

    class _F:
        target = "C150_4"

    ns = {}
    exec(
        "import pandas as pd\n"
        + open(os.path.join(verb, "tableshift_preprocess.py"), encoding="utf-8")
        .read()
        .replace("import pandas as pd\n", "", 1),
        {"pd": pd, "COLLEGE_SCORECARD_FEATURES": _F},
        ns,
    )
    pre = ns["preprocess_college_scorecard"]
    pre.__globals__["COLLEGE_SCORECARD_FEATURES"] = _F

    z = zipfile.ZipFile(
        next(
            os.path.join(a.data, f)
            for f in os.listdir(a.data)
            if f.startswith("Most-Recent-Cohorts-Institution")
        )
    )
    member = next(
        n
        for n in z.namelist()
        if n.lower().endswith(".csv")
        and "institution" in n.lower()
        and "data_dictionary" not in n.lower()
    )
    raw = pd.read_csv(
        io.BytesIO(z.read(member)),
        low_memory=False,
        na_values=["NULL", "PrivacySuppressed"],
    )
    feats = [
        f
        for f in json.load(open(os.path.join(verb, "tableshift_features.json")))
        if f in raw.columns and f != "C150_4"
    ]
    X = raw[feats].copy()
    for c in X.columns:
        if not pd.api.types.is_numeric_dtype(X[c]):
            X[c] = X[c].astype("category").cat.codes

    y_un = pre(raw.copy())["C150_4"].to_numpy()
    obs = raw["C150_4"].notna().to_numpy()
    y_g = (raw["C150_4"] > 0.5).astype(int).to_numpy()
    n = len(raw)

    pu_oof = np.zeros(n, dtype=int)
    pru_oof = np.zeros(n, dtype=float)
    pg_oof = np.zeros(n, dtype=int)
    prg_oof = np.zeros(n, dtype=float)

    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    for fold, (tr, te) in enumerate(kf.split(np.arange(n))):
        mu = HistGradientBoostingClassifier(random_state=fold).fit(X.iloc[tr], y_un[tr])
        pu_oof[te] = mu.predict(X.iloc[te])
        pru_oof[te] = mu.predict_proba(X.iloc[te])[:, 1]

        trg = tr[obs[tr]]
        teg = te[obs[te]]
        mg = HistGradientBoostingClassifier(random_state=fold).fit(X.iloc[trg], y_g[trg])
        pg_oof[teg] = mg.predict(X.iloc[teg])
        prg_oof[teg] = mg.predict_proba(X.iloc[teg])[:, 1]

    # Point estimates on full out-of-fold predictions
    pt_rep_u = metrics(y_un, pu_oof, pru_oof)
    pt_rep_g = metrics(y_g[obs], pg_oof[obs], prg_oof[obs])
    pt_u_on_g = metrics(y_g[obs], pu_oof[obs], pru_oof[obs])

    # Paired institution-level bootstrap
    rng = np.random.default_rng(42)
    boot_rep_gap = {k: [] for k in ("accuracy", "balanced_accuracy", "auroc")}
    boot_true_gap = {k: [] for k in ("accuracy", "balanced_accuracy", "auroc")}
    for _ in range(a.boot):
        idx = rng.integers(0, n, size=n)
        m_u = metrics(y_un[idx], pu_oof[idx], pru_oof[idx])
        idx_o = idx[obs[idx]]
        m_g = metrics(y_g[idx_o], pg_oof[idx_o], prg_oof[idx_o])
        m_ug = metrics(y_g[idx_o], pu_oof[idx_o], pru_oof[idx_o])
        for k in ("accuracy", "balanced_accuracy", "auroc"):
            boot_rep_gap[k].append(m_u[k] - m_g[k])
            boot_true_gap[k].append(m_ug[k] - m_g[k])

    agg = {}
    for k in ("accuracy", "balanced_accuracy", "auroc"):
        r_pt = pt_rep_u[k] - pt_rep_g[k]
        r_lo, r_hi = np.percentile(boot_rep_gap[k], [2.5, 97.5])
        agg["reported_gap_" + k] = [float(r_pt), float(r_lo), float(r_hi)]
        t_pt = pt_u_on_g[k] - pt_rep_g[k]
        t_lo, t_hi = np.percentile(boot_true_gap[k], [2.5, 97.5])
        agg["true_label_gap_" + k] = [float(t_pt), float(t_lo), float(t_hi)]

    out = {
        "note": f"Non-overlapping 5-fold CV (KFold seed 42) across all {n} institutions ({int(obs.sum())} observed), with {a.boot} paired institution-level bootstrap resamples (95% percentile CI).",
        "n_total": int(n),
        "n_observed": int(obs.sum()),
        "boot_resamples": int(a.boot),
        "point_reported_unguarded": pt_rep_u,
        "point_reported_guarded": pt_rep_g,
        "point_unguarded_on_observed": pt_u_on_g,
        "aggregate": agg,
    }
    os.makedirs(a.out, exist_ok=True)
    json.dump(out, open(os.path.join(a.out, "e13b_cv_bootstrap.json"), "w"), indent=1)
    shutil.rmtree(verb, ignore_errors=True)
    print(json.dumps(agg, indent=1))


if __name__ == "__main__":
    main()
