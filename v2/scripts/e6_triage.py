"""EXPLORATORY (not registered): triage of the 256 surviving mutants of E6 by the role of the mutated line.

Roles are assigned by syntax: 'output' (inside a print call or an f-string), 'default' (a default argument), 'module constant' (a
top-level assignment), 'logic' (everything else, read by hand and sub-labelled in the printed listing). Reads the shipped sources and
v2/results/e6_mutation_test.json; nothing is executed.

    python v2/scripts/e6_triage.py [--list logic]
"""
import os
import ast
import sys
import json
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.dirname(HERE)
ROOT = os.path.dirname(V2)
d = json.load(open(os.path.join(V2, "results", "e6_mutation_test.json")))


def role(tree, line):
    best = None
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


by = collections.Counter()
rows = []
trees = {}
for s in d["survivors"]:
    f = s["file"]
    if f not in trees:
        src = open(os.path.join(ROOT, f), encoding="utf-8").read()
        trees[f] = (ast.parse(src), src.splitlines())
    tree, lines = trees[f]
    r = role(tree, s["line"])
    by[(f.split("/")[-1], r)] += 1
    rows.append((f.split("/")[-1], s["line"], s["change"], r, lines[s["line"] - 1].strip()[:110]))
print({f"{k[0]}:{k[1]}": v for k, v in sorted(by.items())})
if "--list" in sys.argv:
    want = sys.argv[sys.argv.index("--list") + 1]
    for r in sorted(rows):
        if r[3] == want:
            print(f"{r[0][:8]} {r[1]:4d} {r[2]:>14s} | {r[4]}")


# Hand classification of the 'logic' lines (read in the printed listing). A = verdict, test, statistic definition; B = data
# splitting, aggregation and training plumbing; D = defaults, entry points, paths, harness printing. Module constants are all
# thresholds, critical values or dose levels, so they count as decision constants.
A = {"check1_label_shift.py": {27, 32, 41}, "check2_pretrain_leakage.py": set(range(107, 113)) | {139, 141, 145, 211, 220}}
B = {"check1_label_shift.py": {38, 85, 90, 92, 95, 109, 111, 136},
     "check2_pretrain_leakage.py": {38, 39, 40, 44, 55, 59, 63, 64, 65, 75, 76, 119, 121, 135, 196}}
cat = collections.Counter()
for f, line, change, r, text in rows:
    if r == "module constant":
        cat["decision constant (threshold, critical value, dose level)"] += 1
    elif r == "output":
        cat["output formatting"] += 1
    elif line in A[f]:
        cat["verdict, test or statistic definition"] += 1
    elif line in B[f]:
        cat["data splitting, aggregation or training plumbing"] += 1
    else:
        cat["defaults, entry points, paths, harness"] += 1
print(dict(cat), "total", sum(cat.values()))
json.dump({"by_role": {f"{k[0]}:{k[1]}": v for k, v in sorted(by.items())}, "by_category": dict(cat), "total": sum(cat.values()),
           "note": "exploratory; categories assigned by the authors after reading each listed line; no mutant was judged equivalent"},
          open(os.path.join(V2, "results", "e6_triage.json"), "w"), indent=1)


# Kill rate by category: regenerate the mutant sites (no tests run) and subtract the survivors.
import importlib.util
spec = importlib.util.spec_from_file_location("e6m", os.path.join(HERE, "e6_mutation_test.py"))
e6m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e6m)


def category(f, line, tree):
    r = role(tree, line)
    if r == "module constant":
        return "decision constant"
    if r == "output":
        return "output formatting"
    if line in A[f]:
        return "verdict, test or statistic definition"
    if line in B[f]:
        return "plumbing"
    return "defaults, entry points, harness"


tot, surv = collections.Counter(), collections.Counter()
for f in ("detectors/checks/check1_label_shift.py", "detectors/checks/check2_pretrain_leakage.py"):
    src = open(os.path.join(ROOT, f), encoding="utf-8").read()
    tree = ast.parse(src)
    for kind, idx, line, desc in e6m.sites(tree):
        try:                                   # the same filter as e6_mutation_test.main: only mutants that were run
            m = e6m.mutate(src, kind, idx)
            ast.parse(m)
        except Exception:
            continue
        if m == ast.unparse(ast.parse(src)):
            continue
        tot[category(f.split("/")[-1], line, tree)] += 1
for f, line, change, r, text in rows:
    tree = trees[[k for k in trees if k.endswith(f)][0]][0]
    surv[category(f, line, tree)] += 1
kr = {c: {"mutants": tot[c], "killed": tot[c] - surv[c], "survived": surv[c]} for c in tot}
print(kr)
json.dump({"by_category": dict(cat), "kill_rate_by_category": kr, "total": sum(cat.values())},
          open(os.path.join(V2, "results", "e6_triage.json"), "w"), indent=1)
