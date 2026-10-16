







import numpy as np


KFOLD_SD_FLAG = 0.05
GAP_FLAG = 0.05
FLOOR_FLAG = 0.70



def _ok(*vals):
    return all(v is not None and not np.isnan(v) for v in vals)


def kfold_cv_instability(metrics):

    v = metrics.get("kfold_sd")
    if not _ok(v):
        return False, False
    return bool(v > KFOLD_SD_FLAG), True


def train_test_gap(metrics):

    a, b = metrics.get("indomain_auroc"), metrics.get("target_auroc")
    if not _ok(a, b):
        return False, False
    return bool((a - b) > GAP_FLAG), True


def external_floor(metrics):

    v = metrics.get("target_auroc")
    if not _ok(v):
        return False, False
    return bool(v < FLOOR_FLAG), True


BASELINES = {
    "kfold_cv_instability": kfold_cv_instability,
    "train_test_gap": train_test_gap,
    "external_floor": external_floor,
}


def auroc(y_true, scores):

    y = np.asarray(y_true, dtype=float)
    s = np.asarray(scores, dtype=float)
    pos, neg = (y > 0.5), (y <= 0.5)
    n_pos, n_neg = int(pos.sum()), int(neg.sum())
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    order = np.argsort(s, kind="mergesort")
    ranks = np.empty(len(s), dtype=float)
    ranks[order] = np.arange(1, len(s) + 1, dtype=float)

    _, inv, counts = np.unique(s, return_inverse=True, return_counts=True)
    sums = np.zeros(len(counts))
    np.add.at(sums, inv, ranks)
    ranks = (sums / counts)[inv]
    return float((ranks[pos].sum() - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))
