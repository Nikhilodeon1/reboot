"""E23 (PREREG_V2_ADDENDUM_16.md): degenerate inputs to verdict-emitting checks of libraries not read in this project. RUN IN COLAB.

    python e23_battery.py --labels e23_labels.csv --out OUTDIR [--only lib,lib]

The harness was written from the libraries' documentation only. For every check, the two ordinary cells (one that should pass, one that
should fail) run first; the degenerate cells of that check run only if both give the expected verdict. The label file must be complete
before anything runs: its hash goes into the output. The harness never uses the labels to decide what to run.

    python e23_battery.py --make-sheet e23_label_sheet.csv     writes the blank label sheet
    python e23_battery.py --selftest                           checks the harness itself with stand-in checks; no library is imported
"""
import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import traceback
import warnings

PYTHON = "3.11"
PINS = {
    "pointblank": ["pointblank==1.3.0", "polars"],
    "patito": ["patito==0.8.6", "polars"],
    "dataframely": ["dataframely==3.1.3", "polars"],
    "cuallee": ["cuallee==0.15.4", "pandas<3"],
    "frictionless": ["frictionless==5.21.0"],
    "whylogs": ["whylogs==1.6.4", "pandas<3", "numpy<2"],
    "datacompy": ["datacompy==1.2.0", "pandas<3"],
    "nannyml": ["nannyml==0.13.1"],
}

# ---------------------------------------------------------------- what is labeled

STATISTICS = {
    "S01": "Passes if every value in the column satisfies a stated condition (for example: lies between 1 and 5, is one of an allowed set, or is not a forbidden value).",
    "S02": "Passes if no value in the column is missing.",
    "S03": "Passes if no value in the column occurs more than once.",
    "S04": "Compares the mean of the column with a stated number (equal within a tolerance, or at least that number).",
    "S05": "Compares the sum of the column with a stated number.",
    "S06": "Passes if the number of missing values in the column is below a stated number.",
    "S07": "Compares the fraction of the column's values that are missing with a stated fraction, within a tolerance.",
    "S08": "Compares the number of rows in the table with a stated number.",
    "S09": "Passes if no value lies more than 3 standard deviations from the column mean.",
    "S10": "Passes if the values of an integer column are consecutive (each is one more than the one before).",
    "S11": "Passes if every group (rows that share a value of the column) has at least 2 rows.",
    "D1": "Two-sample Kolmogorov-Smirnov: the largest distance between the cumulative distributions of a numeric column in a reference sample and a new sample. Alerts if it is too large.",
    "D2": "Jensen-Shannon distance between the distribution of a column in a reference sample and in a new sample. Alerts if it is too large.",
    "D3": "Chi-squared test on the table of category counts of the reference sample and the new sample. Alerts on a significant difference.",
    "D4": "L-infinity distance: the largest absolute difference, over categories, between a category's relative frequency in the reference sample and in the new sample. Alerts if it is too large.",
    "C1": "Two tables are matched row by row on an id column. Passes if the compared value column is equal on the matched rows.",
}

SINGLE_TABLE_INPUTS = {
    "empty": "The table has the column but zero rows.",
    "all_missing": "20 rows; every value of the checked column is missing.",
    "single_row": "One row, holding an ordinary non-missing value.",
}
DRIFT_INPUTS = {
    "analysis_empty": "Reference sample: 1,000 ordinary values. New sample: zero rows.",
    "analysis_all_missing": "Reference sample: 1,000 ordinary values. New sample: 1,000 rows, every value missing.",
    "constant_identical": "Reference and new sample: 1,000 rows each, and every value in both is the same single value.",
    "analysis_single_row": "Reference sample: 1,000 ordinary values. New sample: one row with an ordinary value.",
}
COMPARE_INPUTS = {
    "both_empty": "Both tables have zero rows.",
    "one_empty": "One table has 20 rows and the other has zero rows.",
    "no_common_keys": "Both tables have 20 rows, and no id appears in both.",
    "values_all_missing": "Both tables have the same 20 ids, and the value column is entirely missing in both.",
}


def inputs_for(stat):
    return DRIFT_INPUTS if stat.startswith("D") else COMPARE_INPUTS if stat.startswith("C") else SINGLE_TABLE_INPUTS


def pairs():
    return [(f"{s}-{i}", s, i) for s in STATISTICS for i in inputs_for(s)]


# ---------------------------------------------------------------- the checks and their ordinary data

PASS_NUM = [1.0, 2.0, 3.0, 4.0, 5.0] * 4
COUNTING = [float(i) for i in range(1, 21)]


