"""Standard evaluation checks, returning (flagged, decidable).

  kfold_cv_instability  source k-fold AUROC sd > KFOLD_SD_FLAG
  train_test_gap        in-domain minus cross-site AUROC > GAP_FLAG
  external_floor        cross-site AUROC < FLOOR_FLAG

Thresholds fixed, not tuned per scenario.
"""
import numpy as np

# conventional thresholds
KFOLD_SD_FLAG = 0.05
GAP_FLAG = 0.05
FLOOR_FLAG = 0.70


# Undefined metric -> decidable=False. Never scored as a silent pass.
def _ok(*vals):
    return all(v is not None and not np.isnan(v) for v in vals)


def kfold_cv_instability(metrics):
    """k-fold CV AUROC sd on the source only."""
    v = metrics.get("kfold_sd")
    if not _ok(v):
        return False, False
    return bool(v > KFOLD_SD_FLAG), True


def train_test_gap(metrics):
    """In-domain minus cross-site AUROC. Fires only on degradation."""
    a, b = metrics.get("indomain_auroc"), metrics.get("target_auroc")
    if not _ok(a, b):
        return False, False
    return bool((a - b) > GAP_FLAG), True


def external_floor(metrics):
    """Absolute floor on cross-site AUROC."""
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
    """Rank-based AUROC; nan when only one class is present."""
    y = np.asarray(y_true, dtype=float)
    s = np.asarray(scores, dtype=float)
    pos, neg = (y > 0.5), (y <= 0.5)
    n_pos, n_neg = int(pos.sum()), int(neg.sum())
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    order = np.argsort(s, kind="mergesort")
    ranks = np.empty(len(s), dtype=float)
    ranks[order] = np.arange(1, len(s) + 1, dtype=float)
    # average tied ranks
    _, inv, counts = np.unique(s, return_inverse=True, return_counts=True)
    sums = np.zeros(len(counts))
    np.add.at(sums, inv, ranks)
    ranks = (sums / counts)[inv]
    return float((ranks[pos].sum() - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))
