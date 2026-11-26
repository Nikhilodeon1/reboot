"""E21 (PREREG_V2_ADDENDUM_12.md): the College Scorecard loader comparison with the benchmark's OWN code. RUN IN COLAB, not on the analysis machine.

    python e21_tableshift_run.py --scorecard /content/data/Scorecard.csv --out /content/drive/MyDrive/e21_out

Self-contained: it clones the benchmark at the pinned commit, installs the packages its module-level imports need, overrides only the
Kaggle download step (which demands an account token even when the file is already there), runs get_dataset("college_scorecard") on the
file as distributed (unguarded) and on the same file with rows lacking a completion rate removed (guarded), checks row alignment, and writes
aggregate results only.
"""
import os
import sys
import csv
import json
import shutil
import hashlib
import argparse
import subprocess

COMMIT = "fca9429814703a07e3902d005d46563a207b7f0a"
SHA256 = "fe433bd3c0fe05bc80aaf1454303c8c6e23ca1dafecec3bcd1522f7ee30b1ab1"
REPO = "https://github.com/mlfoundations/tableshift.git"
EXTRA_PACKAGES = ["fairlearn", "folktables", "frozendict", "xport", "ray", "datasets"]


def sh(*cmd):
    print("$", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def is_number(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return False
    return v == v  # excludes NaN


def read_columns(path):
    """UNITID and completion rate per input row, in file order, as text."""
    csv.field_size_limit(10 ** 9)
    units, rates = [], []
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        header = next(r)
        iu, ic = header.index("UNITID"), header.index("C150_4")
        for row in r:
            units.append(row[iu])
            rates.append(row[ic])
    return units, rates


def write_filtered(src, dst):
    """Copy of the file keeping only rows whose completion rate is a number; fields are not otherwise changed."""
    csv.field_size_limit(10 ** 9)
    with open(src, newline="", encoding="utf-8") as f, open(dst, "w", newline="", encoding="utf-8") as g:
        r, w = csv.reader(f), csv.writer(g)
        header = next(r)
        w.writerow(header)
        ic = header.index("C150_4")
        for row in r:
            if is_number(row[ic]):
                w.writerow(row)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scorecard", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--work", default="/content/e21_work")
    ap.add_argument("--skip-install", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    os.makedirs(a.work, exist_ok=True)

    digest = sha256_of(a.scorecard)
    if digest != SHA256:
        raise SystemExit(f"Scorecard.csv does not match the file used before: {digest}")
    if not a.skip_install:
        sh(sys.executable, "-m", "pip", "install", "-q", *EXTRA_PACKAGES)
    repo = os.path.join(a.work, "tableshift")
    if not os.path.isdir(repo):
        sh("git", "clone", "-q", REPO, repo)
    sh("git", "-C", repo, "checkout", "-q", COMMIT)
    sys.path.insert(0, repo)

    import numpy as np
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.metrics import roc_auc_score, balanced_accuracy_score
    from tableshift import get_dataset
    from tableshift.core import data_source

    # the only override: the file is already in place, so do not call the Kaggle command line
    data_source.KaggleDataSource._download_if_not_cached = lambda self: None

    units, rates = read_columns(a.scorecard)
    observed = np.array([is_number(x) for x in rates])
    truth = np.array([1 if (ok and float(x) > 0.5) else 0 for x, ok in zip(rates, observed)])
    keep = np.nonzero(observed)[0]

    def build(name, source_file, expected_rows, expected_target):
        cache = os.path.join(a.work, "cache_" + name)
        dest = os.path.join(cache, "kaggle", "college-scorecard")
        os.makedirs(dest, exist_ok=True)
        shutil.copyfile(source_file, os.path.join(dest, "Scorecard.csv"))
        dset = get_dataset("college_scorecard", cache_dir=cache)
        df = dset._df
        if len(df) != expected_rows:
            raise SystemExit(f"{name}: {len(df)} rows after the pipeline, expected {expected_rows} (rows were removed or added)")
        diff = int((df[dset.target].to_numpy().astype(int) != expected_target).sum())
        if diff:
            raise SystemExit(f"{name}: target differs from completion rate > 0.5 on {diff} rows; rows are not aligned")
        return dset

    guarded_file = os.path.join(a.work, "Scorecard_observed_only.csv")
    write_filtered(a.scorecard, guarded_file)
    U = build("unguarded", a.scorecard, len(rates), truth)
    G = build("guarded", guarded_file, len(keep), truth[keep])

    def xy(dset, rows):
        df = dset._df.iloc[rows]
        cols = [c for c in df.columns if c in dset.feature_names]
        return df[cols], df[dset.target].to_numpy().astype(int)

    splits = {k: np.asarray(v) for k, v in U.splits.items()}
    gsplits = {k: np.asarray(v) for k, v in G.splits.items()}
    out = {"commit": COMMIT, "file_sha256": digest, "rows": len(rates), "rows_with_completion_rate": int(observed.sum()),
           "n_features": len(U.feature_names),
           "unguarded_splits": {k: {"rows": int(len(v)), "without_completion_rate": int((~observed[v]).sum()),
                                    "of_those_labeled_1": int(truth[v][~observed[v]].sum())} for k, v in splits.items()},
           "guarded_splits": {k: {"rows": int(len(v))} for k, v in gsplits.items()}}
    out["gate_training_rows_without_completion_rate"] = int((~observed[splits["train"]]).sum())
    json.dump(out, open(os.path.join(a.out, "e21_tableshift_run.json"), "w"), indent=1)
    print(json.dumps(out, indent=1), flush=True)
    if out["gate_training_rows_without_completion_rate"] == 0:
        print("GATE: the pipeline's training split has no row without a completion rate. No metrics computed.")
        return

    mu = HistGradientBoostingClassifier().fit(*xy(U, splits["train"]))
    mg = HistGradientBoostingClassifier().fit(*xy(G, gsplits["train"]))

    pos_in_guarded = -np.ones(len(rates), dtype=int)
    pos_in_guarded[keep] = np.arange(len(keep))
    rng = np.random.default_rng(20261201)
    unit = np.array(units)

    def score(model, X):
        return model.predict(X), model.predict_proba(X)[:, 1]

    def metrics(y, p, prob, w):
        m_ = w > 0
        y, p, prob, w = y[m_], p[m_], prob[m_], w[m_]
        if len(np.unique(y)) < 2:
            return None
        return {"accuracy": float(np.average(p == y, weights=w)), "auroc": float(roc_auc_score(y, prob, sample_weight=w)),
                "balanced_accuracy": float(balanced_accuracy_score(y, p, sample_weight=w))}

    def compare(rows_a, pred_a, y_a, rows_b, pred_b, y_b):
        ids = np.unique(np.concatenate([unit[rows_a], unit[rows_b]]))
        where = {u: i for i, u in enumerate(ids)}
        ia, ib = np.array([where[u] for u in unit[rows_a]]), np.array([where[u] for u in unit[rows_b]])
        one_a, one_b = np.ones(len(rows_a)), np.ones(len(rows_b))
        point_a, point_b = metrics(y_a, *pred_a, one_a), metrics(y_b, *pred_b, one_b)
        draws = {k: [] for k in point_a}
        for _ in range(2000):
            mult = np.bincount(rng.integers(0, len(ids), len(ids)), minlength=len(ids)).astype(float)
            ma, mb = metrics(y_a, *pred_a, mult[ia]), metrics(y_b, *pred_b, mult[ib])
            if ma and mb:
                for k in draws:
                    draws[k].append(ma[k] - mb[k])
        return {"first": point_a, "second": point_b, "rows_first": int(len(rows_a)), "rows_second": int(len(rows_b)), "institutions": int(len(ids)),
                "gap_first_minus_second": {k: {"point": point_a[k] - point_b[k],
                                               "ci95": [float(np.percentile(draws[k], 2.5)), float(np.percentile(draws[k], 97.5))]} for k in point_a}}

    # reported gaps: each pipeline on its own test split
    for split in ("ood_test", "id_test"):
        ru, rg_local = splits[split], gsplits[split]
        Xu, yu = xy(U, ru)
        Xg, yg = xy(G, rg_local)
        out[f"reported_{split}"] = compare(ru, score(mu, Xu), yu, keep[rg_local], score(mg, Xg), yg)
    # true-label gap: the same observed out-of-domain test rows, each model with its own pipeline's encoding
    common = splits["ood_test"][observed[splits["ood_test"]]]
    Xu, _ = xy(U, common)
    Xg, _ = xy(G, pos_in_guarded[common])
    train_g = set(keep[gsplits["train"]].tolist())
    if train_g & set(common.tolist()) or set(splits["train"].tolist()) & set(common.tolist()):
        raise SystemExit("an evaluation row is in a training split")
    out["true_label_ood"] = compare(common, score(mu, Xu), truth[common], common, score(mg, Xg), truth[common])

    gap_rep = out["reported_ood_test"]["gap_first_minus_second"]["auroc"]["point"]
    gap_true = out["true_label_ood"]["gap_first_minus_second"]["auroc"]["point"]
    out["bounds"] = {"reported_auroc_gap_above_0.02": bool(gap_rep > 0.02), "true_label_auroc_gap_at_most_0.01": bool(gap_true <= 0.01)}
    freeze = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True).stdout
    open(os.path.join(a.out, "e21_pip_freeze.txt"), "w").write(f"python {sys.version}\n{freeze}")
    json.dump(out, open(os.path.join(a.out, "e21_tableshift_run.json"), "w"), indent=1)
    print(json.dumps({k: out[k] for k in ("reported_ood_test", "true_label_ood", "bounds")}, indent=1))
    print("done; results in", a.out)


if __name__ == "__main__":
    main()