def column(name, dtype, ok, bad):
    return {"name": name, "dtype": dtype, "pass": ok, "fail": bad}


NUM_RANGE = column("x", "float", PASS_NUM, PASS_NUM[:-1] + [10.0])
DUPLICATE = column("x", "float", COUNTING, COUNTING[:-1] + [1.0])
ROWS = column("x", "float", PASS_NUM, PASS_NUM[:10])

CHECKS = [
    ("pointblank", "col_vals_between", "S01", NUM_RANGE),
    ("pointblank", "col_vals_not_null", "S02", column("x", "float", PASS_NUM, PASS_NUM[:-1] + [None])),
    ("pointblank", "col_pct_null", "S07", column("x", "float", PASS_NUM, [None] * 10 + [3.0] * 10)),
    ("pointblank", "col_avg_eq", "S04", column("x", "float", PASS_NUM, [10.0] * 20)),
    ("pointblank", "col_avg_ge", "S04", column("x", "float", PASS_NUM, [1.0] * 20)),
    ("pointblank", "col_sum_eq", "S05", column("x", "float", PASS_NUM, [10.0] * 20)),
    ("pointblank", "rows_distinct", "S03", DUPLICATE),
    ("pointblank", "row_count_match", "S08", ROWS),
    ("patito", "unique", "S03", DUPLICATE),
    ("patito", "literal", "S01", column("s", "str", ["a", "b"] * 10, ["a", "b"] * 9 + ["a", "z"])),
    ("patito", "bounds", "S01", NUM_RANGE),
    ("patito", "constraint_expression", "S01", column("n", "int", [2, 4, 6, 8] * 5, [2, 4, 6, 8] * 4 + [2, 4, 6, 7])),
    ("dataframely", "nullable_false", "S02", column("x", "float", PASS_NUM, PASS_NUM[:-1] + [None])),
    ("dataframely", "row_rule", "S01", NUM_RANGE),
    ("dataframely", "group_rule", "S11", column("g", "str", ["a"] * 10 + ["b"] * 10, ["a"] * 19 + ["b"])),
    ("cuallee", "is_complete", "S02", column("x", "float", PASS_NUM, PASS_NUM[:-1] + [None])),
    ("cuallee", "is_unique", "S03", DUPLICATE),
    ("cuallee", "has_mean", "S04", column("x", "float", PASS_NUM, [10.0] * 20)),
    ("cuallee", "is_between", "S01", NUM_RANGE),
    ("cuallee", "is_contained_in", "S01", NUM_RANGE),
    ("frictionless", "table_dimensions", "S08", ROWS),
    ("frictionless", "row_constraint", "S01", NUM_RANGE),
    ("frictionless", "duplicate_row", "S03", DUPLICATE),
    ("frictionless", "forbidden_value", "S01", NUM_RANGE),
    ("frictionless", "sequential_value", "S10", column("x", "int", list(range(1, 21)), list(range(1, 20)) + [30])),
    ("frictionless", "deviated_value", "S09", column("x", "float", PASS_NUM, [3.0] * 19 + [1000.0])),
    ("whylogs", "greater_than_number", "S01", column("x", "float", PASS_NUM, PASS_NUM[:-1] + [-1.0])),
    ("whylogs", "null_values_below_number", "S06", column("x", "float", PASS_NUM, [None] * 6 + [3.0] * 14)),
    ("datacompy", "has_mismatches", "C1", None),
    ("nannyml", "kolmogorov_smirnov_continuous", "D1", {"method": "kolmogorov_smirnov", "categorical": False}),
    ("nannyml", "jensen_shannon_continuous", "D2", {"method": "jensen_shannon", "categorical": False}),
    ("nannyml", "chi2_categorical", "D3", {"method": "chi2", "categorical": True}),
    ("nannyml", "jensen_shannon_categorical", "D2", {"method": "jensen_shannon", "categorical": True}),
    ("nannyml", "l_infinity_categorical", "D4", {"method": "l_infinity", "categorical": True}),
]


