# Pre-registration, v2, addendum 17: E23 dependency versions

Written before E23 was run: no output from it had been received. The checks, inputs, labels, gate, outcomes and analysis of addendum 16 are unchanged.

## Change

Addendum 16 pins each library's version and leaves most of its dependencies open. We resolved every environment without installing it (`uv pip compile` for Linux and Python 3.11, with source builds disabled). Left open, two libraries would receive a major version of a dependency that appeared after their own release: patito 0.8.6 (released February 2026) would receive polars 2.2.0, and NannyML 0.13.1 (released July 2025) would receive pandas 3.1.1. A failure from that pairing would say nothing about the check.

Each environment is now resolved as of 30 days after the release of its library on PyPI (the dates are the constant `AS_OF` in `v2/scripts/e23_battery.py`). Where 30 days after the release is still in the future, the date has no effect. The version limits already written in addendum 16's harness (`pandas<3`, `numpy<2`) stay. All eight environments resolve under this rule.

## E21

The pinned Python 3.8 environment of addendum 14 also resolves, and no change is made to it.
