"""E14 (PREREG_V2_ADDENDUM_5.md): draw the equivalence sample of mutation survivors on decision lines, and summarise the labels.

    python v2/scripts/e14_equivalence_sample.py draw      # writes v2/results/e14_sample.json (25 survivors, with the mutated line and context)
    python v2/scripts/e14_equivalence_sample.py summarise # reads v2/results/e14_labels.json, writes v2/results/e14_equivalence.json

Decision-line survivors are those the E6 triage assigns to 'decision constant' (module-level constants) or 'verdict, test or statistic
definition' (the hand-listed lines A of e6_triage.py): 88 of the 256 survivors. Sample: numpy seed 0, sorted by (file, line, change).
"""
import os
import ast
import sys
import json
import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.dirname(HERE)
ROOT = os.path.dirname(V2)
A = {"check1_label_shift.py": {27, 32, 41}, "check2_pretrain_leakage.py": set(range(107, 113)) | {139, 141, 145, 211, 220}}


def role(tree, line):
    for node in ast.walk(tree):
        if not hasattr(node, "lineno"):
            continue
        if node.lineno <= line <= getattr(node, "end_lineno", node.lineno):
            if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "print":
                return "output"
            if isinstance(node, ast.JoinedStr):
                return "output"
            if isinstance(node, ast.arguments):
                for df in node.defaults + [x for x in node.kw_defaults if x is not None]:
                    if df.lineno <= line <= df.end_lineno:
                        return "default"
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.lineno <= line <= node.end_lineno:
            return "module constant"
    return "logic"


def decision_survivors():
    d = json.load(open(os.path.join(V2, "results", "e6_mutation_test.json")))
    srcs, out = {}, []
    for s in d["survivors"]:
        f = s["file"]
        if f not in srcs:
            src = open(os.path.join(ROOT, f), encoding="utf-8").read()
            srcs[f] = (ast.parse(src), src.splitlines())
        tree, lines = srcs[f]
        r = role(tree, s["line"])
        base = f.split("/")[-1]
        if r == "module constant" or (r == "logic" and s["line"] in A[base]):
            out.append({"file": f, "line": s["line"], "kind": s["kind"], "change": s["change"],
                        "category": "decision constant" if r == "module constant" else "verdict, test or statistic definition",
                        "text": lines[s["line"] - 1].strip(), "context": [x.rstrip() for x in lines[max(0, s["line"] - 6):s["line"] + 3]]})
    out.sort(key=lambda x: (x["file"], x["line"], x["change"]))
    return out


def cp(k, n, a=0.05):
    lo = 0.0 if k == 0 else stats.beta.ppf(a / 2, k, n - k + 1)
    hi = 1.0 if k == n else stats.beta.ppf(1 - a / 2, k + 1, n - k)
    return [float(lo), float(hi)]


def main():
    mode = sys.argv[1]
    surv = decision_survivors()
    if mode == "draw":
        assert len(surv) == 88, len(surv)
        idx = sorted(np.random.default_rng(0).choice(len(surv), 25, replace=False).tolist())
        sample = [dict(surv[i], id=n) for n, i in enumerate(idx)]
        json.dump({"n_decision_survivors": len(surv), "sample": sample}, open(os.path.join(V2, "results", "e14_sample.json"), "w"), indent=1)
        for s in sample:
            print(s["id"], s["file"].split("/")[-1], s["line"], s["change"], "|", s["text"][:100])
    else:
        lab = json.load(open(os.path.join(V2, "results", "e14_labels.json")))
        labels = {int(k): v["label"] for k, v in lab["labels"].items()}
        assert len(labels) == 25 and set(labels.values()) <= {"equivalent", "non-equivalent", "undecided"}
        n = 25
        eq = sum(v == "equivalent" for v in labels.values())
        und = sum(v == "undecided" for v in labels.values())
        non = n - eq
        lo, hi = cp(non, n)
        out = {"n_decision_survivors": 88, "sample": n, "equivalent": eq, "undecided": und, "non_equivalent_incl_undecided": non,
               "cp95_non_equivalent_share": [lo, hi], "implied_non_equivalent_survivors_of_88": [round(lo * 88, 1), round(non / n * 88, 1), round(hi * 88, 1)],
               "decision_line_mutants": 108, "killed": 20,
               "kill_rate_excluding_estimated_equivalents": [20 / (20 + hi * 88), 20 / (20 + non / n * 88), 20 / (20 + lo * 88)]}
        json.dump(out, open(os.path.join(V2, "results", "e14_equivalence.json"), "w"), indent=1)
        print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
