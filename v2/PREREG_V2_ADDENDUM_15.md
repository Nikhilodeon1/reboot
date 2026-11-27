# Pre-registration, v2, addendum 15: model seeds for the loader comparisons (E19b, and E21)

Written after a reproduction check of E19 and before E19b or E21 was run.

## What the check found

Rerunning the E19 script on the same file did not return the committed numbers: 30 reported values differ, including the reported AUROC gap (-0.0078 committed, -0.0051 on the rerun) and the true-label AUROC gap (-0.0358 and -0.0335). Neither of E19's two bound readings changed. The script fits `HistGradientBoostingClassifier` with library defaults and no `random_state`. We attribute the difference to this: with the default early-stopping setting and a training set of this size, the library holds out a random validation subset, so two fits on the same rows can differ. E13 and E13b pass a seed to the model, and their reruns returned the committed values.

## E19b

The E19 script is run unchanged, ten times, with the model constructor given `random_state` 0 to 9. Splits, features, labels, bootstrap and bootstrap seed are E19's. For each reported quantity we give the median of the ten point estimates and their minimum and maximum. We say that an interval excludes zero only if it does so, on the same side, in all ten runs. For each of the two bounds we give the number of seeds that meet it, and the bound is read as met if the median meets it. We also record, for each seed, the number of boosting iterations of each model.

## E21

E21 fits both models once for each `random_state` from 0 to 9 on the same splits, and is summarized in the same way. The reading rule of addendum 12 applies to the medians. Addendum 12's rule for a disagreement between E21 and E19 now compares E21 with E19b.

## What happens to the E19 numbers

The single unseeded run stays in the ledger, marked as not exactly reproducible. The paper will report E19b or E21 in its place and say that the reproduction check led to the change.
