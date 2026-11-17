# Pre-registration, v2, addendum 6: E15 (outside human coding of reachability sites)

Written before the sample is drawn and before any label is returned.

## E15. A person outside the author group codes 40 of the 88 reachability sites

**Question.** How do the labels of a person outside the group, with no language-model check, compare with ours on the sites behind the external Type 1 counts (4 of 48 narrow, 16 of 48 broad)?

**Coder.** One person outside the author group with Python and machine-learning experience. They use no language model and do not see any of our labels or any rater's labels. They receive the committed rubric (RUBRIC_4C.md, reproduced in the sheet), the code at each site with the matched lines marked, and the repository at the pinned commit if they want more context. No name is recorded.

**Sample.** Stratified by our registered label (numpy seed 20261116): all 16 sites labelled REACHABLE_UNGUARDED, 12 of the 32 labelled GUARDED or UNREACHABLE, and 12 of the 40 labelled NOT_APPLICABLE; 40 in all. The order is shuffled with a fixed seed and our labels are hidden. The sampling record and the key stay outside the repository until the labels are in.

**Reported.** (1) Per stratum, the number of sites on which the coder agrees with us, with exact intervals. (2) Cohen's kappa on the four-label scale with each site weighted by its stratum size over its sample size (1, 32/12 and 40/12), and a cluster-free bootstrap interval over sites. (3) Agreement on the binary question reachable and unguarded against everything else. (4) The counts of REACHABLE_UNGUARDED among applicable sites under the coder's labels, scaled to the 88 by the stratum weights, for the narrow and broad readings of the paper. We do not adjudicate disagreements. Every disagreement is listed in the appendix, and a second reading by us is reported separately and labelled as ours.

**Reading rule, fixed now.** A weighted kappa of 0.60 or more reads as agreement with our labels at the line registered for the model raters. A value below 0.60 reads as rubric dependence, as for the model raters. Whatever the value is, it is reported.

**Pre-stated prediction.** The coder labels at least 8 of our 16 positives REACHABLE_UNGUARDED. This is a guess from the range across the four model raters (3 of 61 to 21 of 64) and is not a decision rule.

**Data handling.** The sheet contains public code at pinned commits. Nothing from patient data is involved.