def drift_samples(categorical, which):
    """(reference values, new values) for one cell of a drift check."""
    import random
    rng = random.Random(7)
    if categorical:
        ref = rng.choices(["a", "b", "c"], weights=[0.5, 0.3, 0.2], k=1000)
        shifted = rng.choices(["a", "b", "c"], weights=[0.05, 0.05, 0.9], k=1000)
        constant = "a"
    else:
        ref = [rng.gauss(0.0, 1.0) for _ in range(1000)]
        shifted = [rng.gauss(3.0, 1.0) for _ in range(1000)]
        constant = 1.0
    if which == "constant_identical":
        return [constant] * 1000, [constant] * 1000
    new = {"pass": list(ref), "fail": shifted, "analysis_empty": [], "analysis_all_missing": [None] * 1000,
           "analysis_single_row": ref[:1]}[which]
    return ref, new


def compare_tables(which):
    """(left, right) for one cell of the table comparison, each a dict of column name to (dtype, values)."""
    ids = list(range(1, 21))
    vals = [float(10 * i) for i in ids]

    def table(i, v):
        return {"id": ("int", i), "val": ("float", v)}

    full = table(ids, vals)
    return {
        "pass": (full, table(ids, vals)),
        "fail": (full, table(ids, vals[:-1] + [999.0])),
        "both_empty": (table([], []), table([], [])),
        "one_empty": (full, table([], [])),
        "no_common_keys": (full, table([i + 100 for i in ids], vals)),
        "values_all_missing": (table(ids, [None] * 20), table(ids, [None] * 20)),
    }[which]


def cell_data(stat, spec, which):
    if stat.startswith("D"):
        return drift_samples(spec["categorical"], which)
    if stat.startswith("C"):
        return compare_tables(which)
    if which in ("pass", "fail"):
        values = spec[which]
    else:
        values = {"empty": [], "all_missing": [None] * 20, "single_row": spec["pass"][:1]}[which]
    return {spec["name"]: (spec["dtype"], list(values))}


# ---------------------------------------------------------------- conversions

def to_pandas(table):
    import pandas as pd
    cols = {}
    for name, (dtype, values) in table.items():
        if dtype == "str":
            cols[name] = pd.Series(values, dtype="object")
        elif dtype == "int" and not any(v is None for v in values):
            cols[name] = pd.Series(values, dtype="int64")
        else:
            cols[name] = pd.Series(values, dtype="float64")
    return pd.DataFrame(cols)


def to_polars(table):
    import polars as pl
    types = {"float": pl.Float64, "int": pl.Int64, "str": pl.String}
    return pl.DataFrame([pl.Series(name, values, dtype=types[dtype]) for name, (dtype, values) in table.items()])


def to_rows(table):
    """List of lists with a header, plus a constant companion column so that a row with a missing value is not a blank row."""
    names = list(table) + ["tag"]
    n = len(next(iter(table.values()))[1])
    return [names] + [[table[c][1][i] for c in table] + ["t"] for i in range(n)]


# ---------------------------------------------------------------- adapters: True = passes, False = fails, None = no verdict

def run_pointblank(check, spec, data):
    import pointblank as pb
    args = {
        "col_vals_between": dict(columns="x", left=1, right=5),
        "col_vals_not_null": dict(columns="x"),
        "col_pct_null": dict(columns="x", p=0.0, tol=0.05),
        "col_avg_eq": dict(columns="x", value=3, tol=0.5),
        "col_avg_ge": dict(columns="x", value=2),
        "col_sum_eq": dict(columns="x", value=60),
        "rows_distinct": dict(columns_subset="x"),
        "row_count_match": dict(count=20),
    }[check]
    v = pb.Validate(data=to_polars(data))
    return getattr(v, check)(**args).interrogate().all_passed(), ""


def run_patito(check, spec, data):
    from typing import Literal
    import patito as pt
    import polars as pl
    if check == "unique":
        class Model(pt.Model):
            x: float = pt.Field(unique=True)
    elif check == "literal":
        class Model(pt.Model):
            s: Literal["a", "b"]
    elif check == "bounds":
        class Model(pt.Model):
            x: float = pt.Field(ge=1, le=5)
    else:
        class Model(pt.Model):
            n: int = pt.Field(constraints=pl.col("n") % 2 == 0)
    try:
        Model.validate(to_polars(data))
    except pt.exceptions.DataFrameValidationError as exc:
        return False, str(exc)[:300]
    return True, ""


def run_dataframely(check, spec, data):
    import dataframely as dy
    import polars as pl
    if check == "nullable_false":
        class Schema(dy.Schema):
            x = dy.Float64(nullable=False)
    elif check == "row_rule":
        class Schema(dy.Schema):
            x = dy.Float64()

            @dy.rule()
            def in_range(cls) -> pl.Expr:
                return (pl.col("x") >= 1) & (pl.col("x") <= 5)
    else:
        class Schema(dy.Schema):
            g = dy.String()

            @dy.rule()
            def group_size(cls) -> pl.Expr:
                return (pl.len() >= 2).over("g")
    try:
        Schema.validate(to_polars(data), cast=True)
    except Exception as exc:
        if "ValidationError" in type(exc).__name__:
            return False, f"{type(exc).__name__}: {exc}"[:300]
        raise
    return True, ""


