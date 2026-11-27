# Pre-registration, v2, addendum 16: E23, degenerate inputs to checks of libraries not read in this project

Written before any of the libraries below was installed or run, and before any label was given.

## Question

E17 gave our own five detectors degenerate inputs. Does the same thing, a passing verdict on an input for which the check's quantity has no value, occur in verdict-emitting checks that other groups wrote and that we had not read?

## Libraries and checks

Eight libraries, 34 checks: pointblank 1.3.0 (8), frictionless 5.21.0 (6), cuallee 0.15.4 (5), NannyML 0.13.1 (5), patito 0.8.6 (4), dataframely 3.1.3 (3), whylogs 1.6.4 (2), datacompy 1.2.0 (1). The list of checks, their configurations and their ordinary data are the constant `CHECKS` and the adapters in `v2/scripts/e23_battery.py`.

How they were chosen. A language-model assistant that works on this study proposed widely used Python libraries for data validation, data comparison and drift monitoring. They are not a random sample, and no statement about how common any behavior is will be made from them. Left out because their code or behavior had already been read or run in this project: Great Expectations, pandera, Fairlearn, AIF360, scikit-learn, Deepchecks, Evidently, DomainBed, fairseq2, robustdg and TableShift. A check is included if the library declares or allows Python 3.11 and its documentation names the check and shows how it is configured, or gives its signature. Dropped for documentation reasons: alibi-detect (documentation site not reachable) and aequitas (no documented code that reads a verdict).

## What was read, and what could not be controlled

The harness was written from reports of the documentation pages and package index entries. The assistants that read those pages were told not to open source code, tests or issue trackers, and not to report how a check behaves on empty, missing or constant input. The harness was written by a language model, which may have seen some of these libraries in its training data and could carry knowledge of their behavior into the choice of checks or inputs. We cannot rule this out. The input classes are fixed by the kind of statistic, not chosen per check, which limits that room.

## Inputs

Checks of one table get three degenerate inputs: no rows; 20 rows with every value of the checked column missing; one row with an ordinary value. Two-sample drift checks get four: new sample with no rows; new sample with every value missing; reference and new sample both constant and identical; new sample of one row. The table comparison gets four: both tables empty; one empty; no id in common; compared column entirely missing in both. This gives 53 pairs of statistic and input, and 108 degenerate cells over the 34 checks. The frictionless adapter adds a constant second column to every table, so that a row with a missing value is not rejected as a blank row.

## Labels

One author of the study labels each of the 53 pairs as `defined`, `undefined` or `unsure` from `v2/battery/e23_label_sheet.csv`, which names no library and no outcome. `undefined` means that the number or rule the check computes has no value, or no meaningful truth value, on that input. `defined` means that it has one, whether the right verdict would be pass or fail. The labeler uses no language model or other assistant for the labels. There is no second labeler. The labeler knows the hypothesis of the paper and has seen the E17 results on our own detectors, so the labels are not blind to the hypothesis. They are given before any E23 run. The harness refuses to start without a complete label file, records its SHA-256 in the output with every run, and does not use the labels to decide what to run.

## Gate

Each check first receives one ordinary input that should pass and one that should fail. Its degenerate cells run only if both verdicts are as expected, in the same run. For a check that fails the gate, the adapter may be changed using the output of its two ordinary cells only, and the check is run again with `--only`; every change is committed and listed with the result. Earlier runs are kept in the output file. A check that cannot be made to pass the gate is reported as excluded, with the reason. A library that cannot be installed is reported as such. Library versions are not changed to obtain a different degenerate outcome.

## Outcomes

`pass`: the check reports success, or for a drift check no alert on any chunk of the new sample, with at least one chunk. `fail`: it reports failure or an alert. `no_verdict`: it returns nothing usable (no value, a missing alert flag, no result row). `error`: an exception other than the library's documented way of reporting failure. For patito the documented failure signal is `DataFrameValidationError`. The pages read did not give dataframely's failure signal; the adapter treats any exception whose class name contains `ValidationError` as a failure. A drift check is read from the documented per-chunk alert flag with the library's default chunking and thresholds.

A silent pass is a `pass` on a cell labeled `undefined`.

## Reported

The check is the unit. Primary: of the checks that pass the gate and have at least one cell labeled `undefined`, how many have at least one silent pass; the same per library; and the number of libraries with at least one. Also the counts of the four outcomes over cells, separately for each label, the list of silent-pass cells, the excluded checks, and the same primary count with `unsure` treated as `undefined`. No interval is attached to a proportion, because checks within a library are not independent and the libraries are not a sample. After the run, for each silent-pass cell we read the library's documentation and report whether the behavior is stated there. A silent pass is a statement about this configuration at these versions; it is not a claim that the library has a defect.

## Reading rule

The result is reported in the main text whatever it is, including if no check has a silent pass, in which case the paper says that the pattern seen in our own detectors did not appear in this set.

## Environment and analysis

Google Colab CPU runtime, one isolated Python 3.11 environment per library, pinned library version, installed package list written to the output. The analysis is `v2/scripts/e23_analyse.py`, committed with this addendum and checked on made-up outcomes.
