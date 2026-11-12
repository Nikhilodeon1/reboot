"""Task 5c: the standard cross-site check for detector 1, the log prevalence ratio.

Standard practice compares outcome prevalence across sites. The statistic is
fixed in PREREG_R1.md: the log prevalence ratio. The question is whether it can
separate a labeller mismatch from a genuine case-mix shift. From existing
artifacts only (detectors/results/external1.json, whole-cohort prevalences at
demo scale); nothing is retrained and no label arrays are read.

Each site has five definitions: four SOFA-based sepsis windows and ICD.
Cross-site pairs (MIMIC definition i against eICU definition j) fall in two groups:
  mismatch      one site labelled with ICD, the other with a SOFA variant
  non-mismatch  the same construct at both sites (identical definition, or two
                SOFA operationalisations), so any prevalence gap is case-mix
Detector 1 itself would call the non-mismatch pairs clean (kappa >= 0.6 between
SOFA variants) and the ICD-vs-SOFA pairs flagged.

    python rebuttal/scripts/task5c_prevalence_baseline.py
"""
import os
import json
import math
import itertools

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "detectors", "results", "external1.json")
OUT = os.path.join(ROOT, "rebuttal")

import sys
FULL = len(sys.argv) > 1 and sys.argv[1] == "--full"
base = "SOFA win[-48,+24]"
prev = {"MIMIC": {}, "eICU": {}}
if FULL:   # whole-cohort prevalences at full scale, from the bootstrap driver
    d = json.load(open(os.path.join(OUT, "results", "full_scale_bootstrap_kappa.json")))
    prev = {db: dict(d["prevalence"][db]) for db in prev}
else:
    d = json.load(open(SRC))
    for db in prev:
        prev[db]["ICD"] = d[f"{db} POSITIVE ICD vs {base}"]["prev_a"]
        prev[db][base] = d[f"{db} POSITIVE ICD vs {base}"]["prev_b"]
        for k, v in d.items():
            if k.startswith(f"{db} negative {base} vs "):
                prev[db][k.split(" vs ")[1]] = v["prev_b"]
defs = ["SOFA win[-48,+24]", "SOFA single-point", "SOFA win[-24,+12]", "SOFA win[-72,+24]", "ICD"]
assert all(x in prev[db] for db in prev for x in defs)

rows = []
for i, j in itertools.product(defs, defs):
    a, b = prev["MIMIC"][i], prev["eICU"][j]
    mism = (i == "ICD") != (j == "ICD")
    rows.append({"mimic_def": i, "eicu_def": j, "prev_mimic": a, "prev_eicu": b,
                 "log_pr": math.log(a / b), "abs_log_pr": abs(math.log(a / b)),
                 "group": "mismatch" if mism else "non-mismatch",
                 "identical_definition": i == j})

mm = [r["abs_log_pr"] for r in rows if r["group"] == "mismatch"]
nm = [r["abs_log_pr"] for r in rows if r["group"] == "non-mismatch"]
ident = [r["abs_log_pr"] for r in rows if r["identical_definition"]]
# AUROC of |log PR| for "mismatch" against "non-mismatch" (ties count half)
auc = sum((m > n) + 0.5 * (m == n) for m in mm for n in nm) / (len(mm) * len(nm))
res = {"source": ("rebuttal/results/full_scale_bootstrap_kappa.json (whole-cohort prevalences)" if FULL
                  else "detectors/results/external1.json (whole-cohort prevalences)"),
       "scale": ("full: MIMIC-IV 74829 stays, eICU 132900 stays" if FULL
                 else "demo: MIMIC-IV 117 stays, eICU 1627 stays"),
       "n_pairs": {"mismatch": len(mm), "non_mismatch": len(nm), "identical_definition": len(ident)},
       "abs_log_pr_range": {"mismatch": [min(mm), max(mm)], "non_mismatch": [min(nm), max(nm)],
                            "identical_definition": [min(ident), max(ident)]},
       "auroc_mismatch_vs_non_mismatch": auc,
       "reading": "an AUROC at or below 0.5 means a flag-on-large-ratio rule cannot pick out the mismatch pairs",
       "rows": rows}
os.makedirs(os.path.join(OUT, "results"), exist_ok=True)
os.makedirs(os.path.join(OUT, "tables"), exist_ok=True)
json.dump(res, open(os.path.join(OUT, "results", "task5c_prevalence_baseline" + ("_full" if FULL else "") + ".json"), "w"), indent=1)
with open(os.path.join(OUT, "tables", "task5c_prevalence_pairs" + ("_full" if FULL else "") + ".csv"), "w") as fh:
    fh.write("mimic_def,eicu_def,prev_mimic,prev_eicu,log_pr,group,identical_definition\n")
    for r in rows:
        fh.write(f"{r['mimic_def']},{r['eicu_def']},{r['prev_mimic']:.4f},{r['prev_eicu']:.4f},"
                 f"{r['log_pr']:.3f},{r['group']},{r['identical_definition']}\n")
print(json.dumps({k: v for k, v in res.items() if k != "rows"}, indent=1))
