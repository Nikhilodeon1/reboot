"""E1 runner, executed inside the container with the network disabled.

    python /scripts/e1_run.py --out /out

Each (tool, check, input) cell is run once; the outcome is assigned from the return value, any exception and any warning.
Outcomes: PASS, FAIL (verdict tools); VALUE, NAN (value tools); ERROR; WARN is a flag added when a warning was emitted.
A cell is a vacuous-pass candidate when the a priori mapping says the statistic is undefined on that input, the outcome is PASS or
VALUE, and no warning was emitted. Documented or undocumented status is recorded by a person afterwards and is not in this file.
"""
import os
import sys
import json
import math
import argparse
import warnings
import importlib.metadata as md

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import e1_checks as C


def run_cell(fn, df):
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        try:
            r = fn(df.copy())
            err = None
        except BaseException as e:
            r, err = None, f"{type(e).__name__}: {str(e)[:160]}"
    warned = [f"{x.category.__name__}: {str(x.message)[:120]}" for x in w]
    return r, err, warned


def classify(kind, r, err):
    if err is not None:
        return "ERROR"
    if kind == "verdict":
        return "PASS" if r else "FAIL"
    if r is None or (isinstance(r, float) and math.isnan(r)):
        return "NAN"
    return "VALUE"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    ins = C.inputs()
    versions = {}
    for p in ("great-expectations", "pandera", "fairlearn", "aif360", "scikit-learn", "numpy", "pandas"):
        try:
            versions[p] = md.version(p)
        except Exception:
            versions[p] = "not installed"
    cells = []
    for tool, name, kind, fn, undef in C.CHECKS:
        for iname, df in ins.items():
            r, err, warned = run_cell(fn, df)
            out = classify(kind, r, err)
            undefined = iname in undef
            cand = undefined and out in ("PASS", "VALUE") and not warned
            cells.append({"tool": tool, "check": name, "input": iname, "outcome": out, "value": None if r is None else (r if not isinstance(r, float) or math.isfinite(r) else str(r)),
                          "error": err, "warnings": warned, "undefined_a_priori": undefined, "vacuous_candidate": cand})
    summary = {}
    for tool in sorted({c["tool"] for c in cells}):
        tc = [c for c in cells if c["tool"] == tool and c["input"] != "D0_nominal"]
        und = [c for c in tc if c["undefined_a_priori"]]
        summary[tool] = {"cells": len(tc), "undefined_cells": len(und),
                         "outcomes_on_undefined": {o: sum(c["outcome"] == o for c in und) for o in ("PASS", "FAIL", "VALUE", "NAN", "ERROR")},
                         "vacuous_candidates": sum(c["vacuous_candidate"] for c in und),
                         "nominal_ok": all(c["outcome"] in ("PASS", "VALUE") for c in cells if c["tool"] == tool and c["input"] == "D0_nominal")}
    os.makedirs(a.out, exist_ok=True)
    json.dump({"versions": versions, "python": sys.version.split()[0], "cells": cells, "summary": summary}, open(os.path.join(a.out, "e1_fuzz.json"), "w"), indent=1)
    print(json.dumps(summary, indent=1))
    print(versions)


if __name__ == "__main__":
    main()
