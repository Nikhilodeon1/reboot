"""E12 (PREREG_V2_ADDENDUM_1.md and its addendum 2): consequence studies on four sites in other groups' code.

    python v2/scripts/e12_consequences.py extract --out <scratch dir>          # host: verbatim third-party text at the pinned commits
    python -W ignore v2/scripts/e12_consequences.py s1 --data <dir> [--out DIR]  # host: tableshift College Scorecard
    python -W ignore v2/scripts/e12_consequences.py s23 --verbatim <dir> --out DIR   # inside the container: fairseq2 and robustdg sites

Third-party functions are executed from their verbatim text; nothing from those repositories is imported or installed.
"""
import os
import re
import io
import ast
import sys
import json
import zipfile
import argparse
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
CORPUS = os.environ.get("SCAN_CORPUS", r"C:\Users\nikhi\Codes\RES\src\pclCodebase\scan_corpus")
PIN = {"tableshift": ("tableshift", "fca9429814", "tableshift/datasets/college_scorecard.py"),
       "fairseq2": ("fairseq2", "7f06d6f4f5", "src/fairseq2/data/parquet/arrow_transform.py"),
       "robustdg": ("robustdg", "3eee1730ae", "utils/scripts/utils.py")}


def git_show(key):
    repo, sha, path = PIN[key]
    r = subprocess.run(["git", "-C", os.path.join(CORPUS, repo), "show", f"{sha}:{path}"], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", check=True)
    return r.stdout


def seg(src, name):
    tree = ast.parse(src)
    for n in tree.body:
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return ast.get_source_segment(src, n)
    raise KeyError(name)


def extract(out):
    os.makedirs(out, exist_ok=True)
    fs = git_show("fairseq2")
    header = "\n".join(l for l in fs.splitlines()[:16] if l.startswith(("from ", "import ")))
    body = "\n\n\n".join(seg(fs, n) for n in ("filter_list_by_range", "filter_list_with_min_max_length"))
    open(os.path.join(out, "fairseq2_filters.py"), "w", encoding="utf-8").write(header + "\n\n\n" + body + "\n")
    rg = git_show("robustdg")
    lines = rg.splitlines()
    i = next(k for k, l in enumerate(lines) if "loss_val = max(stats['loss_tr'][-1], stats['loss_te'][-1])" in l)
    open(os.path.join(out, "robustdg_lines.txt"), "w", encoding="utf-8").write("\n".join(lines[i:i + 3]) + "\n")
    m = re.search(r"^MAX_LOSS_VAL\s*=\s*(.+)$", rg, flags=re.M)
    open(os.path.join(out, "robustdg_maxloss.txt"), "w", encoding="utf-8").write((m.group(1) if m else "MISSING") + "\n")
    ts = git_show("tableshift")
    open(os.path.join(out, "tableshift_preprocess.py"), "w", encoding="utf-8").write("import pandas as pd\n\n" + seg(ts, "preprocess_college_scorecard") + "\n")
    feats = re.findall(r"Feature\('([A-Za-z0-9_]+)'", ts)
    open(os.path.join(out, "tableshift_features.json"), "w", encoding="utf-8").write(json.dumps(feats))
    print("extracted", os.listdir(out))


def s23(verbatim, out):
    import numpy as np
    import pyarrow as pa
    import pyarrow.compute as pc
    import polars as pl
    sys.path.insert(0, verbatim)
    import fairseq2_filters as F
    res = {"versions": {"numpy": np.__version__, "pyarrow": pa.__version__, "polars": pl.__version__}, "S2": [], "S3": []}
    rng = np.random.default_rng(12345)
    N = 10000
    for pnull in (0.0, 0.01, 0.05):
        for variant in ("all_non_null_pass", "one_failing_row"):
            vals, lens = [], []
            for i in range(N):
                if rng.random() < pnull:
                    vals.append(None)
                else:
                    k = int(rng.integers(1, 20))
                    vals.append([float(x) for x in rng.uniform(0, 10, size=k)])
            if variant == "one_failing_row":
                vals.append([1.0e6])
            t = pa.table({"x": pa.array(vals, type=pa.list_(pa.float64()))})
            out_t = F.filter_list_by_range(t, "x", 0.0, 100.0)
            rows_in, nulls_in = t.num_rows, int(pc.sum(pc.is_null(t["x"]).cast(pa.int64())).as_py())
            nulls_out = int(pc.sum(pc.is_null(out_t["x"]).cast(pa.int64())).as_py()) if out_t.num_rows else 0
            lt = pa.table({"x": pa.array([(v if v is None else v[:5]) for v in vals], type=pa.list_(pa.float64()))})
            out_l = F.filter_list_with_min_max_length(lt, ["x"], 1, 5) if variant == "all_non_null_pass" else \
                F.filter_list_with_min_max_length(pa.table({"x": pa.array(vals[:-1] + [[0.0] * 9], type=pa.list_(pa.float64()))}), ["x"], 1, 5)
            nulls_out_l = int(pc.sum(pc.is_null(out_l["x"]).cast(pa.int64())).as_py()) if out_l.num_rows else 0
            res["S2"].append({"p_null": pnull, "variant": variant, "rows_in": rows_in, "null_rows_in": nulls_in,
                              "range_filter": {"rows_out": out_t.num_rows, "null_rows_out": nulls_out},
                              "length_filter": {"rows_out": out_l.num_rows, "null_rows_out": nulls_out_l}})
    max_loss = open(os.path.join(verbatim, "robustdg_maxloss.txt"), encoding="utf-8").read().strip()
    lines = open(os.path.join(verbatim, "robustdg_lines.txt"), encoding="utf-8").read()
    for tr, te, label in ((float("nan"), 0.5, "train NaN, test finite"), (0.5, float("nan"), "train finite, test NaN"),
                          (float("nan"), float("nan"), "both NaN"), (0.5, float("inf"), "train finite, test inf")):
        stats = {"loss_tr": [tr], "loss_te": [te]}
        ns = {"np": np, "stats": stats, "diverged": False, "MAX_LOSS_VAL": eval(max_loss, {"np": np}) if max_loss != "MISSING" else 1e6}
        code = lines.strip().splitlines()
        src = "\n".join(l.strip() for l in code[:1]) + "\nif loss_val > MAX_LOSS_VAL: diverged = True\nif not np.isfinite(loss_val): diverged = True\n"
        exec(src, ns)
        res["S3"].append({"case": label, "loss_val": repr(ns["loss_val"]), "diverged": bool(ns["diverged"])})
    os.makedirs(out, exist_ok=True)
    json.dump(res, open(os.path.join(out, "e12_s2_s3.json"), "w"), indent=1)
    print(json.dumps(res, indent=1))


def s1(data, out):
    import numpy as np
    import pandas as pd
    from scipy import stats
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.model_selection import train_test_split
    verb = os.path.join(out, "_verbatim_tmp")
    extract(verb)
    sys.path.insert(0, verb)
    ns = {}

    class _F:
        target = "C150_4"
    exec("import pandas as pd\n" + open(os.path.join(verb, "tableshift_preprocess.py"), encoding="utf-8").read().replace("import pandas as pd\n", "", 1),
         {"pd": pd, "COLLEGE_SCORECARD_FEATURES": _F}, ns)
    pre = ns["preprocess_college_scorecard"]
    ns["COLLEGE_SCORECARD_FEATURES"] = _F
    pre.__globals__["COLLEGE_SCORECARD_FEATURES"] = _F
    z = zipfile.ZipFile(next(os.path.join(data, f) for f in os.listdir(data) if f.startswith("Most-Recent-Cohorts-Institution")))
    member = next(n for n in z.namelist() if n.lower().endswith(".csv") and "institution" in n.lower() and "data_dictionary" not in n.lower())
    raw = pd.read_csv(io.BytesIO(z.read(member)), low_memory=False, na_values=["NULL", "PrivacySuppressed"])
    feats = [f for f in json.load(open(os.path.join(verb, "tableshift_features.json"))) if f in raw.columns and f != "C150_4"]
    n_inst = len(raw)
    n_missing = int(raw["C150_4"].isna().sum())
    unguarded = pre(raw.copy())
    guarded = pre(raw.dropna(subset=["C150_4"]).copy())
    res = {"file": member, "institutions": n_inst, "missing_target": n_missing, "missing_share": n_missing / n_inst,
           "label_balance_unguarded_positive_share": float(unguarded["C150_4"].mean()),
           "label_balance_guarded_positive_share": float(guarded["C150_4"].mean()),
           "n_feature_columns_present": len(feats), "feature_columns_missing_from_file": None}
    allf = json.load(open(os.path.join(verb, "tableshift_features.json")))
    res["feature_columns_missing_from_file"] = [f for f in allf if f not in raw.columns]
    X = raw[feats].copy()
    for c in X.columns:
        if X[c].dtype == object:
            X[c] = X[c].astype("category").cat.codes
    y_un = unguarded["C150_4"].to_numpy()
    obs = raw["C150_4"].notna().to_numpy()
    ctrl = raw["CONTROL"].to_numpy() if "CONTROL" in raw.columns else np.zeros(n_inst)
    deltas_random, deltas_id, deltas_ood = [], [], []
    detail = []
    for seed in range(5):
        tr, te = train_test_split(np.arange(n_inst), test_size=0.3, random_state=seed)
        m = HistGradientBoostingClassifier(random_state=seed).fit(X.iloc[tr], y_un[tr])
        p = m.predict(X.iloc[te])
        a_un = float((p == y_un[te]).mean())
        a_obs = float((p[obs[te]] == y_un[te][obs[te]]).mean())
        deltas_random.append(a_un - a_obs)
        ood = ctrl == 3
        idx_id, idx_ood = np.where(~ood)[0], np.where(ood)[0]
        tr2, te2 = train_test_split(idx_id, test_size=0.3, random_state=seed)
        m2 = HistGradientBoostingClassifier(random_state=seed).fit(X.iloc[tr2], y_un[tr2])
        for name, idx, store in (("id", te2, deltas_id), ("ood", idx_ood, deltas_ood)):
            p2 = m2.predict(X.iloc[idx])
            store.append(float((p2 == y_un[idx]).mean()) - float((p2[obs[idx]] == y_un[idx][obs[idx]]).mean()))
        detail.append({"seed": seed, "acc_unguarded_random": a_un, "acc_observed_only_random": a_obs})

    def ci(v):
        v = np.asarray(v, float)
        m, s = v.mean(), v.std(ddof=1)
        h = stats.t.ppf(0.975, len(v) - 1) * s / np.sqrt(len(v))
        return {"mean_points": float(100 * m), "t95_points": [float(100 * (m - h)), float(100 * (m + h))], "per_seed_points": [float(100 * x) for x in v]}
    res["effect_random_split"] = ci(deltas_random)
    res["effect_domain_split_id"] = ci(deltas_id)
    res["effect_domain_split_ood"] = ci(deltas_ood)
    res["detail"] = detail
    res["class_rule"] = "negligible < 0.5 points, small 0.5 to 2, material > 2 (fixed in the addendum)"
    os.makedirs(out, exist_ok=True)
    json.dump(res, open(os.path.join(out, "e12_s1_tableshift.json"), "w"), indent=1)
    import shutil
    shutil.rmtree(verb, ignore_errors=True)
    print(json.dumps({k: v for k, v in res.items() if k != "detail"}, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["extract", "s1", "s23"])
    ap.add_argument("--out", default=os.path.join(ROOT, "v2", "results"))
    ap.add_argument("--data")
    ap.add_argument("--verbatim")
    a = ap.parse_args()
    if a.stage == "extract":
        extract(a.out)
    elif a.stage == "s1":
        s1(a.data, a.out)
    else:
        s23(a.verbatim, a.out)
