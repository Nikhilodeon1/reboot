# Pre-registration, v2, addendum 1: E2, E12 and E1

Committed before the data for these three experiments are downloaded or any script is run. It extends `PREREG_V2.md` (section 1, commit
829a11c). Same general rules: no detector or threshold of ours is edited; third-party functions are executed verbatim from the pinned
commit or the pinned package version; only aggregates are written under `v2/results/`; intervals for proportions are exact
Clopper-Pearson 95%; a deviation is declared in a later addendum before the affected run.

Data (public, named before download): ACS 2018 1-year person files from `www2.census.gov/programs-surveys/acs/data/pums/2018/1-Year/`
for AK, ND, NH, NM, RI, VT, WY (1.4, 1.6, 2.6, 3.6, 2.1, 1.3, 1.2 MB zipped) and NY (35 MB); UCI Adult `adult.data` and `adult.names`;
the ProPublica `compas-scores-two-years.csv` (2.5 MB); the College Scorecard Most Recent Institution-Level Data file (24 MB zipped,
`collegescorecard.ed.gov/data/`). Downloads land outside the repository; only aggregates enter it.

## E2. A public family of near-threshold verdicts (the four-fifths rule)

**Question.** Among public (dataset, outcome, group contrast) cases, how many have a four-fifths verdict that sits within three audit
standard deviations of its threshold at realistic audit sizes?

**Cases, frozen.** ACS: states AK, ND, NH, NM, RI, VT, WY, NY; outcomes O1 `PINCP > 50000` (age 16 or over), O2 employed (`ESR` in
1, 2, 4, 5; age 16 to 64), O3 insured (`HICOV` = 1; all ages), O4 bachelor's degree or higher (`SCHL` >= 21; age 25 or over);
contrasts C1 `SEX` 2 against 1, C2 `RAC1P` 1 against 2, C3 `RAC1P` 1 against 6, C4 `HISP` not 1 against 1. That is 8 x 4 x 4 = 128
cases. Adult (outcome income above 50K): sex, White against Black, White against Asian-Pac-Islander (3 cases). COMPAS: outcome
`score_text` not equal to Low and outcome `two_year_recid`, each for African-American against Caucasian (2 cases). Total 133 cases.

**Statistic and rule.** R = min(rate_a, rate_b) / max(rate_a, rate_b), the ratio of the lower selection rate to the higher; flag if R < 0.8.
Undecidable if either group has no member in the audit draw or the larger rate is 0; counted separately and never as clean.

**Procedure.** Population value theta* = R on the full file (unweighted). Audit sizes n in {250, 500, 1000}. For each case and size, 2000 audit
draws without replacement (numpy `default_rng`, seed 70000 + 1000 * case_index + size_index). Record the flag rate p_n with an exact
interval over the decidable draws, the audit-draw SD sigma_n of R, the margin m_n = |0.8 - theta*| / sigma_n and the undecidable share.
A case is skipped at a size if its file has fewer than 4 n rows.