def run_cuallee(check, spec, data):
    from cuallee import Check
    c = Check()
    if check == "is_complete":
        c.is_complete("x")
    elif check == "is_unique":
        c.is_unique("x")
    elif check == "has_mean":
        c.has_mean("x", 3.0)
    elif check == "is_between":
        c.is_between("x", (1, 5))
    else:
        c.is_contained_in("x", (1.0, 2.0, 3.0, 4.0, 5.0))
    return c.ok(to_pandas(data)), ""


def run_frictionless(check, spec, data):
    from frictionless import checks, validate
    made = {
        "table_dimensions": lambda: checks.table_dimensions(num_rows=20),
        "row_constraint": lambda: checks.row_constraint(formula="x <= 5"),
        "duplicate_row": lambda: checks.duplicate_row(),
        "forbidden_value": lambda: checks.forbidden_value(field_name="x", values=[10]),
        "sequential_value": lambda: checks.sequential_value(field_name="x"),
        "deviated_value": lambda: checks.deviated_value(field_name="x"),
    }[check]()
    report = validate(to_rows(data), checks=[made])
    try:
        seen = sorted({e.type for t in report.tasks for e in t.errors})
        notes = [str(e)[:120] for e in getattr(report, "errors", [])][:2]
        detail = f"error types {seen} {notes}"
    except Exception as exc:  # detail only; the verdict is report.valid
        detail = f"no detail ({type(exc).__name__})"
    return report.valid, detail


def run_whylogs(check, spec, data):
    import whylogs as why
    from whylogs.core.constraints import ConstraintsBuilder
    from whylogs.core.constraints.factories import greater_than_number, null_values_below_number
    view = why.log(to_pandas(data)).view()
    builder = ConstraintsBuilder(dataset_profile_view=view)
    if check == "greater_than_number":
        builder.add_constraint(greater_than_number(column_name="x", number=0))
    else:
        builder.add_constraint(null_values_below_number(column_name="x", number=5))
    built = builder.build()
    verdict = built.validate()
    try:
        detail = str(built.generate_constraints_report())[:300]
    except Exception as exc:  # detail only
        detail = f"no detail ({type(exc).__name__})"
    return verdict, detail


def run_datacompy(check, spec, data):
    from datacompy import PandasCompare
    left, right = (to_pandas(t) for t in data)
    report = PandasCompare(left, right, join_columns="id").build_report_data()
    mismatched = report.mismatch_stats.has_mismatches
    detail = f"rows: {report.row_summary}"[:300]
    return (None if mismatched is None else not mismatched), detail


def run_nannyml(check, spec, data):
    import nannyml as nml
    import pandas as pd
    dtype = "object" if spec["categorical"] else "float64"
    ref, new = (pd.DataFrame({"x": pd.Series(v, dtype=dtype)}) for v in data)
    kwargs = dict(column_names=["x"])
    if spec["categorical"]:
        kwargs.update(treat_as_categorical=["x"], categorical_methods=[spec["method"]], continuous_methods=["jensen_shannon"])
    else:
        kwargs.update(continuous_methods=[spec["method"]], categorical_methods=["chi2"])
    calc = nml.UnivariateDriftCalculator(**kwargs)
    calc.fit(ref)
    frame = calc.calculate(new).filter(period="analysis", column_names=["x"]).to_df(multilevel=False)
    alert_cols = [c for c in frame.columns if c.endswith("_alert") and spec["method"] in c]
    if len(alert_cols) != 1:
        raise RuntimeError(f"expected one alert column, found {alert_cols} among {list(frame.columns)}")
    alerts = frame[alert_cols[0]].tolist()
    value_cols = [c for c in frame.columns if c.endswith("_value") and spec["method"] in c]
    values = frame[value_cols[0]].tolist() if value_cols else []
    detail = f"chunks={len(alerts)} alerts={alerts[:10]} values={[None if pd.isna(v) else round(float(v), 4) for v in values[:10]]}"
    if not alerts:
        return None, detail
    if any((not pd.isna(a)) and bool(a) for a in alerts):
        return False, detail  # any alert on any analysis chunk is a failed check
    if any(pd.isna(a) for a in alerts):
        return None, detail
    return True, detail


