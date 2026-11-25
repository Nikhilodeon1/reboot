# Pre-registration, v2, addendum 9: E17 (executed degenerate-input test of the five detectors)

Written before the harness ran. The author read the detector code first (to find each detector's entry point and its input types), so the outcomes below are not blind. What is fixed here is the input list, the classification of each input as undefined or defined for the statistic, and the outcome classes. No detector file is edited, and the harness imports each detector read-only.

## Question

For inputs on which a detector's statistic is undefined, does the detector return an error, abstain, flag, or return a clean verdict? A clean verdict on an undefined input is a silent pass, which is Type 1a at the level of the detector's own entry point.

## Cells

Each cell is a (detector, input) pair. Inputs are synthetic and small, no credentialed data is read, and the inputs are generated with numpy seed 20261126.

Detector 1, `diagnose` (arguments: two label arrays for the sites and two audit arrays): nominal agreement (n = 100, 5 disagreements; defined), nominal disagreement (n = 100, 40 disagreements; defined), empty audits (undefined), one row with equal labels (undefined, because the expected agreement is 1), one row with different labels (defined), constant equal arrays of ones (undefined), constant equal arrays of zeros (undefined), audit arrays containing NaN (undefined), audit arrays of unequal length (undefined).

Detector 2, `flag_from_relative` (argument: a vector of per-seed relative changes in held-out loss): nominal flag (five values near -0.05 with spread; defined), nominal null (five values around 0; defined), strong positive effect with the wrong sign (five values near +0.05; defined), empty (undefined), one value (undefined), two values (undefined, because the detector's own rule treats fewer than 3 as unusable), five identical negative values (undefined, because the standard deviation is 0), five zeros (undefined), a NaN entry (undefined), an infinite entry (undefined).

Detector 3, `audit_file` followed by `verdict_for_file` (argument: a Python source file): the buggy fixture (defined, expected contaminated), the fixed fixture (defined, expected ok), an empty file (undefined), a file with no function (undefined), a file with a syntax error (undefined), a file containing a null byte (undefined), a file with invalid UTF-8 (undefined), a sweep whose evaluation loader has an unknown name (undefined).

Detector 4, `is_circular` (arguments: dataset, constraint, lineage): PhysioNet with the Severinghaus constraint (defined, expected circular), MIMIC-IV with the MAP constraint (defined, expected not circular), an unknown dataset name (undefined), an unknown constraint name (undefined), an empty lineage table (undefined), an empty dataset name (undefined).

Detector 5, `run_check_on_stays` (arguments: two lists of per-stay component dictionaries): two identical nominal groups (defined, expected clean), a nominal pair constructed so that one group lacks two components (defined, expected flag if the rule fires; the construction is adjusted before the run until this sanity cell flags, and the adjustment is not counted as a result), both groups empty (undefined), one group empty (undefined), stays with no components (undefined), components that are all NaN (undefined), one stay per group (defined).

## Outcome classes

- error: the call raises an exception.
- abstain: the detector returns an explicit indeterminate verdict (only detector 3 has one, the string INDETERMINATE).
- flag: the verdict is positive.
- clean: the verdict is negative and the call returns normally.

Additional returned values (a NaN statistic, an infinite critical value) are recorded but do not change the class. A warning raised during the call is recorded.

## Reported

For each detector, the number of undefined cells and how many fall in each class. A silent pass is an undefined cell with outcome clean. The table of all cells goes in an appendix. We also report the same count for the 13 public checks of E1 (5 of 22 undefined cells passed or returned a finite value without a warning), so that the two sets are read side by side. Cells are not pooled across detectors into one rate, because the cells within a detector are correlated.

## Pre-stated reading rule

A detector with at least one silent pass on an undefined cell has a Type 1a path at its entry point. A detector whose undefined cells all end in error or abstain does not. Which of the two a user wants is a design choice, and an error that stops a run is as acceptable as an abstention.

## Data handling

No patient-level data is used. The results file holds the outcome class, the returned values and the warning flag for each cell.
