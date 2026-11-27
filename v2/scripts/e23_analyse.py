"""E23 analysis (PREREG_V2_ADDENDUM_16.md): joins the recorded outcomes with the labels.

    python v2/scripts/e23_analyse.py --outcomes e23_outcomes.json --labels e23_labels.csv   ->  v2/results/e23_summary.json
    python v2/scripts/e23_analyse.py --selftest
"""
import argparse
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import e23_battery as e23

OUTCOMES = ("pass", "fail", "no_verdict", "error")


def summarise(checks, labels, undefined_labels):
    """Counts with the check as the unit. A silent pass is a pass on a cell whose label is in undefined_labels."""
    gated = [c for c in checks if c["gate"]]
    eligible, silent, cells = [], [], []
    for c in gated:
        und = [r for r in c["degenerate"] if labels[f"{c['statistic']}-{r['input']}"] in undefined_labels]
        if und:
            eligible.append(c)
        hits = [r["input"] for r in und if r["outcome"] == "pass"]
        if hits:
            silent.append(c)
            cells += [{"library": c["library"], "check": c["check"], "input": i} for i in hits]
    per_library = {}
    for lib in sorted({c["library"] for c in checks}):
        per_library[lib] = {"checks_attempted": sum(c["library"] == lib for c in checks),
                            "checks_through_gate": sum(c["library"] == lib for c in gated),
                            "checks_with_an_undefined_cell": sum(c["library"] == lib for c in eligible),
                            "checks_with_a_silent_pass": sum(c["library"] == lib for c in silent)}
    return {"checks_attempted": len(checks), "checks_through_gate": len(gated), "checks_with_an_undefined_cell": len(eligible),
            "checks_with_a_silent_pass": len(silent), "libraries_with_an_eligible_check": len({c["library"] for c in eligible}),
            "libraries_with_a_silent_pass": len({c["library"] for c in silent}), "per_library": per_library, "silent_pass_cells": cells}


def outcome_counts(checks, labels):
    table = {lab: collections.Counter() for lab in ("undefined", "defined", "unsure")}
    for c in checks:
        for r in c["degenerate"]:
            table[labels[f"{c['statistic']}-{r['input']}"]][r["outcome"]] += 1
    return {lab: {o: int(n[o]) for o in OUTCOMES} for lab, n in table.items()}


def analyse(checks, labels):
    return {"label_counts": dict(collections.Counter(labels.values())),
            "primary": summarise(checks, labels, {"undefined"}),
            "unsure_counted_as_undefined": summarise(checks, labels, {"undefined", "unsure"}),
            "degenerate_cell_outcomes_by_label": outcome_counts(checks, labels),
            "checks_that_failed_the_gate": [{"library": c["library"], "check": c["check"],
                                             "ordinary": [(r["input"], r["outcome"]) for r in c["ordinary"]]} for c in checks if not c["gate"]]}


def selftest():
    labels = {p: "defined" for p, _, _ in e23.pairs()}
    labels["S01-empty"], labels["S01-all_missing"] = "undefined", "unsure"

    def chk(lib, name, gate, outs):
        return {"library": lib, "check": name, "statistic": "S01", "gate": gate, "ordinary": [],
                "degenerate": [{"input": i, "outcome": o} for i, o in outs.items()] if gate else []}

    checks = [chk("a", "silent", True, {"empty": "pass", "all_missing": "fail", "single_row": "pass"}),
              chk("a", "abstains", True, {"empty": "no_verdict", "all_missing": "pass", "single_row": "pass"}),
              chk("b", "nogate", False, {})]
    r = analyse(checks, labels)
    p, u = r["primary"], r["unsure_counted_as_undefined"]
    assert (p["checks_attempted"], p["checks_through_gate"], p["checks_with_an_undefined_cell"], p["checks_with_a_silent_pass"]) == (3, 2, 2, 1)
    assert (p["libraries_with_a_silent_pass"], u["checks_with_a_silent_pass"]) == (1, 2)
    assert r["degenerate_cell_outcomes_by_label"]["undefined"] == {"pass": 1, "fail": 0, "no_verdict": 1, "error": 0}
    print("selftest passed")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outcomes")
    ap.add_argument("--labels")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(HERE), "results"))
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    labels = e23.read_labels(a.labels)
    data = json.load(open(a.outcomes))
    checks = [c for e in data["libraries"].values() for c in e.get("checks", [])]
    out = analyse(checks, labels)
    out["checks_declared"] = len(e23.CHECKS)
    out["libraries_that_failed_to_run"] = {k: e["library_failed"] for k, e in data["libraries"].items() if "library_failed" in e}
    out["labels_sha256"] = e23.sha256_of(a.labels)
    out["runs"] = data["runs"]
    out["labels_hash_matches_every_run"] = all(r["labels_sha256"] == out["labels_sha256"] for r in data["runs"])
    json.dump(out, open(os.path.join(a.out, "e23_summary.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "runs"}, indent=1))


if __name__ == "__main__":
    main()
