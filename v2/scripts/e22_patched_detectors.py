"""E22 (PREREG_V2_ADDENDUM_13.md): the E17 cells on the patched copies, and equivalence with the originals on random defined inputs.

    python -W ignore v2/scripts/e22_patched_detectors.py   ->  v2/results/e22_patched_detectors.json
"""
import os
import sys
import json
import tempfile
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PATCHED = os.path.join(ROOT, "v2", "patched_detectors")
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
sys.path.insert(0, PATCHED)
import numpy as np
from undecidable import Undecidable
import e17_degenerate_inputs as e17
import detectors.checks as pkg

NAMES = ["check1_label_shift", "check2_pretrain_leakage", "check4_circularity", "check5_missingness_scale"]


def load(path, modname):
    spec = importlib.util.spec_from_file_location(modname, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


originals = {n: load(os.path.join(ROOT, "detectors", "checks", n + ".py"), "orig_" + n) for n in NAMES}
patched = {n: load(os.path.join(PATCHED, n + ".py"), "patched_" + n) for n in NAMES}


def run_cells(modules):
    """The E17 cells, same inputs and seed, with the four detectors taken from `modules`."""
    for n, m in modules.items():
        sys.modules["detectors.checks." + n] = m
        setattr(pkg, n, m)
    rng = np.random.default_rng(e17.SEED)
    tmp = tempfile.mkdtemp(prefix="e22_")
    cells = e17.cells_d1(rng) + e17.cells_d2(rng) + e17.cells_d3(tmp) + e17.cells_d4() + e17.cells_d5(rng)
    rows = []
    for det, name, undefined, fn, classify in cells:
        def wrapped(ret, classify=classify):
            first = ret[0] if isinstance(ret, tuple) else ret
            if isinstance(first, Undecidable):
                return "abstain", repr(first)
            return classify(ret)
        cls, detail, warned = e17.outcome(fn, wrapped)
        rows.append({"detector": det, "input": name, "undefined": bool(undefined), "outcome": cls, "detail": detail})
    return rows


def same(x, y):
    if isinstance(x, dict):
        return x.keys() == y.keys() and all(same(x[k], y[k]) for k in x)
    if isinstance(x, (tuple, list)):
        return len(x) == len(y) and all(same(a, b) for a, b in zip(x, y))
    if isinstance(x, float) and x != x:
        return isinstance(y, float) and y != y
    return bool(x == y)


def equivalence():
    rng = np.random.default_rng(20261202)
    res = {}

    def tally(name, pairs):
        n = und = bad = 0
        for call_orig, call_new in pairs:
            n += 1
            new = call_new()
            if isinstance(new[0], Undecidable):
                und += 1
                continue
            bad += not same(call_orig(), new)
        res[name] = {"inputs": n, "undecidable": und, "disagreements": bad}

    def d1():
        for _ in range(10000):
            size = int(rng.integers(20, 601))
            a = (rng.random(size) < rng.random()).astype(int)
            b = np.where(rng.random(size) < rng.random() * 0.5, 1 - a, a)
            yield (lambda a=a, b=b: originals["check1_label_shift"].diagnose("x", a, b, a, b, verbose=False),
                   lambda a=a, b=b: patched["check1_label_shift"].diagnose("x", a, b, a, b, verbose=False))

    def d2():
        for _ in range(10000):
            v = rng.normal(rng.uniform(-0.1, 0.1), rng.uniform(0, 0.05), int(rng.integers(3, 11)))
            yield (lambda v=v: originals["check2_pretrain_leakage"].flag_from_relative(v),
                   lambda v=v: patched["check2_pretrain_leakage"].flag_from_relative(v))

    def d4():
        for (ds, c) in originals["check4_circularity"].EXPECTED:
            yield (lambda ds=ds, c=c: originals["check4_circularity"].is_circular(ds, c),
                   lambda ds=ds, c=c: patched["check4_circularity"].is_circular(ds, c))

    def d5():
        keys = ("MAP", "HH", "SpO2")
        for _ in range(2000):
            def group():
                p = rng.random(3)
                return [{k: float(abs(rng.normal(0.05, 0.02))) for k, q in zip(keys, p) if rng.random() < q} for _ in range(int(rng.integers(1, 51)))]
            A, B = group(), group()
            yield (lambda A=A, B=B: originals["check5_missingness_scale"].run_check_on_stays("A", A, "B", B, verbose=False),
                   lambda A=A, B=B: patched["check5_missingness_scale"].run_check_on_stays("A", A, "B", B, verbose=False))

    for name, gen in [("detector 1", d1), ("detector 2", d2), ("detector 4", d4), ("detector 5", d5)]:
        tally(name, gen())
    return res


def main():
    before = run_cells(originals)
    after = run_cells(patched)
    assert [(r["detector"], r["input"]) for r in before] == [(r["detector"], r["input"]) for r in after]
    summary = {}
    for b, c in zip(before, after):
        d = summary.setdefault(b["detector"], {"undefined": 0, "silent_before": 0, "silent_after": 0, "after_error": 0, "after_abstain": 0,
                                               "after_flag_on_undefined": 0, "defined": 0, "defined_outcome_changed": 0})
        if b["undefined"]:
            d["undefined"] += 1
            d["silent_before"] += b["outcome"] == "clean"
            d["silent_after"] += c["outcome"] == "clean"
            d["after_error"] += c["outcome"] == "error"
            d["after_abstain"] += c["outcome"] == "abstain"
            d["after_flag_on_undefined"] += c["outcome"] == "flag"
        else:
            d["defined"] += 1
            d["defined_outcome_changed"] += b["outcome"] != c["outcome"]
    zeros = np.zeros(5)
    control = {"original": bool(originals["check2_pretrain_leakage"].flag_from_relative(zeros)[0]),
               "patched": repr(patched["check2_pretrain_leakage"].flag_from_relative(zeros)[0])}
    out = {"summary": summary, "equivalence": equivalence(), "detector2_zero_percent_control": control,
           "cells_after": after}
    json.dump(out, open(os.path.join(ROOT, "v2", "results", "e22_patched_detectors.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "cells_after"}, indent=1))
    changed = [(c["detector"], c["input"], b["outcome"], c["outcome"]) for b, c in zip(before, after) if b["outcome"] != c["outcome"]]
    print("changed cells:", len(changed))
    for x in changed:
        print("  ", x)


if __name__ == "__main__":
    main()