ADAPTERS = {"pointblank": run_pointblank, "patito": run_patito, "dataframely": run_dataframely, "cuallee": run_cuallee,
            "frictionless": run_frictionless, "whylogs": run_whylogs, "datacompy": run_datacompy, "nannyml": run_nannyml}


# ---------------------------------------------------------------- running

def classify(verdict):
    if verdict is None:
        return "no_verdict"
    if isinstance(verdict, float) and verdict != verdict:
        return "no_verdict"
    if verdict in (True, False):  # also covers numpy booleans
        return "pass" if verdict else "fail"
    return "no_verdict"


def run_cell(adapter, check, stat, spec, which):
    row = {"input": which, "outcome": None, "detail": "", "warnings": 0}
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            verdict, detail = adapter(check, spec, cell_data(stat, spec, which))
            row["outcome"], row["detail"] = classify(verdict), detail
            if row["outcome"] == "no_verdict":
                row["detail"] = f"returned {verdict!r}; {detail}"[:400]
        except KeyboardInterrupt:
            raise
        except BaseException as exc:  # some libraries raise outside the Exception tree
            row["outcome"] = "error"
            row["detail"] = f"{type(exc).__name__}: {exc}"[:400]
            row["trace"] = traceback.format_exc()[-1500:]
        row["warnings"] = len(caught)
    return row


def run_check(adapter, library, check, stat, spec):
    """The two ordinary cells first; the degenerate cells only if both give the expected verdict."""
    out = {"library": library, "check": check, "statistic": stat, "ordinary": [], "degenerate": []}
    for which in ("pass", "fail"):
        out["ordinary"].append(run_cell(adapter, check, stat, spec, which))
    out["gate"] = [r["outcome"] for r in out["ordinary"]] == ["pass", "fail"]
    if out["gate"]:
        out["degenerate"] = [run_cell(adapter, check, stat, spec, which) for which in inputs_for(stat)]
    return out


def installed_versions():
    from importlib import metadata
    return sorted({f"{d.metadata['Name']}=={d.version}" for d in metadata.distributions()}, key=str.lower)


def worker(library, out_path):
    results = [run_check(ADAPTERS[library], lib, check, stat, spec) for lib, check, stat, spec in CHECKS if lib == library]
    json.dump({"python": sys.version, "installed": installed_versions(), "checks": results}, open(out_path, "w"), indent=1)


