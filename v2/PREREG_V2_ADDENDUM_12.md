# Pre-registration, v2, addendum 12: E21 (the loader comparison run with the benchmark's own code)

Written before the benchmark's code was run. E19 reconstructed the benchmark's domain split and default model from its source and did not reproduce its label encoding or discretization. This experiment runs its pipeline.

## Question

Does the benchmark's own pipeline, run on its own data file, give the label 0 to rows without a completion rate, and what changes when those rows are removed from the input file?

## Setup

The author of this study runs `v2/scripts/e21_tableshift_run.py` in a Google Colab CPU runtime, because third-party code is not run on the analysis machine. The script clones the benchmark repository and checks out commit fca9429814703a07e3902d005d46563a207b7f0a. The repository pins old package versions that do not install on a current runtime, so the script installs, unpinned, only the packages that its module-level imports need, and writes the full package list to the output. One method is overridden at run time: the Kaggle data source's download step, which requires an account token even when the file is already present. The file `Scorecard.csv` is the one used in E19, and the script checks its SHA-256.

The dataset is obtained with the benchmark's `get_dataset("college_scorecard")`, with its splitter, preprocessing configuration, label encoding and discretization. The model is a histogram gradient-boosted classifier with library defaults, which is what the benchmark's `histgbm` option builds when no parameters are passed.

- Unguarded: the file as distributed.
- Guarded: the same file with the rows that have no completion rate removed before the pipeline reads it, every other field unchanged. No benchmark code differs between the two.

## Checks before any metric

The script stops if the unguarded dataset does not have one row per input row, or if its target column differs on any row from `completion rate > 0.5` computed from the input file (and the same for the guarded dataset). These checks confirm that rows are aligned.

## Gate

If the unguarded pipeline's training split contains no row without a completion rate (that is, the pipeline removes them somewhere), the paper deletes the loader claim.

## Reported

The number of rows, the number without a completion rate in each split, and the label they receive. For accuracy, AUROC and balanced accuracy on the out-of-domain test split of each pipeline: unguarded minus guarded (reported gap), and the same on the in-domain test split. True-label gap: both models scored on the same out-of-domain test rows of the unguarded split that have a completion rate, each with its own pipeline's encoding of those rows. Rows out of domain are never in either training split. 95% intervals are percentile bootstraps over institutions (2,000 resamples).

## Reading rule

E19's two bounds are carried over: a reported out-of-domain AUROC gap above 0.02, and a true-label AUROC gap of at most 0.01. Each is reported as met or not met. This run replaces E19 as the paper's primary loader result whatever it shows. If E21 and E19 differ in the sign of a gap whose interval excludes zero in either, the paper reports both.

## If the run fails

If the benchmark code does not run on the current runtime, we record every change needed to make it run. A change that alters preprocessing, splitting or the model ends the claim that the benchmark's own pipeline was run.

## Data handling

The data file is public. Only aggregate results are written.
