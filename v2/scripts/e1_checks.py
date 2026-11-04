"""E1 (PREREG_V2_ADDENDUM_1.md): frozen checks, inputs and a priori undefined cells for the executed fuzz of public checkers.

Imported by e1_run.py inside the container. Nothing here reads the results of a run. A check is a (tool, name, callable,
undefined_on) entry: `undefined_on` lists the inputs on which the statistic the check computes is undefined, fixed before the run.
"""
import numpy as np
import pandas as pd

N = 100


def base(rng):
    return pd.DataFrame({"x": rng.normal(5, 1, N), "y": rng.integers(0, 2, N), "p": rng.integers(0, 2, N), "g": rng.integers(0, 2, N)})


def inputs():
    rng = np.random.default_rng(20261104)
    d0 = base(rng)
    out = {"D0_nominal": d0}
    out["D1_empty"] = d0.iloc[0:0].copy()
    d = d0.copy(); d["x"] = np.nan
    out["D2_all_nan"] = d
    d = d0.copy(); d["x"] = 1.0
    out["D3_constant"] = d
    d = d0.copy(); d["y"] = 1
    out["D4_single_class"] = d
    out["D5_one_row"] = d0.iloc[:1].copy()
    d = d0.copy(); d["g"] = 0
    out["D6_single_group"] = d
    d = d0.copy(); d["x"] = np.inf
    out["D7_infinities"] = d
    return out


# ----- Great Expectations (0.18 line, pandas dataset API) -----
def ge(df, method, *args, **kw):
    import great_expectations as ge_
    r = getattr(ge_.from_pandas(df), method)(*args, **kw)
    return bool(r["success"]) if not hasattr(r, "success") else bool(r.success)


# ----- pandera -----
def pandera_range(df):
    import pandera as pa
    schema = pa.DataFrameSchema({"x": pa.Column(float, pa.Check.in_range(0, 10), nullable=False)})
    schema.validate(df, lazy=False)
    return True


def pandera_mean_check(df):
    import pandera as pa
    schema = pa.DataFrameSchema({"x": pa.Column(float, pa.Check(lambda s: s.mean() < 10, element_wise=False), nullable=True)})
    schema.validate(df, lazy=False)
    return True


# ----- fairlearn -----
def fl_dpr(df):
    from fairlearn.metrics import demographic_parity_ratio
    return float(demographic_parity_ratio(df["y"], df["p"], sensitive_features=df["g"]))


def fl_selection_rate(df):
    from fairlearn.metrics import selection_rate
    return float(selection_rate(df["y"], df["p"]))


def fl_fpr(df):
    from fairlearn.metrics import false_positive_rate
    return float(false_positive_rate(df["y"], df["p"]))


# ----- aif360 -----
def aif_di(df):
    from aif360.datasets import BinaryLabelDataset
    from aif360.metrics import BinaryLabelDatasetMetric
    d = df[["y", "g"]].copy()
    ds = BinaryLabelDataset(df=d, label_names=["y"], protected_attribute_names=["g"], favorable_label=1, unfavorable_label=0)
    m = BinaryLabelDatasetMetric(ds, unprivileged_groups=[{"g": 0}], privileged_groups=[{"g": 1}])
    return float(m.disparate_impact())


# ----- scikit-learn reference -----
def sk_auc(df):
    from sklearn.metrics import roc_auc_score
    return float(roc_auc_score(df["y"], df["p"]))


def sk_kappa(df):
    from sklearn.metrics import cohen_kappa_score
    return float(cohen_kappa_score(df["y"], df["p"]))


def sk_precision(df):
    from sklearn.metrics import precision_score
    return float(precision_score(df["y"], df["p"]))


# kind: "verdict" returns True for pass; "value" returns a number
CHECKS = [
    ("great_expectations", "expect_column_mean_to_be_between", "verdict", lambda df: ge(df, "expect_column_mean_to_be_between", "x", 0, 10), {"D1_empty", "D2_all_nan"}),
    ("great_expectations", "expect_column_values_to_be_between_mostly", "verdict", lambda df: ge(df, "expect_column_values_to_be_between", "x", 0, 10, mostly=0.9), {"D1_empty", "D2_all_nan"}),
    ("great_expectations", "expect_column_stdev_to_be_between", "verdict", lambda df: ge(df, "expect_column_stdev_to_be_between", "x", 0, 5), {"D1_empty", "D2_all_nan", "D5_one_row"}),
    ("great_expectations", "expect_column_proportion_of_unique_values_to_be_between", "verdict", lambda df: ge(df, "expect_column_proportion_of_unique_values_to_be_between", "x", 0.0, 1.0), {"D1_empty"}),
    ("pandera", "Check.in_range_nonnull", "verdict", pandera_range, {"D1_empty"}),
    ("pandera", "Check_mean_lt_10", "verdict", pandera_mean_check, {"D1_empty", "D2_all_nan"}),
    ("fairlearn", "demographic_parity_ratio", "value", fl_dpr, {"D1_empty", "D6_single_group"}),
    ("fairlearn", "selection_rate", "value", fl_selection_rate, {"D1_empty"}),
    ("fairlearn", "false_positive_rate", "value", fl_fpr, {"D1_empty", "D4_single_class"}),
    ("aif360", "disparate_impact", "value", aif_di, {"D1_empty", "D6_single_group"}),
    ("scikit-learn", "roc_auc_score", "value", sk_auc, {"D1_empty", "D4_single_class"}),
    ("scikit-learn", "cohen_kappa_score", "value", sk_kappa, {"D1_empty", "D4_single_class"}),
    ("scikit-learn", "precision_score", "value", sk_precision, {"D1_empty"}),
]