**Reported, descriptive, no hypothesis test.** At each n: the number of cases with m_n <= 3 and with 0.05 <= p_n <= 0.95, each out of the
decidable cases with an exact interval; the ten cases closest to the threshold; the cases whose population verdict (theta* < 0.8) differs
from the majority flag; the undecidable share by case. The sentence we may write if any case has m_500 <= 3 is that such external cases
exist, with the count. This experiment measures the statistical mechanism of Type 2 (a verdict decided by a margin smaller than the
audit's resolution). It does not test the clause of Definition 3 about two interchangeable implementations, and the paper says so.

**Where.** Local CPU. Script `v2/scripts/e2_public_thresholds.py`.

## E12. Consequence studies on four sites in other groups' code

Sites are the four reachable and unguarded sites under the narrow reading (round-1 ledger A2-4c-positives). Each is run from the verbatim
function text at the pinned commit; the effect is classified in advance as: no effect; effect on the data or a count but not on a reported
metric; effect on a reported metric.

**S1. tableshift `preprocess_college_scorecard` (fca9429814).** The function maps the target as `(df[C150_4] > 0.5).astype(int)`, and the
benchmark configuration for this dataset sets `dropna=None`, so a missing target becomes 0. Data: the College Scorecard Most Recent
Institution-Level file (the benchmark's own source is a Kaggle file that needs a login; this is a deviation, declared here). Report the
number of institutions, the number with a missing `C150_4`, and the label balance with and without the missing rows. Effect on a reported
metric: train scikit-learn `HistGradientBoostingClassifier` (default settings, categorical columns label-encoded) on the feature columns
of the TableShift feature list that exist in the file, with 5 random 70/30 splits (seeds 0 to 4) and with the benchmark's CCBASIC domain
split; report test accuracy for a model trained on the unguarded labels and scored (a) on unguarded test labels, which is what the
benchmark reports, and (b) on test rows with an observed target only. The difference (a) minus (b) with a t-interval over seeds is the
effect. Classes: negligible below 0.5 accuracy points, small from 0.5 to 2, material above 2 (fixed now).

**S2. fairseq2 `filter_by_min_max` (line 288) and `filter_list_with_min_max_length` (line 306), 7f06d6f4f5.** The functions return the input
table unchanged if `pc.all(mask)` is true and otherwise call `table.filter(mask)`. Null list rows give a null mask entry, which `pc.all`
ignores and `table.filter` drops. Run on synthetic pyarrow tables of 10,000 rows with 0%, 1% and 5% null list rows, once with every
non-null row passing and once with one failing row added. Report rows returned and null rows returned in each case. Packages `pyarrow`,
`polars` installed in a container at pinned versions.

**S3. robustdg `utils/scripts/utils.py` line 579 (3eee1730ae).** `loss_val = max(loss_tr, loss_te)` followed by `np.isfinite(loss_val)`.
Run the two verbatim lines for the four cases (train NaN, test finite), (train finite, test NaN), (both NaN), (train finite, test inf) and
report whether `diverged` is set.

**Scope statement fixed now.** S2 and S3 execute the code on inputs the code is meant to receive and show what it returns; they are not
reports of an incident. S1 is the only one that measures an effect on a reported metric. The paper says which class each site is in.

**Where.** S1 local CPU; S2 and S3 in a container. Script `v2/scripts/e12_consequences.py` and `v2/docker/e12/`.

## E1. Executed fuzz test of public checkers on degenerate inputs

**Question.** When a public data or fairness checker is given an input on which its statistic is undefined, does it return a pass, a
fail, an error, or an explicit undefined?

**Tools, frozen, installed once in a container (Python 3.11) at the versions pip resolves on the day of the run, recorded by `pip freeze`:**
`great-expectations`, `pandera`, `deepchecks`, `fairlearn`, `aif360`, with `scikit-learn` as a reference that is expected to raise.
After installation the run uses `--network none`.

**Checks, frozen (the calls and their a priori undefined inputs are in `v2/scripts/e1_checks.py`, committed before the run).** For each
tool, three to five built-in checks whose statistic is a mean, a ratio or a proportion, for example `expect_column_mean_to_be_between`,
`expect_column_values_to_be_between` with `mostly`, `expect_column_proportion_of_unique_values_to_be_between`, a pandera `Check` with a
`Column`, the deepchecks conditions that can run on one dataset, `demographic_parity_ratio` and `selection_rate` in fairlearn, and
`disparate_impact` in aif360.

**Inputs, frozen.** D1 empty table (0 rows), D2 all-NaN numeric column, D3 constant column, D4 single-class labels, D5 one-row table,
D6 single sensitive group, D7 column of infinities.

**Outcome per (tool, check, input), assigned by code from the return value and any exception or warning:** PASS (reports success, no
warning), FAIL, ERROR (raises), UNDEFINED_REPORTED (returns NaN or None or emits an explicit warning that the statistic is undefined).
A cell is a vacuous-pass candidate if the a priori mapping says the statistic is undefined on that input and the outcome is PASS. For
each candidate, a person reads the tool's documentation and records whether it states this behaviour (documented or undocumented).

**Reported.** Counts per tool of cells by outcome; vacuous-pass candidates out of the cells with an undefined statistic, with exact intervals;
the documented and undocumented split. Positives go to the maintainer notes. The result is a measurement of behaviour, not a claim that
any tool is wrong; a documented vacuous pass is reported as documented.

**Where.** Local Docker. Scripts `v2/scripts/e1_checks.py` and `v2/scripts/e1_run.py`, `v2/docker/e1/Dockerfile`.

## Addendum 1b (declared before any E12 run): deviations for S1

Committed before S1, S2 and S3 run. The benchmark's own College Scorecard source is a Kaggle file that needs a login, so S1 uses the
official most-recent institution file. Three consequences are declared now. (i) The official file has numeric `CCBASIC` codes and no
text labels, so the benchmark's `CCBASIC` domain split cannot be reproduced. S1 uses a domain split on `CONTROL` instead (out of
domain: private for-profit institutions, `CONTROL` = 3; in domain: the rest, split 70/30 within domain), and also the 5 random splits.
(ii) Feature columns are the TableShift feature names that exist in the official file; the others are listed in the result. (iii) Numeric
features are left raw for `HistGradientBoostingClassifier` (the benchmark discretizes them into 100 bins). The effect measured is the
difference in test accuracy between scoring on the unguarded labels and on observed-target rows only, as written above. S1 therefore
measures the effect of the line on this file with a stand-in pipeline, not a reproduction of a number published by TableShift.

## Addendum 1c (declared before any E1 run): tools and versions for E1

Committed with `v2/scripts/e1_checks.py` and `e1_run.py` before the run. The frozen list is `great-expectations` (the 0.18 line, whose
pandas dataset API is stable), `pandera`, `fairlearn`, `aif360` and `scikit-learn` as the reference, with `pandas<2.2`; other packages are
resolved by pip on the day and recorded by `pip freeze`. `deepchecks` is dropped from the list: its checks need paired train and test data,
so a single-dataset degenerate input is not comparable. Inputs D1 to D7 and a nominal input D0 (every check must succeed on D0, or the check
is reported as not working and excluded). The a priori undefined cells are the `undefined_on` sets in `e1_checks.py`. The cell count is
13 checks x 8 inputs = 104 cells, of which 7 inputs x 13 = 91 are fuzz cells.
