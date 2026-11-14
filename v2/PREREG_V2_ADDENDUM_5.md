# Pre-registration, v2, addendum 5: E13 (guarded against unguarded College Scorecard pipeline) and E14 (equivalence sample of mutation survivors)

Written before either run, in response to a second mock review. Both are exploratory in the sense that neither was in an earlier plan; both are fixed
here before any output exists.

## E13. Guarded against unguarded pipeline

**Question.** The earlier consequence study compared two test subsets of one model trained on the unguarded labels. What does the unguarded line cost a
user compared with the same pipeline with the missing targets dropped?

**Design.** Official most-recent institution file, same features, same five random 70/30 splits (random_state 0 to 4) and same model (histogram
gradient boosting, random_state = split seed) as E12. Unguarded: the shipped line, every row kept, missing target = 0. Guarded: rows with a missing
target dropped, model trained and tested on the observed rows. Reported per pipeline on its own test set (accuracy, balanced accuracy, AUROC). In
addition both models are scored on the observed-target test rows against their true labels.

**Reported.** Mean of the unguarded minus guarded difference over the five splits, with a t-interval (df 4), for the reported metrics ("reported gap")
and for the true-label scores ("true-label gap"). Aggregates only.

**Pre-stated predictions.** (a) The unguarded pipeline reports a higher AUROC than the guarded one (reported gap above 0.02). (b) On observed-target rows
the unguarded-trained model is not better than the guarded-trained model (true-label gap in AUROC at most 0.01). Neither prediction is a registered
decision rule; the result is reported whichever way it falls. This remains a stand-in model on the official file and not the benchmark's own file.

## E14. Equivalence sample of mutation survivors

**Question.** How many of the 88 survivors on decision lines (E6 triage) are equivalent mutants (no observable behaviour change)?

**Design.** A random sample of 25 of the 88 surviving mutants on decision lines (numpy seed 0, sorted by mutant id), drawn by the script
`v2/scripts/e14_equivalence_sample.py`. Each is read and assigned one of three labels by reading the mutated line in its function and, where needed,
running the function on a small input: equivalent (no input changes the output), non-equivalent (some input changes the verdict, statistic or
printed number), or undecided. No label is revised after the other mutants are read, and undecided counts as non-equivalent in the main number.

**Reported.** Counts of each label with exact Clopper-Pearson intervals, and the implied range for the number of non-equivalent survivors among
the 88 (interval endpoints times 88). The kill rate on decision lines is then reported with and without the estimated equivalent mutants.
