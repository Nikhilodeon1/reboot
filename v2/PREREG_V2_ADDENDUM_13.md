# Pre-registration, v2, addendum 13: E22 (a decidability state added to copies of the detectors)

Written before the patched copies were written or run. The detectors in `detectors/checks/` are not edited. The copies live in `v2/patched_detectors/`. The authors approved patching copies after the executed test (E17) was reported.

## Question

Can the silent passes found by E17 be removed by a small guard that returns an explicit undecidable result, without changing any verdict on a defined input?

## The patch rule

Each guard returns a value, UNDECIDABLE, that raises an error if it is used as a true or false value, so that a caller cannot read it as clean by accident. The guards follow the undefined mapping of addendum 9:

- Detector 1: empty audits, an audit entry that is not finite, and chance agreement equal to 1. Unequal lengths keep raising.
- Detector 2: fewer than 3 values, a value that is not finite, and a standard deviation at or below 1e-12.
- Detector 3: no change, since it already errors or abstains on its undefined cells.
- Detector 4: a dataset that is not in the lineage table, and a constraint input with no lineage entry for the dataset. An unknown constraint keeps raising.
- Detector 5: a group with no stay that has a finite component value, and any component value that is not finite.

## What this can and cannot show

The guards are written with the E17 cells known. A second run of E17 on the copies is therefore not independent evidence that the guards find undefined inputs in general. It checks only that the patch does what the rule says.

## Checks and reporting

1. The E17 cells, with the same inputs and seed, on the copies: for each detector the number of undefined cells that end in error, abstain, flag or clean, where UNDECIDABLE counts as abstain, and whether each defined cell keeps its outcome.
2. Equivalence on random defined inputs, seed 20261202: 10,000 audit pairs for detector 1 (sizes 20 to 600, agreement drawn at random), 10,000 vectors for detector 2 (3 to 10 values), every dataset and constraint pair in the shipped table for detector 4, and 2,000 random pairs of stay groups for detector 5. Wherever the copy does not return UNDECIDABLE, its output must equal the original's. We report the number of inputs, the number on which the copy returns UNDECIDABLE, and the number of disagreements.
3. The number of added and removed lines in each copy.
4. Any shipped positive or negative case whose verdict changes. We expect one: detector 2's 0% control compares an arm with itself, so its relative changes are all 0 and the copy must return UNDECIDABLE where the original returns clean.

## Reading rule

The patch is reported as sufficient for the E17 cells if no undefined cell ends clean, every defined cell keeps its outcome, and there is no disagreement on the random inputs.
