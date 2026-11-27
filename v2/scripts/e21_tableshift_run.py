"""E21 (PREREG_V2_ADDENDUM_12.md): the College Scorecard loader comparison with the benchmark's OWN code. RUN IN COLAB, not on the analysis machine.

    python e21_tableshift_run.py --scorecard /content/data/Scorecard.csv --out /content/drive/MyDrive/e21_out

Self-contained: it builds a Python 3.8 environment with the benchmark's own version pins (PREREG_V2_ADDENDUM_14.md), reruns itself in it,
clones the benchmark at the pinned commit, overrides only the Kaggle download step (which demands an account token even when the file is
already there), runs get_dataset("college_scorecard") on the file as distributed (unguarded) and on the same file with rows lacking a
completion rate removed (guarded), checks row alignment, and writes aggregate results only.
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
PYTHON = "3.8"
TORCH = "torch==1.13.0"
TORCH_INDEX = "https://download.pytorch.org/whl/cpu"
SEEDS = list(range(10))
CUTOFF = "2023-06-01T00:00:00Z"  # releases after this date are ignored for everything not pinned here
PINS = ["numpy==1.23.5", "pandas==1.5.3", "scikit-learn==1.1.3", "scipy==1.9.3", "ray==2.2.0", "datasets==2.11.0",
        "fairlearn==0.8.0", "frozendict==2.3.4", "requests==2.28.1", "pyarrow==11.0.0", "huggingface-hub==0.13.3",
        "dill==0.3.6", "fsspec==2022.11.0", "joblib==1.2.0", "threadpoolctl==3.1.0", "folktables", "xport"]


def build_environment(work):
    """A Python 3.8 interpreter with the pinned packages; returns its path."""
    venv = os.path.join(work, "venv38")
    py = os.path.join(venv, "bin", "python")
    sh(sys.executable, "-m", "pip", "install", "-q", "uv")
    if not os.path.exists(py):
        sh(sys.executable, "-m", "uv", "venv", "-q", "--python", PYTHON, venv)
    sh(sys.executable, "-m", "uv", "pip", "install", "-q", "--python", py, "--index-url", TORCH_INDEX, TORCH + "+cpu",
       "typing_extensions==4.4.0")
    sh(sys.executable, "-m", "uv", "pip", "install", "-q", "--python", py, "--exclude-newer", CUTOFF, *PINS)
    return py


def installed_versions():
    from importlib import metadata
    return sorted({f"{d.metadata['Name']}=={d.version}" for d in metadata.distributions()}, key=str.lower)



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
    ap.add_argument("--in-env", action="store_true", help="set by the script itself once it runs inside the pinned environment")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    os.makedirs(a.work, exist_ok=True)

    digest = sha256_of(a.scorecard)
    if digest != SHA256:
        raise SystemExit(f"Scorecard.csv does not match the file used before: {digest}")
    if not a.in_env:
        py = build_environment(a.work)
        env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTHONHOME", "MPLBACKEND")}
        code = subprocess.run([py, os.path.abspath(__file__), "--scorecard", os.path.abspath(a.scorecard),
                               "--out", os.path.abspath(a.out), "--work", os.path.abspath(a.work), "--in-env"], env=env).returncode
        raise SystemExit(code)
    with open(os.path.join(a.out, "e21_pip_freeze.txt"), "w") as f:
        f.write("python " + sys.version + "\n" + "\n".join(installed_versions()) + "\n")
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

    pos_in_guarded = -np.ones(len(rates), dtype=int)
    pos_in_guarded[keep] = np.arange(len(keep))
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

    def compare(rng, rows_a, pred_a, y_a, rows_b, pred_b, y_b):
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

    # evaluation rows, the same for every seed
    common = splits["ood_test"][observed[splits["ood_test"]]]
    train_g = set(keep[gsplits["train"]].tolist())
    if train_g & set(common.tolist()) or set(splits["train"].tolist()) & set(common.tolist()):
        raise SystemExit("an evaluation row is in a training split")
    train_u, train_gg = xy(U, splits["train"]), xy(G, gsplits["train"])
    common_u, common_g = xy(U, common)[0], xy(G, pos_in_guarded[common])[0]

    def evaluate(seed):
        mu = HistGradientBoostingClassifier(random_state=seed).fit(*train_u)
        mg = HistGradientBoostingClassifier(random_state=seed).fit(*train_gg)
        rng = np.random.default_rng(20261201)  # the same bootstrap draws for every model seed
        res = {"iterations": {"unguarded": int(mu.n_iter_), "guarded": int(mg.n_iter_)}}
        # reported gaps: each pipeline on its own test split
        for split in ("ood_test", "id_test"):
            ru, rg_local = splits[split], gsplits[split]
            Xu, yu = xy(U, ru)
            Xg, yg = xy(G, rg_local)
            res["reported_" + split] = compare(rng, ru, score(mu, Xu), yu, keep[rg_local], score(mg, Xg), yg)
        # true-label gap: the same observed out-of-domain test rows, each model with its own pipeline's encoding
        res["true_label_ood"] = compare(rng, common, score(mu, common_u), truth[common], common, score(mg, common_g), truth[common])
        return res

    runs = {}
    for seed in SEEDS:
        runs[seed] = evaluate(seed)
        out["runs"] = runs
        json.dump(out, open(os.path.join(a.out, "e21_tableshift_run.json"), "w"), indent=1)
        print("seed", seed, "reported ood auroc gap %.4f, true-label auroc gap %.4f" % (
            runs[seed]["reported_ood_test"]["gap_first_minus_second"]["auroc"]["point"],
            runs[seed]["true_label_ood"]["gap_first_minus_second"]["auroc"]["point"]), flush=True)

    summary = {}
    for block in ("reported_ood_test", "reported_id_test", "true_label_ood"):
        summary[block] = {}
        for k in ("accuracy", "auroc", "balanced_accuracy"):
            gaps = [runs[s][block]["gap_first_minus_second"][k] for s in SEEDS]
            points = [g["point"] for g in gaps]
            summary[block][k] = {"median": float(np.median(points)), "min": float(min(points)), "max": float(max(points)),
                                 "seeds_interval_above_zero": int(sum(g["ci95"][0] > 0 for g in gaps)),
                                 "seeds_interval_below_zero": int(sum(g["ci95"][1] < 0 for g in gaps))}
    rep_points = [runs[s]["reported_ood_test"]["gap_first_minus_second"]["auroc"]["point"] for s in SEEDS]
    true_points = [runs[s]["true_label_ood"]["gap_first_minus_second"]["auroc"]["point"] for s in SEEDS]
    out["summary"] = summary
    out["bounds"] = {"reported_auroc_gap_above_0.02": {"seeds_meeting": int(sum(x > 0.02 for x in rep_points)),
                                                       "median_meets": bool(np.median(rep_points) > 0.02)},
                     "true_label_auroc_gap_at_most_0.01": {"seeds_meeting": int(sum(x <= 0.01 for x in true_points)),
                                                           "median_meets": bool(np.median(true_points) <= 0.01)}}
    json.dump(out, open(os.path.join(a.out, "e21_tableshift_run.json"), "w"), indent=1)
    print(json.dumps({"summary": summary, "bounds": out["bounds"]}, indent=1))
    print("done; results in", a.out)


if __name__ == "__main__":
    main()
