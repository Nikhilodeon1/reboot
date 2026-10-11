"""Agreement between the second labeller's labels on the 12 spot-check sites and the labels
committed before the detector ran (task3b_labels.json, task4c_labels.json).
Writes rebuttal/results/spotcheck_agreement.json (aggregate counts and per-site labels of
third-party code locations only; no patient-level data)."""
import json
import os
from scipy.stats import beta

ROOT = os.path.join(os.path.dirname(__file__), "..")


def cp(k, n, a=0.05):
    lo = 0.0 if k == 0 else float(beta.ppf(a / 2, k, n - k + 1))
    hi = 1.0 if k == n else float(beta.ppf(1 - a / 2, k + 1, n - k))
    return round(lo, 3), round(hi, 3)


T3 = json.load(open(os.path.join(ROOT, "results", "task3b_labels.json")))
T4 = json.load(open(os.path.join(ROOT, "results", "task4c_labels.json")))
# (part, repo, file suffix, line, second labeller's label)
SITES = [
    (1, "MIMIC-IV-Data-Pipeline", "model/behrt_train.py", 215, "SOUND"),
    (1, "HIRID-ICU-Benchmark", "synthetic_data/collect_stats.py", 35, "NOT_SELECTION"),
    (1, "MIMIC-IV-Data-Pipeline", "feature_selection_icu.py", 169, "NOT_SELECTION"),
    (1, "TPC-LoS-prediction", "best_hyperparameters.py", 50, "SOUND"),
    (1, "Benchmarking_DL_MIMICIII", "bart_utils.py", 1179, "NOT_SELECTION"),
    (1, "TPC-LoS-prediction", "best_hyperparameters.py", 77, "SOUND"),
    (2, "mimic3-benchmarks", "keras_utils.py", 62, "GUARDED"),
    (2, "omop-learn", "model_lr.py", 49, "UNREACHABLE"),
    (2, "FIDDLE", "steps.py", 314, "GUARDED"),
    (2, "circEWS", "data.py", 139, "NOT_APPLICABLE"),
    (2, "mimic3-benchmarks", "keras_utils.py", 221, "UNREACHABLE"),
    (2, "fairseq2", "checkpoint.py", 104, "REACHABLE_UNGUARDED"),
]
rows = []
for part, repo, f, line, other in SITES:
    src = T3 if part == 1 else T4
    m = [x for x in src if x["repo"] == repo and x["file"].endswith(f) and x["start"] <= line <= x["end"]]
    assert len(m) >= 1, (repo, f, line)
    mine = m[0]["label"]
    rows.append({"part": part, "repo": repo, "file": m[0]["file"], "lines": [m[0]["start"], m[0]["end"]],
                 "committed_label": mine, "second_label": other, "agree": mine == other})
k = sum(r["agree"] for r in rows)
out = {"agree": k, "n": len(rows), "cp95": cp(k, len(rows)),
       "part1": [sum(r["agree"] for r in rows if r["part"] == 1), 6],
       "part2": [sum(r["agree"] for r in rows if r["part"] == 2), 6],
       "sensitivity": {
           "note": "adopt the second labeller's labels at the disagreeing sites; no site becomes CONTAMINATED",
           "type1_narrow": [5, 49, cp(5, 49)], "type1_broad": [17, 49, cp(17, 49)],
           "detector3_real_selection_sites": [0, 25, cp(0, 25)]},
       "sites": rows}
json.dump(out, open(os.path.join(ROOT, "results", "spotcheck_agreement.json"), "w"), indent=1)
print(k, len(rows), out["cp95"], out["part1"], out["part2"])
for r in rows:
    if not r["agree"]:
        print(r["part"], r["repo"], r["committed_label"], "vs", r["second_label"])
