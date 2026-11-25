"""E17 (PREREG_V2_ADDENDUM_9.md): executed degenerate-input test of the five detectors.

Each cell is a (detector, input) pair. `undefined` says whether the statistic the detector computes is undefined for that input;
it was fixed in the addendum before this file ran. The detectors are imported read-only and no detector file is edited.
Inputs are small synthetic objects, no credentialed data is read.

    python v2/scripts/e17_degenerate_inputs.py   ->  v2/results/e17_degenerate_inputs.json
"""
import os
import sys
import json
import tempfile
import warnings

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
import numpy as np

SEED = 20261126


def outcome(fn, classify):
    """Run fn, return (class, detail, warned)."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        try:
            ret = fn()
        except BaseException as e:  # a detector that raises is an 'error' outcome
            return "error", f"{type(e).__name__}: {str(e)[:90]}", bool(w)
        cls, detail = classify(ret)
        return cls, detail, bool(w)


def cells_d1(rng):
    from detectors.checks import check1_label_shift as c1

    def mk(n, k):
        a = rng.integers(0, 2, n)
        b = a.copy()
        idx = rng.choice(n, k, replace=False)
        b[idx] = 1 - b[idx]
        return a, b

    def call(a1, a2, s1=None, s2=None):
        s1 = a1 if s1 is None else s1
        s2 = a2 if s2 is None else s2
        return lambda: c1.diagnose("cell", s1, s2, a1, a2, verbose=False)

    def classify(ret):
        flagged, k, ratio = ret
        return ("flag" if flagged else "clean"), f"kappa={k}, ratio={ratio}"

    a, b = mk(100, 5)
    a2, b2 = mk(100, 40)
    ones, zeros = np.ones(100, int), np.zeros(100, int)
    nanarr = np.array([1.0, 0.0, np.nan, 1.0] * 25)
    cells = [
        ("nominal_agreement", False, call(a, b)),
        ("nominal_disagreement", False, call(a2, b2)),
        ("empty_audits", True, call(np.array([], int), np.array([], int))),
        ("one_row_equal", True, call(np.array([1]), np.array([1]))),
        ("one_row_different", False, call(np.array([1]), np.array([0]))),
        ("constant_equal_ones", True, call(ones, ones.copy())),
        ("constant_equal_zeros", True, call(zeros, zeros.copy())),
        ("nan_in_audit", True, call(nanarr, nanarr.copy())),
        ("unequal_length", True, call(a, b[:50])),
    ]
    return [("detector 1 (diagnose)", n, u, f, classify) for n, u, f in cells]


def cells_d2(rng):
    from detectors.checks import check2_pretrain_leakage as c2

    def call(v):
        return lambda: c2.flag_from_relative(np.asarray(v, float))

    def classify(ret):
        flagged, t, crit = ret
        return ("flag" if flagged else "clean"), f"t={t}, crit={crit}"

    cells = [
        ("nominal_flag", False, call([-0.050, -0.042, -0.061, -0.047, -0.055])),
        ("nominal_null", False, call([0.010, -0.010, 0.020, -0.020, 0.000])),
        ("wrong_sign_effect", False, call([0.050, 0.042, 0.061, 0.047, 0.055])),
        ("empty", True, call([])),
        ("one_value", True, call([-0.05])),
        ("two_values", True, call([-0.05, -0.06])),
        ("identical_negative", True, call([-0.05] * 5)),
        ("all_zero", True, call([0.0] * 5)),
        ("nan_entry", True, call([-0.05, -0.04, np.nan, -0.05, -0.06])),
        ("infinite_entry", True, call([-np.inf, -0.04, -0.05, -0.05, -0.06])),
    ]
    return [("detector 2 (flag_from_relative)", n, u, f, classify) for n, u, f in cells]


def cells_d3(tmp):
    from detectors.checks import check3_selection_audit as c3

    def write(name, data, mode="w"):
        p = os.path.join(tmp, name)
        with open(p, mode) as f:
            f.write(data)
        return p

    unknown_loader = (
        "def lambda_sweep(model, data):\n"
        "    for lam in [0.1, 1.0]:\n"
        "        m = train_model(lam)\n"
        "        evaluate_model(m, my_loader)\n"
    )
    paths = {
        "nominal_buggy_fixture": os.path.join(ROOT, "detectors", "fixtures", "sweep_BUGGY.py"),
        "nominal_fixed_fixture": os.path.join(ROOT, "detectors", "fixtures", "sweep_FIXED.py"),
        "empty_file": write("empty.py", ""),
        "no_function": write("nofn.py", "x = 1\n"),
        "syntax_error": write("syn.py", "def f(:\n"),
        "null_byte": write("nul.py", b"def f():\n    pass\x00\n", "wb"),
        "invalid_utf8": write("bad.py", b"\xff\xfe\x00", "wb"),
        "unknown_loader_sweep": write("unk.py", unknown_loader),
    }
    undefined = {"nominal_buggy_fixture": False, "nominal_fixed_fixture": False}

    def classify(ret):
        v = ret
        return {"CONTAMINATED": "flag", "OK": "clean", "INDETERMINATE": "abstain"}.get(v, "clean"), f"verdict={v}"

    out = []
    for n, p in paths.items():
        out.append(("detector 3 (audit_file)", n, undefined.get(n, True),
                    (lambda p=p: c3.verdict_for_file(c3.audit_file(p))), classify))
    return out


def cells_d4():
    from detectors.checks import check4_circularity as c4

    def classify(ret):
        circ, why = ret
        return ("flag" if circ else "clean"), f"reason={why!r}"

    def call(ds, cons, **kw):
        return lambda: c4.is_circular(ds, cons, **kw)

    cells = [
        ("nominal_circular", False, call("PhysioNet", "Severinghaus")),
        ("nominal_not_circular", False, call("MIMIC-IV", "MAP")),
        ("unknown_dataset", True, call("UnknownDB", "Severinghaus")),
        ("unknown_constraint", True, call("PhysioNet", "NoSuchConstraint")),
        ("empty_lineage", True, call("PhysioNet", "Severinghaus", lineage={})),
        ("empty_dataset_name", True, call("", "MAP")),
    ]
    return [("detector 4 (is_circular)", n, u, f, classify) for n, u, f in cells]


def cells_d5(rng):
    from detectors.checks import check5_missingness_scale as c5

    def stay(keys):
        return {k: float(abs(rng.normal(0.05, 0.01))) for k in keys}

    full = ("MAP", "HH", "SpO2")
    A = [stay(full) for _ in range(200)]
    B_same = [stay(full) for _ in range(200)]
    B_lacking = [stay(("SpO2",)) for _ in range(200)]
    nan_stays = [{k: float("nan") for k in full} for _ in range(20)]

    def call(a, b):
        return lambda: c5.run_check_on_stays("A", a, "B", b, verbose=False)

    def classify(ret):
        flagged, stats = ret
        return ("flag" if flagged else "clean"), json.dumps({k: (None if v != v else v) for k, v in stats.items()}, default=str)

    cells = [
        ("nominal_identical_groups", False, call(A, B_same)),
        ("nominal_group_lacks_components", False, call(A, B_lacking)),
        ("both_groups_empty", True, call([], [])),
        ("one_group_empty", True, call([], B_same)),
        ("stays_without_components", True, call([{}, {}], [{}, {}])),
        ("all_nan_components", True, call(nan_stays, nan_stays)),
        ("one_stay_per_group", False, call(A[:1], B_same[:1])),
    ]
    return [("detector 5 (run_check_on_stays)", n, u, f, classify) for n, u, f in cells]


def main():
    rng = np.random.default_rng(SEED)
    tmp = tempfile.mkdtemp(prefix="e17_")
    all_cells = cells_d1(rng) + cells_d2(rng) + cells_d3(tmp) + cells_d4() + cells_d5(rng)
    rows = []
    for det, name, undefined, fn, classify in all_cells:
        cls, detail, warned = outcome(fn, classify)
        rows.append({"detector": det, "input": name, "undefined": bool(undefined), "outcome": cls, "detail": detail, "warned": warned,
                     "silent_pass": bool(undefined and cls == "clean")})
    summary = {}
    for r in rows:
        d = summary.setdefault(r["detector"], {"cells": 0, "undefined_cells": 0, "silent_pass": 0, "error": 0, "abstain": 0, "flag_on_undefined": 0,
                                               "defined_cells": 0, "defined_cells_as_expected_sanity": None})
        d["cells"] += 1
        if r["undefined"]:
            d["undefined_cells"] += 1
            d["silent_pass"] += r["silent_pass"]
            d["error"] += r["outcome"] == "error"
            d["abstain"] += r["outcome"] == "abstain"
            d["flag_on_undefined"] += r["outcome"] == "flag"
        else:
            d["defined_cells"] += 1
    out = {"seed": SEED, "cells": rows, "summary": summary}
    path = os.path.join(ROOT, "v2", "results", "e17_degenerate_inputs.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=1)
    for r in rows:
        print(f"{r['detector'][:30]:<31}{r['input']:<34}undef={int(r['undefined'])} -> {r['outcome']:<8} warn={int(r['warned'])}  {r['detail'][:80]}")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
