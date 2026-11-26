# Pre-registration, v2, addendum 11: E19 (the loader comparison on the benchmark's own data file and domain split)

Written before the benchmark's data file was obtained. The script `v2/scripts/e19_tableshift_own_file.py` has run only on a synthetic frame.

## Question

E13 measured the effect of the loader line that maps a missing completion rate to the label 0, on the official most-recent institution file with random splits. Does the reported gap remain on the benchmark's own file, with the benchmark's domain split and its default model?

## Data

`Scorecard.csv` from the Kaggle dataset `kaggle/college-scorecard`, which the benchmark's loader reads (commit fca9429814). The file stacks several years, so one institution has several rows. We record the SHA-256 of the file used.

## Pipelines

As in the script: the unguarded pipeline keeps every row and applies the verbatim preprocessing function; the guarded pipeline drops rows without a completion rate before splitting. Both use the benchmark's domain split on CCBASIC (the eight listed values are out of domain), with its sizes and random state, and a histogram gradient-boosted classifier with library defaults. The benchmark's label encoding and 100-bin discretization are not reproduced.

## Reported

For accuracy, AUROC and balanced accuracy: the unguarded pipeline's own out-of-domain test value minus the guarded pipeline's own value (reported gap), and the difference between the two models on the same observed-target out-of-domain rows with true labels (true-label gap). 95% intervals come from 2,000 bootstrap resamples of institutions. Also the number of rows, the share without a completion rate, and the number of features used.

## Reading rule and predictions

The same two bounds as E13: a reported AUROC gap above 0.02, and a true-label AUROC gap of at most 0.01. We report each as met or not met, with the number. Accuracy is the benchmark's reported metric, so we also give the accuracy gap; it mixes the label change with a change of base rate. If the script fails on the real file (for example because a column or a category label differs), we record the change we make to it and say so.

## Data handling

The data file is public and stays outside the repository. Only aggregate results are written.
