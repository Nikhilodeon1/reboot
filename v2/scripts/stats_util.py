"""Shared helpers for the v2 scripts: exact (Clopper-Pearson) intervals and the normal CDF."""
import math

from scipy.stats import beta


def clopper_pearson(k, n, alpha=0.05):
    if n == 0:
        return (0.0, 1.0)
    lo = 0.0 if k == 0 else float(beta.ppf(alpha / 2, k, n - k + 1))
    hi = 1.0 if k == n else float(beta.ppf(1 - alpha / 2, k + 1, n - k))
    return (round(lo, 4), round(hi, 4))


def phi(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))