def sha256_of(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def read_labels(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    labels = {}
    for r in rows:
        pid, label = (r.get("pair_id") or "").strip(), (r.get("label") or "").strip().lower()
        if pid in labels:
            raise SystemExit(f"label file: {pid} appears twice")
        labels[pid] = label
    wanted = [p for p, _, _ in pairs()]
    missing = [p for p in wanted if p not in labels]
    bad = [p for p in wanted if p in labels and labels[p] not in ("defined", "undefined", "unsure")]
    if missing or bad or len(labels) != len(wanted):
        raise SystemExit(f"label file is not complete. Missing rows: {missing}. Rows whose label is not defined/undefined/unsure: {bad}. "
                         f"Rows found {len(labels)}, expected {len(wanted)}.")
    return labels


def make_sheet(path):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["pair_id", "what_the_check_computes", "input_it_is_given", "label", "note_optional"])
        for pid, s, i in pairs():
            w.writerow([pid, STATISTICS[s], inputs_for(s)[i], "", ""])
    print("wrote", path, len(pairs()), "rows")


def selftest():
    assert len(CHECKS) == 34 and len({c[0] for c in CHECKS}) == 8 and len({(c[0], c[1]) for c in CHECKS}) == 34
    assert len(pairs()) == 53 and len({p for p, _, _ in pairs()}) == 53
    assert {c[2] for c in CHECKS} == set(STATISTICS)
    assert set(ADAPTERS) == set(PINS) == {c[0] for c in CHECKS}
    n_cells = 0
    for _, _, stat, spec in CHECKS:
        for which in ["pass", "fail", *inputs_for(stat)]:
            cell_data(stat, spec, which)
            n_cells += 1
        if spec and "pass" in spec:
            assert spec["pass"] != spec["fail"]
    spec = NUM_RANGE

    def in_range(check, sp, data):
        return all(v is not None and 1 <= v <= 5 for v in data["x"][1]), ""

    good = run_check(in_range, "stub", "good", "S01", spec)
    assert good["gate"] and [r["outcome"] for r in good["degenerate"]] == ["pass", "fail", "pass"]
    always = run_check(lambda c, s, d: (True, ""), "stub", "always", "S01", spec)
    assert not always["gate"] and always["degenerate"] == []

    def boom(c, s, d):
        raise ValueError("boom")

    broken = run_check(boom, "stub", "broken", "S01", spec)
    assert not broken["gate"] and broken["ordinary"][0]["outcome"] == "error" and broken["degenerate"] == []
    assert [classify(v) for v in (True, False, None, float("nan"), "yes")] == ["pass", "fail", "no_verdict", "no_verdict", "no_verdict"]
    print("selftest passed:", len(CHECKS), "checks,", len(pairs()), "labeled pairs,", n_cells, "cells")


def sh(*cmd, **kw):
    print("$", " ".join(cmd), flush=True)
    return subprocess.run(cmd, **kw)


def driver(a):
    read_labels(a.labels)
    os.makedirs(a.out, exist_ok=True)
    os.makedirs(a.work, exist_ok=True)
    wanted = a.only.split(",") if a.only else list(PINS)
    unknown = [w for w in wanted if w not in PINS]
    if unknown:
        raise SystemExit(f"unknown library: {unknown}")
    labels_hash, harness_hash = sha256_of(a.labels), sha256_of(os.path.abspath(__file__))
    shutil.copyfile(a.labels, os.path.join(a.out, f"e23_labels_used_{labels_hash[:12]}.csv"))
    shutil.copyfile(os.path.abspath(__file__), os.path.join(a.out, f"e23_harness_used_{harness_hash[:12]}.py"))
    out_path = os.path.join(a.out, "e23_outcomes.json")
    merged = json.load(open(out_path)) if os.path.exists(out_path) else {"runs": [], "libraries": {}}
    merged["runs"].append({"libraries": wanted, "labels_sha256": labels_hash, "harness_sha256": harness_hash})
    sh(sys.executable, "-m", "pip", "install", "-q", "uv", check=True)
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTHONHOME", "MPLBACKEND")}
    env["WHYLOGS_NO_ANALYTICS"] = "true"
    for lib in wanted:
        entry = {"pins": PINS[lib], "harness_sha256": harness_hash}
        try:
            venv = os.path.join(a.work, "venv_" + lib)
            py = os.path.join(venv, "bin", "python")
            if not os.path.exists(py):
                sh(sys.executable, "-m", "uv", "venv", "-q", "--python", PYTHON, venv, check=True)
            sh(sys.executable, "-m", "uv", "pip", "install", "-q", "--python", py, *PINS[lib], check=True)
            part = os.path.join(a.work, f"part_{lib}.json")
            if os.path.exists(part):
                os.remove(part)
            sh(py, os.path.abspath(__file__), "--worker", lib, "--out", part, env=env, check=True, timeout=1800)
            entry.update(json.load(open(part)))
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
            entry["library_failed"] = str(exc)[:500]
        if lib in merged["libraries"]:
            merged.setdefault("replaced", []).append({lib: merged["libraries"][lib]})  # nothing is thrown away
        merged["libraries"][lib] = entry
        json.dump(merged, open(out_path, "w"), indent=1)
        report(lib, entry)
    total = [c for e in merged["libraries"].values() for c in e.get("checks", [])]
    print(f"\nchecks that passed the ordinary-input gate: {sum(c['gate'] for c in total)} of {len(CHECKS)}")
    print("done. Send the whole folder:", a.out)


def report(lib, entry):
    """Prints only the gate. Degenerate outcomes are written to the file and not printed."""
    if "library_failed" in entry:
        print(f"[{lib}] FAILED to install or run: {entry['library_failed']}")
        return
    for c in entry["checks"]:
        line = f"[{lib}] {c['check']}: gate {'passed' if c['gate'] else 'FAILED'}"
        if not c["gate"]:
            line += " | " + " | ".join(f"{r['input']}: {r['outcome']} {r['detail'][:160]}" for r in c["ordinary"])
        print(line, flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels")
    ap.add_argument("--out")
    ap.add_argument("--work", default="/content/e23_work")
    ap.add_argument("--only")
    ap.add_argument("--worker")
    ap.add_argument("--make-sheet")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
    elif a.make_sheet:
        make_sheet(a.make_sheet)
    elif a.worker:
        worker(a.worker, a.out)
    else:
        if not (a.labels and a.out):
            ap.error("--labels and --out are required")
        driver(a)


if __name__ == "__main__":
    main()
